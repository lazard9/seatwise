import pytest

from app.utils.slugs import MAX_SLUG_LENGTH, slugify


@pytest.mark.parametrize(
    ("title", "slug"),
    [
        ("Jazz Night", "jazz-night"),
        ("Đorđe Balašević", "djordje-balasevic"),
        ("Ђорђе Балашевић", "djordje-balasevic"),
        ("Čačak, Šabac i Žabalj", "cacak-sabac-i-zabalj"),
        ("Љубав и Њујорк Џез", "ljubav-i-njujork-dzez"),
        ("ЋЕВАПИ & ЏЕЗ", "cevapi-dzez"),
        ("Café Noël", "cafe-noel"),
        ("  --Rock   2026!!  ", "rock-2026"),
    ],
)
def test_slugify(title: str, slug: str) -> None:
    assert slugify(title) == slug


def test_a_title_without_letters_gets_a_fallback() -> None:
    assert slugify("!!! ???") == "event"


def test_a_long_title_is_cut_at_a_word_boundary() -> None:
    slug = slugify("word " * 40)

    assert len(slug) <= MAX_SLUG_LENGTH
    assert not slug.endswith("-")
    assert set(slug.split("-")) == {"word"}
