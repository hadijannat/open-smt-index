"""CLI interface for SMT Index."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

app = typer.Typer(
    name="smt-index",
    help="CLI tool for indexing AAS Submodel Templates from IDTA and GitHub.",
    add_completion=False,
)
console = Console()


@app.command()
def build(
    out: Annotated[
        Path,
        typer.Option(
            "--out",
            "-o",
            help="Output directory for index.json and index.csv",
        ),
    ] = Path("dist"),
    no_playwright: Annotated[
        bool,
        typer.Option(
            "--no-playwright",
            help="Disable Playwright fallback for IDTA scraping",
        ),
    ] = False,
) -> None:
    """Build the SMT index from IDTA and GitHub sources."""
    from smt_index.build import run_build

    try:
        run_build(out, use_playwright=not no_playwright)
    except Exception as e:
        console.print(f"[bold red]Build failed:[/bold red] {e}")
        raise typer.Exit(1) from None


@app.command()
def serve(
    host: Annotated[
        str,
        typer.Option("--host", "-h", help="Host to bind to"),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Port to bind to"),
    ] = 8000,
    index: Annotated[
        Path,
        typer.Option("--index", "-i", help="Path to index.json file"),
    ] = Path("dist/index.json"),
) -> None:
    """Serve the SMT index via REST API."""
    import uvicorn

    from smt_index.server import create_app

    if not index.exists():
        console.print(f"[bold red]Index file not found:[/bold red] {index}")
        console.print("Run 'smt-index build' first to create the index.")
        raise typer.Exit(1)

    console.print(f"[blue]Loading index from {index}...[/blue]")
    app_instance = create_app(index)

    console.print(f"[green]Starting server at http://{host}:{port}[/green]")
    console.print("Press Ctrl+C to stop.")

    uvicorn.run(app_instance, host=host, port=port, log_level="info")


@app.command()
def validate(
    index: Annotated[
        Path,
        typer.Option("--index", "-i", help="Path to index.json file"),
    ] = Path("dist/index.json"),
) -> None:
    """Validate a built index for common issues."""
    from smt_index.validate import load_and_validate, print_validation_report

    index_obj, issues = load_and_validate(index)
    is_valid = print_validation_report(index_obj, issues)

    if not is_valid:
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show the version."""
    from smt_index import __version__

    console.print(f"smt-index {__version__}")


if __name__ == "__main__":
    app()
