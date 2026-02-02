---
layout: default
title: Quick Start
---

# Quick Start

Get a working submodel template index in under 5 minutes.

## 1. Install

```bash
pip install smt-index
playwright install chromium
```

## 2. Build the Index

```bash
smt-index build --out dist/
```

This will:
1. Scrape the IDTA Content Hub for template metadata
2. Fetch the GitHub repository for version information
3. Merge both sources into a unified index
4. Write output files to `dist/`

Output files created:
- `dist/index.json` - Structured JSON with full metadata
- `dist/index.csv` - Flat CSV with one row per template+version

## 3. Explore the Data

### View JSON structure

```bash
# Pretty print first template
python -c "import json; print(json.dumps(json.load(open('dist/index.json'))['templates'][0], indent=2))"
```

### View CSV in terminal

```bash
# Show first few rows
head -5 dist/index.csv
```

## 4. Serve via API

```bash
smt-index serve --port 8000
```

The API is now running at `http://localhost:8000`.

## 5. Query Templates

### List all templates

```bash
curl http://localhost:8000/templates
```

### Filter by status

```bash
curl "http://localhost:8000/templates?status=Published"
```

### Search by keyword

```bash
curl "http://localhost:8000/templates?q=carbon"
```

### Get specific template

```bash
curl http://localhost:8000/templates/IDTA-02006
```

## 6. Validate the Index

Ensure data quality:

```bash
smt-index validate --index dist/index.json
```

This checks for:
- Required fields present
- Valid URLs
- Consistent data structure

---

## Next Steps

- [CLI Reference](cli-reference.md) - All commands and options
- [API Reference](api-reference.md) - Full endpoint documentation
- [Output Schema](output-schema.md) - Understand the data format
- [Examples](examples.md) - Integration patterns

---

[← Installation](installation.md) | [CLI Reference →](cli-reference.md)
