from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

from delivery_boy.models import ChannelConfig


@dataclass(slots=True, frozen=True)
class AppConfig:
    bot_token: str
    chat_id: str
    message_thread_id: int | None
    channels_file: Path
    database_path: Path
    log_file_path: Path
    poll_interval_seconds: int
    request_timeout_seconds: float
    request_retries: int
    max_posts_per_channel: int
    max_message_length: int
    telegram_web_base_url: str
    log_level: str
    user_agent: str
    channels: list[ChannelConfig]


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Environment variable {name} is required.")
    return value


def _read_channels(channels_file: Path) -> list[ChannelConfig]:
    if not channels_file.exists():
        raise FileNotFoundError(
            f"Channels file {channels_file} does not exist. "
            "Create it from channels.yaml.example."
        )

    raw = yaml.safe_load(channels_file.read_text(encoding="utf-8")) or {}
    items = raw.get("channels", [])
    channels: list[ChannelConfig] = []
    seen: set[str] = set()

    for item in items:
        if isinstance(item, str):
            username = item.strip().lstrip("@")
        elif isinstance(item, dict):
            if item.get("enabled", True) is False:
                continue
            username = str(item.get("username", "")).strip().lstrip("@")
        else:
            continue

        if not username:
            continue
        if username in seen:
            continue

        seen.add(username)
        channels.append(ChannelConfig(username=username))

    if not channels:
        raise ValueError("No channels configured in channels.yaml.")
    return channels


def load_config() -> AppConfig:
    load_dotenv()

    project_root = Path.cwd()
    channels_file = project_root / os.getenv("CHANNELS_FILE", "channels.yaml")
    database_path = project_root / os.getenv("DATABASE_PATH", "var/data/delivery_boy.db")
    log_file_path = project_root / os.getenv("LOG_FILE_PATH", "var/log/delivery-boy.log")

    config = AppConfig(
        bot_token=_require_env("TELEGRAM_BOT_TOKEN"),
        chat_id=_require_env("TELEGRAM_CHAT_ID"),
        message_thread_id=(
            int(os.getenv("TELEGRAM_MESSAGE_THREAD_ID", "").strip())
            if os.getenv("TELEGRAM_MESSAGE_THREAD_ID", "").strip()
            else None
        ),
        channels_file=channels_file,
        database_path=database_path,
        log_file_path=log_file_path,
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "60")),
        request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15")),
        request_retries=int(os.getenv("REQUEST_RETRIES", "3")),
        max_posts_per_channel=int(os.getenv("MAX_POSTS_PER_CHANNEL", "10")),
        max_message_length=int(os.getenv("MAX_MESSAGE_LENGTH", "4096")),
        telegram_web_base_url=os.getenv("TELEGRAM_WEB_BASE_URL", "https://t.me").rstrip("/"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        user_agent=os.getenv(
            "HTTP_USER_AGENT",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/123.0 Safari/537.36",
        ),
        channels=_read_channels(channels_file),
    )

    if config.poll_interval_seconds < 10:
        raise ValueError("POLL_INTERVAL_SECONDS must be at least 10.")
    if config.max_message_length <= 0:
        raise ValueError("MAX_MESSAGE_LENGTH must be positive.")

    return config
