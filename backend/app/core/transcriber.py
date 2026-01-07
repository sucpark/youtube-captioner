"""Audio transcription using ElevenLabs STT API."""

import json
import logging
from elevenlabs.client import ElevenLabs
from app.core import config

logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: str, api_key: str) -> dict:
    """
    Transcribe audio file using ElevenLabs STT API.

    Args:
        audio_path: Path to the audio file
        api_key: ElevenLabs API key

    Returns:
        Transcription result with words and timestamps
    """
    client = ElevenLabs(api_key=api_key)

    logger.info(f"Starting transcription: {audio_path}")

    try:
        with open(audio_path, "rb") as audio_file:
            transcription = client.speech_to_text.convert(
                file=audio_file,
                model_id="scribe_v1",
                tag_audio_events=True,
                diarize=True,
            )
        logger.info("Transcription complete")

        result_dict = transcription.model_dump()
        lang_code_from_api = result_dict.get('language_code')
        standard_lang_code = config.convert_to_iso639_1(lang_code_from_api)

        if standard_lang_code:
            logger.info(f"Language code normalized: '{lang_code_from_api}' -> '{standard_lang_code}'")
            result_dict['language_code'] = standard_lang_code

        return result_dict

    except FileNotFoundError:
        logger.error(f"Audio file not found: {audio_path}")
        raise
    except Exception as e:
        logger.error(f"ElevenLabs API error: {e}")
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
