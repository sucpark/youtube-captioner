# main.py

import os
import logging
import argparse # argparse 추가
from src.modules.downloader import download_youtube_audio

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description="YouTube 오디오 다운로더")
    parser.add_argument("url", help="다운로드할 YouTube 비디오 URL")
    parser.add_argument("-o", "--output", default="output", help="오디오 파일을 저장할 디렉터리 (기본값: output)")
    args = parser.parse_args()

    youtube_url = args.url
    output_directory = args.output

    # 출력 폴더가 없으면 생성
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        logging.info(f"출력 폴더 생성: {output_directory}")

    logging.info(f"--- 다운로드 시작 ---")
    logging.info(f"URL: {youtube_url}")

    try:
        # 우리가 만든 다운로더 함수 호출
        file_path, title = download_youtube_audio(youtube_url, output_directory)
        logging.info(f"\n[ 성공! ]")
        logging.info(f"-> 파일 경로: {file_path}")
        logging.info(f"-> 비디오 제목: {title}")
        logging.info(f"'{output_directory}' 폴더를 확인하여 파일이 제대로 생성되었는지 보세요.")
    except Exception as e:
        logging.error(f"\n[ 실패! ]")
        logging.error(f"-> 에러: {e}")
    
    logging.info(f"--- 작업 종료 ---")

if __name__ == "__main__":
    main()