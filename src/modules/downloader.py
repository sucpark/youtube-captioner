import os
import yt_dlp
import re
import logging

# 로깅 설정 (print 대신 사용)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_youtube_audio(youtube_url: str, output_path: str) -> tuple[str, str]:
    """
    주어진 YouTube URL에서 오디오를 다운로드하고, 파일 경로와 제목을 반환합니다.

    :param youtube_url: 다운로드할 YouTube 비디오의 URL
    :param output_path: 오디오 파일을 저장할 디렉터리 경로
    :return: (저장된 파일의 전체 경로, 비디오 제목) 튜플
    :raises ValueError: 유효하지 않은 URL이거나 다운로드 실패 시 발생
    """
    # 1. 더 견고한 URL 유효성 검사
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    
    if not re.match(youtube_regex, youtube_url):
        raise ValueError(f"❌ 유효하지 않은 YouTube URL입니다: {youtube_url}")

    # 2. 오디오만 다운로드하도록 옵션 최적화
    ydl_opts = {
        'format': 'bestaudio/best',  # 최고 품질의 오디오만 선택
        'outtmpl': os.path.join(output_path, '%(id)s.%(ext)s'), # 파일명으로 영상 ID 사용 (특수문자 문제 방지)
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',  # mp3 형식으로 오디오 추출
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 3. 더 안정적인 정보 추출 및 다운로드
            logging.info(f"'{youtube_url}' 다운로드를 시작합니다...")
            info_dict = ydl.extract_info(youtube_url, download=True)
            
            video_id = info_dict.get('id', None)
            video_title = info_dict.get('title', 'untitled')
            
            # 4. 후처리 후 최종 파일 경로 확인
            # yt-dlp가 mp3로 변환 후 원래 파일을 삭제하므로, 최종 파일명은 id.mp3가 됨
            downloaded_filepath = os.path.join(output_path, f"{video_id}.mp3")

            if os.path.exists(downloaded_filepath):
                logging.info(f"✔️ 다운로드 및 변환 완료: {downloaded_filepath}")
                return downloaded_filepath, video_title
            else:
                # 이 경우는 거의 발생하지 않으나, 예외 처리를 위해 추가
                raise ValueError("다운로드 후 파일을 찾을 수 없습니다.")

    # 5. 구체적인 예외 처리
    except yt_dlp.utils.DownloadError as e:
        logging.error(f"yt-dlp 다운로드 에러: {e}")
        raise ValueError(f"❌ 비디오 다운로드 중 에러가 발생했습니다: {youtube_url}")
    except Exception as e:
        logging.error(f"예상치 못한 에러: {e}")
        raise ValueError(f"❌ 알 수 없는 에러가 발생했습니다: {youtube_url}")