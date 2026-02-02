"""Scraper for the IDTA Content Hub to extract template metadata."""

import re
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from rich.console import Console

from smt_index.models import TemplateStatus
from smt_index.util import extract_idta_number, slugify

console = Console()

# Playwright is optional - check if available
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    async_playwright = None  # type: ignore[assignment]

IDTA_URLS = [
    "https://industrialdigitaltwin.org/content-hub/teilmodelle",
    "https://industrialdigitaltwin.org/en/content-hub/submodels",
]


@dataclass
class IDTATemplate:
    """Parsed template data from IDTA registry."""

    name: str
    idta_number: str | None = None
    version: str | None = None
    status: TemplateStatus = "unknown"
    raw_status: str | None = None  # Original status text before normalization
    description: str | None = None
    pdf_link: str | None = None
    github_link: str | None = None
    slug: str = field(default="", init=False)

    def __post_init__(self) -> None:
        self.slug = slugify(self.name)
        if self.idta_number:
            self.id = f"idta-{self.idta_number}"
        else:
            self.id = f"ext-{self.slug}"


async def fetch_idta_html(url: str, use_playwright: bool = False) -> str:
    """Fetch the IDTA Content Hub HTML.

    Args:
        url: URL to fetch
        use_playwright: If True, use Playwright for JS-rendered content.
    """
    if use_playwright:
        return await _fetch_with_playwright(url)
    else:
        return await _fetch_with_httpx(url)


async def _fetch_with_httpx(url: str) -> str:
    """Fetch using httpx (faster, but may miss JS-rendered content)."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def _fetch_with_playwright(url: str) -> str:
    """Fetch using Playwright for JS-rendered content."""
    if not PLAYWRIGHT_AVAILABLE or async_playwright is None:
        raise ImportError(
            "Playwright is not installed. Install with: pip install 'smt-index[scraper]'"
        )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        # Wait for content to render
        await page.wait_for_timeout(2000)
        content = await page.content()
        await browser.close()
        return content


def parse_idta_html(html: str) -> list[IDTATemplate]:
    """Parse IDTA HTML to extract template records.

    The IDTA page structure uses a series of tokens (text and links).
    We look for template entries by finding name headers followed by
    "Downloads & Links" sections.
    """
    soup = BeautifulSoup(html, "lxml")
    templates: list[IDTATemplate] = []

    # Find all template cards/sections
    # The page structure varies, so we try multiple selectors
    cards = _find_template_cards(soup)

    for card in cards:
        template = _parse_template_card(card)
        if template:
            templates.append(template)

    if not templates:
        templates = _parse_by_tokens(soup)

    return templates


def _find_template_cards(soup: BeautifulSoup) -> list[Tag]:
    """Find all template card elements on the page.

    The IDTA page uses a grid layout with div.parts__title elements
    containing template rows. Each row has columns:
    - col-span-4: Template name
    - col-span-2: IDTA number (or "extern")
    - col-span-2: Version
    - col-span-2: Status
    - col-span-2: Links (GitHub, PDF)
    """
    # Primary: Find div.parts__title elements (current page structure)
    cards = soup.select("div.parts__title")
    if cards:
        return cards

    # Fallback: Try older selectors in case page structure changes
    accordion_items = soup.select(".accordion-item, .template-card, .teilmodell-item")
    if accordion_items:
        return list(accordion_items)

    return []


def _parse_template_card(card: Tag) -> IDTATemplate | None:
    """Parse a single template card element.

    The card is a grid row with these columns:
    - col-span-4: Template name
    - col-span-2: IDTA number (or "extern" for non-IDTA)
    - col-span-2: Version (e.g., "1.0", "2.0.1")
    - col-span-2: Status (e.g., "Published", "In Review")
    - col-span-2: Links section with GitHub/PDF links
    """
    # Try grid-based parsing first (current page structure)
    result = _parse_grid_card(card)
    if result:
        return result

    # Fallback to generic parsing
    name = _extract_name(card)
    if not name:
        return None

    idta_number = extract_idta_number(name) or extract_idta_number(card.get_text())
    status = _extract_status(card)
    version = _extract_version(card)
    description = _extract_description(card)
    pdf_link, github_link = _extract_links(card)

    return IDTATemplate(
        name=name,
        idta_number=idta_number,
        version=version,
        status=status,
        raw_status=None,  # Generic parsing doesn't have access to raw status
        description=description,
        pdf_link=pdf_link,
        github_link=github_link,
    )


def _parse_grid_card(card: Tag) -> IDTATemplate | None:
    """Parse a grid-based template card (current IDTA page structure)."""
    # Find all grid columns
    col4 = card.select_one(".col-span-4")
    col2_divs = card.select(".col-span-2")

    if not col4 or len(col2_divs) < 4:
        return None

    # Extract name from col-span-4
    name = col4.get_text(strip=True)
    if not name:
        return None

    # Extract IDTA number from first col-span-2
    idta_text = col2_divs[0].get_text(strip=True)
    idta_number: str | None = None
    if idta_text and idta_text.lower() != "extern":
        # Try to extract numeric IDTA number
        idta_number = extract_idta_number(idta_text)
        if not idta_number and re.match(r"^\d+$", idta_text):
            idta_number = idta_text

    # Extract version from second col-span-2
    version = col2_divs[1].get_text(strip=True) or None

    # Extract status from third col-span-2
    raw_status_text = col2_divs[2].get_text(strip=True)
    status_text = raw_status_text.lower()
    status: TemplateStatus = "unknown"
    if "published" in status_text:
        status = "Published"
    elif "review" in status_text:
        status = "In Review"
    elif "development" in status_text:
        status = "In Development"
    elif "proposal" in status_text:
        status = "Proposal submitted"

    # Extract links from fourth col-span-2
    pdf_link: str | None = None
    github_link: str | None = None
    links_div = col2_divs[3]
    for a in links_div.find_all("a", href=True):
        href = str(a["href"])
        link_text = a.get_text().lower()
        if "github" in href.lower() or "github" in link_text:
            github_link = href
        elif ".pdf" in href.lower() or "pdf" in link_text:
            pdf_link = href

    return IDTATemplate(
        name=name,
        idta_number=idta_number,
        version=version,
        status=status,
        raw_status=raw_status_text or None,
        description=None,  # Grid layout doesn't show description in header
        pdf_link=pdf_link,
        github_link=github_link,
    )


def _extract_name(card: Tag) -> str | None:
    """Extract template name from card."""
    # Try heading elements first
    for tag in ["h2", "h3", "h4", "h5"]:
        heading = card.find(tag)
        if heading:
            text = heading.get_text(strip=True)
            # Clean up the name
            text = re.sub(r"^IDTA\s*\d+[-\s]*", "", text)
            text = re.sub(r"\s*[-–]\s*V?\d+\.\d+.*$", "", text)
            if text:
                return text.strip()

    # Try title attribute or data attribute
    title = card.get("title") or card.get("data-title")
    if title:
        return str(title).strip()

    return None


def _extract_status(card: Tag) -> TemplateStatus:
    """Extract template status from card."""
    text = card.get_text().lower()

    if "published" in text or "veröffentlicht" in text:
        return "Published"
    elif "in review" in text or "in prüfung" in text:
        return "In Review"
    elif "in development" in text or "in entwicklung" in text:
        return "In Development"
    elif "proposal submitted" in text or "vorschlag" in text:
        return "Proposal submitted"

    # Check for status badges/labels
    status_elem = card.find(class_=re.compile(r"status|badge|label"))
    if status_elem:
        status_text = status_elem.get_text().lower()
        if "published" in status_text:
            return "Published"
        elif "review" in status_text:
            return "In Review"
        elif "development" in status_text:
            return "In Development"

    return "unknown"


def _extract_version(card: Tag) -> str | None:
    """Extract version string from card."""
    text = card.get_text()

    # Match version patterns like "V1.0", "v2.1.0", "Version 3.0"
    patterns = [
        r"[Vv]ersion\s*(\d+\.\d+(?:\.\d+)?)",
        r"[Vv](\d+\.\d+(?:\.\d+)?)",
        r"\b(\d+\.\d+\.\d+)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return None


def _extract_description(card: Tag) -> str | None:
    """Extract description text from card."""
    # Look for description paragraphs
    desc_elem = card.find(class_=re.compile(r"description|desc|summary|abstract"))
    if desc_elem:
        return desc_elem.get_text(strip=True)

    # Try the first paragraph that's long enough
    for p in card.find_all("p"):
        text = p.get_text(strip=True)
        if len(text) > 50:  # Skip short paragraphs
            return text

    return None


def _extract_links(card: Tag) -> tuple[str | None, str | None]:
    """Extract PDF and GitHub links from card."""
    pdf_link: str | None = None
    github_link: str | None = None

    for a in card.find_all("a", href=True):
        href = str(a["href"])

        if not pdf_link and (".pdf" in href.lower() or "pdf" in a.get_text().lower()):
            pdf_link = href

        if not github_link and "github.com" in href.lower():
            github_link = href

    return pdf_link, github_link


async def scrape_idta(use_playwright_fallback: bool = True) -> tuple[list[IDTATemplate], str]:
    """Scrape the IDTA Content Hub for template metadata.

    First tries httpx, falls back to Playwright if no results.
    """
    console.print("[blue]Fetching IDTA Content Hub...[/blue]")

    # Try httpx on each URL first
    for url in IDTA_URLS:
        html = await fetch_idta_html(url, use_playwright=False)
        templates = parse_idta_html(html)
        if templates:
            console.print(f"[green]Found {len(templates)} templates from IDTA[/green]")
            return templates, url

    # If no templates found and fallback enabled, try Playwright
    if use_playwright_fallback:
        if not PLAYWRIGHT_AVAILABLE:
            console.print(
                "[yellow]No templates found with httpx. "
                "Playwright not installed for JS fallback.[/yellow]"
            )
            console.print(
                "[dim]Install Playwright with: pip install 'smt-index[scraper]' && "
                "playwright install chromium[/dim]"
            )
        else:
            console.print("[yellow]No templates found with httpx, trying Playwright...[/yellow]")
            for url in IDTA_URLS:
                html = await fetch_idta_html(url, use_playwright=True)
                templates = parse_idta_html(html)
                if templates:
                    console.print(f"[green]Found {len(templates)} templates from IDTA[/green]")
                    return templates, url

    console.print("[yellow]No templates found from IDTA[/yellow]")
    return [], IDTA_URLS[0]


class _TextToken:
    def __init__(self, text: str) -> None:
        self.text = text


class _LinkToken:
    def __init__(self, text: str, href: str) -> None:
        self.text = text
        self.href = href


def _compact_spaces(text: str) -> str:
    return " ".join(text.split())


def _iter_tokens(soup: BeautifulSoup) -> list[_TextToken | _LinkToken]:
    tokens: list[_TextToken | _LinkToken] = []
    body = soup.body or soup
    for el in body.descendants:
        if isinstance(el, NavigableString):
            if el.parent and getattr(el.parent, "name", "") == "a":
                continue
            txt = _compact_spaces(str(el))
            if txt:
                tokens.append(_TextToken(txt))
        elif isinstance(el, Tag) and el.name == "a":
            href = el.get("href")
            if not href:
                continue
            txt = _compact_spaces(el.get_text(" ", strip=True))
            if txt:
                # href can be a list in edge cases, use first value or convert to string
                href_str = href[0] if isinstance(href, list) else str(href)
                tokens.append(_LinkToken(txt, href_str))
    return tokens


def _looks_like_idta_number(text: str) -> bool:
    t = text.strip().lower()
    if t == "external":
        return True
    return bool(re.fullmatch(r"\d{5}", text.strip()))


def _looks_like_version(text: str) -> bool:
    return bool(re.fullmatch(r"\d+\.\d+(?:\.\d+)?", text.strip()))


def _normalize_status(text: str) -> TemplateStatus:
    t = text.strip().lower()
    if "published" in t or "veröffentlicht" in t:
        return "Published"
    if "in review" in t or "in prüfung" in t:
        return "In Review"
    if "in development" in t or "in entwicklung" in t:
        return "In Development"
    if "proposal submitted" in t or "vorschlag" in t:
        return "Proposal submitted"
    return "unknown"


def _next_text(
    tokens: list[_TextToken | _LinkToken], start: int, skip: set[str]
) -> tuple[str, int]:
    i = start
    while i < len(tokens):
        tok = tokens[i]
        if isinstance(tok, _TextToken):
            tx = tok.text.strip()
            if tx and tx not in skip:
                return tx, i + 1
        i += 1
    raise ValueError("No text token found")


def _take_until_marker(
    tokens: list[_TextToken | _LinkToken], start: int, marker_text: str
) -> tuple[list[_TextToken | _LinkToken], int]:
    out: list[_TextToken | _LinkToken] = []
    i = start
    while i < len(tokens):
        tok = tokens[i]
        if isinstance(tok, _TextToken) and tok.text == marker_text:
            return out, i
        out.append(tok)
        i += 1
    return out, i


def _parse_by_tokens(soup: BeautifulSoup) -> list[IDTATemplate]:
    tokens = _iter_tokens(soup)
    skip = {
        "Submodel Template",
        "IDTA Number",
        "Version",
        "Status",
        "Downloads & Links",
        "Coming soon",
        "Select sorting",
        "Sort by IDTA numbers",
        "Sort by name",
    }

    entries: list[IDTATemplate] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if isinstance(tok, _TextToken) and tok.text == "Downloads & Links":
            try:
                name, j = _next_text(tokens, i + 1, skip)
                idta_no_raw, j = _next_text(tokens, j, skip)
                version_raw, j = _next_text(tokens, j, skip)
                status_raw, j = _next_text(tokens, j, skip)

                if not _looks_like_idta_number(idta_no_raw):
                    i += 1
                    continue
                if not _looks_like_version(version_raw):
                    i += 1
                    continue

                status = _normalize_status(status_raw)
                raw_status = status_raw.strip() or None
                idta_no = None if idta_no_raw.strip().lower() == "external" else idta_no_raw

                tail, k = _take_until_marker(tokens, j, marker_text="Submodel Template")

                pdf_link = None
                github_link = None
                desc_parts: list[str] = []

                for t in tail:
                    if isinstance(t, _LinkToken):
                        if not pdf_link and (
                            ".pdf" in t.href.lower()
                            or "pdf" in t.text.lower()
                            or t.text.lower().startswith("download")
                        ):
                            pdf_link = t.href
                        elif not github_link and "github.com" in t.href.lower():
                            github_link = t.href
                    elif isinstance(t, _TextToken):
                        tx = t.text
                        if tx in skip:
                            continue
                        if tx.startswith("Each submodel template that passes"):
                            continue
                        desc_parts.append(tx)

                description = _compact_spaces(" ".join(desc_parts)) or None

                entries.append(
                    IDTATemplate(
                        name=name,
                        idta_number=idta_no,
                        version=version_raw,
                        status=status,
                        raw_status=raw_status,
                        description=description,
                        pdf_link=pdf_link,
                        github_link=github_link,
                    )
                )

                i = k
                continue
            except Exception:
                pass
        i += 1

    uniq: dict[tuple[str | None, str | None, str], IDTATemplate] = {}
    for e in entries:
        key = (e.idta_number, e.version, e.name)
        uniq[key] = e
    return list(uniq.values())
