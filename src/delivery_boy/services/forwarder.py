from __future__ import annotations

import logging
from asyncio import sleep

from telegram import Bot
from telegram.error import RetryAfter, TelegramError

from delivery_boy.models import ParsedPost


class TelegramForwarder:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        message_thread_id: int | None,
        max_message_length: int,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._bot = Bot(token=bot_token)
        self._chat_id = chat_id
        self._message_thread_id = message_thread_id
        self._max_message_length = max_message_length

    async def initialize(self) -> None:
        await self._bot.initialize()

    async def close(self) -> None:
        await self._bot.shutdown()

    async def forward_post(self, post: ParsedPost) -> None:
        message = self._build_message(post)
        for attempt in range(1, 3):
            try:
                await self._bot.send_message(
                    chat_id=self._chat_id,
                    text=message,
                    message_thread_id=self._message_thread_id,
                    disable_web_page_preview=True,
                )
                return
            except RetryAfter as error:
                self._logger.warning(
                    "Telegram flood control for channel=%s post_id=%s, sleeping %.1f seconds before retry.",
                    post.channel_username,
                    post.post_id,
                    error.retry_after,
                )
                if attempt >= 2:
                    raise
                await sleep(float(error.retry_after) + 1.0)
            except TelegramError:
                self._logger.exception(
                    "Failed to forward post channel=%s post_id=%s",
                    post.channel_username,
                    post.post_id,
                )
                raise

    def _build_message(self, post: ParsedPost) -> str:
        prefix = f"@{post.channel_username}"
        body = post.text.strip() or "[Post without text content]"
        link_label = f"Original: {post.url}"
        separator = "\n\n"
        available = self._max_message_length - len(prefix) - len(link_label) - len(separator) * 2

        if available < 1:
            available = 1

        if len(body) > available:
            body = body[: max(available - 1, 1)].rstrip() + "…"

        return f"{prefix}{separator}{body}{separator}{link_label}"
