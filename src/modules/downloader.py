import os
import yt_dlp
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_video_id(url: str) -> str:
    """
    URL에서 YouTube 비디오 ID를 추출합니다.
    """
    match = re.search(r"(?<=v=)[a-zA-Z0-9_-]{11}", url)
    if match: return match.group(0)
    match = re.search(r"(?<=youtu.be/)[a-zA-Z0-9_-]{11}", url)
    if match: return match.group(0)
    raise ValueError(f"❌ 유효한 YouTube 비디오 ID를 찾을 수 없습니다: {url}")

def fetch_video_info(youtube_url: str) -> dict:
    """
    yt-dlp를 사용하여 비디오의 메타데이터를 다운로드 없이 가져옵니다.
    """
    logging.info(f"비디오 메타데이터를 가져옵니다: {youtube_url}")
    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=False)
            return info_dict
    except Exception as e:
        raise ValueError(f"❌ 비디오 정보 추출 중 에러 발생: {e}")

def download_youtube_audio(youtube_url: str, output_path: str, video_id: str) -> str:
    """
    주어진 YouTube URL에서 오디오를 다운로드하고 mp3로 변환합니다.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, f'{video_id}.%(ext)s'),
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'quiet': True, 'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logging.info(f"오디오 다운로드를 시작합니다...")
            ydl.download([youtube_url])
            filepath = os.path.join(output_path, f"{video_id}.mp3")
            if os.path.exists(filepath):
                logging.info(f"✔️ 오디오 다운로드 및 변환 완료: {filepath}")
                return filepath
            else:
                raise ValueError("오디오 다운로드 후 파일을 찾을 수 없습니다.")
    except Exception as e:
        raise ValueError(f"❌ 오디오 다운로드 중 에러가 발생했습니다: {e}")

def download_youtube_video(youtube_url: str, output_path: str, video_id: str, quality: str = 'high') -> str:
    """
    주어진 YouTube URL에서 비디오를 다운로드합니다.
    """
    quality_formats = {
        'high': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'medium': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'low': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }
    if quality not in quality_formats:
        raise ValueError(f"❌ 유효하지 않은 화질 옵션입니다: {quality}. 'high', 'medium', 'low' 중에서 선택해주세요.")

    ydl_opts = {
        'format': quality_formats[quality],
        'outtmpl': os.path.join(output_path, f'{video_id}.mp4'),
        'quiet': True, 'no_warnings': True,
        'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logging.info(f"'{quality}' 화질 비디오 다운로드를 시작합니다...")
            ydl.download([youtube_url])
            filepath = os.path.join(output_path, f"{video_id}.mp4")
            if os.path.exists(filepath):
                logging.info(f"✔️ 비디오 다운로드 완료: {filepath}")
                return filepath
            else:
                raise ValueError("비디오 다운로드 후 파일을 찾을 수 없습니다.")
    except Exception as e:
        raise ValueError(f"❌ 비디오 다운로드 중 에러가 발생했습니다: {e}")