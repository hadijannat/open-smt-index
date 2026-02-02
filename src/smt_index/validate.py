"""Validation checks for the built index."""

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.table import Table

from smt_index.models import TemplateIndex
from smt_index.util import SemVer

console = Console()


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""

    severity: Severity
    template_id: str | None
    message: str


def validate_index(index: TemplateIndex) -> list[ValidationIssue]:
    """Run all validation checks on an index.

    Checks:
    - Duplicate template IDs
    - Missing required links (PDF or GitHub)
    - Invalid/unparseable versions
    - Templates without any versions
    - Broken URL patterns
    """
    issues: list[ValidationIssue] = []

    issues.extend(_check_duplicate_ids(index))
    issues.extend(_check_missing_links(index))
    issues.extend(_check_invalid_versions(index))
    issues.extend(_check_no_versions(index))
    issues.extend(_check_url_patterns(index))

    return issues


def _check_duplicate_ids(index: TemplateIndex) -> list[ValidationIssue]:
    """Check for duplicate template IDs."""
    issues: list[ValidationIssue] = []
    seen: dict[str, int] = {}

    for template in index.templates:
        if template.id in seen:
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    template_id=template.id,
                    message=f"Duplicate template ID (first at index {seen[template.id]})",
                )
            )
        else:
            seen[template.id] = len(seen)

    return issues


def _check_missing_links(index: TemplateIndex) -> list[ValidationIssue]:
    """Check for templates/versions missing required links."""
    issues: list[ValidationIssue] = []

    for template in index.templates:
        for version in template.versions:
            has_pdf = bool(version.links.pdf)
            has_github = bool(version.links.github)

            if not has_pdf and not has_github:
                issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        template_id=template.id,
                        message=f"Version {version.version} has no PDF or GitHub link",
                    )
                )

    return issues


def _check_invalid_versions(index: TemplateIndex) -> list[ValidationIssue]:
    """Check for unparseable version strings."""
    issues: list[ValidationIssue] = []

    for template in index.templates:
        for version in template.versions:
            semver = SemVer.parse(version.version)
            if semver is None:
                issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        template_id=template.id,
                        message=f"Invalid version format: '{version.version}'",
                    )
                )

    return issues


def _check_no_versions(index: TemplateIndex) -> list[ValidationIssue]:
    """Check for templates without any versions."""
    issues: list[ValidationIssue] = []

    for template in index.templates:
        if not template.versions:
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    template_id=template.id,
                    message="Template has no versions",
                )
            )

    return issues


def _check_url_patterns(index: TemplateIndex) -> list[ValidationIssue]:
    """Check for broken or malformed URLs."""
    issues: list[ValidationIssue] = []

    url_pattern = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

    for template in index.templates:
        for version in template.versions:
            # Check PDF link
            if version.links.pdf and not url_pattern.match(version.links.pdf):
                issues.append(
                    ValidationIssue(
                        severity=Severity.WARNING,
                        template_id=template.id,
                        message=f"Malformed PDF URL: '{version.links.pdf}'",
                    )
                )

            # Check GitHub link
            if version.links.github:
                if not url_pattern.match(version.links.github):
                    issues.append(
                        ValidationIssue(
                            severity=Severity.WARNING,
                            template_id=template.id,
                            message=f"Malformed GitHub URL: '{version.links.github}'",
                        )
                    )
                elif "github.com" not in version.links.github.lower():
                    issues.append(
                        ValidationIssue(
                            severity=Severity.INFO,
                            template_id=template.id,
                            message=f"Non-GitHub URL in github field: '{version.links.github}'",
                        )
                    )

    return issues


def load_and_validate(index_path: Path) -> tuple[TemplateIndex | None, list[ValidationIssue]]:
    """Load an index from file and validate it."""
    try:
        with open(index_path, encoding="utf-8") as f:
            data = json.load(f)
        index = TemplateIndex.model_validate(data)
    except FileNotFoundError:
        return None, [
            ValidationIssue(
                severity=Severity.ERROR,
                template_id=None,
                message=f"Index file not found: {index_path}",
            )
        ]
    except json.JSONDecodeError as e:
        return None, [
            ValidationIssue(
                severity=Severity.ERROR,
                template_id=None,
                message=f"Invalid JSON: {e}",
            )
        ]
    except Exception as e:
        return None, [
            ValidationIssue(
                severity=Severity.ERROR,
                template_id=None,
                message=f"Failed to parse index: {e}",
            )
        ]

    issues = validate_index(index)
    return index, issues


def print_validation_report(
    index: TemplateIndex | None,
    issues: list[ValidationIssue],
) -> bool:
    """Print a validation report and return True if valid (no errors)."""
    # Print summary
    if index:
        console.print("\n[bold]Index Summary[/bold]")
        console.print(f"  Schema version: {index.schema_version}")
        console.print(f"  Generated: {index.generated_at}")
        console.print(f"  Templates: {len(index.templates)}")

        # Count versions
        total_versions = sum(len(t.versions) for t in index.templates)
        console.print(f"  Total versions: {total_versions}")

    # Count issues by severity
    errors = [i for i in issues if i.severity == Severity.ERROR]
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    infos = [i for i in issues if i.severity == Severity.INFO]

    console.print("\n[bold]Validation Results[/bold]")
    console.print(f"  Errors: {len(errors)}")
    console.print(f"  Warnings: {len(warnings)}")
    console.print(f"  Info: {len(infos)}")

    # Print issues table
    if issues:
        console.print()
        table = Table(title="Issues")
        table.add_column("Severity", style="bold")
        table.add_column("Template ID")
        table.add_column("Message")

        for issue in issues:
            style = {
                Severity.ERROR: "red",
                Severity.WARNING: "yellow",
                Severity.INFO: "blue",
            }.get(issue.severity, "white")

            table.add_row(
                issue.severity.value,
                issue.template_id or "-",
                issue.message,
                style=style,
            )

        console.print(table)

    # Return status
    is_valid = len(errors) == 0
    if is_valid:
        console.print("\n[bold green]Validation passed![/bold green]")
    else:
        console.print("\n[bold red]Validation failed with errors.[/bold red]")

    return is_valid
