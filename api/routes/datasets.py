"""
routes/datasets.py
------------------
Dataset management endpoints:

  POST   /api/v1/datasets                    Create a new dataset (upload file + auto metadata)
  GET    /api/v1/datasets/{dataset_id}       Get dataset info
  POST   /api/v1/datasets/{dataset_id}/files Upload a file to an existing dataset
  POST   /api/v1/datasets/{dataset_id}/publish  Publish a dataset
  GET    /api/v1/datasets/search             Search Dataverse
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Optional

import requests
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from api.models import (
    CreateDatasetResponse,
    DatasetInfoResponse,
    PublishRequest,
    PublishResponse,
    SearchResponse,
    SearchResult,
    UploadFileResponse,
)
from modules.metadata_generator import generate_dataverse_metadata

router = APIRouter(prefix="/datasets", tags=["Datasets"])

DATAVERSE_BASE_URL = os.getenv("DATAVERSE_BASE_URL", "https://dataverse.harvard.edu")
DATAVERSE_API_TOKEN = os.getenv("DATAVERSE_API_TOKEN", "")


def _headers():
    return {"X-Dataverse-key": DATAVERSE_API_TOKEN}


def _require_token():
    if not DATAVERSE_API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="DATAVERSE_API_TOKEN not configured. Add it to your .env file.",
        )


# ---------------------------------------------------------------------------
# Create dataset (with auto-metadata from uploaded file)
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=CreateDatasetResponse,
    status_code=201,
    summary="Create a new dataset with auto-generated metadata",
    description=(
        "Upload a data file. The API auto-generates Dataverse metadata using GPT-4o, "
        "then creates a new draft dataset record in Dataverse. "
        "Returns the dataset persistent ID (DOI) for use in subsequent calls."
    ),
)
async def create_dataset(
    file: UploadFile = File(..., description="Dataset file to analyse for metadata"),
    dataverse_alias: str = Form(
        default="root", description="Dataverse alias to publish into"
    ),
    author_name: str = Form(..., description="Author's full name"),
    author_affiliation: str = Form(default="", description="Author's institution"),
    contact_email: str = Form(..., description="Contact email for the dataset"),
):
    _require_token()

    suffix = Path(file.filename).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        metadata = generate_dataverse_metadata(
            file_path=tmp_path,
            author_name=author_name,
            author_affiliation=author_affiliation,
            contact_email=contact_email,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    url = f"{DATAVERSE_BASE_URL}/api/dataverses/{dataverse_alias}/datasets"
    resp = requests.post(url, headers=_headers(), json=metadata, timeout=30)

    if resp.status_code != 201:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Dataverse API error: {resp.text[:500]}",
        )

    data = resp.json()["data"]
    return CreateDatasetResponse(
        success=True,
        persistent_id=data.get("persistentId", ""),
        numeric_id=str(data.get("id", "")),
        status="DRAFT",
        message=(
            f"Dataset created successfully. "
            f"Use persistent_id '{data.get('persistentId')}' to upload files."
        ),
    )


# ---------------------------------------------------------------------------
# Get dataset info
# ---------------------------------------------------------------------------

@router.get(
    "/{dataset_id:path}",
    response_model=DatasetInfoResponse,
    summary="Get dataset information",
    description="Retrieve metadata, version status, and file list for a dataset.",
)
def get_dataset_info(dataset_id: str):
    _require_token()

    if dataset_id.startswith("doi:") or dataset_id.startswith("hdl:"):
        url = f"{DATAVERSE_BASE_URL}/api/datasets/:persistentId/?persistentId={dataset_id}"
    else:
        url = f"{DATAVERSE_BASE_URL}/api/datasets/{dataset_id}"

    resp = requests.get(url, headers=_headers(), timeout=30)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:300])

    data = resp.json().get("data", {})
    version = data.get("latestVersion", {})
    files = version.get("files", [])
    citation_fields = (
        version.get("metadataBlocks", {}).get("citation", {}).get("fields", [])
    )
    title_field = next(
        (f for f in citation_fields if f.get("typeName") == "title"), {}
    )

    return DatasetInfoResponse(
        success=True,
        dataset_id=dataset_id,
        title=title_field.get("value", "N/A"),
        status=version.get("versionState", "UNKNOWN"),
        file_count=len(files),
        files=[f.get("dataFile", {}).get("filename", "unknown") for f in files],
    )


# ---------------------------------------------------------------------------
# Upload file to existing dataset
# ---------------------------------------------------------------------------

@router.post(
    "/{dataset_id:path}/files",
    response_model=UploadFileResponse,
    summary="Upload a file to an existing dataset",
    description=(
        "Attach a file to an existing draft dataset. "
        "The dataset_id can be a persistent ID (doi:...) or numeric ID."
    ),
)
async def upload_file(
    dataset_id: str,
    file: UploadFile = File(...),
    description: str = Form(default=""),
    directory_label: str = Form(default="data"),
):
    _require_token()

    suffix = Path(file.filename).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        if dataset_id.startswith("doi:") or dataset_id.startswith("hdl:"):
            url = (
                f"{DATAVERSE_BASE_URL}/api/datasets/:persistentId/add"
                f"?persistentId={dataset_id}"
            )
        else:
            url = f"{DATAVERSE_BASE_URL}/api/datasets/{dataset_id}/add"

        json_data = {
            "description": description,
            "directoryLabel": directory_label,
            "categories": ["Data"],
            "restrict": False,
        }

        with open(tmp_path, "rb") as f:
            files_payload = {
                "file": (file.filename, f, "application/octet-stream"),
                "jsonData": (None, json.dumps(json_data), "application/json"),
            }
            resp = requests.post(
                url, headers=_headers(), files=files_payload, timeout=60
            )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:500])

    resp_data = resp.json().get("data", {})
    file_id = (
        resp_data.get("files", [{}])[0].get("dataFile", {}).get("id")
        if resp_data.get("files")
        else None
    )

    return UploadFileResponse(
        success=True,
        dataset_id=dataset_id,
        filename=file.filename,
        file_id=str(file_id) if file_id else None,
        directory=directory_label,
        message=f"File '{file.filename}' uploaded to dataset '{dataset_id}'.",
    )


# ---------------------------------------------------------------------------
# Publish dataset
# ---------------------------------------------------------------------------

@router.post(
    "/{dataset_id:path}/publish",
    response_model=PublishResponse,
    summary="Publish a dataset draft",
    description=(
        "Publish a draft dataset, making it publicly accessible with a permanent DOI. "
        "⚠️ This action is irreversible — ensure metadata and files are correct first."
    ),
)
def publish_dataset(dataset_id: str, body: PublishRequest = None):
    _require_token()
    version_type = body.version_type if body else "major"

    if dataset_id.startswith("doi:") or dataset_id.startswith("hdl:"):
        url = (
            f"{DATAVERSE_BASE_URL}/api/datasets/:persistentId/actions/:publish"
            f"?persistentId={dataset_id}&type={version_type}"
        )
    else:
        url = (
            f"{DATAVERSE_BASE_URL}/api/datasets/{dataset_id}"
            f"/actions/:publish?type={version_type}"
        )

    resp = requests.post(url, headers=_headers(), timeout=30)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:500])

    data = resp.json().get("data", {})
    public_url = data.get("persistentUrl", f"https://dataverse.harvard.edu/dataset.xhtml?persistentId={dataset_id}")

    return PublishResponse(
        success=True,
        dataset_id=dataset_id,
        public_url=public_url,
        version=str(version_type),
        message="Dataset published successfully and is now publicly accessible.",
    )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search Harvard Dataverse",
    description="Search for existing datasets by keyword.",
)
def search_dataverse(
    q: str = Query(..., description="Search query"),
    max_results: int = Query(default=5, le=20, description="Max results to return"),
):
    url = f"{DATAVERSE_BASE_URL}/api/search"
    params = {"q": q, "type": "dataset", "per_page": max_results}
    resp = requests.get(url, params=params, timeout=30)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:300])

    items = resp.json().get("data", {}).get("items", [])
    return SearchResponse(
        success=True,
        query=q,
        total_results=len(items),
        results=[
            SearchResult(
                name=item.get("name", "N/A"),
                url=item.get("url", ""),
                published_at=item.get("published_at"),
                description=item.get("description", "")[:200] if item.get("description") else None,
            )
            for item in items
        ],
    )
