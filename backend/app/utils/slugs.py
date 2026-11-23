import re
import unicodedata

MAX_SLUG_LENGTH = 80
FALLBACK_SLUG = "event"

# Serbian letters that Unicode decomposition does not turn into the usual ASCII spelling.
# The alphabet is listed in Cyrillic order; the Latin list follows the same order.
_CYRILLIC = "абвгдђежзијклљмнњопрстћуфхцчџш"
_LATIN = [
    "a",
    "b",
    "v",
    "g",
    "d",
    "dj",
    "e",
    "z",
    "z",
    "i",
    "j",
    "k",
    "l",
    "lj",
    "m",
    "n",
    "nj",
    "o",
    "p",
    "r",
    "s",
    "t",
    "c",
    "u",
    "f",
    "h",
    "c",
    "c",
    "dz",
    "s",
]
_TABLE = str.maketrans({"đ": "dj", **dict(zip(_CYRILLIC, _LATIN, strict=True))})
_NOT_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Lowercase ASCII words joined by hyphens. `Ђорђе Балашевић` and `Đorđe Balašević`
    both give `djordje-balasevic`. Never empty: a title with no letters gives `event`."""
    lowered = text.lower().translate(_TABLE)
    # NFKD splits č into c and a combining mark; encoding to ASCII drops the mark.
    ascii_text = unicodedata.normalize("NFKD", lowered).encode("ascii", "ignore").decode()
    slug = _NOT_ALNUM.sub("-", ascii_text).strip("-")
    if len(slug) > MAX_SLUG_LENGTH:
        cut = slug[:MAX_SLUG_LENGTH]
        # Cut at a word boundary when there is one, so the slug does not end mid-word.
        slug = cut.rsplit("-", 1)[0] if "-" in cut else cut
    return slug or FALLBACK_SLUG
