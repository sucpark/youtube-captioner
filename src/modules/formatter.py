import json
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_translated_segments(
    translated_segments: list[dict], video_id: str, 
    target_lang_code: str, output_filepath: str) -> str:
    """
    번역된 세그먼트 리스트를 중간 결과물인 JSON 파일로 저장합니다.
    파일 이름에 언어 코드를 사용합니다.

    Args:
        translated_segments (list[dict]): 번역된 세그먼트 데이터.
        video_id (str): 유튜브 비디오 ID.
        target_lang_code (str): 번역된 언어의 ISO 639-1 코드 (예: 'ko').
        output_filepath (str): 저장할 파일의 전체 경로.

    Returns:
        str: 저장된 파일의 전체 경로.
    """
    try:
        output_data = {
            "video_id": video_id,
            "target_language": target_lang_code,
            "segments": translated_segments
        }
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        logging.info(f"✔️ 번역 결과를 성공적으로 저장했습니다: {output_filepath}")
        return output_filepath
    except Exception as e:
        raise e