"""SRT subtitle file generation."""

import os
import re
import logging

logger = logging.getLogger(__name__)


def _format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,ms)."""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def _group_words_into_sentences(words: list[dict], pause_threshold: float) -> list[list[dict]]:
    """Group words into sentences based on punctuation, speaker change, or long pauses."""
    if not words:
        return []
    sentences, current_sentence = [], []
    for i, word_data in enumerate(words):
        if word_data.get('type') == 'spacing':
            continue
        current_sentence.append(word_data)
        word_text = word_data.get('text', '').strip()
        is_end_of_sentence = word_text and word_text[-1] in '.?!...'
        is_break_condition = False
        if i + 1 < len(words):
            next_word = words[i + 1]
            if next_word.get('type') == 'spacing' and i + 2 < len(words):
                next_word = words[i + 2]
            is_new_speaker = next_word.get('speaker_id') != word_data.get('speaker_id')
            is_long_pause = (next_word.get('start', 0) - word_data.get('end', 0)) > pause_threshold
            if is_new_speaker or is_long_pause:
                is_break_condition = True
        if is_end_of_sentence or is_break_condition:
            sentences.append(current_sentence)
            current_sentence = []
    if current_sentence:
        sentences.append(current_sentence)
    return sentences


def _split_long_line(text: str, max_length: int, has_prefix: bool) -> list[str]:
    """Split text into multiple lines based on max length."""
    speaker_prefix = ""
    if has_prefix:
        match = re.match(r"(speaker_\d+: |unknown: )", text)
        if match:
            speaker_prefix = match.group(0)
            text = text[len(speaker_prefix):].strip()

    sentences = [s.strip() for s in re.split(r'(?<=[.?!...])\s*', text) if s.strip()]
    merged_lines = []
    current_line = ""
    for sentence in sentences:
        if not current_line:
            current_line = sentence
            continue
        if len(current_line) + len(sentence) + 1 <= max_length:
            current_line += " " + sentence
        else:
            merged_lines.append(current_line)
            current_line = sentence
    if current_line:
        merged_lines.append(current_line)

    final_lines = []
    for line in merged_lines:
        if len(line) <= max_length:
            final_lines.append(line)
            continue
        words, new_line = line.split(), ""
        for word in words:
            if len(new_line) + len(word) + 1 > max_length:
                if new_line:
                    final_lines.append(new_line.strip())
                new_line = word
            else:
                new_line += (" " if new_line else "") + word
        if new_line:
            final_lines.append(new_line.strip())

    if final_lines and speaker_prefix:
        final_lines[0] = speaker_prefix + final_lines[0]
    return [line for line in final_lines if line]


def _generate_segments_from_source(words: list[dict], max_line_length: int, pause_threshold: float) -> list[dict]:
    """Generate subtitle segments from source words."""
    sentences = _group_words_into_sentences(words, pause_threshold)

    merged_lines_info = []
    current_line_sentences = []
    for sentence in sentences:
        is_same_speaker = True
        if current_line_sentences:
            is_same_speaker = sentence[0]['speaker_id'] == current_line_sentences[0][0]['speaker_id']

        current_text = ' '.join(' '.join(w['text'] for w in s) for s in current_line_sentences)
        sentence_text = ' '.join(w['text'] for w in sentence)

        if not current_line_sentences or ((len(current_text) + len(sentence_text) + 1) <= max_line_length and is_same_speaker):
            current_line_sentences.append(sentence)
        else:
            merged_lines_info.append(current_line_sentences)
            current_line_sentences = [sentence]

    if current_line_sentences:
        merged_lines_info.append(current_line_sentences)

    temp_segments = []
    last_speaker_id = None
    for line_group in merged_lines_info:
        first_word, last_word = line_group[0][0], line_group[-1][-1]
        text = ' '.join(' '.join(w['text'] for w in s) for s in line_group)
        current_speaker_id = first_word['speaker_id']

        has_prefix = False
        if current_speaker_id != last_speaker_id:
            prefix = f"speaker_{current_speaker_id}: " if current_speaker_id is not None else "unknown: "
            text = prefix + text
            has_prefix = True

        last_speaker_id = current_speaker_id
        if not text.strip() or text.strip() in ['...', '...']:
            continue
        temp_segments.append({
            'start': first_word['start'],
            'end': last_word['end'],
            'text': text,
            'has_prefix': has_prefix
        })

    final_segments = []
    for segment in temp_segments:
        lines = _split_long_line(segment['text'], max_line_length, segment['has_prefix'])
        if not lines:
            continue
        total_duration = segment['end'] - segment['start']
        total_chars = sum(len(line) for line in lines)
        current_time = segment['start']
        for line in lines:
            line_char_ratio = len(line) / total_chars if total_chars > 0 else 0
            line_duration = total_duration * line_char_ratio
            if line_duration < 0.5:
                line_duration = 0.5
            final_segments.append({
                'start': current_time,
                'end': current_time + line_duration,
                'text': line.strip()
            })
            current_time += line_duration
    return final_segments


def _generate_segments_from_translation(translated_data: list[dict], max_line_length: int) -> list[dict]:
    """Generate subtitle segments from translated data."""
    final_segments = []
    for segment in translated_data:
        start, end, text = segment['start'], segment['end'], segment['translated_text']
        lines = _split_long_line(text, max_line_length, has_prefix=True)
        total_duration = end - start
        total_chars = sum(len(line) for line in lines)
        if not lines:
            continue
        current_time = start
        for line in lines:
            line_char_ratio = len(line) / total_chars if total_chars > 0 else 0
            line_duration = total_duration * line_char_ratio
            if line_duration < 0.5:
                line_duration = 0.5
            final_segments.append({
                'start': current_time,
                'end': current_time + line_duration,
                'text': line.strip()
            })
            current_time += line_duration
    return final_segments


def generate_srt_content(segments: list[dict]) -> str:
    """Generate SRT content string from segments."""
    srt_content = ""
    for i, segment in enumerate(segments):
        start_time = _format_srt_time(segment['start'])
        end_time = _format_srt_time(segment['end'])
        text = segment['text']
        srt_content += f"{i + 1}\n{start_time} --> {end_time}\n{text}\n\n"
    return srt_content


def create_srt_file(
    data: dict | list,
    mode: str,
    video_id: str,
    lang_code: str,
    output_dir: str,
    max_line_length: int,
    pause_threshold: float = 1.0,
) -> tuple[str, list[dict]]:
    """
    Create SRT subtitle file.

    Returns:
        Tuple of (filepath, segments)
    """
    segments = []
    if mode == 'source':
        segments = _generate_segments_from_source(data.get('words', []), max_line_length, pause_threshold)
    elif mode == 'translated':
        segments = _generate_segments_from_translation(data, max_line_length)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    srt_content = generate_srt_content(segments)

    lang_suffix = lang_code if mode == 'translated' else data.get('language_code', 'source')
    filename = f"{video_id}_{lang_suffix}.srt"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    logger.info(f"SRT file created: {filepath}")

    return filepath, segments
