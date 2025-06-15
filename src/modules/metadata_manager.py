import os
import json
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

METADATA_FILE = "metadata.json"

def load_metadata(output_dir: str) -> dict:
    """
    지정된 경로에서 metadata.json 파일을 로드합니다.
    파일이 없거나 손상된 경우, 빈 딕셔너리를 반환합니다.
    """
    filepath = os.path.join(output_dir, METADATA_FILE)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.info(f"메타데이터 파일('{filepath}')을 찾을 수 없거나 손상되었습니다. 새 파일을 생성합니다.")
        return {}

def save_metadata(output_dir: str, data: dict):
    """
    메타데이터 딕셔너리를 metadata.json 파일에 저장합니다.
    """
    filepath = os.path.join(output_dir, METADATA_FILE)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"✔️ 메타데이터를 성공적으로 저장했습니다: {filepath}")
    except Exception as e:
        logging.error(f"❌ 메타데이터 저장 실패: {e}")

def update_video_entry(metadata: dict, video_id: str, info_dict: dict):
    """
    yt-dlp에서 가져온 정보로 메타데이터 엔트리를 생성하거나 업데이트합니다.
    정보가 누락된 경우를 안전하게 처리합니다.
    """
    if video_id not in metadata:
        metadata[video_id] = {'files': {}}

    # .get()을 사용하여 키가 없더라도 오류 없이 안전하게 값을 가져옴
    metadata[video_id].update({
        "title": info_dict.get('title', 'Unknown Title'),
        "url": info_dict.get('webpage_url', ''),
        "channel": info_dict.get('channel', 'Unknown Channel'),
        "upload_date": info_dict.get('upload_date', None),
        "duration_string": info_dict.get('duration_string', '0'),
        "last_fetched": datetime.now(timezone.utc).isoformat()
    })

def add_file_to_entry(metadata: dict, video_id: str, file_key: str, filepath: str):
    """
    특정 비디오 엔트리에 생성된 파일 정보를 추가합니다.
    """
    if video_id in metadata:
        # 전체 경로가 아닌 파일 이름만 저장
        metadata[video_id]['files'][file_key] = os.path.basename(filepath)
        metadata[video_id]["last_updated"] = datetime.now(timezone.utc).isoformat()
        logging.info(f"메타데이터 업데이트: '{video_id}'에 '{file_key}' 파일 정보 추가.")