"""
dataverse_tools.py
------------------
LangChain tools wrapping the Harvard Dataverse Native API.

Dataverse API reference: https://guides.dataverse.org/en/latest/api/native-api.html

Tools available:
  - CreateDatasetTool   : Create a new draft dataset record with metadata
  - UploadFileTool      : Upload a file to an existing dataset
  - PublishDatasetTool  : Publish a draft dataset (make it publicly visible)
  - GetDatasetInfoTool  : Retrieve metadata/status of an existing dataset
  - SearchDataverseTool : Search for datasets by keyword

Required env vars:
  DATAVERSE_API_TOKEN  — your Harvard Dataverse API token
  DATAVERSE_BASE_URL   — default: https://dataverse.harvard.edu
  DATAVERSE_ALIAS      — the dataverse alias to publish into (e.g. "harvard" or your own)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Type

import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATAVERSE_BASE_URL = os.getenv("DATAVERSE_BASE_URL", "https://dataverse.harvard.edu")
DATAVERSE_API_TOKEN = os.getenv("DATAVERSE_API_TOKEN", "")
DATAVERSE_ALIAS = os.getenv("DATAVERSE_ALIAS", "root")


def _headers() -> Dict[str, str]:
    return {"X-Dataverse-key": DATAVERSE_API_TOKEN}


def _check_token() -> None:
    if not DATAVERSE_API_TOKEN:
        raise EnvironmentError(
            "DATAVERSE_API_TOKEN not set. Add it to your .env file."
        )


# ---------------------------------------------------------------------------
# Tool input schemas
# ---------------------------------------------------------------------------

class CreateDatasetInput(BaseModel):
    metadata_json: str = Field(
        description=(
            "A JSON string conforming to the Dataverse dataset metadata schema. "
            "Must include title, author, description, subject, and contact fields."
        )
    )
    dataverse_alias: str = Field(
        default=DATAVERSE_ALIAS,
        description="The alias of the dataverse to create the dataset in.",
    )


class UploadFileInput(BaseModel):
    dataset_id: str = Field(
        description="The persistent ID (e.g. doi:10.7910/DVN/XXXXX) or numeric ID of the dataset."
    )
    file_path: str = Field(
        description="Absolute or relative path to the file to upload."
    )
    description: str = Field(
        default="",
        description="Optional description for this file.",
    )
    directory_label: str = Field(
        default="data",
        description="Folder label within the dataset (e.g. 'data', 'raw').",
    )


class PublishDatasetInput(BaseModel):
    dataset_id: str = Field(
        description="Persistent ID (doi:...) or numeric ID of the dataset to publish."
    )
    version_type: str = Field(
        default="major",
        description="Version type: 'major' (1.0) or 'minor' (0.1 update).",
    )


class GetDatasetInfoInput(BaseModel):
    dataset_id: str = Field(
        description="Persistent ID (doi:...) or numeric ID of the dataset."
    )


class SearchDataverseInput(BaseModel):
    query: str = Field(description="Search query string.")
    dataset_type: str = Field(
        default="dataset",
        description="Type filter: 'dataset', 'file', or 'dataverse'.",
    )
    max_results: int = Field(default=5, description="Maximum number of results to return.")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

class CreateDatasetTool(BaseTool):
    """Create a new draft dataset in Harvard Dataverse."""

    name: str = "create_dataverse_dataset"
    description: str = (
        "Create a new draft dataset record in Harvard Dataverse with the provided metadata. "
        "Returns the dataset persistent ID (DOI) and numeric ID on success. "
        "Use this BEFORE uploading files."
    )
    args_schema: Type[BaseModel] = CreateDatasetInput

    def _run(self, metadata_json: str, dataverse_alias: str = DATAVERSE_ALIAS) -> str:
        _check_token()
        try:
            metadata = json.loads(metadata_json)
        except json.JSONDecodeError as e:
            return f"ERROR: Invalid JSON in metadata — {e}"

        url = f"{DATAVERSE_BASE_URL}/api/dataverses/{dataverse_alias}/datasets"
        response = requests.post(url, headers=_headers(), json=metadata, timeout=30)

        if response.status_code == 201:
            data = response.json()["data"]
            persistent_id = data.get("persistentId", "N/A")
            numeric_id = data.get("id", "N/A")
            return (
                f"SUCCESS: Dataset created.\n"
                f"  Persistent ID : {persistent_id}\n"
                f"  Numeric ID    : {numeric_id}\n"
                f"  Status        : DRAFT (not yet public)\n"
                f"  Next step     : Upload files using persistent_id='{persistent_id}'"
            )
        else:
            return (
                f"ERROR {response.status_code}: {response.text[:500]}"
            )

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported.")


class UploadFileTool(BaseTool):
    """Upload a file to an existing Dataverse dataset."""

    name: str = "upload_file_to_dataset"
    description: str = (
        "Upload a local file to an existing Harvard Dataverse dataset. "
        "The dataset must already exist (use create_dataverse_dataset first). "
        "Returns upload confirmation with the file ID."
    )
    args_schema: Type[BaseModel] = UploadFileInput

    def _run(
        self,
        dataset_id: str,
        file_path: str,
        description: str = "",
        directory_label: str = "data",
    ) -> str:
        _check_token()
        path = Path(file_path)
        if not path.exists():
            return f"ERROR: File not found at '{file_path}'"

        # Use persistentId if it looks like a DOI, else numeric
        if dataset_id.startswith("doi:") or dataset_id.startswith("hdl:"):
            url = f"{DATAVERSE_BASE_URL}/api/datasets/:persistentId/add?persistentId={dataset_id}"
        else:
            url = f"{DATAVERSE_BASE_URL}/api/datasets/{dataset_id}/add"

        json_data = {
            "description": description,
            "directoryLabel": directory_label,
            "categories": ["Data"],
            "restrict": False,
        }

        with open(path, "rb") as f:
            files = {
                "file": (path.name, f, "text/csv"),
                "jsonData": (None, json.dumps(json_data), "application/json"),
            }
            response = requests.post(url, headers=_headers(), files=files, timeout=60)

        if response.status_code == 200:
            data = response.json().get("data", {})
            file_id = data.get("files", [{}])[0].get("dataFile", {}).get("id", "N/A")
            return (
                f"SUCCESS: File '{path.name}' uploaded.\n"
                f"  File ID       : {file_id}\n"
                f"  Dataset       : {dataset_id}\n"
                f"  Directory     : {directory_label}/\n"
                f"  Next step     : Publish dataset using publish_dataverse_dataset"
            )
        else:
            return f"ERROR {response.status_code}: {response.text[:500]}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported.")


class PublishDatasetTool(BaseTool):
    """Publish a Dataverse dataset draft to make it publicly visible."""

    name: str = "publish_dataverse_dataset"
    description: str = (
        "Publish a draft dataset in Harvard Dataverse, making it publicly accessible. "
        "WARNING: Once published, the dataset gets a DOI and is public. "
        "Ensure metadata and files are correct before calling this."
    )
    args_schema: Type[BaseModel] = PublishDatasetInput

    def _run(self, dataset_id: str, version_type: str = "major") -> str:
        _check_token()

        if dataset_id.startswith("doi:") or dataset_id.startswith("hdl:"):
            url = (
                f"{DATAVERSE_BASE_URL}/api/datasets/:persistentId/actions/:publish"
                f"?persistentId={dataset_id}&type={version_type}"
            )
            locks_url = (
                f"{DATAVERSE_BASE_URL}/api/datasets/:persistentId/locks"
                f"?persistentId={dataset_id}"
            )
        else:
            url = f"{DATAVERSE_BASE_URL}/api/datasets/{dataset_id}/actions/:publish?type={version_type}"
            locks_url = f"{DATAVERSE_BASE_URL}/api/datasets/{dataset_id}/locks"

        # Wait for any ingest/edit locks to clear before publishing
        max_wait_seconds = 120
        poll_interval = 8
        waited = 0
        while waited < max_wait_seconds:
            lock_resp = requests.get(locks_url, headers=_headers(), timeout=15)
            if lock_resp.status_code == 200:
                locks = lock_resp.json().get("data", [])
                if not locks:
                    break  # No locks — safe to publish
                lock_types = [l.get("lockType", "") for l in locks]
                print(f"[PublishTool] Dataset locked ({lock_types}), waiting {poll_interval}s…")
                time.sleep(poll_interval)
                waited += poll_interval
            else:
                break  # Can't check locks — attempt publish anyway

        if waited >= max_wait_seconds:
            return (
                "ERROR: Dataset is still locked after 2 minutes (Dataverse ingest is slow). "
                "Please try publishing again in a few minutes via the Dataverse web UI or retry this tool."
            )

        response = requests.post(url, headers=_headers(), timeout=30)

        if response.status_code == 200:
            data = response.json().get("data", {})
            pid = data.get("persistentUrl", dataset_id)
            return (
                f"SUCCESS: Dataset published!\n"
                f"  Public URL    : {pid}\n"
                f"  Version       : {version_type}\n"
                f"  The dataset is now publicly visible on Harvard Dataverse."
            )
        else:
            return f"ERROR {response.status_code}: {response.text[:500]}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported.")


class GetDatasetInfoTool(BaseTool):
    """Retrieve metadata and status of an existing Dataverse dataset."""

    name: str = "get_dataset_info"
    description: str = (
        "Retrieve the current metadata, version status, and file list for a "
        "Harvard Dataverse dataset. Useful to verify a dataset before publishing."
    )
    args_schema: Type[BaseModel] = GetDatasetInfoInput

    def _run(self, dataset_id: str) -> str:
        _check_token()

        if dataset_id.startswith("doi:") or dataset_id.startswith("hdl:"):
            url = f"{DATAVERSE_BASE_URL}/api/datasets/:persistentId/?persistentId={dataset_id}"
        else:
            url = f"{DATAVERSE_BASE_URL}/api/datasets/{dataset_id}"

        response = requests.get(url, headers=_headers(), timeout=30)

        if response.status_code == 200:
            data = response.json().get("data", {})
            version = data.get("latestVersion", {})
            status = version.get("versionState", "UNKNOWN")
            files = version.get("files", [])
            title_field = next(
                (f for f in version.get("metadataBlocks", {})
                 .get("citation", {}).get("fields", [])
                 if f.get("typeName") == "title"), {}
            )
            title = title_field.get("value", "N/A")
            return (
                f"Dataset: {title}\n"
                f"  ID     : {dataset_id}\n"
                f"  Status : {status}\n"
                f"  Files  : {len(files)} file(s)\n"
                + "\n".join(
                    f"    - {f.get('dataFile', {}).get('filename', 'unknown')}"
                    for f in files
                )
            )
        else:
            return f"ERROR {response.status_code}: {response.text[:300]}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported.")


class SearchDataverseTool(BaseTool):
    """Search Harvard Dataverse for existing datasets."""

    name: str = "search_dataverse"
    description: str = (
        "Search Harvard Dataverse for existing datasets by keyword, subject, or topic. "
        "Useful for checking if a dataset already exists before creating a duplicate."
    )
    args_schema: Type[BaseModel] = SearchDataverseInput

    def _run(self, query: str, dataset_type: str = "dataset", max_results: int = 5) -> str:
        url = f"{DATAVERSE_BASE_URL}/api/search"
        params = {
            "q": query,
            "type": dataset_type,
            "per_page": max_results,
            "sort": "date",
            "order": "desc",
        }
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            items = response.json().get("data", {}).get("items", [])
            if not items:
                return f"No results found for '{query}'."
            results = [f"Found {len(items)} result(s) for '{query}':"]
            for item in items:
                results.append(
                    f"  • {item.get('name', 'N/A')}\n"
                    f"    URL: {item.get('url', 'N/A')}\n"
                    f"    Published: {item.get('published_at', 'N/A')}"
                )
            return "\n".join(results)
        else:
            return f"ERROR {response.status_code}: {response.text[:300]}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported.")


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

def get_dataverse_tools() -> list:
    """Return all Dataverse tools for use with a LangChain agent."""
    return [
        CreateDatasetTool(),
        UploadFileTool(),
        PublishDatasetTool(),
        GetDatasetInfoTool(),
        SearchDataverseTool(),
    ]
