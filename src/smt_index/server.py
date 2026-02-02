"""FastAPI server for querying the SMT Index."""

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from smt_index.models import TemplateIndex, TemplateRecord


def create_app(index_path: Path) -> FastAPI:
    """Create a FastAPI app with the given index loaded.

    Args:
        index_path: Path to the index.json file

    Returns:
        Configured FastAPI application
    """
    # Load the index
    with open(index_path, encoding="utf-8") as f:
        data = json.load(f)
    index = TemplateIndex.model_validate(data)

    # Build a lookup dict for faster access
    templates_by_id: dict[str, TemplateRecord] = {t.id: t for t in index.templates}

    app = FastAPI(
        title="SMT Index API",
        description="REST API for querying AAS Submodel Templates index",
        version="1.0.0",
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}

    @app.get("/templates")
    async def list_templates(
        status: str | None = Query(
            default=None,
            description="Filter by status (e.g., 'Published', 'In Review')",
        ),
        q: str | None = Query(
            default=None,
            description="Search query for template name or description",
        ),
    ) -> list[dict[str, Any]]:
        """List all templates with optional filtering."""
        results = index.templates

        # Filter by status
        if status:
            status_lower = status.lower()
            results = [t for t in results if t.status.lower() == status_lower]

        # Filter by search query
        if q:
            q_lower = q.lower()
            results = [
                t
                for t in results
                if q_lower in t.name.lower()
                or (t.description and q_lower in t.description.lower())
                or (t.idta_number and q_lower in t.idta_number)
                or q_lower in t.id.lower()
            ]

        # Return summary format (not full versions)
        return [
            {
                "id": t.id,
                "name": t.name,
                "idta_number": t.idta_number,
                "status": t.status,
                "version_count": len(t.versions),
                "latest_version": t.versions[0].version if t.versions else None,
            }
            for t in results
        ]

    @app.get("/templates/{template_id}")
    async def get_template(template_id: str) -> dict[str, Any]:
        """Get a specific template by ID."""
        template = templates_by_id.get(template_id)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template not found: {template_id}")

        return template.model_dump(mode="json")

    @app.get("/index")
    async def get_full_index() -> JSONResponse:
        """Get the full index (for debugging/export)."""
        return JSONResponse(content=index.model_dump(mode="json"))

    @app.get("/stats")
    async def get_stats() -> dict[str, Any]:
        """Get index statistics."""
        # Count by status
        status_counts: dict[str, int] = {}
        for t in index.templates:
            status_counts[t.status] = status_counts.get(t.status, 0) + 1

        # Count by ID prefix
        prefix_counts: dict[str, int] = {}
        for t in index.templates:
            prefix = t.id.split("-")[0]
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

        return {
            "schema_version": index.schema_version,
            "generated_at": index.generated_at.isoformat(),
            "total_templates": len(index.templates),
            "total_versions": sum(len(t.versions) for t in index.templates),
            "by_status": status_counts,
            "by_prefix": prefix_counts,
        }

    return app


# For direct uvicorn usage: uvicorn smt_index.server:app
# This creates a default app with dist/index.json
def _get_default_app() -> FastAPI:
    """Get the default app for direct uvicorn usage."""
    index_path = Path("dist/index.json")
    if index_path.exists():
        return create_app(index_path)
    else:
        # Return a minimal app that explains the issue
        app = FastAPI(title="SMT Index API (Not Configured)")

        @app.get("/")
        async def root() -> dict[str, str]:
            return {
                "error": "Index not found",
                "message": "Run 'smt-index build' to create the index, or use 'smt-index serve --index <path>'",
            }

        return app


app = _get_default_app()
