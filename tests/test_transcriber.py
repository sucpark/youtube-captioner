# poetry run pytest

import pytest
from unittest.mock import patch, MagicMock
import json

# 테스트 대상 함수 임포트
from src.modules.transcriber import transcribe_audio_elevenlabs, save_transcription_result

# ElevenLabs API의 가짜 응답 데이터
FAKE_API_RESPONSE = {
    "language_code": "en",
    "text": "Hello world!",
    "words": [
        {"text": "Hello", "start": 0.0, "end": 0.5, "speaker_id": "speaker_1"},
        {"text": "world!", "start": 0.6, "end": 1.2, "speaker_id": "speaker_1"}
    ]
}

# Pydantic 모델을 흉내 내기 위한 간단한 Mock 클래스
class MockTranscriptionResponse:
    def model_dump(self):
        return FAKE_API_RESPONSE

@patch('src.modules.transcriber.elevenlabs_client')
def test_transcribe_audio_success(mock_client):
    """ElevenLabs 오디오 전사 성공 케이스를 테스트합니다."""
    # 클라이언트의 speech_to_text.convert 메소드가 가짜 응답을 반환하도록 설정
    mock_client.speech_to_text.convert.return_value = MockTranscriptionResponse()

    # 가짜 오디오 파일 경로
    fake_audio_path = "fake/audio.mp3"

    # with open(...) 구문을 모킹하여 실제 파일 IO를 방지
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        result = transcribe_audio_elevenlabs(fake_audio_path)

        # 결과가 올바른지 검증
        assert result == FAKE_API_RESPONSE
        
        # open 함수가 올바른 경로와 모드로 호출되었는지 확인
        mock_open.assert_called_with(fake_audio_path, "rb")
        
        # ElevenLabs API가 올바른 인자(diarize=True)로 호출되었는지 확인
        mock_client.speech_to_text.convert.assert_called_once()
        _, kwargs = mock_client.speech_to_text.convert.call_args
        assert kwargs.get('diarize') is True

def test_save_transcription_result(tmp_path):
    """결과 딕셔너리가 JSON 파일로 올바르게 저장되는지 테스트합니다."""
    output_file = tmp_path / "result.json"
    
    save_transcription_result(FAKE_API_RESPONSE, str(output_file))

    assert output_file.exists()
    with open(output_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    assert saved_data == FAKE_API_RESPONSE