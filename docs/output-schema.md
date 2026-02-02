---
layout: default
title: Output Schema
---

# Output Schema

Documentation for the JSON and CSV output formats.

---

## JSON Format

The primary output file `index.json` contains the complete index.

### Top-Level Structure

```json
{
  "schema_version": "1.0",
  "generated_at": "2024-01-15T10:30:00Z",
  "sources": {
    "idta_registered_templates": "https://industrialdigitaltwin.org/content-hub/teilmodelle",
    "github_submodel_templates": "https://github.com/admin-shell-io/submodel-templates"
  },
  "provenance": {
    "build_started_at": "2024-01-15T10:29:55Z",
    "build_completed_at": "2024-01-15T10:30:00Z",
    "build_duration_seconds": 5.2,
    "sources": [
      {
        "url": "https://industrialdigitaltwin.org/content-hub/teilmodelle",
        "fetched_at": "2024-01-15T10:29:58Z",
        "record_count": 42
      },
      {
        "url": "https://github.com/admin-shell-io/submodel-templates",
        "fetched_at": "2024-01-15T10:29:57Z",
        "record_count": 35
      }
    ],
    "git_commit": "abc123def456",
    "tool_version": "0.1.0"
  },
  "templates": [...]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Version of this schema format |
| `generated_at` | string | ISO 8601 timestamp of generation |
| `sources` | object | URLs of data sources |
| `provenance` | object | Build provenance metadata (optional) |
| `templates` | array | List of template objects |

### Build Provenance Object

The `provenance` field contains metadata about the build process.

| Field | Type | Description |
|-------|------|-------------|
| `build_started_at` | string | ISO 8601 timestamp when build started |
| `build_completed_at` | string | ISO 8601 timestamp when build completed |
| `build_duration_seconds` | number | Total build duration in seconds |
| `sources` | array | Provenance for each data source |
| `git_commit` | string | Short git commit hash (if in a git repo) |
| `tool_version` | string | Version of smt-index tool used |

### Source Provenance Object

Each source in the `provenance.sources` array contains:

| Field | Type | Description |
|-------|------|-------------|
| `url` | string | URL of the data source |
| `fetched_at` | string | ISO 8601 timestamp when source was fetched |
| `record_count` | number | Number of records retrieved from this source |

### Template Object

```json
{
  "id": "idta-02006-digital-nameplate-for-industrial-equipment",
  "name": "Digital Nameplate for Industrial Equipment",
  "idta_number": "02006",
  "status": "Published",
  "raw_status": "Published",
  "description": "The Submodel Template Digital Nameplate contains...",
  "versions": [
    {
      "version": "2.0.0",
      "is_latest": true,
      "links": {
        "pdf": "https://industrialdigitaltwin.org/wp-content/uploads/...",
        "github": "https://github.com/admin-shell-io/submodel-templates/tree/main/..."
      },
      "github": [
        {
          "version": "2.0.0",
          "area": "published",
          "repo_path": "published/Digital Nameplate/2/0",
          "github_url": "https://github.com/admin-shell-io/submodel-templates/tree/main/published/Digital%20Nameplate/2/0"
        }
      ]
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier: `idta-{number}-{slug}`, `ext-{slug}`, or `gh-{slug}` |
| `name` | string | Yes | Human-readable template name |
| `idta_number` | string | No | IDTA number (e.g., `02006`) |
| `status` | string | Yes | Normalized publication status |
| `raw_status` | string | No | Original status text before normalization |
| `description` | string | No | Template description from IDTA |
| `versions` | array | Yes | List of version objects |

### Version Object

```json
{
  "version": "2.0.0",
  "is_latest": true,
  "links": {
    "pdf": "https://...",
    "github": "https://..."
  },
  "github": [...]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Semver version number (e.g., `2.0.0`, `1.0.1`) |
| `is_latest` | boolean | Yes | Whether this is the latest version |
| `links` | object | Yes | Links associated with this version |
| `github` | array | No | GitHub repository entries for this version |

### Version Links Object

| Field | Type | Description |
|-------|------|-------------|
| `pdf` | string | Link to PDF specification |
| `github` | string | Link to GitHub folder |

### GitHub Version Object

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Semver version string |
| `area` | string | Either `published` or `deprecated` |
| `repo_path` | string | Path within the repository |
| `github_url` | string | Full GitHub URL to the version folder |

### Status Values

The `status` field is normalized to one of these values:

| Status | Description |
|--------|-------------|
| `Published` | Officially released and available |
| `In Review` | Under review process |
| `In Development` | Actively being developed |
| `Proposal submitted` | Initial proposal stage |
| `unknown` | Status could not be determined |

The `raw_status` field preserves the original status text from the source before normalization.

---

## CSV Format

The `index.csv` file provides a flat view with one row per template+version combination.

### Columns

| Column | Description |
|--------|-------------|
| `id` | Template unique identifier |
| `name` | Template name |
| `idta_number` | IDTA number if applicable |
| `status` | Normalized publication status |
| `version` | Version number |
| `is_latest` | Whether this is the latest version |
| `description` | Template description |
| `pdf_url` | PDF specification URL |
| `github_url` | GitHub repository URL |

### Example

```csv
id,name,idta_number,status,version,is_latest,description,pdf_url,github_url
idta-02006-digital-nameplate,Digital Nameplate,02006,Published,2.0.0,true,...,...,...
idta-02006-digital-nameplate,Digital Nameplate,02006,Published,1.0.0,false,...,...,...
idta-02007-software-nameplate,Software Nameplate,02007,Published,1.0.0,true,...,...,...
```

### Notes

- Multiple rows exist for templates with multiple versions
- Empty fields are represented as empty strings
- UTF-8 encoding
- Standard CSV escaping for special characters

---

## Parsing Examples

### Python - JSON

```python
import json

with open("dist/index.json") as f:
    index = json.load(f)

# Count templates by status
from collections import Counter
statuses = Counter(t["status"] for t in index["templates"])
print(statuses)
# Counter({'Published': 35, 'In Review': 5, 'unknown': 2})

# Get templates with their latest versions
for template in index["templates"]:
    latest = next((v for v in template["versions"] if v["is_latest"]), None)
    if latest:
        print(f"{template['name']}: v{latest['version']}")
```

### Python - CSV

```python
import csv

with open("dist/index.csv") as f:
    reader = csv.DictReader(f)
    published = [row for row in reader if row["status"] == "Published"]
    print(f"Found {len(published)} published template versions")
```

### jq - JSON

```bash
# Count templates
jq '.templates | length' dist/index.json

# Get all template IDs
jq -r '.templates[].id' dist/index.json

# Filter by status
jq '.templates[] | select(.status == "Published")' dist/index.json

# Get latest version of each template
jq '.templates[] | {name, latest: (.versions[] | select(.is_latest))}' dist/index.json
```

---

[← API Reference](api-reference.md) | [Examples →](examples.md)
