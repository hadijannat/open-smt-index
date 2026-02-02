---
layout: default
title: Installation
---

# Installation

## Prerequisites

- **Python 3.11+** - Required for running the CLI
- **pip** - Python package manager
- **Chromium** - Required for IDTA scraper (installed via Playwright)

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

## Install Playwright Browser

The IDTA Content Hub scraper requires a browser for JavaScript-rendered pages:

```bash
playwright install chromium
```

This downloads a Chromium browser that Playwright will use for scraping.

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

For running tests and linting:

```bash
pip install -e ".[dev]"
```

This includes:
- `pytest` - Testing framework
- `ruff` - Linter and formatter
- `mypy` - Type checker

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

---

[← Back to Home](index.md) | [Quick Start →](quickstart.md)
