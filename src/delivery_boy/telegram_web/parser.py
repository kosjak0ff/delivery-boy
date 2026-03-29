from __future__ import annotations

from datetime import datetime
from html import escape
import re

from bs4 import BeautifulSoup, NavigableString, Tag

from delivery_boy.models import ParsedPost


def _render_html(node: Tag | NavigableString, base_url: str) -> str:
    if isinstance(node, NavigableString):
        return escape(str(node))

    if not isinstance(node, Tag):
        return ""

    if node.name == "br":
        return "\n"

    if node.name in {"p", "div", "blockquote"}:
        return "".join(_render_html(child, base_url) for child in node.children) + "\n"

    if node.name == "li":
        return "- " + "".join(_render_html(child, base_url) for child in node.children) + "\n"

    if node.name == "a":
        href = (node.get("href") or "").strip()
        if href.startswith("/"):
            href = f"{base_url}{href}"
        content = "".join(_render_html(child, base_url) for child in node.children).strip()
        if href and content:
            return f'<a href="{escape(href, quote=True)}">{content}</a>'
        return content

    if node.name in {"b", "strong", "i", "em", "u", "s", "code", "pre"}:
        content = "".join(_render_html(child, base_url) for child in node.children)
        if content:
            return f"<{node.name}>{content}</{node.name}>"
        return ""

    return "".join(_render_html(child, base_url) for child in node.children)


def _normalize_text(text_node: Tag) -> str:
    fragment = BeautifulSoup(str(text_node), "html.parser")

    for br in fragment.select("br"):
        br.replace_with("\n")

    for block in fragment.select("p, div, blockquote"):
        block.append("\n")

    for item in fragment.select("li"):
        item.insert(0, "- ")
        item.append("\n")

    raw_text = fragment.get_text("", strip=False).replace("\xa0", " ")
    raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)

    lines = [line.strip() for line in raw_text.splitlines()]
    text = "\n".join(lines).strip()
    text = re.sub(r" +", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text


def _normalize_html(text_node: Tag, base_url: str) -> str:
    html = "".join(_render_html(child, base_url) for child in text_node.children)
    html = re.sub(r"\n{3,}", "\n\n", html)
    html = re.sub(r" *\n *", "\n", html)
    return html.strip()


def _has_audio(message: Tag) -> bool:
    if message.select_one(
        ".tgme_widget_message_voice, .tgme_widget_message_audio, "
        ".tgme_widget_message_document, .tgme_widget_message_document_wrap, audio"
    ):
        return True

    for link in message.select("a[href]"):
        href = (link.get("href") or "").lower()
        if any(ext in href for ext in [".mp3", ".m4a", ".ogg", ".wav", ".flac", ".aac"]):
            return True

    return False


def parse_channel_page(html: str, channel_username: str, base_url: str) -> list[ParsedPost]:
    soup = BeautifulSoup(html, "html.parser")
    posts: list[ParsedPost] = []

    for message in soup.select("div.tgme_widget_message[data-post]"):
        classes = set(message.get("class", []))
        if "service_message" in classes:
            continue

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
        text = _normalize_text(text_node) if text_node else ""
        html_text = _normalize_html(text_node, base_url) if text_node else ""
        has_audio = _has_audio(message)

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
                html_text=html_text,
                has_audio=has_audio,
                published_at=published_at,
            )
        )

    posts.sort(key=lambda post: post.post_id)
    return posts
