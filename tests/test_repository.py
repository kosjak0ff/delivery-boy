from datetime import UTC, datetime

from delivery_boy.models import ParsedPost
from delivery_boy.storage.db import connect, initialize
from delivery_boy.storage.repository import Repository


def test_repository_deduplicates_sent_posts(tmp_path) -> None:
    connection = connect(tmp_path / "test.db")
    initialize(connection)
    repository = Repository(connection)

    post = ParsedPost(
        channel_username="samplechannel",
        post_id=5,
        url="https://t.me/samplechannel/5",
        text="hello",
        html_text="hello",
        published_at=datetime.now(UTC),
    )

    assert repository.has_sent_post("samplechannel", 5) is False
    repository.mark_post_sent(post)
    repository.mark_post_sent(post)
    assert repository.has_sent_post("samplechannel", 5) is True


def test_repository_updates_channel_state(tmp_path) -> None:
    connection = connect(tmp_path / "test.db")
    initialize(connection)
    repository = Repository(connection)

    checked_at = datetime(2026, 3, 25, 19, 0, tzinfo=UTC)
    repository.update_channel_check("samplechannel", checked_at)

    state = repository.get_channel_state("samplechannel")

    assert state.channel_username == "samplechannel"
    assert state.last_successful_check == checked_at
