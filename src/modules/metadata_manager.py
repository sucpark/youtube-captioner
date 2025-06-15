import os
import json
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

METADATA_FILE = "metadata.json"

def load_metadata(output_dir: str) -> dict:
    """지정된 경로에서 metadata.json 파일을 로드합니다."""
    filepath = os.path.join(output_dir, METADATA_FILE)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_metadata(output_dir: str, data: dict):
    """메타데이터 딕셔너리를 metadata.json 파일에 저장합니다."""
    filepath = os.path.join(output_dir, METADATA_FILE)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"✔️ 메타데이터를 성공적으로 저장했습니다: {filepath}")
    except Exception as e:
        logging.error(f"❌ 메타데이터 저장 실패: {e}")

def create_info_file(video_id: str, video_entry: dict, video_output_dir: str):
    """
    [신규 기능] 사람이 읽기 쉬운 정보 파일(_info.txt)을 생성합니다.
    이 파일은 프로그램 로직에 영향을 주지 않으며, 오직 사용자 편의를 위함입니다.
    """
    info_filepath = os.path.join(video_output_dir, "_info.txt")
    try:
        title = video_entry.get('title', 'N/A')
        url = video_entry.get('url', 'N/A')
        channel = video_entry.get('channel', 'N/A')
        duration = video_entry.get('duration_string', 'N/A')

        content = (
            f"[Video Information]\n\n"
            f"ID:    {video_id}\n"
            f"Title: {title}\n"
            f"URL:   {url}\n"
            f"Channel: {channel}\n"
            f"Duration: {duration}\n"
        )
        with open(info_filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"✔️ 정보 파일 생성/업데이트 완료: {info_filepath}")
    except Exception as e:
        logging.warning(f"정보 파일(_info.txt) 생성 중 오류 발생: {e}")


def file_exists_in_metadata(video_entry: dict, file_key: str, output_dir: str) -> bool:
    """메타데이터에 파일 정보가 있고, 실제 파일도 존재하는지 확인합니다."""
    if file_key in video_entry.get('files', {}):
        filename = video_entry['files'][file_key]
        if not filename: return False
        
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            return True
        else:
            logging.warning(f"메타데이터에는 '{file_key}' 파일({filename})이 기록되어 있지만, 실제 파일이 없습니다. 재생성합니다.")
    return False

def update_video_entry(metadata: dict, video_id: str, info_dict: dict):
    """yt-dlp에서 가져온 정보로 메타데이터 엔트리를 생성하거나 업데이트합니다."""
    if video_id not in metadata:
        metadata[video_id] = {'files': {}}
    metadata[video_id].update({
        "title": info_dict.get('title', 'Unknown Title'),
        "url": info_dict.get('webpage_url', ''),
        "channel": info_dict.get('channel', 'Unknown Channel'),
        "upload_date": info_dict.get('upload_date', None),
        "duration_string": info_dict.get('duration_string', '0'),
        "last_fetched": datetime.now(timezone.utc).isoformat()
    })

def add_file_to_entry(metadata: dict, video_id: str, file_key: str, filepath: str):
    """특정 비디오 엔트리에 생성된 파일 정보를 추가합니다."""
    if video_id in metadata:
        metadata[video_id]['files'][file_key] = os.path.basename(filepath)
        metadata[video_id]["last_updated"] = datetime.now(timezone.utc).isoformat()

def ensure_source_language(metadata: dict, video_id: str, transcription_filepath: str):
    """메타데이터에 원본 언어 코드가 없으면, 전사 파일에서 읽어와 추가합니다."""
    video_entry = metadata.get(video_id)
    if not video_entry or 'source_language_code' in video_entry:
        return
    try:
        with open(transcription_filepath, 'r', encoding='utf-8') as f:
            transcription_data = json.load(f)
        lang_code = transcription_data.get('language_code')
        if lang_code:
            video_entry['source_language_code'] = lang_code
            logging.info(f"메타데이터 업데이트: '{video_id}'에 원본 언어 코드 '{lang_code}' 추가.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.warning(f"원본 언어 코드를 확인하기 위해 전사 파일을 읽는 중 오류 발생: {e}")
