from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

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
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._channels = channels
        self._repository = repository
        self._telegram_web_client = telegram_web_client
        self._forwarder = forwarder
        self._max_posts_per_channel = max_posts_per_channel
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

        recent_posts = posts[-self._max_posts_per_channel :]
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
        return 1
