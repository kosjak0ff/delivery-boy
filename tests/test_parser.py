from delivery_boy.telegram_web.parser import parse_channel_page


def test_parse_channel_page_extracts_posts_in_order() -> None:
    html = """
    <div class="tgme_widget_message" data-post="samplechannel/42">
      <div class="tgme_widget_message_text">Hello <b>world</b></div>
      <a class="tgme_widget_message_date">
        <time datetime="2026-03-25T10:30:00+00:00"></time>
      </a>
    </div>
    <div class="tgme_widget_message" data-post="samplechannel/41">
      <div class="tgme_widget_message_text">Older post</div>
      <a class="tgme_widget_message_date">
        <time datetime="2026-03-25T09:30:00+00:00"></time>
      </a>
    </div>
    """

    posts = parse_channel_page(html, "samplechannel", "https://t.me")

    assert [post.post_id for post in posts] == [41, 42]
    assert posts[1].text == "Hello\nworld"
    assert posts[1].url == "https://t.me/samplechannel/42"
