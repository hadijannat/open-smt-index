# Open SMT Index

A CLI tool for creating a machine-readable index of AAS Submodel Templates by combining data from the IDTA registry and GitHub repository.

## Features

- **Build**: Scrapes IDTA Content Hub and GitHub to create a unified template index
- **Serve**: FastAPI server for querying the index
- **Validate**: Sanity checks on the built index

## Installation

```bash
pip install -e .
playwright install chromium  # Required for IDTA scraper fallback
```

## Usage

### Build the index

```bash
smt-index build --out dist/
```

This creates:
- `dist/index.json` - Structured index with all template metadata
- `dist/index.csv` - Flat view with one row per template+version

### Serve the API

```bash
smt-index serve --port 8000
```

Endpoints:
- `GET /health` - Health check
- `GET /templates` - List all templates (supports `?status=` and `?q=` filters)
- `GET /templates/{id}` - Get a specific template

### Validate the index

```bash
smt-index validate --index dist/index.json
```

## Data Sources

- **IDTA Content Hub**: Official registry with status, descriptions, and PDF links
- **GitHub Repository**: `admin-shell-io/submodel-templates` with version folders

## Output Schema

```json
{
  "schema_version": "1.0",
  "generated_at": "2024-01-01T00:00:00Z",
  "sources": {
    "idta_registered_templates": "https://industrialdigitaltwin.org/...",
    "github_submodel_templates": "https://github.com/admin-shell-io/..."
  },
  "templates": [...]
}
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## License

Apache License 2.0
