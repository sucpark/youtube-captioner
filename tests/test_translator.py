import pytest
from unittest.mock import patch, MagicMock

from src.modules.translator import translate_text_gpt, _create_translation_chunks

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
    chunks = _create_translation_chunks(FAKE_TRANSCRIPTION, max_chunk_words=10)
    assert len(chunks) == 2
    assert chunks[0]['source_text'] == "speaker_1: Hello world."
    assert chunks[1]['source_text'] == "speaker_2: How are you?"

@patch('src.modules.translator.openai_client')
def test_translate_text_gpt_with_history(mock_openai_client):
    """GPT 번역 시 대화 기록이 올바르게 전달되는지 테스트합니다."""
    # API가 호출될 때마다 다른 응답을 하도록 설정
    mock_openai_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=MagicMock(content="speaker_1: 안녕 세상."))]),
        MagicMock(choices=[MagicMock(message=MagicMock(content="speaker_2: 어떻게 지내?"))])
    ]

    # 함수 실행
    translated_data = translate_text_gpt(FAKE_TRANSCRIPTION, "Korean", history_size=1)

    # 결과 검증
    assert len(translated_data) == 2
    assert "안녕 세상" in translated_data[0]['translated_text']
    assert "어떻게 지내" in translated_data[1]['translated_text']

    # API 호출 기록 확인
    call_args_list = mock_openai_client.chat.completions.create.call_args_list
    assert len(call_args_list) == 2  # 청크가 2개이므로 API 호출도 2번

    # 첫 번째 호출의 메시지 확인 (기록 없음)
    first_call_messages = call_args_list[0].kwargs['messages']
    assert len(first_call_messages) == 2 # system, user
    assert first_call_messages[1]['role'] == 'user'
    assert first_call_messages[1]['content'] == 'speaker_1: Hello world.'

    # 두 번째 호출의 메시지 확인 (기록 1개 포함)
    second_call_messages = call_args_list[1].kwargs['messages']
    assert len(second_call_messages) == 4 # system, user, assistant, user
    assert second_call_messages[1]['role'] == 'user'
    assert second_call_messages[1]['content'] == 'speaker_1: Hello world.'
    assert second_call_messages[2]['role'] == 'assistant'
    assert second_call_messages[2]['content'] == 'speaker_1: 안녕 세상.'
    assert second_call_messages[3]['role'] == 'user'
    assert second_call_messages[3]['content'] == 'speaker_2: How are you?'
