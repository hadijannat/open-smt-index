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
  "templates": [...]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Version of this schema format |
| `generated_at` | string | ISO 8601 timestamp of generation |
| `sources` | object | URLs of data sources |
| `templates` | array | List of template objects |

### Template Object

```json
{
  "id": "IDTA-02006",
  "title": "Digital Nameplate for Industrial Equipment",
  "status": "Published",
  "description": "The Submodel Template Digital Nameplate contains...",
  "idta_url": "https://industrialdigitaltwin.org/content-hub/teilmodelle/digital-nameplate",
  "github_url": "https://github.com/admin-shell-io/submodel-templates/tree/main/published/Digital%20Nameplate",
  "versions": [
    {
      "version": "2.0",
      "folder": "IDTA 02006-2-0_Submodel_Digital Nameplate",
      "aasx_url": "https://github.com/.../IDTA-02006-2-0_Template.aasx",
      "pdf_url": "https://industrialdigitaltwin.org/wp-content/uploads/..."
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | IDTA identifier (e.g., `IDTA-02006`) |
| `title` | string | Yes | Human-readable title |
| `status` | string | Yes | Publication status |
| `description` | string | No | Template description |
| `idta_url` | string | No | Link to IDTA Content Hub page |
| `github_url` | string | No | Link to GitHub folder |
| `versions` | array | Yes | List of version objects |

### Version Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Version number (e.g., `2.0`) |
| `folder` | string | No | GitHub folder name |
| `aasx_url` | string | No | Direct link to AASX file |
| `pdf_url` | string | No | Direct link to PDF specification |

### Status Values

| Status | Description |
|--------|-------------|
| `Published` | Officially released |
| `In Review` | Under review process |
| `Draft` | Early development stage |
| `Deprecated` | No longer recommended |

---

## CSV Format

The `index.csv` file provides a flat view with one row per template+version combination.

### Columns

| Column | Description |
|--------|-------------|
| `id` | Template IDTA identifier |
| `title` | Template title |
| `status` | Publication status |
| `version` | Version number |
| `description` | Template description |
| `idta_url` | IDTA Content Hub URL |
| `github_url` | GitHub repository URL |
| `aasx_url` | Direct AASX download URL |
| `pdf_url` | PDF specification URL |

### Example

```csv
id,title,status,version,description,idta_url,github_url,aasx_url,pdf_url
IDTA-02006,Digital Nameplate for Industrial Equipment,Published,2.0,...,...,...,...,...
IDTA-02006,Digital Nameplate for Industrial Equipment,Published,1.0,...,...,...,...,...
IDTA-02007,Software Nameplate,Published,1.0,...,...,...,...,...
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
# Counter({'Published': 35, 'In Review': 5, 'Draft': 2})
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
```

---

[← API Reference](api-reference.md) | [Examples →](examples.md)
