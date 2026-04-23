# Agent Architecture

## Overview

The MASBio Dataverse Agent is a **LangChain ReAct agent** that reasons step-by-step to publish a dataset. It is backed by a FastAPI web server and a hybrid Groq + RAG metadata pipeline.

---

## Component Map

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser UI  (static/index.html)                                    │
│  • Upload CSV                                                        │
│  • Preview metadata                                                  │
│  • One-click publish                                                 │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP (multipart/form-data)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FastAPI Server  (server.py + api/routes/)                          │
│                                                                     │
│  POST /api/publish         →  pipeline.py   (end-to-end)           │
│  POST /api/metadata/preview→  metadata.py   (preview only)         │
│  GET  /api/datasets        →  datasets.py   (list)                 │
│  POST /api/agent/chat      →  agent_chat.py (interactive)          │
└───────────┬─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Metadata Pipeline  (modules/metadata_generator.py)                 │
│                                                                     │
│  ┌──────────────────────────┐   ┌──────────────────────────────┐   │
│  │  RAG — local, offline    │   │  Groq LLM — free API         │   │
│  │  sentence-transformers   │   │  Llama 3 70B                 │   │
│  │  all-MiniLM-L6-v2        │   │                              │   │
│  │                          │   │  • Description               │   │
│  │  • Time period detection │   │  • Keywords                  │   │
│  │  • Geography detection   │   │  • Subject classification    │   │
│  │  • Data source detection │   │                              │   │
│  │  • 20-entry KB           │   │                              │   │
│  └────────────┬─────────────┘   └──────────────┬───────────────┘   │
│               │                                 │                   │
│               └────────────┬────────────────────┘                   │
│                            ▼                                        │
│               Merged metadata JSON                                  │
│               (title always from filename)                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LangChain ReAct Agent  (agent.py)                                  │
│  Model: Claude Sonnet (Anthropic)                                   │
│                                                                     │
│  Loop: Thought → Action → Observation → Thought …                   │
│                                                                     │
│  Tools available:                                                   │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ generate_dataset_metadata   reads file, calls pipeline     │    │
│  │ search_dataverse            GET /api/search                │    │
│  │ create_dataverse_dataset    POST /api/dataverses/{alias}   │    │
│  │ upload_file_to_dataset      POST /api/datasets/{id}/add    │    │
│  │ get_dataset_info            GET /api/datasets/{id}         │    │
│  │ publish_dataverse_dataset   polls /locks → POST /publish   │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Harvard Dataverse API  (dataverse.harvard.edu)                     │
│  Native API v1                                                      │
│  • CC0 1.0 license                                                  │
│  • Permanent DOI  (10.7910/DVN/…)                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Metadata Pipeline Detail

### RAG (Retrieval-Augmented Generation)

File: `modules/rag_metadata_generator.py`

**Step 1 — Feature extraction** (`extract_file_features`)
- Reads up to 30 rows of the CSV
- Detects time columns (year, date, month patterns)
- Detects geographic columns (country, region, lat/lon patterns)
- Infers data source from filename keywords (FAOSTAT, FAO, USDA, NASA, etc.)

**Step 2 — Embedding & retrieval** (`retrieve_top_k`)
- Builds a query string from column names + sample values
- Embeds with `all-MiniLM-L6-v2` (384-dim dense vectors)
- Cosine similarity against all 20 knowledge base entries
- Returns top-3 matches

**Step 3 — Template fill** (`fill_metadata_template`)
- Blends subject, description template, and keywords from top-3 matches
- Appends detected features (time range, geography, source)

### Knowledge Base

File: `modules/rag_metadata_kb.py`

20 hand-written entries covering:

| Domain | Example entry |
|---|---|
| Forestry / biomass | FAOSTAT forestry production data |
| Marine sensors | Oceanographic sensor time series |
| Agriculture | Crop yield and production statistics |
| Bioenergy | Biofuel feedstock characterisation |
| Carbon | GHG emissions and carbon accounting |
| Water quality | River/lake water quality monitoring |
| Land use | Land cover change analysis |
| Fisheries | Catch and aquaculture data |
| Climate | Weather station and climate records |
| Biodiversity | Species occurrence data |
| Algae | Microalgae cultivation experiments |
| Renewable energy | Solar/wind resource data |
| Soil | Soil carbon and nutrient measurements |
| Trade | Agricultural trade statistics |
| Air quality | Atmospheric pollution monitoring |
| Population | Socioeconomic and demographic data |
| Forest carbon | Forest carbon stock inventories |
| Health | Epidemiological and health outcome data |
| Ocean remote sensing | Satellite oceanography |
| Energy policy | Governance and policy documents |

---

## Ingest Lock Handling

Harvard Dataverse processes uploaded files asynchronously. Publishing before ingest completes returns a `"This dataset is locked. Reason: Ingest"` error.

The agent handles this in `modules/dataverse_tools.py` (`PublishDatasetTool`) and `api/routes/pipeline.py`:

```python
# Poll /api/datasets/{id}/locks every 8 seconds, up to 120 seconds
for attempt in range(15):
    locks = requests.get(f"{base}/api/datasets/{id}/locks", ...)
    if not locks.json().get("data"):
        break   # no locks — safe to publish
    time.sleep(8)
```

---

## Agent Reasoning Format

The LangChain ReAct agent uses the standard Thought / Action / Action Input / Observation cycle:

```
Question: Please publish data.csv to Harvard Dataverse.

Thought: I should first generate metadata from the file.
Action: generate_dataset_metadata
Action Input: {"file_path": "data.csv"}
Observation: {"title": "Data", "description": "...", ...}

Thought: I should search for duplicates before creating.
Action: search_dataverse
Action Input: {"query": "Data"}
Observation: No existing datasets found.

Thought: Safe to create. I'll call create_dataverse_dataset.
...

Thought: I now know the final answer.
Final Answer: Dataset published successfully. DOI: 10.7910/DVN/XXXXX
```

Max iterations: 12. Parsing errors are handled gracefully.
