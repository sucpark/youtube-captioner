import os
import json
from src.modules.formatter import save_translated_segments

FAKE_TRANSLATED_SEGMENTS = [
    {"start": 0.0, "end": 1.2, "translated_text": "speaker_1: 안녕 세상.", "source_text": "speaker_1: Hello world."},
    {"start": 1.5, "end": 2.5, "translated_text": "speaker_2: 어떻게 지내?", "source_text": "speaker_2: How are you?"}
]

def test_save_translated_segments(tmp_path):
    """번역된 세그먼트가 JSON 파일로 올바르게 저장되는지 테스트합니다."""
    video_id = "test_video"
    lang = "Korean"
    
    # 함수 실행
    filepath = save_translated_segments(FAKE_TRANSLATED_SEGMENTS, video_id, lang, str(tmp_path))

    # 파일이 생성되었고, 이름이 올바른지 확인
    assert os.path.exists(filepath)
    assert os.path.basename(filepath) == "test_video_Korean.json"

    # 파일 내용이 올바른지 확인
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data["video_id"] == video_id
    assert data["target_language"] == lang
    assert data["segments"] == FAKE_TRANSLATED_SEGMENTS