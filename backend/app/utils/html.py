import html
import re

import nh3

# What the description editor can produce. h1 is left out: the event title is the page's h1.
ALLOWED_TAGS = frozenset(
    {"p", "br", "h2", "h3", "h4", "strong", "em", "u", "s", "a", "ul", "ol", "li", "blockquote"}
)
ALLOWED_ATTRIBUTES = {"a": {"href"}}
URL_SCHEMES = frozenset({"http", "https", "mailto"})
# Links in user content must not pass the page's referrer or ranking to unknown sites.
LINK_REL = "noopener noreferrer nofollow"

_BLOCK_START = re.compile(r"<(/?)(p|br|h2|h3|h4|li|blockquote)\b", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")


def sanitize_html(value: str) -> str:
    """Keep only the allowed tags and attributes. Scripts and their content, event handlers
    and `javascript:` links are removed; the text of other unknown tags is kept."""
    return nh3.clean(
        value,
        tags=set(ALLOWED_TAGS),
        attributes={tag: set(attrs) for tag, attrs in ALLOWED_ATTRIBUTES.items()},
        url_schemes=set(URL_SCHEMES),
        link_rel=LINK_REL,
    ).strip()


def html_to_text(value: str) -> str:
    """Plain text of an HTML fragment, for search and for checking that it says something."""
    # A space at each block edge, so `<p>a</p><p>b</p>` reads `a b`, not `ab`.
    spaced = _BLOCK_START.sub(r" <\1\2", value)
    text = html.unescape(nh3.clean(spaced, tags=set()))
    return _WHITESPACE.sub(" ", text).strip()
