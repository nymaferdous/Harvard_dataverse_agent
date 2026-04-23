# MASBio Dataverse Agent

An autonomous AI agent that publishes research datasets to [Harvard Dataverse](https://dataverse.harvard.edu) — from CSV upload to a permanent, citable DOI — in under 60 seconds.

Built for the [MASBio Consortium](https://masbio.wvu.edu/home) as part of its FAIR data management initiative.

---

## What It Does

Researchers upload a CSV file through a web UI (or CLI). The agent:

1. **Generates metadata automatically** — title from filename, description and keywords via Groq LLM (free), structural fields (time period, geography, subject) via local RAG
2. **Checks for duplicates** — searches Dataverse before creating anything
3. **Creates a dataset record** — POST to Harvard Dataverse API
4. **Uploads the file** — attaches the CSV to the draft
5. **Waits for ingest** — polls the Dataverse locks endpoint so publish never fails
6. **Publishes** — returns a permanent DOI to the researcher

No programming knowledge required. No recurring API costs.

---

## Architecture

```
Researcher (browser)
        │
        ▼
  FastAPI Web Server  (server.py)
        │
   ┌────┴─────────────────────────────────┐
   │                                      │
   ▼                                      ▼
RAG Pipeline                       Groq LLM (Llama 3 70B)
(sentence-transformers)            Free API — no credits
   │  Time period, geography,      │  Description, keywords,
   │  data source detection        │  subject classification
   └────────────┬───────────────────┘
                ▼
        Merged Metadata
        (title always from filename)
                │
                ▼
   LangChain ReAct Agent  (agent.py)
        │
        ├── search_dataverse      → duplicate check
        ├── create_dataverse_dataset → POST /api/dataverses/.../datasets
        ├── upload_file_to_dataset   → POST /api/datasets/.../add
        ├── get_dataset_info         → verify before publish
        └── publish_dataverse_dataset → polls /locks → POST .../publish
                │
                ▼
        Harvard Dataverse
        Permanent DOI returned
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | [LangChain](https://langchain.com) ReAct |
| LLM (metadata) | [Groq](https://console.groq.com) — Llama 3 70B (free) |
| RAG (metadata) | [sentence-transformers](https://www.sbert.net) — all-MiniLM-L6-v2 (local, offline) |
| Agent LLM | [Anthropic](https://console.anthropic.com) Claude Sonnet |
| Web API | [FastAPI](https://fastapi.tiangolo.com) + Uvicorn |
| Data repository | [Harvard Dataverse](https://dataverse.harvard.edu) Native API |

---

## Project Structure

```
dataverse_agent/
├── agent.py                    # LangChain ReAct agent (CLI entry point)
├── server.py                   # FastAPI application factory
├── requirements.txt
├── .env.example                # Copy to .env and fill in your keys
│
├── modules/
│   ├── dataverse_tools.py      # LangChain Tools wrapping Dataverse API calls
│   ├── metadata_generator.py   # Hybrid Groq + RAG metadata pipeline
│   ├── rag_metadata_generator.py  # RAG pipeline (feature extraction + retrieval)
│   └── rag_metadata_kb.py      # 20-entry domain knowledge base
│
├── api/
│   ├── models.py               # Pydantic request/response models
│   └── routes/
│       ├── pipeline.py         # POST /api/publish — full end-to-end pipeline
│       ├── metadata.py         # POST /api/metadata/preview — preview only
│       ├── datasets.py         # GET  /api/datasets  — list published datasets
│       └── agent_chat.py       # POST /api/agent/chat — interactive agent
│
└── static/
    └── index.html              # Single-page web UI
```

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/masbio-dataverse-agent.git
cd masbio-dataverse-agent
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Open .env and fill in your API keys (see Configuration section below)
```

### 3. Run the web server

```bash
python server.py
```

Open [http://localhost:8000](http://localhost:8000) — upload a CSV, preview metadata, publish.

### 4. Or use the CLI

```bash
# Preview metadata without publishing
python agent.py --preview-metadata path/to/data.csv

# Full publish workflow (dry run — stops before publishing)
python agent.py --file path/to/data.csv --dry-run

# Full publish
python agent.py --file path/to/data.csv

# Interactive session
python agent.py --interactive
```

---

## Configuration

Copy `.env.example` to `.env` and fill in the following:

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Free key from [console.groq.com](https://console.groq.com) |
| `ANTHROPIC_API_KEY` | Yes | From [console.anthropic.com](https://console.anthropic.com) |
| `DATAVERSE_API_TOKEN` | Yes | From your Dataverse account → API Token |
| `DATAVERSE_BASE_URL` | Yes | `https://dataverse.harvard.edu` or `https://demo.dataverse.org` for testing |
| `DATAVERSE_ALIAS` | Yes | Your personal dataverse alias (shown in your Dataverse profile URL) |
| `DATAVERSE_AUTHOR_NAME` | Yes | Your name — appears on all published datasets |
| `DATAVERSE_AUTHOR_AFFILIATION` | Yes | Your institution |
| `DATAVERSE_CONTACT_EMAIL` | Yes | Contact email for datasets |

> **Tip:** Use `https://demo.dataverse.org` while testing. Harvard Dataverse requires a curation review for new accounts.

---

## Metadata Pipeline

Metadata is generated through a **two-stage hybrid pipeline** with zero recurring cost:

### Stage 1 — RAG (local, offline)
`modules/rag_metadata_generator.py` reads the CSV file and:
- Extracts column names, sample values, time columns, and geographic columns
- Embeds a query using `all-MiniLM-L6-v2` (runs on CPU, no GPU needed)
- Retrieves the 3 most similar entries from the 20-entry domain knowledge base (`rag_metadata_kb.py`)
- Detects: time period, geographic coverage, data source

The knowledge base covers 20 biomass/agriculture domains including forestry, marine sensors, bioenergy, carbon emissions, water quality, land use, fisheries, and more.

### Stage 2 — Groq LLM (free API)
`modules/metadata_generator.py` calls Groq (Llama 3 70B) for:
- Human-readable description (2–3 sentences)
- Keywords (5–8 terms)
- Dataverse subject classification

### Merge
The two outputs are combined. The **title is always derived from the filename** — never from the LLM — to avoid hallucinations.

---

## API Reference

The FastAPI server exposes these endpoints:

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Web UI |
| `POST` | `/api/publish` | Full pipeline: upload CSV → publish → return DOI |
| `POST` | `/api/metadata/preview` | Preview auto-generated metadata without publishing |
| `GET` | `/api/datasets` | List datasets in your Dataverse |
| `POST` | `/api/agent/chat` | Send a message to the interactive agent |

Full request/response schemas are in `api/models.py`.

---

## FAIR Data Compliance

All datasets published by this agent are:

- **Findable** — permanent DOI, machine-readable metadata, indexed by Dataverse search
- **Accessible** — open HTTP download, no login required
- **Interoperable** — standard Dataverse metadata schema, CSV format
- **Reusable** — CC0 1.0 license applied automatically

---

## Requirements

```
Python >= 3.10
langchain == 0.2.16
langchain-core >= 0.2.38, < 0.3
langchain-anthropic == 0.1.23
langchain-groq == 0.1.9
anthropic >= 0.30.0
groq >= 0.9.0
sentence-transformers == 3.0.1
fastapi == 0.115.0
uvicorn[standard] == 0.30.6
python-dotenv == 1.0.1
rich == 13.8.1
requests == 2.32.3
pydantic == 2.8.2
```

See `requirements.txt` for the full pinned list.

---

## Citation

If you use this tool in your research, please cite:

> Ferdous, S. N. (2026). *MASBio Dataverse Agent: An AI-powered pipeline for automated research data publishing to Harvard Dataverse.* North Carolina State University. https://github.com/YOUR_USERNAME/masbio-dataverse-agent

---

## Acknowledgements

This work is supported by the Sustainable Agricultural Systems project, award no. 2020-68012-31881, from the U.S. Department of Agriculture's National Institute of Food and Agriculture (NIFA).

---

## Author

**Syeda Nyma Ferdous** — Data Manager, MASBio Consortium  
North Carolina State University  
snferdou@ncsu.edu
