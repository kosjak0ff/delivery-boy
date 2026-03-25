from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from delivery_boy.models import ChannelState, ParsedPost


class Repository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def has_sent_post(self, channel_username: str, post_id: int) -> bool:
        row = self.connection.execute(
            """
            SELECT 1
            FROM sent_posts
            WHERE channel_username = ? AND post_id = ?
            """,
            (channel_username, post_id),
        ).fetchone()
        return row is not None

    def mark_post_sent(self, post: ParsedPost) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO sent_posts (
                channel_username,
                post_id,
                forwarded_at,
                original_url
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                post.channel_username,
                post.post_id,
                datetime.now(UTC).isoformat(),
                post.url,
            ),
        )
        self.connection.commit()

    def get_channel_state(self, channel_username: str) -> ChannelState:
        row = self.connection.execute(
            """
            SELECT channel_username, last_successful_check
            FROM channel_state
            WHERE channel_username = ?
            """,
            (channel_username,),
        ).fetchone()
        if row is None:
            return ChannelState(channel_username=channel_username, last_successful_check=None)

        last_successful_check = (
            datetime.fromisoformat(row["last_successful_check"])
            if row["last_successful_check"]
            else None
        )
        return ChannelState(
            channel_username=row["channel_username"],
            last_successful_check=last_successful_check,
        )

    def update_channel_check(self, channel_username: str, checked_at: datetime) -> None:
        self.connection.execute(
            """
            INSERT INTO channel_state (channel_username, last_successful_check)
            VALUES (?, ?)
            ON CONFLICT(channel_username)
            DO UPDATE SET last_successful_check = excluded.last_successful_check
            """,
            (channel_username, checked_at.isoformat()),
        )
        self.connection.commit()
