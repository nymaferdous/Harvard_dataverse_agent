# API Reference

The FastAPI server (`server.py`) exposes a REST API and serves the web UI.

Base URL (local): `http://localhost:8000`

---

## Endpoints

### `GET /`

Returns the web UI (`static/index.html`).

---

### `POST /api/publish`

Full end-to-end pipeline: receive a CSV file → generate metadata → publish to Dataverse → return DOI.

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | CSV dataset to publish |
| `dry_run` | bool | No (default: false) | If true, stops before publishing |

**Response** — `application/json`

```json
{
  "success": true,
  "doi": "10.7910/DVN/XXXXXX",
  "persistent_id": "doi:10.7910/DVN/XXXXXX",
  "dataset_id": 12345,
  "title": "My Dataset Title",
  "steps": {
    "metadata": "generated",
    "duplicate_check": "no duplicates found",
    "create": "created",
    "upload": "uploaded",
    "verify": "verified",
    "publish": "published"
  }
}
```

On error:
```json
{
  "success": false,
  "error": "Dataset creation failed: ...",
  "step": "create"
}
```

---

### `POST /api/metadata/preview`

Generates and returns metadata for a CSV file without creating anything in Dataverse.
Useful for reviewing auto-generated metadata before publishing.

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | CSV file to analyse |

**Response** — `application/json`

```json
{
  "title": "Faostat Forestry Data",
  "description": "This dataset contains forestry production statistics ...",
  "keywords": ["forestry", "biomass", "production", "FAOSTAT"],
  "subject": "Agricultural Sciences",
  "time_period_start": "2000",
  "time_period_end": "2023",
  "geographic_coverage": "Global",
  "data_source": "FAOSTAT"
}
```

---

### `GET /api/datasets`

Lists datasets in your configured Dataverse (`DATAVERSE_ALIAS`).

**Response** — `application/json`

```json
{
  "datasets": [
    {
      "id": 12345,
      "persistent_id": "doi:10.7910/DVN/XXXXXX",
      "title": "My Dataset",
      "publication_date": "2026-01-15",
      "status": "RELEASED"
    }
  ],
  "total": 1
}
```

---

### `POST /api/agent/chat`

Send a free-text message to the LangChain ReAct agent. Returns the agent's response and intermediate reasoning steps.

**Request** — `application/json`

```json
{
  "message": "Search for any datasets about biochar in my dataverse"
}
```

**Response** — `application/json`

```json
{
  "output": "I found 2 datasets matching 'biochar': ...",
  "steps": [
    {
      "action": "search_dataverse",
      "input": "biochar",
      "observation": "Found: Biochar Soil Amendment Study (doi:...)"
    }
  ]
}
```

---

## Error Codes

| HTTP Status | Meaning |
|---|---|
| `200` | Success |
| `422` | Validation error (missing required field) |
| `500` | Internal error — check the `error` field in the response body |

Common error messages:

| Error | Cause | Fix |
|---|---|---|
| `Can't find dataverse with identifier='root'` | `DATAVERSE_ALIAS` not set | Set your personal alias in `.env` |
| `Invalid controlled vocabulary` | Wrong value in metadata field | Fixed in current version — uses `otherGeographicCoverage` |
| `This dataset is locked. Reason: Ingest` | File still processing | Fixed in current version — agent polls before publishing |
| `did not pass automated metadata validation` | New Harvard Dataverse accounts require curation | Use `demo.dataverse.org` for testing |
