"""
server.py
---------
Harvard Dataverse Publishing Agent — FastAPI application.

Start the server:
    uvicorn server:app --reload --port 8000

Interactive API docs:
    http://localhost:8000/docs      ← Swagger UI
    http://localhost:8000/redoc     ← ReDoc

API prefix: /api/v1
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

from api.routes import metadata, datasets, pipeline, agent_chat

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Harvard Dataverse Publishing Agent API",
    description="""
A LangChain-powered REST API for publishing research datasets to Harvard Dataverse.

## Features
- **Auto-metadata generation** — GPT-4o analyses your dataset and generates rich metadata
- **Full publish pipeline** — one endpoint to go from raw file to published dataset
- **Async jobs** — background task support for large files
- **Agent chat** — natural language interface to the Dataverse agent
- **Duplicate detection** — automatic search before publishing

## Authentication
Add your API credentials to `.env`:
- `OPENAI_API_KEY` — for metadata generation
- `DATAVERSE_API_TOKEN` — from your Harvard Dataverse account (Account → API Token)

## Quick start
1. `POST /api/v1/metadata/preview` — preview auto-generated metadata for your file
2. `POST /api/v1/pipeline/publish` — publish in one step (dry_run=true to test first)
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
)

# ---------------------------------------------------------------------------
# CORS (adjust origins for production)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

API_PREFIX = "/api/v1"

app.include_router(metadata.router, prefix=API_PREFIX)
app.include_router(datasets.router, prefix=API_PREFIX)
app.include_router(pipeline.router, prefix=API_PREFIX)
app.include_router(agent_chat.router, prefix=API_PREFIX)

# Serve the web UI static files
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ---------------------------------------------------------------------------
# Health & root
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root():
    """Serve the web UI."""
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {
        "service": "Harvard Dataverse Publishing Agent API",
        "version": "1.0.0",
        "ui": "Run with static/index.html present for web UI",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get(f"{API_PREFIX}/health", tags=["Health"])
def health_check():
    """Check service health and configuration status."""
    return JSONResponse({
        "status": "ok",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "dataverse_configured": bool(os.getenv("DATAVERSE_API_TOKEN")),
        "dataverse_url": os.getenv("DATAVERSE_BASE_URL", "https://dataverse.harvard.edu"),
        "dataverse_alias": os.getenv("DATAVERSE_ALIAS", "root"),
    })


# ---------------------------------------------------------------------------
# Dev server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info",
    )
