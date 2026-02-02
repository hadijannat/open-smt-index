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

Get all templates with optional filtering.

```
GET /templates
```

#### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status (e.g., `Published`, `In Review`) |
| `q` | string | Search in title and description |

#### Response

```json
{
  "templates": [
    {
      "id": "IDTA-02006",
      "title": "Digital Nameplate for Industrial Equipment",
      "status": "Published",
      "versions": ["1.0", "2.0"],
      "description": "...",
      "idta_url": "https://...",
      "github_url": "https://..."
    }
  ],
  "count": 42
}
```

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

Get a specific template by its IDTA identifier.

```
GET /templates/{id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Template ID (e.g., `IDTA-02006`) |

#### Response

```json
{
  "id": "IDTA-02006",
  "title": "Digital Nameplate for Industrial Equipment",
  "status": "Published",
  "description": "The Submodel Template Digital Nameplate contains...",
  "versions": [
    {
      "version": "2.0",
      "release_date": "2022-12-01",
      "aasx_url": "https://github.com/.../IDTA-02006-2-0.aasx",
      "pdf_url": "https://..."
    },
    {
      "version": "1.0",
      "release_date": "2021-06-15",
      "aasx_url": "https://github.com/.../IDTA-02006-1-0.aasx"
    }
  ],
  "idta_url": "https://industrialdigitaltwin.org/...",
  "github_url": "https://github.com/admin-shell-io/submodel-templates/tree/main/..."
}
```

#### Error Response

```json
{
  "detail": "Template not found: IDTA-99999"
}
```

Status: `404 Not Found`

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
templates = response.json()["templates"]

# Get specific template
template = client.get("/templates/IDTA-02006").json()
print(template["title"])
```

### JavaScript

```javascript
// Fetch all templates
const response = await fetch('http://localhost:8000/templates');
const { templates } = await response.json();

// Search for templates
const search = await fetch('http://localhost:8000/templates?q=carbon');
const results = await search.json();
```

---

[← CLI Reference](cli-reference.md) | [Output Schema →](output-schema.md)
