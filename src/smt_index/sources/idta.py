"""Scraper for the IDTA Content Hub to extract template metadata."""

import re
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup, Tag
from rich.console import Console

from smt_index.models import TemplateStatus
from smt_index.util import extract_idta_number, slugify

console = Console()

IDTA_URL = "https://industrialdigitaltwin.org/content-hub/teilmodelle"


@dataclass
class IDTATemplate:
    """Parsed template data from IDTA registry."""

    name: str
    idta_number: str | None = None
    version: str | None = None
    status: TemplateStatus = "unknown"
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


async def fetch_idta_html(use_playwright: bool = False) -> str:
    """Fetch the IDTA Content Hub HTML.

    Args:
        use_playwright: If True, use Playwright for JS-rendered content.
    """
    if use_playwright:
        return await _fetch_with_playwright()
    else:
        return await _fetch_with_httpx()


async def _fetch_with_httpx() -> str:
    """Fetch using httpx (faster, but may miss JS-rendered content)."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(IDTA_URL)
        response.raise_for_status()
        return response.text


async def _fetch_with_playwright() -> str:
    """Fetch using Playwright for JS-rendered content."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(IDTA_URL, wait_until="networkidle")
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

    return templates


def _find_template_cards(soup: BeautifulSoup) -> list[Tag]:
    """Find all template card elements on the page."""
    cards: list[Tag] = []

    # Try different selectors based on page structure
    # Method 1: Look for accordion items
    accordion_items = soup.select(".accordion-item, .template-card, .teilmodell-item")
    if accordion_items:
        cards.extend(accordion_items)

    # Method 2: Look for sections with template-like content
    if not cards:
        sections = soup.find_all(["article", "section", "div"], class_=re.compile(r"template|model"))
        cards.extend(sections)

    # Method 3: Look for headings followed by content
    if not cards:
        headings = soup.find_all(["h2", "h3", "h4"], string=re.compile(r"IDTA|Submodel|Teilmodell"))
        for h in headings:
            parent = h.find_parent(["article", "section", "div"])
            if parent and parent not in cards:
                cards.append(parent)

    return cards


def _parse_template_card(card: Tag) -> IDTATemplate | None:
    """Parse a single template card element."""
    # Extract template name
    name = _extract_name(card)
    if not name:
        return None

    # Extract IDTA number from name or card content
    idta_number = extract_idta_number(name) or extract_idta_number(card.get_text())

    # Extract status
    status = _extract_status(card)

    # Extract version
    version = _extract_version(card)

    # Extract description
    description = _extract_description(card)

    # Extract links
    pdf_link, github_link = _extract_links(card)

    return IDTATemplate(
        name=name,
        idta_number=idta_number,
        version=version,
        status=status,
        description=description,
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


async def scrape_idta(use_playwright_fallback: bool = True) -> list[IDTATemplate]:
    """Scrape the IDTA Content Hub for template metadata.

    First tries httpx, falls back to Playwright if no results.
    """
    console.print("[blue]Fetching IDTA Content Hub...[/blue]")

    # Try httpx first
    html = await fetch_idta_html(use_playwright=False)
    templates = parse_idta_html(html)

    # If no templates found and fallback enabled, try Playwright
    if not templates and use_playwright_fallback:
        console.print("[yellow]No templates found with httpx, trying Playwright...[/yellow]")
        html = await fetch_idta_html(use_playwright=True)
        templates = parse_idta_html(html)

    console.print(f"[green]Found {len(templates)} templates from IDTA[/green]")
    return templates
