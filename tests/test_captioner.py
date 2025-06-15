import pytest
import os
from src.modules.captioner import (
    _format_srt_time,
    _generate_segments_from_source,
    _split_long_line,
    create_srt_file,
)

@pytest.fixture
def sample_source_words():
    """테스트를 위한 샘플 'words' 리스트를 제공하는 Fixture."""
    return [
        {'text': 'Pleasure.', 'start': 9.179, 'end': 9.619, 'type': 'word', 'speaker_id': 1},
        {'text': 'Thank', 'start': 9.619, 'end': 9.879, 'type': 'word', 'speaker_id': 1},
        {'text': 'you.', 'start': 9.879, 'end': 9.999, 'type': 'word', 'speaker_id': 1},
        {'text': 'So,', 'start': 11.5, 'end': 11.8, 'type': 'word', 'speaker_id': 0},
        {'text': 'Phrase', 'start': 11.9, 'end': 12.5, 'type': 'word', 'speaker_id': 0},
        {'text': 'is', 'start': 12.5, 'end': 12.8, 'type': 'word', 'speaker_id': 0},
        {'text': 'a', 'start': 12.8, 'end': 12.9, 'type': 'word', 'speaker_id': 0},
        {'text': 'world', 'start': 12.9, 'end': 13.2, 'type': 'word', 'speaker_id': 0},
        {'text': 'leader', 'start': 13.2, 'end': 13.6, 'type': 'word', 'speaker_id': 0},
        {'text': 'in', 'start': 13.6, 'end': 13.7, 'type': 'word', 'speaker_id': 0},
        {'text': 'localization.', 'start': 13.7, 'end': 14.8, 'type': 'word', 'speaker_id': 0},
        {'text': 'Yes,', 'start': 15.0, 'end': 15.5, 'type': 'word', 'speaker_id': 1},
        {'text': 'it', 'start': 15.5, 'end': 15.7, 'type': 'word', 'speaker_id': 1},
        {'text': 'is!', 'start': 15.7, 'end': 16.0, 'type': 'word', 'speaker_id': 1},
    ]

@pytest.fixture
def sample_translated_segments():
    """테스트를 위한 샘플 번역 세그먼트 Fixture."""
    return [
        {"start": 9.179, "end": 9.999, "translated_text": "speaker_1: 반갑습니다. 감사합니다."},
        {"start": 11.5, "end": 16.0, "translated_text": "speaker_0: 그래서 Phrase는 로컬라이제이션의 세계적인 선두주자입니다. speaker_1: 네, 맞습니다!"}
    ]

def test_format_srt_time():
    assert _format_srt_time(61.555) == "00:01:01,555"

def test_generate_segments_from_source(sample_source_words):
    """'병합 우선' 전략 및 화자 변경에 따른 분리 테스트 (기대값 수정)."""
    segments = _generate_segments_from_source(sample_source_words, max_line_length=100, pause_threshold=1.0)
    # 화자/긴침묵 기준으로 3개의 세그먼트가 생성되어야 함
    assert len(segments) == 3
    assert segments[0]['text'] == "speaker_1: Pleasure. Thank you."
    assert segments[1]['text'] == "speaker_0: So, Phrase is a world leader in localization."
    assert segments[2]['text'] == "speaker_1: Yes, it is!"

def test_generate_segments_from_source_with_long_line(sample_source_words):
    """max_line_length 제약 조건이 올바르게 동작하는지 테스트."""
    segments = _generate_segments_from_source(sample_source_words, max_line_length=25, pause_threshold=1.0)
    assert len(segments) == 4
    assert segments[0]['text'] == 'speaker_1: Pleasure. Thank you.'
    assert segments[1]['text'] == 'speaker_0: So, Phrase is a world'
    assert segments[2]['text'] == 'leader in localization.'
    assert segments[3]['text'] == 'speaker_1: Yes, it is!'

def test_split_long_line():
    """'병합 우선, 분할 차선' 로직을 테스트."""
    # has_prefix 인자 추가에 따른 테스트 수정
    text1 = "speaker_0: 안녕하세요. 반갑습니다."
    lines1 = _split_long_line(text1, max_length=40, has_prefix=True)
    assert len(lines1) == 1
    assert lines1[0] == "speaker_0: 안녕하세요. 반갑습니다."

    text2 = "speaker_0: 안녕하세요. 반갑습니다."
    lines2 = _split_long_line(text2, max_length=10, has_prefix=True)
    assert len(lines2) == 2
    assert lines2[0] == "speaker_0: 안녕하세요."
    assert lines2[1] == "반갑습니다."

    text3 = "speaker_1: 이것은 하나의 매우 길고 긴 문장입니다."
    lines3 = _split_long_line(text3, max_length=20, has_prefix=True)
    assert len(lines3) == 2
    assert lines3[0] == "speaker_1: 이것은 하나의 매우 길고 긴"
    assert lines3[1] == "문장입니다."

def test_create_srt_file_source_mode(sample_source_words, tmp_path):
    """'source' 모드 통합 테스트 (기대값 수정)."""
    output_dir = tmp_path
    data = {"words": sample_source_words, "language_code": "en"}
    
    srt_path = create_srt_file(
        data=data, mode="source", video_id="test_video", lang_code="en",
        output_dir=output_dir, max_line_length=25, pause_threshold=1.0
    )
    assert os.path.exists(srt_path)
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 수정된 로직에 따른 정확한 타임스탬프와 텍스트를 검증
        assert "1\n00:00:09,179 --> 00:00:09,999\nspeaker_1: Pleasure. Thank you.\n\n" in content
        assert "2\n00:00:11,500 --> 00:00:13,420\nspeaker_0: So, Phrase is a world\n\n" in content
        assert "3\n00:00:13,420 --> 00:00:14,800\nleader in localization.\n\n" in content
        assert "4\n00:00:15,000 --> 00:00:16,000\nspeaker_1: Yes, it is!\n\n" in content

def test_create_srt_file_translated_mode(sample_translated_segments, tmp_path):
    """'translated' 모드 통합 테스트."""
    output_dir = tmp_path
    srt_path = create_srt_file(
        data=sample_translated_segments, mode="translated", video_id="test_video",
        lang_code="Korean", output_dir=output_dir, max_line_length=25
    )
    assert os.path.exists(srt_path)
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        assert "1\n00:00:09,179 --> 00:00:09,999\nspeaker_1: 반갑습니다. 감사합니다.\n\n" in content
        assert "speaker_0: 그래서 Phrase는 로컬라이제이션의 세계적인" in content
        assert "선두주자입니다." in content
        assert "speaker_1: 네, 맞습니다!" in content



