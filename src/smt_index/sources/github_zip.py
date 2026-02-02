"""Enumerator for GitHub submodel-templates repository via ZIP download."""

import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import quote

import httpx
from rich.console import Console

from smt_index.models import GitHubVersion
from smt_index.util import SemVer, slugify

console = Console()

GITHUB_REPO = "admin-shell-io/submodel-templates"
GITHUB_ZIP_URL = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip"
GITHUB_BASE_URL = f"https://github.com/{GITHUB_REPO}"


@dataclass
class GitHubTemplateEntry:
    """A template version found in the GitHub repository."""

    template_name: str
    area: str  # 'published' or 'deprecated'
    version: SemVer
    repo_path: str
    github_url: str
    slug: str

    def to_github_version(self) -> GitHubVersion:
        """Convert to GitHubVersion model."""
        return GitHubVersion(
            version=str(self.version),
            area=self.area,  # type: ignore[arg-type]
            repo_path=self.repo_path,
            github_url=self.github_url,
        )


async def fetch_github_zip() -> bytes:
    """Download the GitHub repository as a ZIP file."""
    console.print("[blue]Downloading GitHub repository ZIP...[/blue]")

    async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
        response = await client.get(GITHUB_ZIP_URL)
        response.raise_for_status()
        console.print(f"[green]Downloaded {len(response.content) / 1024 / 1024:.1f} MB[/green]")
        return response.content


def enumerate_zip(zip_content: bytes) -> list[GitHubTemplateEntry]:
    """Walk the ZIP file and find all version folders.

    The repository structure is:
        submodel-templates-main/
            published/
                TemplateName/
                    1/
                        0/
                            docs/
                            ...
            deprecated/
                OldTemplate/
                    1/
                        0/
                            docs/
    """
    entries: list[GitHubTemplateEntry] = []

    with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
        # Get all directory names
        names = [n for n in zf.namelist() if n.endswith("/")]

        for name in names:
            entry = _parse_path(name)
            if entry:
                entries.append(entry)

    console.print(f"[green]Found {len(entries)} version entries from GitHub[/green]")
    return entries


def _parse_path(path: str) -> GitHubTemplateEntry | None:
    """Parse a ZIP path to extract template version info.

    Looking for patterns like:
        submodel-templates-main/published/DigitalNameplate/3/0/1/
        submodel-templates-main/deprecated/OldTemplate/1/0/

    We identify a version folder by:
    1. Being in published/ or deprecated/
    2. Having numeric path segments for version
    3. Being the deepest version folder (containing docs/ or files)
    """
    parts = PurePosixPath(path).parts

    # Need at least: root/area/template_name/major/minor
    if len(parts) < 5:
        return None

    # Skip the root directory (e.g., "submodel-templates-main")
    area_idx = _find_area_index(parts)
    if area_idx is None:
        return None

    area = parts[area_idx]
    if area not in ("published", "deprecated"):
        return None

    # Template name follows the area
    if area_idx + 1 >= len(parts):
        return None
    template_name = parts[area_idx + 1]

    # Version parts follow the template name
    version_parts = _extract_version_parts(parts[area_idx + 2 :])
    if not version_parts:
        return None

    # Check if this is a leaf version folder (not an intermediate)
    # We want the deepest version folder that has a docs/ or similar
    if not _is_leaf_version_path(path, parts, area_idx, version_parts):
        return None

    version = SemVer.from_path_parts(version_parts)
    if version is None:
        return None

    # Build the repository path (without the root dir)
    repo_path = "/".join(parts[area_idx:])
    # URL-encode the path (spaces become %20)
    encoded_path = "/".join(quote(p, safe="") for p in parts[area_idx:])
    github_url = f"{GITHUB_BASE_URL}/tree/main/{encoded_path}"

    return GitHubTemplateEntry(
        template_name=template_name,
        area=area,
        version=version,
        repo_path=repo_path,
        github_url=github_url,
        slug=slugify(template_name),
    )


def _find_area_index(parts: tuple[str, ...]) -> int | None:
    """Find the index of 'published' or 'deprecated' in path parts."""
    for i, part in enumerate(parts):
        if part in ("published", "deprecated"):
            return i
    return None


def _extract_version_parts(parts: tuple[str, ...]) -> list[str]:
    """Extract version number parts from path segments.

    Returns list of numeric strings like ['3', '0', '1'].
    """
    version_parts: list[str] = []

    for part in parts:
        if re.match(r"^\d+$", part):
            version_parts.append(part)
        else:
            # Stop at first non-numeric part (e.g., 'docs')
            break

    return version_parts


def _is_leaf_version_path(
    path: str, parts: tuple[str, ...], area_idx: int, version_parts: list[str]
) -> bool:
    """Check if this is the deepest version folder.

    We consider it a leaf if:
    - The path ends right after the version parts, or
    - The next part is 'docs' or similar content folder
    """
    # Calculate expected length for a version folder
    # area_idx + 1 (template) + len(version_parts) + 1 (trailing slash makes extra part)
    expected_min_parts = area_idx + 1 + len(version_parts) + 1

    # If path has exactly the version folder (no subdirs), it's a leaf
    if len(parts) == expected_min_parts:
        return True

    # If next part after version is docs/ or contains files
    if len(parts) > expected_min_parts:
        next_part = parts[area_idx + 1 + len(version_parts)]
        # Don't treat the version folder itself as leaf if it has more version parts
        # Accept common content folders (non-numeric paths)
        return not re.match(r"^\d+$", next_part)

    return False


async def scrape_github() -> list[GitHubTemplateEntry]:
    """Scrape the GitHub repository for all template versions."""
    zip_content = await fetch_github_zip()
    return enumerate_zip(zip_content)


def group_by_template(entries: list[GitHubTemplateEntry]) -> dict[str, list[GitHubTemplateEntry]]:
    """Group entries by template slug."""
    grouped: dict[str, list[GitHubTemplateEntry]] = {}

    for entry in entries:
        if entry.slug not in grouped:
            grouped[entry.slug] = []
        grouped[entry.slug].append(entry)

    # Sort versions within each template
    for versions in grouped.values():
        versions.sort(key=lambda e: e.version, reverse=True)

    return grouped
