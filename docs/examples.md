---
layout: default
title: Examples
---

# Examples

Common use cases and integration patterns.

---

## Use Cases

### Build a Custom Index

Build an index and filter for specific templates:

```bash
# Build full index
smt-index build --out dist/

# Extract only published templates
jq '{
  schema_version: .schema_version,
  generated_at: .generated_at,
  templates: [.templates[] | select(.status == "Published")]
}' dist/index.json > dist/published-only.json
```

### Automated Index Updates

Set up a cron job or GitHub Action to rebuild periodically:

```yaml
# .github/workflows/update-index.yml
name: Update Index

on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday at 6 AM

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install smt-index
        run: |
          pip install smt-index
          playwright install chromium

      - name: Build index
        run: smt-index build --out dist/

      - name: Commit changes
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add dist/
          git diff --staged --quiet || git commit -m "Update index $(date +%Y-%m-%d)"
          git push
```

---

## API Integration

### Python Client

```python
import httpx
from dataclasses import dataclass

@dataclass
class Template:
    id: str
    title: str
    status: str
    versions: list

class SMTIndexClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.client = httpx.Client(base_url=base_url)

    def list_templates(self, status: str = None, query: str = None) -> list[Template]:
        params = {}
        if status:
            params["status"] = status
        if query:
            params["q"] = query

        response = self.client.get("/templates", params=params)
        response.raise_for_status()

        return [
            Template(**t)
            for t in response.json()["templates"]
        ]

    def get_template(self, template_id: str) -> Template:
        response = self.client.get(f"/templates/{template_id}")
        response.raise_for_status()
        return Template(**response.json())

# Usage
client = SMTIndexClient()
published = client.list_templates(status="Published")
print(f"Found {len(published)} published templates")
```

### JavaScript/TypeScript

```typescript
interface Template {
  id: string;
  title: string;
  status: string;
  versions: Version[];
}

interface Version {
  version: string;
  aasx_url?: string;
  pdf_url?: string;
}

async function fetchTemplates(
  baseUrl = 'http://localhost:8000'
): Promise<Template[]> {
  const response = await fetch(`${baseUrl}/templates`);
  const data = await response.json();
  return data.templates;
}

async function searchTemplates(query: string): Promise<Template[]> {
  const response = await fetch(
    `http://localhost:8000/templates?q=${encodeURIComponent(query)}`
  );
  const data = await response.json();
  return data.templates;
}

// Usage
const templates = await fetchTemplates();
const carbonTemplates = await searchTemplates('carbon');
```

---

## Data Processing

### Find Templates with Missing Data

```python
import json

with open("dist/index.json") as f:
    index = json.load(f)

# Find templates without descriptions
missing_desc = [
    t["id"] for t in index["templates"]
    if not t.get("description")
]
print(f"Templates without descriptions: {missing_desc}")

# Find versions without AASX files
missing_aasx = []
for template in index["templates"]:
    for version in template.get("versions", []):
        if not version.get("aasx_url"):
            missing_aasx.append(f"{template['id']} v{version['version']}")

print(f"Versions without AASX: {missing_aasx}")
```

### Export to Different Formats

```python
import json
import pandas as pd

# Load JSON
with open("dist/index.json") as f:
    index = json.load(f)

# Flatten to DataFrame
rows = []
for t in index["templates"]:
    for v in t.get("versions", []):
        rows.append({
            "id": t["id"],
            "title": t["title"],
            "status": t["status"],
            "version": v["version"],
            "aasx_url": v.get("aasx_url", ""),
        })

df = pd.DataFrame(rows)

# Export to Excel
df.to_excel("templates.xlsx", index=False)

# Export to Parquet
df.to_parquet("templates.parquet")
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install smt-index

# Install Playwright browser
RUN playwright install chromium && \
    playwright install-deps chromium

# Build index at startup
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
```

### entrypoint.sh

```bash
#!/bin/bash
set -e

# Build fresh index
smt-index build --out /data/

# Serve the API
exec smt-index serve --host 0.0.0.0 --port 8000 --index /data/index.json
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  smt-index:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - index-data:/data

volumes:
  index-data:
```

---

## Validation Scripting

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

if [ -f "dist/index.json" ]; then
    echo "Validating index..."
    smt-index validate --index dist/index.json
    if [ $? -ne 0 ]; then
        echo "Index validation failed!"
        exit 1
    fi
fi
```

---

[← Output Schema](output-schema.md) | [Contributing →](contributing.md)
