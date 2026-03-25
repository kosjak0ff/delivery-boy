from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from delivery_boy.models import ParsedPost


def parse_channel_page(html: str, channel_username: str, base_url: str) -> list[ParsedPost]:
    soup = BeautifulSoup(html, "html.parser")
    posts: list[ParsedPost] = []

    for message in soup.select("div.tgme_widget_message[data-post]"):
        data_post = message.get("data-post", "").strip()
        if "/" not in data_post:
            continue

        channel_name, post_id_text = data_post.split("/", maxsplit=1)
        if channel_name.lstrip("@") != channel_username.lstrip("@"):
            continue

        try:
            post_id = int(post_id_text)
        except ValueError:
            continue

        text_node = message.select_one(".tgme_widget_message_text")
        text = text_node.get_text("\n", strip=True) if text_node else ""

        date_node = message.select_one("a.tgme_widget_message_date time")
        published_at = None
        if date_node and date_node.has_attr("datetime"):
            try:
                published_at = datetime.fromisoformat(date_node["datetime"].replace("Z", "+00:00"))
            except ValueError:
                published_at = None

        posts.append(
            ParsedPost(
                channel_username=channel_username.lstrip("@"),
                post_id=post_id,
                url=f"{base_url}/{channel_username.lstrip('@')}/{post_id}",
                text=text,
                published_at=published_at,
            )
        )

    posts.sort(key=lambda post: post.post_id)
    return posts
