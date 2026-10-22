import hashlib
from pathlib import Path

from app.services.extractor import extract

FIXTURE_DIR = Path(__file__).parent / "fixtures"
PAGE_URL = "https://example.com/story"


def test_extracts_main_content_metadata_and_links():
    html = (FIXTURE_DIR / "article.html").read_text(encoding="utf-8")

    result = extract(html, PAGE_URL)

    assert result.title == "Example article"
    assert result.description == "An article description"
    assert result.language == "en"
    assert result.canonical_url == "https://example.com/articles/example"
    assert result.links == (
        "https://example.com/related",
        "https://external.example/reference",
    )
    assert "# Example article" in result.markdown
    assert "## Details" in result.markdown
    assert "[a related article](https://example.com/related)" in result.markdown
    assert "Home navigation" not in result.markdown
    assert "Privacy footer" not in result.markdown
    assert "<nav" not in result.cleaned_html
    assert "<footer" not in result.cleaned_html
    assert result.content_hash == hashlib.sha256(result.markdown.encode("utf-8")).hexdigest()


def test_falls_back_for_short_pages_and_resolves_links():
    html = (
        '<html lang="fr"><body><nav>menu</nav><h1>Short</h1><p>Brief body.</p>'
        '<a href="/next">Next</a><footer>bye</footer></body></html>'
    )

    result = extract(html, PAGE_URL)

    assert result.title == "Short"
    assert result.description is None
    assert result.language == "fr"
    assert result.links == ("https://example.com/next",)
    assert "# Short" in result.markdown
    assert "Brief body." in result.markdown
    assert "menu" not in result.markdown
    assert "bye" not in result.markdown
