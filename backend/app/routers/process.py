"""Processing API router."""

import os
import asyncio
import logging
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import jobs
from app.jobs import JobStatus, job_to_dict
from app.core import downloader, transcriber, translator, captioner
from app.core.config import get_language_name
from app.routers.websocket import send_progress, send_completed, send_error

logger = logging.getLogger(__name__)

router = APIRouter()

# Storage directory
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)


class ProcessRequest(BaseModel):
    youtube_url: str
    target_language: str = "ko"
    srt_type: str = "both"  # source, translated, both
    max_line_length: int = 80
    pause_threshold: float = 1.0


class ProcessResponse(BaseModel):
    job_id: str
    status: str


@router.post("/process", response_model=ProcessResponse)
async def start_processing(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    x_elevenlabs_key: str = Header(..., alias="X-ElevenLabs-Key"),
    x_openai_key: str = Header(..., alias="X-OpenAI-Key"),
):
    """Start video processing job."""
    # Validate language
    lang_name = get_language_name(request.target_language)
    if not lang_name:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {request.target_language}")

    # Create job
    job = jobs.create_job(
        youtube_url=request.youtube_url,
        target_language=request.target_language,
        srt_type=request.srt_type,
    )

    # Start background processing
    background_tasks.add_task(
        run_pipeline,
        job.id,
        request.youtube_url,
        request.target_language,
        request.srt_type,
        request.max_line_length,
        request.pause_threshold,
        x_elevenlabs_key,
        x_openai_key,
    )

    return ProcessResponse(job_id=job.id, status=job.status.value)


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status."""
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_to_dict(job)


@router.get("/jobs/{job_id}/download/{file_type}")
async def download_file(job_id: str, file_type: str):
    """Download generated file."""
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")

    file_key = f"{file_type}_path"
    if file_key not in job.result:
        raise HTTPException(status_code=404, detail=f"File not found: {file_type}")

    filepath = job.result[file_key]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found on disk")

    filename = os.path.basename(filepath)
    return FileResponse(filepath, filename=filename)


async def run_pipeline(
    job_id: str,
    youtube_url: str,
    target_language: str,
    srt_type: str,
    max_line_length: int,
    pause_threshold: float,
    elevenlabs_key: str,
    openai_key: str,
):
    """Run the processing pipeline in background."""
    try:
        # Get video ID and create output directory
        video_id = downloader.get_video_id(youtube_url)
        output_dir = os.path.join(STORAGE_DIR, video_id)
        os.makedirs(output_dir, exist_ok=True)

        result = {"video_id": video_id}

        # Step 1: Download audio (0-25%)
        jobs.update_job(job_id, status=JobStatus.DOWNLOADING, progress=0, message="Downloading audio...")
        await send_progress(job_id, "downloading", 0, "Downloading audio...")

        # Run sync function in thread pool
        loop = asyncio.get_event_loop()
        audio_path = await loop.run_in_executor(
            None,
            downloader.download_youtube_audio,
            youtube_url,
            output_dir,
            video_id,
        )
        result["audio_path"] = audio_path

        jobs.update_job(job_id, progress=25, message="Audio download complete")
        await send_progress(job_id, "downloading", 25, "Audio download complete")

        # Step 2: Transcribe (25-50%)
        jobs.update_job(job_id, status=JobStatus.TRANSCRIBING, progress=25, message="Transcribing audio...")
        await send_progress(job_id, "transcribing", 25, "Transcribing audio...")

        transcription = await loop.run_in_executor(
            None,
            transcriber.transcribe_audio,
            audio_path,
            elevenlabs_key,
        )
        result["transcription"] = transcription
        result["source_language"] = transcription.get("language_code", "en")

        jobs.update_job(job_id, progress=50, message="Transcription complete")
        await send_progress(job_id, "transcribing", 50, "Transcription complete")

        # Step 3: Translate (50-75%) - only if needed
        if srt_type in ["translated", "both"]:
            jobs.update_job(job_id, status=JobStatus.TRANSLATING, progress=50, message="Translating...")
            await send_progress(job_id, "translating", 50, "Translating...")

            lang_name = get_language_name(target_language)

            def translate_with_progress():
                def progress_callback(progress: int, message: str):
                    # Scale progress from 0-100 to 50-75
                    scaled = 50 + int(progress * 0.25)
                    jobs.update_job(job_id, progress=scaled, message=message)
                    # Note: Can't await in sync callback, so we skip WebSocket here
                    # Progress will be sent via polling

                return translator.translate_text(
                    transcription,
                    lang_name,
                    openai_key,
                    progress_callback=progress_callback,
                )

            translated_segments = await loop.run_in_executor(None, translate_with_progress)
            result["translated_segments"] = translated_segments

            jobs.update_job(job_id, progress=75, message="Translation complete")
            await send_progress(job_id, "translating", 75, "Translation complete")
        else:
            jobs.update_job(job_id, progress=75, message="Skipping translation")
            await send_progress(job_id, "translating", 75, "Skipping translation")

        # Step 4: Generate SRT (75-100%)
        jobs.update_job(job_id, status=JobStatus.CAPTIONING, progress=75, message="Generating subtitles...")
        await send_progress(job_id, "captioning", 75, "Generating subtitles...")

        # Source SRT
        if srt_type in ["source", "both"]:
            source_lang = transcription.get("language_code", "en")
            srt_path, segments = await loop.run_in_executor(
                None,
                lambda: captioner.create_srt_file(
                    transcription,
                    "source",
                    video_id,
                    source_lang,
                    output_dir,
                    max_line_length,
                    pause_threshold,
                ),
            )
            result["source_srt_path"] = srt_path
            result["source_segments"] = segments

        # Translated SRT
        if srt_type in ["translated", "both"]:
            srt_path, segments = await loop.run_in_executor(
                None,
                lambda: captioner.create_srt_file(
                    result["translated_segments"],
                    "translated",
                    video_id,
                    target_language,
                    output_dir,
                    max_line_length,
                ),
            )
            result["translated_srt_path"] = srt_path
            result["translated_segments"] = segments

        # Complete
        jobs.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress=100,
            message="Processing complete",
            result=result,
        )
        await send_completed(job_id, {
            "video_id": video_id,
            "source_language": result.get("source_language"),
            "has_source_srt": "source_srt_path" in result,
            "has_translated_srt": "translated_srt_path" in result,
        })

    except Exception as e:
        logger.exception(f"Pipeline error: {e}")
        jobs.update_job(job_id, status=JobStatus.FAILED, error=str(e))
        await send_error(job_id, str(e))
