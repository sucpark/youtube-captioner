import os
import logging
import json
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ElevenLabs 클라이언트 초기화
try:
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY가 .env 파일에 설정되지 않았습니다.")
    elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
except Exception as e:
    logging.error(f"ElevenLabs 클라이언트 초기화 실패: {e}")
    elevenlabs_client = None

def transcribe_audio_elevenlabs(audio_path: str) -> dict:
    """
    주어진 오디오 파일을 ElevenLabs STT API를 사용하여 텍스트로 변환합니다.
    화자 분리 및 단어 단위 타임스탬프를 포함합니다.

    :param audio_path: 변환할 오디오 파일의 경로
    :return: ElevenLabs API가 반환한 전사 결과 (딕셔너리)
    :raises ValueError: 클라이언트 초기화 실패 또는 API 에러 발생 시
    :raises FileNotFoundError: 오디오 파일이 없을 때 발생
    """
    if not elevenlabs_client:
        raise ValueError("ElevenLabs 클라이언트가 올바르게 초기화되지 않았습니다.")

    logging.info(f"오디오 파일 '{audio_path}'의 전사를 시작합니다...")
    
    try:
        with open(audio_path, "rb") as audio_file:
            # speech_to_text.convert는 Pydantic 모델을 반환하므로, .model_dump()로 딕셔너리 변환
            transcription = elevenlabs_client.speech_to_text.convert(
                file=audio_file,
                model_id="scribe_v1", # Model to use, for now only "scribe_v1" is supported
                tag_audio_events=True, # Tag audio events like laughter, applause, etc.
                diarize=True, # 화자 분리 기능 활성화
            )
            logging.info("✔️ 오디오 전사 완료.")
            return transcription.model_dump()

    except FileNotFoundError:
        logging.error(f"오디오 파일을 찾을 수 없습니다: {audio_path}")
        raise
    except Exception as e:
        logging.error(f"ElevenLabs API 호출 중 에러 발생: {e}")
        raise ValueError(f"API 호출 실패: {e}")

def save_transcription_result(result: dict, output_filepath: str):
    """
    전사 결과(딕셔너리)를 JSON 파일로 저장합니다.

    :param result: 저장할 전사 결과 딕셔너리
    :param output_filepath: 저장될 JSON 파일의 경로
    """
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        logging.info(f"✔️ 전사 결과를 성공적으로 저장했습니다: {output_filepath}")
    except Exception as e:
        logging.error(f"전사 결과 저장 중 에러 발생: {e}")
        raise