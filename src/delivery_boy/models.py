from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class ChannelConfig:
    username: str


@dataclass(slots=True, frozen=True)
class ParsedPost:
    channel_username: str
    post_id: int
    url: str
    text: str
    html_text: str
    has_audio: bool
    published_at: datetime | None


@dataclass(slots=True, frozen=True)
class ChannelState:
    channel_username: str
    last_successful_check: datetime | None
