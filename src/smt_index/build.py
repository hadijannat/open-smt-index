"""Build command to orchestrate index creation."""

import asyncio
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from smt_index.merge import merge_sources
from smt_index.models import IndexSources, TemplateIndex
from smt_index.sources.github_zip import scrape_github
from smt_index.sources.idta import scrape_idta

console = Console()


async def build_index(
    output_dir: Path,
    use_playwright: bool = True,
) -> TemplateIndex:
    """Build the complete template index.

    Orchestrates:
    1. Fetch IDTA Content Hub data
    2. Fetch GitHub repository data
    3. Merge sources
    4. Output JSON and CSV

    Args:
        output_dir: Directory to write index.json and index.csv
        use_playwright: Whether to use Playwright fallback for IDTA

    Returns:
        The built TemplateIndex
    """
    console.print("[bold blue]Building SMT Index...[/bold blue]")

    # Fetch data from both sources concurrently
    idta_task = scrape_idta(use_playwright_fallback=use_playwright)
    github_task = scrape_github()

    (idta_templates, idta_url), github_entries = await asyncio.gather(idta_task, github_task)

    # Merge the data
    records = merge_sources(idta_templates, github_entries)

    # Create the index
    index = TemplateIndex(
        schema_version="1.0",
        generated_at=datetime.now(UTC),
        sources=IndexSources(
            idta_registered_templates=idta_url,
            github_submodel_templates="https://github.com/admin-shell-io/submodel-templates",
        ),
        templates=records,
    )

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON output
    json_path = output_dir / "index.json"
    _write_json(index, json_path)

    # Write CSV output
    csv_path = output_dir / "index.csv"
    _write_csv(index, csv_path)

    console.print("\n[bold green]Index built successfully![/bold green]")
    console.print(f"  Templates: {len(index.templates)}")
    console.print(f"  JSON: {json_path}")
    console.print(f"  CSV: {csv_path}")

    return index


def _write_json(index: TemplateIndex, path: Path) -> None:
    """Write the index as JSON."""
    console.print(f"[blue]Writing {path}...[/blue]")

    # Use model_dump with mode='json' for proper serialization
    data = index.model_dump(mode="json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def _write_csv(index: TemplateIndex, path: Path) -> None:
    """Write a flat CSV with one row per template+version."""
    console.print(f"[blue]Writing {path}...[/blue]")

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "template_id",
            "template_name",
            "idta_number",
            "status",
            "version",
            "is_latest",
            "pdf_link",
            "github_link",
            "github_area",
            "github_repo_path",
            "github_versions",
        ])

        # Rows
        for template in index.templates:
            if template.versions:
                for version in template.versions:
                    # Get GitHub area/path from first GitHub entry if available
                    gh_area = ""
                    gh_path = ""
                    if version.github:
                        gh_area = version.github[0].area
                        gh_path = version.github[0].repo_path
                    gh_versions = ";".join(
                        [f"{g.area}:{g.repo_path}" for g in version.github]
                    )

                    writer.writerow([
                        template.id,
                        template.name,
                        template.idta_number or "",
                        template.status,
                        version.version,
                        version.is_latest,
                        version.links.pdf or "",
                        version.links.github or "",
                        gh_area,
                        gh_path,
                        gh_versions,
                    ])
            else:
                # Template with no versions
                writer.writerow([
                    template.id,
                    template.name,
                    template.idta_number or "",
                    template.status,
                    "",  # version
                    "",  # is_latest
                    "",  # pdf_link
                    "",  # github_link
                    "",  # github_area
                    "",  # github_repo_path
                    "",  # github_versions
                ])


def run_build(output_dir: Path, use_playwright: bool = True) -> TemplateIndex:
    """Synchronous wrapper for build_index."""
    return asyncio.run(build_index(output_dir, use_playwright))
