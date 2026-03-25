from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS sent_posts (
            channel_username TEXT NOT NULL,
            post_id INTEGER NOT NULL,
            forwarded_at TEXT NOT NULL,
            original_url TEXT NOT NULL,
            PRIMARY KEY (channel_username, post_id)
        );

        CREATE TABLE IF NOT EXISTS channel_state (
            channel_username TEXT PRIMARY KEY,
            last_successful_check TEXT
        );
        """
    )
    connection.commit()
