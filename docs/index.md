---
layout: default
title: Open SMT Index
---

# Open SMT Index

A CLI tool for creating a **machine-readable index** of AAS Submodel Templates by combining data from the IDTA registry and GitHub repository.

---

## What is SMT Index?

The **Asset Administration Shell (AAS)** ecosystem includes standardized Submodel Templates maintained by the Industrial Digital Twin Association (IDTA). However, accessing and querying these templates programmatically has been challenging.

**Open SMT Index** solves this by:
- Scraping the official IDTA Content Hub for template metadata and status
- Parsing the admin-shell-io/submodel-templates GitHub repository for version information
- Merging both sources into a unified, queryable index
- Exposing the data via REST API or static JSON/CSV files

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Build** | Merge IDTA registry + GitHub sources into unified index |
| **Serve** | Query templates via REST API with filtering support |
| **Validate** | Sanity checks to ensure data quality |
| **Export** | Output as JSON (structured) or CSV (flat) |

---

## Quick Start

```bash
# Install
pip install smt-index
playwright install chromium

# Build the index
smt-index build --out dist/

# Serve via API
smt-index serve --port 8000

# Query templates
curl http://localhost:8000/templates
```

---

## Documentation

- [Installation](installation.md) - Detailed setup instructions
- [Quick Start](quickstart.md) - Get up and running in 5 minutes
- [CLI Reference](cli-reference.md) - All commands and options
- [API Reference](api-reference.md) - REST endpoint documentation
- [Output Schema](output-schema.md) - JSON and CSV format details
- [Examples](examples.md) - Common use cases and integrations
- [Contributing](contributing.md) - Development guide

---

## Data Sources

| Source | URL | Data Provided |
|--------|-----|---------------|
| IDTA Content Hub | [industrialdigitaltwin.org](https://industrialdigitaltwin.org/content-hub/teilmodelle) | Status, descriptions, PDF links |
| GitHub Repository | [admin-shell-io/submodel-templates](https://github.com/admin-shell-io/submodel-templates) | Version folders, AASX files |

---

## License

Apache License 2.0 - See [LICENSE](https://github.com/hadijannat/open-smt-index/blob/main/LICENSE)
