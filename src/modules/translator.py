import os
import logging
import json
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
        """Helper function to finalize and append the current chunk."""
        nonlocal current_chunk_words, current_chunk_text, current_speaker
        if current_chunk_words:
            chunks.append({
                "source_text": current_chunk_text.strip(),
                "start_time": current_chunk_words[0]['start'],
                "end_time": current_chunk_words[-1]['end'],
                "words": current_chunk_words,
            })
            current_chunk_words = []
            current_chunk_text = ""
            current_speaker = None

    for word_data in transcription_result['words']:
        if word_data.get('type') == 'spacing':
            continue

        speaker = word_data.get('speaker_id', 'unknown')

        # 조건 확인: 1) 화자가 바뀌었거나, 2) 청크가 최대 단어 수에 도달했을 때
        if (speaker != current_speaker and current_speaker is not None) or \
           (len(current_chunk_words) >= max_chunk_words):
            finalize_chunk()

        current_chunk_words.append(word_data)
        
        # 새 청크의 시작
        if current_speaker is None:
            current_speaker = speaker
            current_chunk_text += f"{speaker}: "
        
        current_chunk_text += word_data.get('text', '') + " "
    
    # 루프가 끝난 후 마지막으로 남은 청크 추가
    finalize_chunk()
            
    return chunks

def translate_text_gpt(transcription_result: dict, target_language: str) -> list[dict]:
    """
    전사된 텍스트 청크를 GPT-4o-mini를 사용하여 번역합니다.

    :param transcription_result: ElevenLabs API의 전사 결과 딕셔너리
    :param target_language: 번역할 목표 언어 (예: "Korean", "Japanese")
    :return: 번역된 세그먼트 리스트. 각 요소는 딕셔너리 형태.
             (예: [{'start': 0.0, 'end': 5.2, 'text': '번역된 텍스트'}])
    """
    if not openai_client:
        raise ValueError("OpenAI 클라이언트가 올바르게 초기화되지 않았습니다.")
    
    chunks = _create_translation_chunks(transcription_result)
    translated_segments = []
    
    logging.info(f"총 {len(chunks)}개의 청크를 '{target_language}'(으)로 번역합니다...")

    for i, chunk in enumerate(chunks):
        try:
            logging.info(f"청크 {i+1}/{len(chunks)} 번역 중...")
            
            system_prompt = f"You are a professional translator. Translate the following dialogue into natural {target_language}. Maintain the speaker labels (e.g., speaker_1:) and translate only the content."
            
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk["source_text"]}
                ],
                temperature=0.3,
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            translated_segments.append({
                "start": chunk["start_time"],
                "end": chunk["end_time"],
                "translated_text": translated_text,
                "source_text": chunk["source_text"]
            })

        except Exception as e:
            logging.error(f"청크 번역 중 에러 발생: {e}")
            # 에러가 발생해도 일단 원본 텍스트를 포함하여 다음으로 넘어감
            translated_segments.append({
                "start": chunk["start_time"],
                "end": chunk["end_time"],
                "translated_text": f"[번역 실패] {chunk['source_text']}",
                "source_text": chunk["source_text"]
            })
            
    logging.info("✔️ 번역 작업 완료.")
    return translated_segments
