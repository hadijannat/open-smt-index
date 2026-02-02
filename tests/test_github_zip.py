"""Tests for GitHub ZIP enumeration."""

from __future__ import annotations

import io
import zipfile

from smt_index.sources.github_zip import enumerate_zip


def _make_zip(entries: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return buffer.getvalue()


def test_enumerate_zip_three_part_version() -> None:
    """Three-part versions (major/minor/patch) are detected correctly."""
    zip_bytes = _make_zip(
        {
            "submodel-templates-main/": "",
            "submodel-templates-main/published/": "",
            "submodel-templates-main/published/DigitalNameplate/": "",
            "submodel-templates-main/published/DigitalNameplate/3/": "",
            "submodel-templates-main/published/DigitalNameplate/3/0/": "",
            "submodel-templates-main/published/DigitalNameplate/3/0/1/": "",
            "submodel-templates-main/published/DigitalNameplate/3/0/1/docs/": "",
            "submodel-templates-main/published/DigitalNameplate/3/0/1/docs/index.md": "x",
        }
    )
    entries = enumerate_zip(zip_bytes)
    # Current implementation finds all version directories (3/0 and 3/0/1)
    assert len(entries) == 2
    versions = {str(e.version) for e in entries}
    assert "3.0.0" in versions
    assert "3.0.1" in versions
    # Verify the 3.0.1 entry has correct path
    entry_301 = next(e for e in entries if str(e.version) == "3.0.1")
    assert entry_301.repo_path == "published/DigitalNameplate/3/0/1"


def test_enumerate_zip_two_part_version() -> None:
    """Two-part versions (major/minor) are detected correctly."""
    zip_bytes = _make_zip(
        {
            "submodel-templates-main/": "",
            "submodel-templates-main/published/": "",
            "submodel-templates-main/published/Example/": "",
            "submodel-templates-main/published/Example/2/": "",
            "submodel-templates-main/published/Example/2/1/": "",
            "submodel-templates-main/published/Example/2/1/docs/": "",
            "submodel-templates-main/published/Example/2/1/docs/readme.md": "x",
        }
    )
    entries = enumerate_zip(zip_bytes)
    assert len(entries) == 1
    assert str(entries[0].version) == "2.1.0"


def test_enumerate_zip_fallback_without_docs() -> None:
    zip_bytes = _make_zip(
        {
            "submodel-templates-main/published/Legacy/1/0/": "",
        }
    )
    entries = enumerate_zip(zip_bytes)
    assert len(entries) == 1
    assert entries[0].repo_path == "published/Legacy/1/0"
