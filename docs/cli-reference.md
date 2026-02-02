---
layout: default
title: CLI Reference
---

# CLI Reference

Complete reference for all `smt-index` commands.

## Global Options

```bash
smt-index [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version and exit |

---

## Commands

### `build`

Build the submodel template index from all sources.

```bash
smt-index build [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--out`, `-o` | `dist/` | Output directory for generated files |
| `--no-playwright` | `false` | Disable Playwright fallback for IDTA scraping |

#### Output Files

- `index.json` - Structured JSON with full metadata
- `index.csv` - Flat CSV format (one row per template+version)

#### Example

```bash
# Build to default location
smt-index build

# Build to custom directory
smt-index build --out /path/to/output/
```

---

### `serve`

Start the REST API server.

```bash
smt-index serve [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host`, `-h` | `127.0.0.1` | Host to bind to |
| `--port`, `-p` | `8000` | Port to run the server on |
| `--index`, `-i` | `dist/index.json` | Path to index file |

#### Example

```bash
# Start on default port
smt-index serve

# Start on custom port, accessible from network
smt-index serve --port 3000 --host 0.0.0.0

# Use specific index file
smt-index serve --index /path/to/index.json
```

---

### `validate`

Validate an index file for correctness.

```bash
smt-index validate [OPTIONS]
```

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--index`, `-i` | `dist/index.json` | Path to index file to validate |

#### Checks Performed

- Schema version present
- Required template fields exist
- URLs are valid format
- No duplicate template IDs
- Version numbers are parseable

#### Example

```bash
# Validate default location
smt-index validate

# Validate specific file
smt-index validate --index /path/to/index.json
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Validation passed |
| `1` | Validation failed |

---

### `version`

Display the current version.

```bash
smt-index version
```

---

## Examples

### CI/CD Pipeline

```bash
#!/bin/bash
set -e

# Build fresh index
smt-index build --out artifacts/

# Validate before publishing
smt-index validate --index artifacts/index.json

# Upload artifacts
# ...
```

### Development Workflow

```bash
# Build and serve in one terminal
smt-index build && smt-index serve

# In another terminal, test queries
curl http://localhost:8000/templates | jq '.templates | length'
```

---

[← Quick Start](quickstart.md) | [API Reference →](api-reference.md)
