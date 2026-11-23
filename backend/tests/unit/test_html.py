import pytest

from app.utils.html import html_to_text, sanitize_html


@pytest.mark.parametrize(
    "allowed",
    [
        "<h2>Program</h2>",
        "<h3>Day one</h3><h4>Morning</h4>",
        "<p>Plain <strong>bold</strong> <em>italic</em> <u>under</u> <s>gone</s><br>next</p>",
        "<ul><li>one</li></ul><ol><li>two</li></ol>",
        "<blockquote><p>Quote</p></blockquote>",
    ],
)
def test_allowed_markup_is_kept(allowed: str) -> None:
    assert sanitize_html(allowed) == allowed


@pytest.mark.parametrize(
    ("dirty", "clean"),
    [
        ("<p>Hi<script>alert(1)</script></p>", "<p>Hi</p>"),
        ('<p onclick="steal()">Hi</p>', "<p>Hi</p>"),
        ('<p style="color:red" class="x">Hi</p>', "<p>Hi</p>"),
        ('<img src="x" onerror="steal()">', ""),
        ("<iframe src='https://evil.example'></iframe><p>Hi</p>", "<p>Hi</p>"),
        ("<h1>Title</h1>", "Title"),
        ("<div><span>Hi</span></div>", "Hi"),
    ],
)
def test_unsafe_or_unknown_markup_is_removed(dirty: str, clean: str) -> None:
    assert sanitize_html(dirty) == clean


def test_links_keep_safe_urls_and_get_rel() -> None:
    cleaned = sanitize_html('<a href="https://seatwise.rs" target="_blank">site</a>')

    assert cleaned == ('<a href="https://seatwise.rs" rel="noopener noreferrer nofollow">site</a>')


@pytest.mark.parametrize("href", ["javascript:alert(1)", "data:text/html,<b>x</b>", "vbscript:x"])
def test_dangerous_link_urls_are_dropped(href: str) -> None:
    assert "href" not in sanitize_html(f'<a href="{href}">x</a>')


def test_text_separates_blocks_and_decodes_entities() -> None:
    text = html_to_text("<h2>Program</h2><p>Rock &amp; roll</p><ul><li>one</li><li>two</li></ul>")

    assert text == "Program Rock & roll one two"


def test_text_of_empty_markup_is_empty() -> None:
    assert html_to_text("<p> </p><p><br></p>") == ""
