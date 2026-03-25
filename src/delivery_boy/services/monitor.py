from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from telegram.error import RetryAfter

from delivery_boy.models import ChannelConfig, ParsedPost
from delivery_boy.services.forwarder import TelegramForwarder
from delivery_boy.storage.repository import Repository
from delivery_boy.telegram_web.client import TelegramWebClient


class ChannelMonitor:
    def __init__(
        self,
        channels: list[ChannelConfig],
        repository: Repository,
        telegram_web_client: TelegramWebClient,
        forwarder: TelegramForwarder,
        max_posts_per_channel: int,
        first_run_max_posts_per_channel: int,
        send_delay_seconds: float,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._channels = channels
        self._repository = repository
        self._telegram_web_client = telegram_web_client
        self._forwarder = forwarder
        self._max_posts_per_channel = max_posts_per_channel
        self._first_run_max_posts_per_channel = first_run_max_posts_per_channel
        self._send_delay_seconds = send_delay_seconds
        self._lock = asyncio.Lock()

    async def run_once(self) -> None:
        if self._lock.locked():
            self._logger.info("Previous monitoring cycle is still running, skipping overlap.")
            return

        async with self._lock:
            self._logger.info("Monitoring cycle started.")
            total_sent = 0

            for channel in self._channels:
                total_sent += await self._process_channel(channel)

            self._logger.info("Monitoring cycle finished. sent_messages=%s", total_sent)

    async def _process_channel(self, channel: ChannelConfig) -> int:
        self._logger.info("Checking channel=%s", channel.username)

        try:
            posts = await self._telegram_web_client.fetch_posts(channel.username)
        except Exception:
            self._logger.exception("Channel check failed for channel=%s", channel.username)
            return 0

        channel_state = self._repository.get_channel_state(channel.username)
        recent_posts = posts[-self._max_posts_per_channel :]
        if channel_state.last_successful_check is None and len(recent_posts) > self._first_run_max_posts_per_channel:
            recent_posts = recent_posts[-self._first_run_max_posts_per_channel :]
            self._logger.info(
                "First run for channel=%s, limiting initial backfill to %s posts.",
                channel.username,
                self._first_run_max_posts_per_channel,
            )
        new_posts = [post for post in recent_posts if not self._repository.has_sent_post(post.channel_username, post.post_id)]
        self._logger.info(
            "Channel=%s fetched_posts=%s new_posts=%s",
            channel.username,
            len(recent_posts),
            len(new_posts),
        )

        sent_count = 0
        for post in new_posts:
            try:
                sent_count += await self._forward_post(post)
            except RetryAfter as error:
                self._logger.warning(
                    "Stopping channel=%s for this cycle after Telegram asked to retry in %.1f seconds.",
                    channel.username,
                    error.retry_after,
                )
                break
            except Exception:
                self._logger.exception(
                    "Post forwarding failed for channel=%s post_id=%s",
                    post.channel_username,
                    post.post_id,
                )

        self._repository.update_channel_check(channel.username, datetime.now(UTC))
        self._logger.info(
            "Channel=%s last_successful_check updated, sent_messages=%s",
            channel.username,
            sent_count,
        )
        return sent_count

    async def _forward_post(self, post: ParsedPost) -> int:
        if self._repository.has_sent_post(post.channel_username, post.post_id):
            return 0

        await self._forwarder.forward_post(post)
        self._repository.mark_post_sent(post)
        self._logger.info(
            "Forwarded post channel=%s post_id=%s",
            post.channel_username,
            post.post_id,
        )
        if self._send_delay_seconds > 0:
            await asyncio.sleep(self._send_delay_seconds)
        return 1
