"""Utility functions for semver parsing and name normalization."""

import re
from functools import total_ordering

from slugify import slugify as _slugify


def slugify(name: str) -> str:
    """Convert a template name to a URL-safe slug.

    Examples:
        >>> slugify("Digital Nameplate")
        'digital-nameplate'
        >>> slugify("Generic Frame for Technical Data")
        'generic-frame-for-technical-data'
    """
    return _slugify(name, lowercase=True, separator="-")


@total_ordering
class SemVer:
    """A semantic version that supports comparison and sorting."""

    def __init__(self, major: int, minor: int, patch: int = 0):
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def parse(cls, version_str: str) -> "SemVer | None":
        """Parse a version string into a SemVer object.

        Supports formats:
        - "1.0.0" or "1.0" or "1"
        - "V1.0" or "v1.0"

        Returns None if parsing fails.
        """
        # Remove leading 'v' or 'V'
        version_str = version_str.lstrip("vV").strip()

        # Try to match version patterns
        match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?$", version_str)
        if not match:
            return None

        major = int(match.group(1))
        minor = int(match.group(2)) if match.group(2) else 0
        patch = int(match.group(3)) if match.group(3) else 0

        return cls(major, minor, patch)

    @classmethod
    def from_path_parts(cls, parts: list[str]) -> "SemVer | None":
        """Create a SemVer from path parts like ['3', '0', '1'].

        Handles 2 or 3 part versions.
        """
        if len(parts) < 2:
            return None

        try:
            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2]) if len(parts) >= 3 else 0
            return cls(major, minor, patch)
        except ValueError:
            return None

    def __str__(self) -> str:
        """Return version as 'major.minor.patch' string."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        return f"SemVer({self.major}, {self.minor}, {self.patch})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    def __lt__(self, other: "SemVer") -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))


def parse_version(version_str: str) -> SemVer | None:
    """Parse a version string, returning None if invalid."""
    return SemVer.parse(version_str)


def sort_versions(versions: list[str], reverse: bool = True) -> list[str]:
    """Sort version strings by semantic version.

    Args:
        versions: List of version strings
        reverse: If True (default), sort descending (newest first)

    Returns:
        Sorted list of version strings. Invalid versions are placed at the end.
    """
    valid: list[tuple[SemVer, str]] = []
    invalid: list[str] = []

    for v in versions:
        semver = SemVer.parse(v)
        if semver:
            valid.append((semver, v))
        else:
            invalid.append(v)

    # Sort valid versions by semver
    valid.sort(key=lambda x: x[0], reverse=reverse)

    # Invalid versions always go at the end, sorted alphabetically
    invalid.sort()

    return [v for _, v in valid] + invalid


def extract_idta_number(text: str) -> str | None:
    """Extract an IDTA number like '02006' from text.

    Examples:
        >>> extract_idta_number("IDTA 02006 Digital Nameplate")
        '02006'
        >>> extract_idta_number("SMT 02006-3-0")
        '02006'
    """
    match = re.search(r"\b(\d{5})\b", text)
    return match.group(1) if match else None


def normalize_github_url(url: str) -> str:
    """Normalize a GitHub URL to a consistent format.

    Removes trailing slashes and /tree/main/ variations.
    """
    url = url.rstrip("/")
    # Remove /tree/main or /tree/master suffix
    url = re.sub(r"/tree/(main|master)/?$", "", url)
    return url
