"""
routes/metadata.py
------------------
POST /api/v1/metadata/preview

Upload a file and get back auto-generated Dataverse-compliant metadata.
Uses the free local RAG pipeline (sentence-transformers) — no API key needed.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.models import MetadataPreviewResponse, GeneratedMetadata
from modules.rag_metadata_generator import generate_metadata_rag
from modules.metadata_generator import build_dataverse_metadata

router = APIRouter(prefix="/metadata", tags=["Metadata"])


@router.post(
    "/preview",
    response_model=MetadataPreviewResponse,
    summary="Generate metadata for a dataset file",
    description=(
        "Upload a CSV or TXT file. The API analyses its content using a local "
        "RAG pipeline and returns a complete Harvard Dataverse-compliant metadata "
        "record. No API key or credits required."
    ),
)
async def preview_metadata(
    file: UploadFile = File(..., description="Dataset file (CSV, TXT, MD)"),
    author_name: str = Form(default="", description="Author name for the dataset"),
    author_affiliation: str = Form(default="", description="Author's institution"),
    contact_email: str = Form(default="contact@example.com", description="Contact email"),
):
    allowed_extensions = {".csv", ".txt", ".md"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Supported: {allowed_extensions}",
        )

    # Save to temp file for analysis
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=suffix, mode="wb"
    ) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Use the free RAG-based generator (no API call, runs locally)
        generated = generate_metadata_rag(
            tmp_path,
            author_name=author_name or os.getenv("DATAVERSE_AUTHOR_NAME", "Author"),
            author_affiliation=author_affiliation,
            contact_email=contact_email,
            original_filename=file.filename,
        )
        dataverse_schema = build_dataverse_metadata(
            generated,
            author_name=author_name or os.getenv("DATAVERSE_AUTHOR_NAME", "Author"),
            author_affiliation=author_affiliation,
            contact_email=contact_email,
        )
    except Exception as exc:
        Path(tmp_path).unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Metadata generation failed: {exc}",
        )
    else:
        Path(tmp_path).unlink(missing_ok=True)

    return MetadataPreviewResponse(
        success=True,
        filename=file.filename,
        metadata=GeneratedMetadata(**generated),
        dataverse_schema=dataverse_schema,
    )
