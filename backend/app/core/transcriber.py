"""Audio transcription using OpenAI gpt-4o-transcribe API."""

import json
import logging
import re
from openai import OpenAI
from app.core import config

logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: str, api_key: str) -> dict:
    """
    Transcribe audio file using OpenAI gpt-4o-transcribe API.

    Args:
        audio_path: Path to the audio file
        api_key: OpenAI API key

    Returns:
        Transcription result with segments and timestamps
    """
    client = OpenAI(api_key=api_key)

    logger.info(f"Starting transcription: {audio_path}")

    try:
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=audio_file,
                response_format="verbose_json",
            )
        logger.info("Transcription complete")

        # Parse segments and convert speaker labels to IDs
        segments = []
        for seg in transcription.segments:
            # Handle speaker field if present (diarization)
            speaker_id = 0
            speaker = getattr(seg, 'speaker', None)
            if speaker:
                # "Speaker 1" -> 0, "Speaker 2" -> 1, etc.
                speaker_match = re.search(r'Speaker\s*(\d+)', speaker)
                if speaker_match:
                    speaker_id = int(speaker_match.group(1)) - 1

            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
                "speaker_id": speaker_id
            })

        # Detect language from response or default to "en"
        lang_code = getattr(transcription, 'language', 'en')
        standard_lang_code = config.convert_to_iso639_1(lang_code)

        if standard_lang_code:
            logger.info(f"Language code normalized: '{lang_code}' -> '{standard_lang_code}'")

        return {
            "language_code": standard_lang_code or "en",
            "segments": segments
        }

    except FileNotFoundError:
        logger.error(f"Audio file not found: {audio_path}")
        raise
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise ValueError(f"Transcription failed: {e}")


def save_transcription(result: dict, output_path: str):
    """Save transcription result to JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        logger.info(f"Transcription saved: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save transcription: {e}")
        raise
