from __future__ import annotations

import asyncio
import logging

import httpx

from delivery_boy.models import ParsedPost
from delivery_boy.telegram_web.parser import parse_channel_page


class TelegramWebClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        retries: int,
        user_agent: str,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._base_url = base_url.rstrip("/")
        self._retries = max(retries, 1)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_posts(self, channel_username: str) -> list[ParsedPost]:
        url = f"{self._base_url}/s/{channel_username.lstrip('@')}"
        last_error: Exception | None = None

        for attempt in range(1, self._retries + 1):
            try:
                response = await self._client.get(url)
                response.raise_for_status()
                return parse_channel_page(
                    html=response.text,
                    channel_username=channel_username,
                    base_url=self._base_url,
                )
            except (httpx.HTTPError, httpx.TimeoutException) as error:
                last_error = error
                self._logger.warning(
                    "Telegram web request failed for channel=%s attempt=%s/%s: %s",
                    channel_username,
                    attempt,
                    self._retries,
                    error,
                )
                if attempt < self._retries:
                    await asyncio.sleep(attempt)

        assert last_error is not None
        raise last_error
