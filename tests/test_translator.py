import pytest
from unittest.mock import patch, MagicMock

# 테스트 대상 함수 임포트
from src.modules.translator import translate_text_gpt, _create_translation_chunks

# ElevenLabs의 가짜 전사 결과
FAKE_TRANSCRIPTION = {
    "words": [
        {'text': 'Hello', 'start': 0.0, 'end': 0.5, 'speaker_id': 'speaker_1'},
        {'text': 'world.', 'start': 0.6, 'end': 1.2, 'speaker_id': 'speaker_1'},
        {'text': 'How', 'start': 1.5, 'end': 1.8, 'speaker_id': 'speaker_2'},
        {'text': 'are', 'start': 1.8, 'end': 2.0, 'speaker_id': 'speaker_2'},
        {'text': 'you?', 'start': 2.0, 'end': 2.5, 'speaker_id': 'speaker_2'}
    ]
}

def test_create_translation_chunks():
    """텍스트가 화자 변경 시 올바르게 묶이는지 테스트합니다."""
    # max_chunk_words를 크게 설정하여 화자 변경 로직만 테스트
    chunks = _create_translation_chunks(FAKE_TRANSCRIPTION, max_chunk_words=10)
    
    assert len(chunks) == 2
    # 첫 번째 청크는 speaker_1의 말만 포함해야 함
    assert chunks[0]['source_text'] == "speaker_1: Hello world."
    assert chunks[0]['start_time'] == 0.0
    assert chunks[0]['end_time'] == 1.2
    # 두 번째 청크는 speaker_2의 말만 포함해야 함
    assert chunks[1]['source_text'] == "speaker_2: How are you?"
    assert chunks[1]['start_time'] == 1.5
    assert chunks[1]['end_time'] == 2.5

@patch('src.modules.translator.openai_client')
def test_translate_text_gpt_success(mock_openai_client):
    """GPT 번역 성공 케이스를 테스트합니다."""
    # OpenAI API의 가짜 응답 설정
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "speaker_1: 안녕 세상."
    mock_openai_client.chat.completions.create.return_value = mock_response

    # 함수 실행
    translated_data = translate_text_gpt(FAKE_TRANSCRIPTION, "Korean")

    # 결과 검증
    assert len(translated_data) > 0 # 청크가 여러 개일 수 있으므로
    assert "안녕 세상" in translated_data[0]['translated_text']
    
    # OpenAI API가 올바른 프롬프트로 호출되었는지 확인
    assert mock_openai_client.chat.completions.create.called
    call_args = mock_openai_client.chat.completions.create.call_args_list[0]
    messages = call_args.kwargs['messages']
    assert "Translate the following dialogue into natural Korean" in messages[0]['content']
