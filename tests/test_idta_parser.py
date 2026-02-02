"""Tests for IDTA HTML parsing."""


from smt_index.sources.idta import (
    _extract_links,
    _extract_status,
    _extract_version,
    parse_idta_html,
)
from smt_index.util import extract_idta_number, slugify


class TestExtractIdtaNumber:
    """Tests for IDTA number extraction."""

    def test_extract_from_text(self) -> None:
        assert extract_idta_number("IDTA 02006 Digital Nameplate") == "02006"

    def test_extract_from_smt_format(self) -> None:
        assert extract_idta_number("SMT 02006-3-0") == "02006"

    def test_no_number(self) -> None:
        assert extract_idta_number("Some text without number") is None

    def test_wrong_length(self) -> None:
        # Only 5-digit numbers should match
        assert extract_idta_number("Number 1234") is None
        assert extract_idta_number("Number 123456") is None


class TestSlugify:
    """Tests for name slugification."""

    def test_basic(self) -> None:
        assert slugify("Digital Nameplate") == "digital-nameplate"

    def test_with_special_chars(self) -> None:
        assert slugify("Generic Frame for Technical Data") == "generic-frame-for-technical-data"

    def test_already_slugified(self) -> None:
        assert slugify("digital-nameplate") == "digital-nameplate"


class TestParseIdtaHtml:
    """Tests for IDTA HTML parsing."""

    def test_parse_simple_card(self) -> None:
        html = """
        <html>
        <body>
        <div class="accordion-item">
            <h3>IDTA 02006 Digital Nameplate V3.0</h3>
            <p class="description">The Digital Nameplate provides standardized identification information.</p>
            <span class="badge">Published</span>
            <a href="https://github.com/admin-shell-io/submodel-templates/tree/main/published/DigitalNameplate">GitHub</a>
            <a href="https://example.com/spec.pdf">PDF</a>
        </div>
        </body>
        </html>
        """
        templates = parse_idta_html(html)

        # Should find at least one template
        assert len(templates) >= 1

        # Check first template (may need adjustment based on parsing)
        if templates:
            t = templates[0]
            assert "02006" in (t.idta_number or "")
            assert t.status == "Published"

    def test_parse_empty_html(self) -> None:
        html = "<html><body></body></html>"
        templates = parse_idta_html(html)
        assert templates == []

    def test_parse_multiple_cards(self) -> None:
        html = """
        <html>
        <body>
        <div class="accordion-item">
            <h3>Template One</h3>
        </div>
        <div class="accordion-item">
            <h3>Template Two</h3>
        </div>
        </body>
        </html>
        """
        templates = parse_idta_html(html)
        # Should find multiple templates
        assert len(templates) >= 2


class TestExtractStatus:
    """Tests for status extraction from HTML elements."""

    def test_status_published(self) -> None:
        from bs4 import BeautifulSoup

        html = '<div><span class="badge">Published</span></div>'
        soup = BeautifulSoup(html, "lxml")
        card = soup.find("div")
        assert card is not None
        status = _extract_status(card)
        assert status == "Published"

    def test_status_in_review(self) -> None:
        from bs4 import BeautifulSoup

        html = "<div>Status: In Review</div>"
        soup = BeautifulSoup(html, "lxml")
        card = soup.find("div")
        assert card is not None
        status = _extract_status(card)
        assert status == "In Review"

    def test_status_unknown(self) -> None:
        from bs4 import BeautifulSoup

        html = "<div>No status here</div>"
        soup = BeautifulSoup(html, "lxml")
        card = soup.find("div")
        assert card is not None
        status = _extract_status(card)
        assert status == "unknown"


class TestExtractVersion:
    """Tests for version extraction."""

    def test_version_with_v(self) -> None:
        from bs4 import BeautifulSoup

        html = "<div>Template V3.0</div>"
        soup = BeautifulSoup(html, "lxml")
        card = soup.find("div")
        assert card is not None
        version = _extract_version(card)
        assert version == "3.0"

    def test_version_full(self) -> None:
        from bs4 import BeautifulSoup

        html = "<div>Version 1.2.3 released</div>"
        soup = BeautifulSoup(html, "lxml")
        card = soup.find("div")
        assert card is not None
        version = _extract_version(card)
        assert version == "1.2.3"


class TestExtractLinks:
    """Tests for link extraction."""

    def test_extract_pdf_and_github(self) -> None:
        from bs4 import BeautifulSoup

        html = """
        <div>
            <a href="https://example.com/doc.pdf">PDF</a>
            <a href="https://github.com/admin-shell-io/submodel-templates">GitHub</a>
        </div>
        """
        soup = BeautifulSoup(html, "lxml")
        card = soup.find("div")
        assert card is not None
        pdf, github = _extract_links(card)
        assert pdf == "https://example.com/doc.pdf"
        assert github is not None
        assert "github.com" in github

    def test_extract_pdf_by_extension(self) -> None:
        from bs4 import BeautifulSoup

        html = '<div><a href="https://example.com/spec.pdf">Download</a></div>'
        soup = BeautifulSoup(html, "lxml")
        card = soup.find("div")
        assert card is not None
        pdf, github = _extract_links(card)
        assert pdf == "https://example.com/spec.pdf"
        assert github is None
