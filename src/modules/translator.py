import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# OpenAI 클라이언트 초기화
try:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    logging.error(f"OpenAI 클라이언트 초기화 실패: {e}")
    openai_client = None

def _create_translation_chunks(transcription_result: dict, max_chunk_words: int = 50) -> list[dict]:
    """전사 결과를 번역하기 좋은 '청크' 단위로 묶습니다. 화자가 바뀌면 새로운 청크를 시작합니다."""
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

def translate_text_gpt(transcription_result: dict, target_language: str, history_size: int = 3) -> list[dict]:
    """
    전사된 텍스트 청크를 GPT-4o-mini를 사용하여 번역합니다.
    이전 대화 내용을 포함하여 문맥을 유지합니다.

    :param transcription_result: ElevenLabs API의 전사 결과 딕셔너리
    :param target_language: 번역할 목표 언어 (예: "Korean", "Japanese")
    :param history_size: 문맥으로 기억할 이전 대화 청크의 수
    :return: 번역된 세그먼트 리스트.
    """
    if not openai_client:
        raise ValueError("OpenAI 클라이언트가 올바르게 초기화되지 않았습니다.")
    
    chunks = _create_translation_chunks(transcription_result)
    translated_segments = []
    conversation_history = [] # 대화 기록을 저장할 리스트
    
    logging.info(f"총 {len(chunks)}개의 청크를 '{target_language}'(으)로 번역합니다... (History Size: {history_size})")

    for i, chunk in enumerate(chunks):
        try:
            logging.info(f"청크 {i+1}/{len(chunks)} 번역 중...")
            
            system_prompt = f"You are a professional translator. Translate the following dialogue into natural {target_language}. Maintain the speaker labels (e.g., speaker_1:) and translate only the content."
            
            # API에 보낼 메시지 목록 구성 (시스템 프롬프트 + 대화 기록 + 현재 청크)
            messages_to_send = [{"role": "system", "content": system_prompt}]
            messages_to_send.extend(conversation_history)
            messages_to_send.append({"role": "user", "content": chunk["source_text"]})

            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_to_send,
                temperature=0.3,
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # 번역된 결과를 리스트에 추가
            translated_segments.append({
                "start": chunk["start_time"],
                "end": chunk["end_time"],
                "translated_text": translated_text,
                "source_text": chunk["source_text"]
            })
            
            # 대화 기록에 현재 '원본(user)'과 '번역본(assistant)'을 추가
            conversation_history.append({"role": "user", "content": chunk["source_text"]})
            conversation_history.append({"role": "assistant", "content": translated_text})

            # 대화 기록의 크기를 제한 (오래된 기록부터 제거)
            if len(conversation_history) > history_size * 2:
                conversation_history = conversation_history[-history_size * 2:]

        except Exception as e:
            logging.error(f"청크 번역 중 에러 발생: {e}")
            translated_segments.append({
                "start": chunk["start_time"],
                "end": chunk["end_time"],
                "translated_text": f"[번역 실패] {chunk['source_text']}",
                "source_text": chunk["source_text"]
            })
            
    logging.info("✔️ 번역 작업 완료.")
    return translated_segments
