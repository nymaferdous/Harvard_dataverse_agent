"""
models.py
---------
Pydantic request and response models for the Dataverse Publishing API.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"


class VersionType(str, Enum):
    MAJOR = "major"
    MINOR = "minor"


# ---------------------------------------------------------------------------
# Shared / base
# ---------------------------------------------------------------------------

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

class GeneratedMetadata(BaseModel):
    title: str
    description: str
    keywords: List[str]
    subject: str
    geographic_coverage: str
    time_period_start: str
    time_period_end: str
    data_source: str
    license: str = "CC0 1.0"
    related_publication: Optional[str] = ""


class MetadataPreviewResponse(BaseModel):
    success: bool
    filename: str
    metadata: GeneratedMetadata
    dataverse_schema: Dict[str, Any] = Field(
        description="Full Dataverse-ready metadata JSON (POST-ready)"
    )


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class CreateDatasetRequest(BaseModel):
    dataverse_alias: str = Field(
        default="root",
        description="The dataverse alias to create the dataset in",
        examples=["myresearch"],
    )
    author_name: str = Field(examples=["Jane Smith"])
    author_affiliation: str = Field(default="", examples=["Harvard University"])
    contact_email: str = Field(examples=["jane@harvard.edu"])


class CreateDatasetResponse(BaseModel):
    success: bool
    persistent_id: str = Field(description="Dataset DOI, e.g. doi:10.7910/DVN/XXXXX")
    numeric_id: str
    status: str = "DRAFT"
    message: str


class DatasetInfoResponse(BaseModel):
    success: bool
    dataset_id: str
    title: str
    status: str
    file_count: int
    files: List[str]


# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------

class UploadFileResponse(BaseModel):
    success: bool
    dataset_id: str
    filename: str
    file_id: Optional[str]
    directory: str
    message: str


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------

class PublishRequest(BaseModel):
    version_type: VersionType = VersionType.MAJOR


class PublishResponse(BaseModel):
    success: bool
    dataset_id: str
    public_url: str
    version: str
    message: str


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SearchResult(BaseModel):
    name: str
    url: str
    published_at: Optional[str]
    description: Optional[str]


class SearchResponse(BaseModel):
    success: bool
    query: str
    total_results: int
    results: List[SearchResult]


# ---------------------------------------------------------------------------
# Full pipeline (publish workflow)
# ---------------------------------------------------------------------------

class PublishPipelineRequest(BaseModel):
    dataverse_alias: str = Field(default="root")
    author_name: str = Field(examples=["Jane Smith"])
    author_affiliation: str = Field(default="", examples=["Harvard University"])
    contact_email: str = Field(examples=["jane@harvard.edu"])
    dry_run: bool = Field(
        default=False,
        description="If true, runs the full workflow but skips the final publish step",
    )


class PipelineStepResult(BaseModel):
    step: str
    status: str
    detail: str


class PublishPipelineResponse(BaseModel):
    success: bool
    dry_run: bool
    filename: str
    persistent_id: Optional[str] = None
    public_url: Optional[str] = None
    steps: List[PipelineStepResult]
    message: str


# ---------------------------------------------------------------------------
# Agent chat
# ---------------------------------------------------------------------------

class AgentChatRequest(BaseModel):
    message: str = Field(
        description="Natural language instruction for the agent",
        examples=["Publish my dataset FAOSTAT.csv to Harvard Dataverse"],
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for conversational continuity",
    )


class AgentChatResponse(BaseModel):
    success: bool
    session_id: str
    answer: str
    steps_taken: int


# ---------------------------------------------------------------------------
# Job tracking (for async long-running tasks)
# ---------------------------------------------------------------------------

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    result: Optional[Dict[str, Any]] = None
