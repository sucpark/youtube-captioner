import os
import re
import json
import logging
import argparse
from src.modules.downloader import download_youtube_audio
from src.modules.transcriber import transcribe_audio_elevenlabs, save_transcription_result
from src.modules.translator import translate_text_gpt
from src.modules.formatter import save_translated_segments

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_video_id(url):
    match = re.search(r"(?<=v=)[^&#]+", url)
    if not match:
        match = re.search(r"(?<=youtu.be/)[^&#]+", url)
    return match.group(0) if match else None

def main():
    parser = argparse.ArgumentParser(description="YouTube Caption Generator")
    parser.add_argument("--url", default="https://www.youtube.com/watch?v=FsUMdkCYluc", help="다운로드할 YouTube 비디오 URL")
    parser.add_argument("--lang", default="Korean", help="번역할 목표 언어 (기본값: Korean)")
    parser.add_argument("--output", default="output", help="결과물을 저장할 디렉터리 (기본값: output)")
    parser.add_argument("--history", type=int, default=3, help="번역 문맥으로 기억할 이전 대화 청크 수 (기본값: 3)")
    args = parser.parse_args()

    # ... (파일 경로 정의 및 폴더 생성은 이전과 동일) ...
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    video_id = get_video_id(args.url)
    if not video_id:
        logging.error("유효한 YouTube 비디오 ID를 URL에서 찾을 수 없습니다.")
        return
    audio_path = os.path.join(args.output, f"{video_id}.mp3")
    transcription_filepath = os.path.join(args.output, f"{video_id}.json")
    translation_filepath = os.path.join(args.output, f"{video_id}_{args.lang}.json")
    title = ""

    try:
        # --- 1, 2단계: 다운로드 및 음성 인식 (스킵 로직 포함) ---
        if os.path.exists(audio_path):
            logging.info(f"✔️ 오디오 파일이 이미 존재합니다. 다운로드를 건너뜁니다: {audio_path}")
            title = video_id 
        else:
            logging.info("--- 1. 오디오 다운로드 시작 ---")
            audio_path, title = download_youtube_audio(args.url, args.output)
            logging.info(f"✔️ 다운로드 완료: {audio_path}")

        if os.path.exists(transcription_filepath):
            logging.info(f"✔️ 전사 결과 파일이 이미 존재합니다. API 호출을 건너뛰고 파일을 로드합니다: {transcription_filepath}")
            with open(transcription_filepath, 'r', encoding='utf-8') as f:
                transcription_result = json.load(f)
            title = transcription_result.get('title', title)
        else:
            logging.info("\n--- 2. 음성 인식 시작 ---")
            transcription_result = transcribe_audio_elevenlabs(audio_path)
            transcription_result['title'] = title 
            logging.info("\n--- 3. 결과 파일로 저장 ---")
            save_transcription_result(transcription_result, transcription_filepath)
        
        # --- 4단계: 번역 (스킵 로직 및 history_size 인자 전달) ---
        if os.path.exists(translation_filepath):
            logging.info(f"✔️ 번역 파일이 이미 존재합니다. API 호출을 건너뜁니다: {translation_filepath}")
            with open(translation_filepath, 'r', encoding='utf-8') as f:
                translation_data = json.load(f)
            translated_segments = translation_data.get('segments', [])
        else:
            logging.info("\n--- 4. 텍스트 번역 시작 ---")
            translated_segments = translate_text_gpt(
                transcription_result, 
                target_language=args.lang, 
                history_size=args.history
            )
            logging.info("\n--- 5. 번역 결과 저장 ---")
            save_translated_segments(translated_segments, video_id, args.lang, args.output)

        print("\n[ 번역 결과 (첫 2개 청크) ]")
        for i, segment in enumerate(translated_segments[:2]):
            print(f"\n--- 청크 {i+1} ---")
            print(f"  [원본] {segment['source_text']}")
            print(f"  [번역] {segment['translated_text']}")
            
    except Exception as e:
        logging.error(f"\n[ 파이프라인 실패! ] 에러: {e}")
    finally:
        logging.info(f"--- 작업 종료 ---")

if __name__ == "__main__":
    main()
