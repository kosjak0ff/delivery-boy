from __future__ import annotations

from datetime import UTC, datetime

import pytest

from delivery_boy.models import ChannelConfig, ChannelState, ParsedPost
from delivery_boy.services.monitor import ChannelMonitor


class DummyRepository:
    def __init__(self) -> None:
        self.sent_posts: set[tuple[str, int]] = set()
        self.channel_state = ChannelState(channel_username="samplechannel", last_successful_check=None)
        self.updated_checks: list[tuple[str, datetime]] = []

    def has_sent_post(self, channel_username: str, post_id: int) -> bool:
        return (channel_username, post_id) in self.sent_posts

    def mark_post_sent(self, post: ParsedPost) -> None:
        self.sent_posts.add((post.channel_username, post.post_id))

    def get_channel_state(self, channel_username: str) -> ChannelState:
        return self.channel_state

    def update_channel_check(self, channel_username: str, checked_at: datetime) -> None:
        self.updated_checks.append((channel_username, checked_at))
        self.channel_state = ChannelState(channel_username=channel_username, last_successful_check=checked_at)


class DummyTelegramWebClient:
    def __init__(self, posts: list[ParsedPost]) -> None:
        self.posts = posts

    async def fetch_posts(self, channel_username: str) -> list[ParsedPost]:
        return self.posts


class DummyForwarder:
    def __init__(self) -> None:
        self.forwarded_posts: list[int] = []

    async def forward_post(self, post: ParsedPost) -> None:
        self.forwarded_posts.append(post.post_id)


def build_post(post_id: int) -> ParsedPost:
    return ParsedPost(
        channel_username="samplechannel",
        post_id=post_id,
        url=f"https://t.me/samplechannel/{post_id}",
        text=f"post {post_id}",
        published_at=datetime.now(UTC),
    )


@pytest.mark.anyio
async def test_monitor_limits_initial_backfill() -> None:
    repository = DummyRepository()
    forwarder = DummyForwarder()
    client = DummyTelegramWebClient([build_post(1), build_post(2), build_post(3), build_post(4)])
    monitor = ChannelMonitor(
        channels=[ChannelConfig(username="samplechannel")],
        repository=repository,
        telegram_web_client=client,
        forwarder=forwarder,
        max_posts_per_channel=10,
        first_run_max_posts_per_channel=2,
        send_delay_seconds=0,
    )

    await monitor.run_once()

    assert forwarder.forwarded_posts == [3, 4]
