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
    assert posts[1].text == "Hello world"
    assert posts[1].html_text == "Hello <b>world</b>"
    assert posts[1].url == "https://t.me/samplechannel/42"


def test_parse_channel_page_skips_service_messages_and_keeps_line_breaks() -> None:
    html = """
    <div class="tgme_widget_message service_message" data-post="samplechannel/100">
      <div class="tgme_widget_message_text">samplechannel pinned a photo</div>
      <a class="tgme_widget_message_date">
        <time datetime="2026-03-25T10:00:00+00:00"></time>
      </a>
    </div>
    <div class="tgme_widget_message" data-post="samplechannel/101">
      <div class="tgme_widget_message_text">
        First line<br/>Second <b>line</b>
      </div>
      <a class="tgme_widget_message_date">
        <time datetime="2026-03-25T10:30:00+00:00"></time>
      </a>
    </div>
    """

    posts = parse_channel_page(html, "samplechannel", "https://t.me")

    assert [post.post_id for post in posts] == [101]
    assert posts[0].text == "First line\nSecond line"
    assert posts[0].html_text == "First line<br>Second <b>line</b>"


def test_parse_channel_page_keeps_hidden_links() -> None:
    html = """
    <div class="tgme_widget_message" data-post="samplechannel/150">
      <div class="tgme_widget_message_text">
        Read <a href="https://example.com/guide">the guide</a> please
      </div>
      <a class="tgme_widget_message_date">
        <time datetime="2026-03-25T10:30:00+00:00"></time>
      </a>
    </div>
    """

    posts = parse_channel_page(html, "samplechannel", "https://t.me")

    assert posts[0].text == "Read the guide please"
    assert posts[0].html_text == 'Read <a href="https://example.com/guide">the guide</a> please'
