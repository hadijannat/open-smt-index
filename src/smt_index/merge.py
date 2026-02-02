"""Merge logic to combine IDTA and GitHub data sources."""

from collections import defaultdict
from urllib.parse import quote

from rich.console import Console

from smt_index.models import TemplateRecord, TemplateVersion, VersionLinks
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

    # Group IDTA templates by slug (same template may have multiple version entries)
    # Using slug ensures entries with/without IDTA numbers get grouped together
    idta_by_slug: dict[str, list[IDTATemplate]] = defaultdict(list)
    for idta in idta_templates:
        idta_by_slug[idta.slug].append(idta)

    # Process grouped IDTA templates
    records: list[TemplateRecord] = []

    for _slug, idta_group in idta_by_slug.items():
        # Find best primary entry (prefer one with IDTA number)
        primary = next((t for t in idta_group if t.idta_number), idta_group[0])

        # Try to find matching GitHub entries (using primary IDTA entry)
        github_matches = _find_github_matches(
            primary, github_by_slug, github_by_url_prefix
        )

        if github_matches:
            matched_github_slugs.add(github_matches[0].slug)

        record = _create_record_from_idta_group(idta_group, github_matches)
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
        base_path = _template_root_path(entry.repo_path)
        encoded = _encode_path(base_path)
        base_url = f"https://github.com/admin-shell-io/submodel-templates/tree/main/{encoded}"
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
        if "/tree/" in normalized_url:
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


def _template_root_path(repo_path: str) -> str:
    """Strip version segments to get the template root path."""
    parts = repo_path.strip("/").split("/")
    while parts and parts[-1].isdigit():
        parts.pop()
    return "/".join(parts)


def _encode_path(path: str) -> str:
    """URL-encode each path segment."""
    return "/".join(quote(p, safe="") for p in path.split("/"))


def _create_record_from_idta_group(
    idta_group: list[IDTATemplate],
    github_entries: list[GitHubTemplateEntry],
) -> TemplateRecord:
    """Create a TemplateRecord from multiple IDTA entries and optional GitHub matches.

    When the same template has multiple version entries in IDTA, they're combined here.
    """
    if not idta_group:
        raise ValueError("Cannot create record from empty IDTA group")

    # Find best primary entry (prefer one with IDTA number for consistent ID)
    primary = next((t for t in idta_group if t.idta_number), idta_group[0])

    # Collect all versions from IDTA entries
    versions_map: dict[str, TemplateVersion] = {}

    for idta in idta_group:
        if idta.version:
            version_str = _normalize_version(idta.version)
            if version_str not in versions_map:
                versions_map[version_str] = TemplateVersion(
                    version=version_str,
                    links=VersionLinks(pdf=idta.pdf_link, github=idta.github_link),
                )
            else:
                # Merge links if this version already exists
                existing = versions_map[version_str]
                if not existing.links.pdf and idta.pdf_link:
                    existing.links.pdf = idta.pdf_link
                if not existing.links.github and idta.github_link:
                    existing.links.github = idta.github_link

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

    # Find the best description (prefer non-None)
    description = next((t.description for t in idta_group if t.description), None)

    # Generate unique ID: prefer idta-{number}-{slug} for uniqueness
    if primary.idta_number:
        template_id = f"idta-{primary.idta_number}-{primary.slug}"
    else:
        template_id = f"ext-{primary.slug}"

    return TemplateRecord(
        id=template_id,
        name=primary.name,
        idta_number=primary.idta_number,
        status=primary.status,
        description=description,
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

    # Clear any existing markers then set latest
    for v in sorted_versions:
        v.is_latest = False
    if sorted_versions:
        sorted_versions[0].is_latest = True

    return sorted_versions
