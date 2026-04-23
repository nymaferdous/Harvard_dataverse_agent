"""
routes/pipeline.py
------------------
POST /api/v1/pipeline/publish  — Full one-shot publish workflow

Accepts a file upload + author info, then:
  1. Auto-generates metadata (LLM)
  2. Checks for duplicates (Dataverse search)
  3. Creates dataset record
  4. Uploads the file
  5. Verifies
  6. Publishes (unless dry_run=true)

Also exposes background job tracking for async runs.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict

import requests
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from api.models import (
    JobResponse,
    JobStatus,
    PipelineStepResult,
    PublishPipelineResponse,
)
from modules.metadata_generator import generate_dataverse_metadata

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

DATAVERSE_BASE_URL = os.getenv("DATAVERSE_BASE_URL", "https://dataverse.harvard.edu")
DATAVERSE_API_TOKEN = os.getenv("DATAVERSE_API_TOKEN", "")

# In-memory job store (replace with Redis/DB for production)
_jobs: Dict[str, dict] = {}


def _headers():
    return {"X-Dataverse-key": DATAVERSE_API_TOKEN}


def _require_token():
    if not DATAVERSE_API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="DATAVERSE_API_TOKEN not configured.",
        )


# ---------------------------------------------------------------------------
# Synchronous full pipeline
# ---------------------------------------------------------------------------

@router.post(
    "/publish",
    response_model=PublishPipelineResponse,
    summary="Full publish pipeline (synchronous)",
    description=(
        "Upload a file and run the complete publish workflow in one request: "
        "metadata generation → duplicate check → dataset creation → file upload → publish. "
        "Set dry_run=true to stop before the final publish step."
    ),
)
async def publish_pipeline(
    file: UploadFile = File(..., description="Dataset file to publish"),
    dataverse_alias: str = Form(default="root"),
    author_name: str = Form(...),
    author_affiliation: str = Form(default=""),
    contact_email: str = Form(...),
    dry_run: bool = Form(
        default=False,
        description="If true, run all steps except the final publish",
    ),
):
    _require_token()

    steps: list[PipelineStepResult] = []
    persistent_id = None
    public_url = None

    # Save uploaded file temporarily
    suffix = Path(file.filename).suffix.lower()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # ── Step 1: Generate metadata ────────────────────────────────────────
        try:
            metadata = generate_dataverse_metadata(
                file_path=tmp_path,
                author_name=author_name,
                author_affiliation=author_affiliation,
                contact_email=contact_email,
                original_filename=file.filename,
            )
            title = (
                metadata.get("datasetVersion", {})
                .get("metadataBlocks", {})
                .get("citation", {})
                .get("fields", [{}])[0]
                .get("value", file.filename)
            )
            steps.append(PipelineStepResult(
                step="metadata_generation",
                status="success",
                detail=f"Generated metadata: title='{title}'",
            ))
        except Exception as e:
            steps.append(PipelineStepResult(
                step="metadata_generation", status="failed", detail=str(e)
            ))
            raise HTTPException(status_code=500, detail=f"Metadata generation failed: {e}")

        # ── Step 2: Check for duplicates ─────────────────────────────────────
        search_url = f"{DATAVERSE_BASE_URL}/api/search"
        search_resp = requests.get(
            search_url,
            params={"q": file.filename, "type": "dataset", "per_page": 3},
            timeout=15,
        )
        duplicate_found = False
        if search_resp.status_code == 200:
            hits = search_resp.json().get("data", {}).get("items", [])
            duplicate_found = len(hits) > 0
        steps.append(PipelineStepResult(
            step="duplicate_check",
            status="warning" if duplicate_found else "success",
            detail=(
                f"Found {len(hits)} potentially similar dataset(s) — proceeding anyway."
                if duplicate_found else "No duplicates found."
            ),
        ))

        # ── Step 3: Create dataset record ────────────────────────────────────
        create_url = f"{DATAVERSE_BASE_URL}/api/dataverses/{dataverse_alias}/datasets"
        create_resp = requests.post(
            create_url, headers=_headers(), json=metadata, timeout=30
        )
        if create_resp.status_code != 201:
            steps.append(PipelineStepResult(
                step="create_dataset", status="failed",
                detail=create_resp.text[:300],
            ))
            raise HTTPException(
                status_code=create_resp.status_code,
                detail=f"Dataset creation failed: {create_resp.text[:300]}",
            )
        dataset_data = create_resp.json()["data"]
        persistent_id = dataset_data.get("persistentId", "")
        numeric_id = str(dataset_data.get("id", ""))
        steps.append(PipelineStepResult(
            step="create_dataset",
            status="success",
            detail=f"Dataset created. Persistent ID: {persistent_id}",
        ))

        # ── Step 4: Upload file ───────────────────────────────────────────────
        if persistent_id.startswith("doi:") or persistent_id.startswith("hdl:"):
            upload_url = (
                f"{DATAVERSE_BASE_URL}/api/datasets/:persistentId/add"
                f"?persistentId={persistent_id}"
            )
        else:
            upload_url = f"{DATAVERSE_BASE_URL}/api/datasets/{numeric_id}/add"

        json_data = {
            "description": f"Data file: {file.filename}",
            "directoryLabel": "data",
            "categories": ["Data"],
            "restrict": False,
        }
        with open(tmp_path, "rb") as f_obj:
            upload_resp = requests.post(
                upload_url,
                headers=_headers(),
                files={
                    "file": (file.filename, f_obj, "application/octet-stream"),
                    "jsonData": (None, json.dumps(json_data), "application/json"),
                },
                timeout=60,
            )
        if upload_resp.status_code != 200:
            steps.append(PipelineStepResult(
                step="upload_file", status="failed",
                detail=upload_resp.text[:300],
            ))
            raise HTTPException(
                status_code=upload_resp.status_code,
                detail=f"File upload failed: {upload_resp.text[:300]}",
            )
        steps.append(PipelineStepResult(
            step="upload_file",
            status="success",
            detail=f"File '{file.filename}' uploaded successfully.",
        ))

        # ── Step 5: Verify ────────────────────────────────────────────────────
        verify_url = (
            f"{DATAVERSE_BASE_URL}/api/datasets/:persistentId/"
            f"?persistentId={persistent_id}"
        )
        verify_resp = requests.get(verify_url, headers=_headers(), timeout=15)
        if verify_resp.status_code == 200:
            v_data = verify_resp.json().get("data", {})
            state = v_data.get("latestVersion", {}).get("versionState", "UNKNOWN")
            file_count = len(v_data.get("latestVersion", {}).get("files", []))
            steps.append(PipelineStepResult(
                step="verify",
                status="success",
                detail=f"Dataset state: {state}, files: {file_count}",
            ))
        else:
            steps.append(PipelineStepResult(
                step="verify", status="warning",
                detail="Could not verify dataset state — continuing.",
            ))

        # ── Step 6: Publish (skip if dry_run) ─────────────────────────────────
        if dry_run:
            steps.append(PipelineStepResult(
                step="publish",
                status="skipped",
                detail="Dry run mode — dataset was NOT published.",
            ))
        else:
            # Wait for Dataverse ingest lock to clear before publishing
            locks_url = (
                f"{DATAVERSE_BASE_URL}/api/datasets/:persistentId/locks"
                f"?persistentId={persistent_id}"
            )
            pub_url = (
                f"{DATAVERSE_BASE_URL}/api/datasets/:persistentId/actions/:publish"
                f"?persistentId={persistent_id}&type=major"
            )
            max_wait, poll_interval, waited = 120, 8, 0
            while waited < max_wait:
                lock_resp = requests.get(locks_url, headers=_headers(), timeout=15)
                if lock_resp.status_code == 200:
                    locks = lock_resp.json().get("data", [])
                    if not locks:
                        break  # No locks — safe to publish
                    lock_types = [l.get("lockType", "?") for l in locks]
                    steps_detail = f"Waiting for ingest lock to clear ({lock_types})… {waited}s elapsed"
                    print(f"[Pipeline] {steps_detail}")
                    time.sleep(poll_interval)
                    waited += poll_interval
                else:
                    break  # Can't check — attempt anyway

            pub_resp = requests.post(pub_url, headers=_headers(), timeout=30)
            if pub_resp.status_code == 200:
                pub_data = pub_resp.json().get("data", {})
                public_url = pub_data.get(
                    "persistentUrl",
                    f"https://dataverse.harvard.edu/dataset.xhtml?persistentId={persistent_id}",
                )
                steps.append(PipelineStepResult(
                    step="publish",
                    status="success",
                    detail=f"Published! Public URL: {public_url}",
                ))
            else:
                steps.append(PipelineStepResult(
                    step="publish", status="failed",
                    detail=pub_resp.text[:300],
                ))
                raise HTTPException(
                    status_code=pub_resp.status_code,
                    detail=f"Publish failed: {pub_resp.text[:300]}",
                )

    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)

    all_ok = all(s.status in ("success", "warning", "skipped") for s in steps)
    return PublishPipelineResponse(
        success=all_ok,
        dry_run=dry_run,
        filename=file.filename,
        persistent_id=persistent_id,
        public_url=public_url,
        steps=steps,
        message=(
            f"Pipeline completed. Dataset {'created (dry run)' if dry_run else 'published'} "
            f"with ID: {persistent_id}"
        ),
    )


# ---------------------------------------------------------------------------
# Async pipeline with job tracking
# ---------------------------------------------------------------------------

def _run_pipeline_job(job_id: str, file_path: str, filename: str, kwargs: dict):
    """Background task: run the pipeline and store result in _jobs."""
    _jobs[job_id]["status"] = JobStatus.RUNNING
    try:
        # Simplified inline run for background task
        metadata = generate_dataverse_metadata(
            file_path=file_path,
            author_name=kwargs.get("author_name", ""),
            author_affiliation=kwargs.get("author_affiliation", ""),
            contact_email=kwargs.get("contact_email", ""),
        )
        alias = kwargs.get("dataverse_alias", "root")
        url = f"{DATAVERSE_BASE_URL}/api/dataverses/{alias}/datasets"
        resp = requests.post(url, headers=_headers(), json=metadata, timeout=30)
        if resp.status_code == 201:
            pid = resp.json()["data"].get("persistentId", "")
            _jobs[job_id].update({
                "status": JobStatus.COMPLETED,
                "result": {"persistent_id": pid, "status": "DRAFT"},
                "message": f"Dataset created: {pid}",
            })
        else:
            _jobs[job_id].update({
                "status": JobStatus.FAILED,
                "message": resp.text[:300],
            })
    except Exception as e:
        _jobs[job_id].update({
            "status": JobStatus.FAILED,
            "message": str(e),
        })
    finally:
        Path(file_path).unlink(missing_ok=True)


@router.post(
    "/publish/async",
    response_model=JobResponse,
    status_code=202,
    summary="Full publish pipeline (async / background job)",
    description=(
        "Start the publish pipeline as a background job. "
        "Returns a job_id immediately. Poll GET /pipeline/jobs/{job_id} for status."
    ),
)
async def publish_pipeline_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dataverse_alias: str = Form(default="root"),
    author_name: str = Form(...),
    author_affiliation: str = Form(default=""),
    contact_email: str = Form(...),
):
    _require_token()

    job_id = str(uuid.uuid4())
    suffix = Path(file.filename).suffix.lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    _jobs[job_id] = {
        "status": JobStatus.PENDING,
        "message": "Job queued",
        "result": None,
    }

    background_tasks.add_task(
        _run_pipeline_job,
        job_id,
        tmp_path,
        file.filename,
        {
            "dataverse_alias": dataverse_alias,
            "author_name": author_name,
            "author_affiliation": author_affiliation,
            "contact_email": contact_email,
        },
    )

    return JobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Job queued. Poll /api/v1/pipeline/jobs/{job_id} for status.",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="Get background job status",
)
def get_job_status(job_id: str):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    job = _jobs[job_id]
    return JobResponse(
        job_id=job_id,
        status=job["status"],
        message=job["message"],
        result=job.get("result"),
    )
