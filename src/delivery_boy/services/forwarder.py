from __future__ import annotations

import logging
from asyncio import sleep
from html import escape

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import BadRequest, RetryAfter, TelegramError

from delivery_boy.models import ParsedPost


class TelegramForwarder:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        message_thread_id: int | None,
        audio_chat_id: str | None,
        audio_message_thread_id: int | None,
        max_message_length: int,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._bot = Bot(token=bot_token)
        self._chat_id = chat_id
        self._message_thread_id = message_thread_id
        self._audio_chat_id = audio_chat_id
        self._audio_message_thread_id = audio_message_thread_id
        self._max_message_length = max_message_length

    async def initialize(self) -> None:
        await self._bot.initialize()

    async def close(self) -> None:
        await self._bot.shutdown()

    async def forward_post(self, post: ParsedPost) -> None:
        message, parse_mode = self._build_message(post)
        plain_message = self._build_plain_message(post)
        chat_id, message_thread_id = self._resolve_destination(post)
        for attempt in range(1, 3):
            try:
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    message_thread_id=message_thread_id,
                    parse_mode=parse_mode,
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
            except BadRequest as error:
                if parse_mode == ParseMode.HTML and "Can't parse entities" in str(error):
                    self._logger.warning(
                        "Telegram rejected HTML entities for channel=%s post_id=%s, retrying as plain text.",
                        post.channel_username,
                        post.post_id,
                    )
                    message = plain_message
                    parse_mode = None
                    continue
                self._logger.exception(
                    "Bad request while forwarding post channel=%s post_id=%s",
                    post.channel_username,
                    post.post_id,
                )
                raise
            except TelegramError:
                self._logger.exception(
                    "Failed to forward post channel=%s post_id=%s",
                    post.channel_username,
                    post.post_id,
                )
                raise

    def _resolve_destination(self, post: ParsedPost) -> tuple[str, int | None]:
        if post.has_audio and self._audio_chat_id:
            return self._audio_chat_id, self._audio_message_thread_id
        return self._chat_id, self._message_thread_id

    def _build_message(self, post: ParsedPost) -> tuple[str, str | None]:
        prefix_text = f"@{post.channel_username}"
        prefix_html = escape(prefix_text)
        body = post.text.strip() or "[Post without text content]"
        body_html = post.html_text.strip() or escape(body)
        link_label = f"Original: {post.url}"
        link_html = f'Original: <a href="{escape(post.url, quote=True)}">{escape(post.url)}</a>'
        separator = "\n\n"
        available = self._max_message_length - len(prefix_text) - len(link_label) - len(separator) * 2

        if available < 1:
            available = 1

        if len(body) > available:
            body = body[: max(available - 1, 1)].rstrip() + "…"
            return (
                f"{prefix_text}{separator}{body}{separator}{link_label}",
                None,
            )

        return (
            f"{prefix_html}{separator}{body_html}{separator}{link_html}",
            ParseMode.HTML,
        )

    def _build_plain_message(self, post: ParsedPost) -> str:
        prefix_text = f"@{post.channel_username}"
        body = post.text.strip() or "[Post without text content]"
        link_label = f"Original: {post.url}"
        separator = "\n\n"
        available = self._max_message_length - len(prefix_text) - len(link_label) - len(separator) * 2

        if available < 1:
            available = 1

        if len(body) > available:
            body = body[: max(available - 1, 1)].rstrip() + "…"

        return f"{prefix_text}{separator}{body}{separator}{link_label}"
