---
layout: default
title: Contributing
---

# Contributing

Guide for setting up the development environment and contributing to Open SMT Index.

---

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/hadijannat/open-smt-index.git
cd open-smt-index
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
pip install -e ".[dev]"
playwright install chromium
```

### 4. Verify Setup

```bash
# Run tests
pytest -v

# Run linter
ruff check .

# Check formatting
ruff format --check .
```

---

## Project Structure

```
open-smt-index/
├── src/
│   └── smt_index/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py           # CLI commands
│       ├── server.py        # FastAPI server
│       ├── validate.py      # Index validation
│       ├── models.py        # Pydantic models
│       ├── util.py          # Utilities
│       └── sources/
│           ├── __init__.py
│           ├── idta.py      # IDTA scraper
│           └── github_zip.py # GitHub parser
├── tests/
│   └── ...
├── docs/                    # GitHub Pages documentation
├── dist/                    # Build output (gitignored)
├── pyproject.toml
└── README.md
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=smt_index

# Run specific test file
pytest tests/test_github_zip.py

# Run with verbose output
pytest -v
```

### Linting and Formatting

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .

# Check formatting only
ruff format --check .
```

### Type Checking

```bash
mypy src/smt_index
```

---

## Adding Features

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following existing patterns
- Add tests for new functionality
- Update documentation if needed

### 3. Run Checks

```bash
# All checks should pass
pytest
ruff check .
ruff format --check .
```

### 4. Commit and Push

```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### 5. Open Pull Request

Open a PR against the `main` branch with:
- Clear description of changes
- Any breaking changes noted
- Tests passing

---

## Code Style

### General Guidelines

- Follow PEP 8 (enforced by ruff)
- Use type hints for function signatures
- Write docstrings for public functions
- Keep functions focused and small

### Example

```python
from pydantic import BaseModel

class TemplateVersion(BaseModel):
    """A specific version of a submodel template."""

    version: str
    folder: str | None = None
    aasx_url: str | None = None
    pdf_url: str | None = None


def parse_version(version_str: str) -> tuple[int, int]:
    """
    Parse a version string into major and minor components.

    Args:
        version_str: Version string like "2.0" or "1.1"

    Returns:
        Tuple of (major, minor) version numbers

    Raises:
        ValueError: If version string is invalid
    """
    parts = version_str.split(".")
    if len(parts) != 2:
        raise ValueError(f"Invalid version format: {version_str}")
    return int(parts[0]), int(parts[1])
```

---

## Testing Guidelines

### Test Structure

```python
import pytest
from smt_index.sources.github_zip import parse_version

def test_parse_version_simple():
    """Test parsing a simple version string."""
    assert parse_version("2.0") == (2, 0)

def test_parse_version_with_minor():
    """Test parsing version with minor number."""
    assert parse_version("1.2") == (1, 2)

def test_parse_version_invalid():
    """Test that invalid versions raise ValueError."""
    with pytest.raises(ValueError):
        parse_version("invalid")
```

### Test Naming

- Test files: `test_<module>.py`
- Test functions: `test_<what_is_being_tested>`
- Use descriptive names that explain the test case

---

## Documentation

### Updating Docs

Documentation lives in the `docs/` folder and is deployed via GitHub Pages.

1. Edit markdown files in `docs/`
2. Preview locally (optional):
   ```bash
   cd docs && bundle exec jekyll serve
   ```
3. Commit changes - docs auto-deploy on push to `main`

### README Updates

Keep the README in sync with features. Update:
- Quick start examples if CLI changes
- Feature list for new capabilities
- Badges if CI/coverage changes

---

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG (if maintained)
3. Create a git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. CI will build and publish to PyPI (when configured)

---

## Getting Help

- Open an [issue](https://github.com/hadijannat/open-smt-index/issues) for bugs
- Start a [discussion](https://github.com/hadijannat/open-smt-index/discussions) for questions
- Check existing issues before creating new ones

---

[← Examples](examples.md) | [Home](index.md)
