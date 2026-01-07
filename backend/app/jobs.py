"""In-memory job management."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class JobStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    TRANSLATING = "translating"
    CAPTIONING = "captioning"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobInfo:
    id: str
    youtube_url: str
    target_language: str
    srt_type: str
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    message: str = ""
    error: str | None = None
    result: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# In-memory job storage
jobs: dict[str, JobInfo] = {}


def create_job(youtube_url: str, target_language: str, srt_type: str) -> JobInfo:
    """Create a new job."""
    job_id = str(uuid.uuid4())
    job = JobInfo(
        id=job_id,
        youtube_url=youtube_url,
        target_language=target_language,
        srt_type=srt_type,
    )
    jobs[job_id] = job
    return job


def get_job(job_id: str) -> JobInfo | None:
    """Get job by ID."""
    return jobs.get(job_id)


def update_job(
    job_id: str,
    status: JobStatus | None = None,
    progress: int | None = None,
    message: str | None = None,
    error: str | None = None,
    result: dict[str, Any] | None = None,
) -> JobInfo | None:
    """Update job status and progress."""
    job = jobs.get(job_id)
    if not job:
        return None

    if status is not None:
        job.status = status
    if progress is not None:
        job.progress = progress
    if message is not None:
        job.message = message
    if error is not None:
        job.error = error
    if result is not None:
        job.result.update(result)
    job.updated_at = datetime.now()

    return job


def delete_job(job_id: str) -> bool:
    """Delete job by ID."""
    if job_id in jobs:
        del jobs[job_id]
        return True
    return False


def job_to_dict(job: JobInfo) -> dict:
    """Convert job to dictionary for JSON response."""
    return {
        "id": job.id,
        "youtube_url": job.youtube_url,
        "target_language": job.target_language,
        "srt_type": job.srt_type,
        "status": job.status.value,
        "progress": job.progress,
        "message": job.message,
        "error": job.error,
        "result": job.result,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }
