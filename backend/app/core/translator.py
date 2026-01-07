"""Text translation using OpenAI GPT API."""

import logging
from typing import Callable
from openai import OpenAI

logger = logging.getLogger(__name__)


def _create_translation_chunks(transcription_result: dict, max_chunk_words: int = 50) -> list[dict]:
    """Group transcription into chunks for translation. New chunk on speaker change."""
    chunks = []
    current_chunk_words = []
    current_chunk_text = ""
    current_speaker = None

    if 'words' not in transcription_result or not transcription_result['words']:
        return []

    def finalize_chunk():
        nonlocal current_chunk_words, current_chunk_text, current_speaker
        if current_chunk_words:
            chunks.append({
                "source_text": current_chunk_text.strip(),
                "start_time": current_chunk_words[0]['start'],
                "end_time": current_chunk_words[-1]['end']
            })
            current_chunk_words = []
            current_chunk_text = ""
            current_speaker = None

    for word_data in transcription_result['words']:
        if word_data.get('type') == 'spacing':
            continue
        speaker = word_data.get('speaker_id', 'unknown')
        if (speaker != current_speaker and current_speaker is not None) or \
           (len(current_chunk_words) >= max_chunk_words):
            finalize_chunk()
        current_chunk_words.append(word_data)
        if current_speaker is None:
            current_speaker = speaker
            current_chunk_text += f"{speaker}: "
        current_chunk_text += word_data.get('text', '') + " "
    finalize_chunk()
    return chunks


def translate_text(
    transcription_result: dict,
    target_language: str,
    api_key: str,
    history_size: int = 3,
    progress_callback: Callable[[int, str], None] | None = None
) -> list[dict]:
    """
    Translate transcribed text using GPT-4o-mini.

    Args:
        transcription_result: Transcription result from ElevenLabs
        target_language: Target language name (e.g., "Korean", "Japanese")
        api_key: OpenAI API key
        history_size: Number of previous chunks to keep for context
        progress_callback: Optional callback for progress updates (progress%, message)

    Returns:
        List of translated segments
    """
    client = OpenAI(api_key=api_key)
    chunks = _create_translation_chunks(transcription_result)
    translated_segments = []
    conversation_history = []

    total_chunks = len(chunks)
    logger.info(f"Translating {total_chunks} chunks to '{target_language}'...")

    for i, chunk in enumerate(chunks):
        try:
            if progress_callback:
                progress = int((i / total_chunks) * 100)
                progress_callback(progress, f"Translating chunk {i+1}/{total_chunks}")

            logger.info(f"Translating chunk {i+1}/{total_chunks}...")

            system_prompt = (
                f"You are a professional translator. Translate the following dialogue "
                f"into natural {target_language}. Maintain the speaker labels "
                f"(e.g., speaker_1:) and translate only the content."
            )

            messages_to_send = [{"role": "system", "content": system_prompt}]
            messages_to_send.extend(conversation_history)
            messages_to_send.append({"role": "user", "content": chunk["source_text"]})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_to_send,
                temperature=0.3,
            )

            translated_text = response.choices[0].message.content.strip()

            translated_segments.append({
                "start": chunk["start_time"],
                "end": chunk["end_time"],
                "translated_text": translated_text,
                "source_text": chunk["source_text"]
            })

            conversation_history.append({"role": "user", "content": chunk["source_text"]})
            conversation_history.append({"role": "assistant", "content": translated_text})

            if len(conversation_history) > history_size * 2:
                conversation_history = conversation_history[-history_size * 2:]

        except Exception as e:
            logger.error(f"Translation error: {e}")
            translated_segments.append({
                "start": chunk["start_time"],
                "end": chunk["end_time"],
                "translated_text": f"[Translation failed] {chunk['source_text']}",
                "source_text": chunk["source_text"]
            })

    if progress_callback:
        progress_callback(100, "Translation complete")

    logger.info("Translation complete")
    return translated_segments
