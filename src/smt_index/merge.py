"""Merge logic to combine IDTA and GitHub data sources."""

from collections import defaultdict

from rich.console import Console

from smt_index.models import (
    TemplateRecord,
    TemplateVersion,
    VersionLinks,
)
from smt_index.sources.github_zip import GitHubTemplateEntry, group_by_template
from smt_index.sources.idta import IDTATemplate
from smt_index.util import SemVer, normalize_github_url

console = Console()


def merge_sources(
    idta_templates: list[IDTATemplate],
    github_entries: list[GitHubTemplateEntry],
) -> list[TemplateRecord]:
    """Merge IDTA registry data with GitHub repository data.

    Matching strategy:
    1. Primary: Match by GitHub URL prefix
    2. Fallback: Match by normalized name (slug)

    Unmatched GitHub entries get 'gh-' prefix IDs.
    """
    # Group GitHub entries by template
    github_by_slug = group_by_template(github_entries)

    # Index for URL-based matching
    github_by_url_prefix = _build_url_index(github_entries)

    # Track which GitHub templates have been matched
    matched_github_slugs: set[str] = set()

    # Process IDTA templates
    records: list[TemplateRecord] = []

    for idta in idta_templates:
        # Try to find matching GitHub entries
        github_matches = _find_github_matches(
            idta, github_by_slug, github_by_url_prefix
        )

        if github_matches:
            matched_github_slugs.add(github_matches[0].slug)

        record = _create_record_from_idta(idta, github_matches)
        records.append(record)

    # Add unmatched GitHub-only templates
    for slug, gh_entries in github_by_slug.items():
        if slug not in matched_github_slugs:
            record = _create_record_from_github(gh_entries)
            records.append(record)

    # Sort by ID
    records.sort(key=lambda r: r.id)

    console.print(f"[green]Merged into {len(records)} template records[/green]")
    return records


def _build_url_index(entries: list[GitHubTemplateEntry]) -> dict[str, list[GitHubTemplateEntry]]:
    """Build an index of GitHub entries by URL prefix for matching."""
    index: dict[str, list[GitHubTemplateEntry]] = defaultdict(list)

    for entry in entries:
        # Extract the base URL (without version path)
        # e.g., https://github.com/admin-shell-io/submodel-templates/tree/main/published/DigitalNameplate
        base_url = entry.github_url.rsplit("/", len(str(entry.version).split(".")))[0]
        normalized = normalize_github_url(base_url)
        index[normalized].append(entry)

    return dict(index)


def _find_github_matches(
    idta: IDTATemplate,
    github_by_slug: dict[str, list[GitHubTemplateEntry]],
    github_by_url_prefix: dict[str, list[GitHubTemplateEntry]],
) -> list[GitHubTemplateEntry]:
    """Find GitHub entries matching an IDTA template."""
    # Try URL-based matching first
    if idta.github_link:
        normalized_url = normalize_github_url(idta.github_link)
        # Check for prefix match
        for url_prefix, entries in github_by_url_prefix.items():
            if normalized_url.startswith(url_prefix) or url_prefix.startswith(normalized_url):
                return entries

    # Fallback to slug-based matching
    if idta.slug in github_by_slug:
        return github_by_slug[idta.slug]

    # Try fuzzy slug matching (handle variations)
    for github_slug, entries in github_by_slug.items():
        if _slugs_match(idta.slug, github_slug):
            return entries

    return []


def _slugs_match(slug1: str, slug2: str) -> bool:
    """Check if two slugs are similar enough to be the same template."""
    # Exact match
    if slug1 == slug2:
        return True

    # One contains the other
    if slug1 in slug2 or slug2 in slug1:
        return True

    # Handle common variations
    # e.g., "digital-nameplate" vs "digitalnamplate"
    normalized1 = slug1.replace("-", "")
    normalized2 = slug2.replace("-", "")
    return normalized1 == normalized2


def _create_record_from_idta(
    idta: IDTATemplate,
    github_entries: list[GitHubTemplateEntry],
) -> TemplateRecord:
    """Create a TemplateRecord from IDTA data and optional GitHub matches."""
    # Collect all versions
    versions_map: dict[str, TemplateVersion] = {}

    # Add version from IDTA if available
    if idta.version:
        version_str = _normalize_version(idta.version)
        versions_map[version_str] = TemplateVersion(
            version=version_str,
            links=VersionLinks(pdf=idta.pdf_link, github=idta.github_link),
        )

    # Add/merge GitHub versions
    for gh_entry in github_entries:
        version_str = str(gh_entry.version)
        if version_str in versions_map:
            # Merge GitHub info into existing version
            versions_map[version_str].github.append(gh_entry.to_github_version())
            # Update GitHub link if not set
            if not versions_map[version_str].links.github:
                versions_map[version_str].links.github = gh_entry.github_url
        else:
            # New version from GitHub
            versions_map[version_str] = TemplateVersion(
                version=version_str,
                links=VersionLinks(github=gh_entry.github_url),
                github=[gh_entry.to_github_version()],
            )

    # Sort versions and mark latest
    versions = _sort_and_mark_latest(list(versions_map.values()))

    return TemplateRecord(
        id=idta.id,
        name=idta.name,
        idta_number=idta.idta_number,
        status=idta.status,
        description=idta.description,
        versions=versions,
    )


def _create_record_from_github(
    github_entries: list[GitHubTemplateEntry],
) -> TemplateRecord:
    """Create a TemplateRecord from GitHub-only data."""
    if not github_entries:
        raise ValueError("Cannot create record from empty GitHub entries")

    # Use first entry for template metadata
    first = github_entries[0]

    versions: list[TemplateVersion] = []
    for gh_entry in github_entries:
        version_str = str(gh_entry.version)
        versions.append(
            TemplateVersion(
                version=version_str,
                links=VersionLinks(github=gh_entry.github_url),
                github=[gh_entry.to_github_version()],
            )
        )

    # Sort and mark latest
    versions = _sort_and_mark_latest(versions)

    # Determine status from area
    status = "Published" if any(e.area == "published" for e in github_entries) else "unknown"

    return TemplateRecord(
        id=f"gh-{first.slug}",
        name=first.template_name,
        idta_number=None,
        status=status,  # type: ignore[arg-type]
        description=None,
        versions=versions,
    )


def _normalize_version(version: str) -> str:
    """Normalize a version string to semver format."""
    semver = SemVer.parse(version)
    if semver:
        return str(semver)
    return version


def _sort_and_mark_latest(versions: list[TemplateVersion]) -> list[TemplateVersion]:
    """Sort versions by semver (newest first) and mark the latest."""
    if not versions:
        return versions

    # Sort by parsed semver
    def sort_key(v: TemplateVersion) -> tuple[int, int, int, int]:
        semver = SemVer.parse(v.version)
        if semver:
            return (0, -semver.major, -semver.minor, -semver.patch)
        return (1, 0, 0, 0)

    sorted_versions = sorted(versions, key=sort_key)

    # Mark first (highest) version as latest
    if sorted_versions:
        sorted_versions[0].is_latest = True

    return sorted_versions
