---
layout: default
title: Installation
---

# Installation

## Prerequisites

- **Python 3.11+** - Required for running the CLI
- **pip** - Python package manager
- **Chromium** (optional) - Required for IDTA scraper fallback when httpx fails

## Install from PyPI

```bash
pip install smt-index
```

## Install from Source

```bash
# Clone the repository
git clone https://github.com/hadijannat/open-smt-index.git
cd open-smt-index

# Install in development mode
pip install -e .
```

## Optional: Playwright Scraper

The IDTA Content Hub is first scraped using httpx. If no templates are found (e.g., if the page requires JavaScript rendering), the scraper can fall back to Playwright.

To enable this fallback:

```bash
# Install with scraper extras
pip install "smt-index[scraper]"

# Install Chromium browser for Playwright
playwright install chromium
```

Without Playwright, the build command will still work but will show a warning if httpx cannot find templates.

## Verify Installation

```bash
# Check CLI is available
smt-index --help

# Check version
smt-index version
```

Expected output:

```
smt-index version 0.1.0
```

## Optional: Development Dependencies

For running tests, linting, and type checking:

```bash
pip install -e ".[dev]"
```

This includes:
- `pytest` - Testing framework
- `ruff` - Linter and formatter
- `mypy` - Type checker
- `playwright` - Browser automation (for scraper tests)

## Troubleshooting

### Command not found: smt-index

Ensure the Python scripts directory is in your PATH:

```bash
# Check where pip installs scripts
python -m site --user-base

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$PATH:$(python -m site --user-base)/bin"
```

### Playwright browser issues

If Playwright fails to launch:

```bash
# Reinstall browsers
playwright install --force chromium

# Check system dependencies (Linux)
playwright install-deps chromium
```

### Build works but no templates found

If `smt-index build` completes but finds no IDTA templates:

1. Check if the IDTA website is accessible
2. Try installing Playwright for JavaScript-rendered content:
   ```bash
   pip install "smt-index[scraper]"
   playwright install chromium
   ```
3. Re-run the build

---

[← Back to Home](index.md) | [Quick Start →](quickstart.md)
