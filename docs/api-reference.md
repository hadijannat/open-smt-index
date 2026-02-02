---
layout: default
title: API Reference
---

# API Reference

REST API documentation for the `smt-index serve` server.

## Base URL

```
http://localhost:8000
```

---

## Endpoints

### Health Check

Check if the server is running.

```
GET /health
```

#### Response

```json
{
  "status": "healthy"
}
```

---

### List Templates

Get all templates with optional filtering. Returns a summary view with basic metadata.

```
GET /templates
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (e.g., `Published`, `In Review`) |
| `q` | string | Search in name, description, IDTA number, and ID |

#### Response

```json
[
  {
    "id": "idta-02006-digital-nameplate-for-industrial-equipment",
    "name": "Digital Nameplate for Industrial Equipment",
    "idta_number": "02006",
    "status": "Published",
    "version_count": 3,
    "latest_version": "2.0.0"
  }
]
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique template identifier |
| `name` | string | Human-readable template name |
| `idta_number` | string | IDTA number (e.g., `02006`) or `null` |
| `status` | string | Normalized publication status |
| `version_count` | integer | Number of available versions |
| `latest_version` | string | Latest version number or `null` |

#### Examples

```bash
# Get all templates
curl http://localhost:8000/templates

# Filter by status
curl "http://localhost:8000/templates?status=Published"

# Search by keyword
curl "http://localhost:8000/templates?q=nameplate"

# Combine filters
curl "http://localhost:8000/templates?status=Published&q=carbon"
```

---

### Get Template by ID

Get a specific template with full details including all versions.

```
GET /templates/{template_id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `template_id` | string | Template ID (e.g., `idta-02006-digital-nameplate-for-industrial-equipment`) |

#### Response

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
        "pdf": "https://industrialdigitaltwin.org/...",
        "github": "https://github.com/admin-shell-io/submodel-templates/..."
      },
      "github": [
        {
          "version": "2.0.0",
          "area": "published",
          "repo_path": "published/Digital Nameplate/2/0",
          "github_url": "https://github.com/..."
        }
      ]
    },
    {
      "version": "1.0.0",
      "is_latest": false,
      "links": {
        "pdf": null,
        "github": "https://github.com/..."
      },
      "github": []
    }
  ]
}
```

#### Error Response

```json
{
  "detail": "Template not found: invalid-id"
}
```

Status: `404 Not Found`

---

### Get Full Index

Get the complete index data (for debugging or export).

```
GET /index
```

#### Response

Returns the full `TemplateIndex` object including `schema_version`, `generated_at`, `sources`, and all templates with full version details.

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

---

### Get Statistics

Get aggregate statistics about the index.

```
GET /stats
```

#### Response

```json
{
  "schema_version": "1.0",
  "generated_at": "2024-01-15T10:30:00Z",
  "total_templates": 42,
  "total_versions": 78,
  "by_status": {
    "Published": 35,
    "In Review": 5,
    "unknown": 2
  },
  "by_prefix": {
    "idta": 38,
    "ext": 2,
    "gh": 2
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Index schema version |
| `generated_at` | string | ISO 8601 timestamp of generation |
| `total_templates` | integer | Total number of templates |
| `total_versions` | integer | Total number of versions across all templates |
| `by_status` | object | Count of templates by status |
| `by_prefix` | object | Count of templates by ID prefix (`idta`, `ext`, `gh`) |

---

## Response Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `404` | Template not found |
| `500` | Server error |

---

## Content Types

All responses are `application/json`.

---

## CORS

The API supports CORS for browser-based clients:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, OPTIONS
```

---

## Rate Limiting

No rate limiting is applied by default. For production deployments, consider adding a reverse proxy with rate limiting.

---

## Example Integration

### Python

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# List all published templates
response = client.get("/templates", params={"status": "Published"})
templates = response.json()

for t in templates:
    print(f"{t['name']} - {t['latest_version']}")

# Get specific template with full details
template = client.get("/templates/idta-02006-digital-nameplate-for-industrial-equipment").json()
print(f"{template['name']}: {len(template['versions'])} versions")

# Get statistics
stats = client.get("/stats").json()
print(f"Total templates: {stats['total_templates']}")
```

### JavaScript

```javascript
// Fetch all templates
const response = await fetch('http://localhost:8000/templates');
const templates = await response.json();

// Search for templates
const search = await fetch('http://localhost:8000/templates?q=carbon');
const results = await search.json();

// Get statistics
const statsResponse = await fetch('http://localhost:8000/stats');
const stats = await statsResponse.json();
console.log(`Total templates: ${stats.total_templates}`);
```

### cURL

```bash
# Get all templates
curl http://localhost:8000/templates | jq '.[].name'

# Get template details
curl http://localhost:8000/templates/idta-02006-digital-nameplate-for-industrial-equipment | jq

# Get stats
curl http://localhost:8000/stats | jq '.by_status'
```

---

[← CLI Reference](cli-reference.md) | [Output Schema →](output-schema.md)
