# main.py

import os
from src.modules.downloader import download_youtube_audio

def main():
    # 테스트할 유튜브 URL (저작권 문제 없는 짧은 영상 추천)
    test_url = "https://www.youtube.com/watch?v=LXb3EKWsInQ"  # 예시: Google I/O 영상
    output_directory = "output"

    # 출력 폴더가 없으면 생성
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    print(f"--- 실제 환경 다운로드 테스트 시작 ---")
    print(f"URL: {test_url}")

    try:
        # 우리가 만든 다운로더 함수 호출
        file_path, title = download_youtube_audio(test_url, output_directory)
        print(f"\n[ 성공! ]")
        print(f"-> 파일 경로: {file_path}")
        print(f"-> 비디오 제목: {title}")
        print(f"'{output_directory}' 폴더를 확인하여 파일이 제대로 생성되었는지 보세요.")
    except Exception as e:
        print(f"\n[ 실패! ]")
        print(f"-> 에러: {e}")
    
    print(f"--- 테스트 종료 ---")

if __name__ == "__main__":
    main()