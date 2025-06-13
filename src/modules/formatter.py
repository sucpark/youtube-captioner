import json
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def save_translated_segments(
    translated_segments: list[dict], 
    video_id: str, 
    target_language: str, 
    output_dir: str
) -> str:
    """
    번역된 세그먼트 리스트를 타임스탬프 정보와 함께 JSON 파일로 저장합니다.

    :param translated_segments: 번역된 세그먼트 딕셔너리의 리스트
    :param video_id: YouTube 비디오 ID
    :param target_language: 번역된 언어 코드 (예: "Korean")
    :param output_dir: 저장할 디렉터리
    :return: 저장된 파일의 경로
    """
    # 파일명 형식: [video_id]_[language].json (예: FsUMdkCYluc_Korean.json)
    filename = f"{video_id}_{target_language}.json"
    filepath = os.path.join(output_dir, filename)

    try:
        # 저장할 데이터 구조화 (필요시 추가 정보 포함 가능)
        output_data = {
            "video_id": video_id,
            "target_language": target_language,
            "segments": translated_segments
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        
        logging.info(f"✔️ 번역 결과를 성공적으로 저장했습니다: {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"번역 결과 저장 중 에러 발생: {e}")
        raise