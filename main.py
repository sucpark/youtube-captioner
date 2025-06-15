import os
import re
import json
import logging
import argparse
from src.modules.downloader import download_youtube_audio
from src.modules.transcriber import transcribe_audio_elevenlabs, save_transcription_result
from src.modules.translator import translate_text_gpt
from src.modules.formatter import save_translated_segments
from src.modules.captioner import create_srt_file # 변경된 함수 임포트

# 로깅 기본 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_video_id(url):
    """URL에서 YouTube 비디오 ID를 추출합니다."""
    match = re.search(r"(?<=v=)[a-zA-Z0-9_-]{11}", url)
    if match: return match.group(0)
    match = re.search(r"(?<=youtu.be/)[a-zA-Z0-9_-]{11}", url)
    if match: return match.group(0)
    return None

def main():
    # 커맨드라인 인자 파서 설정
    parser = argparse.ArgumentParser(description="YouTube Caption Generator")
    parser.add_argument("--url", default="https://www.youtube.com/watch?v=FsUMdkCYluc", help="YouTube 비디오 URL")
    parser.add_argument("--lang", default="Korean", help="번역할 목표 언어")
    parser.add_argument("--srt-type", default="both", choices=["source", "translated", "both"], help="생성할 자막의 종류 (source: 원본, translated: 번역본, both: 둘 다)")
    parser.add_argument("--history", type=int, default=3, help="번역 문맥으로 기억할 이전 대화 청크 수")
    parser.add_argument("--output", default="output", help="결과물 저장 디렉터리")
    parser.add_argument("--max-line-length", type=int, default=80, help="자막 한 줄의 최대 길이 (권장: 35~42)")
    parser.add_argument("--pause-threshold", type=float, default=1.0, help="원본 자막 생성 시, 문장으로 간주할 단어 사이의 최대 쉼 간격(초)")
    args = parser.parse_args()

    if not os.path.exists(args.output): os.makedirs(args.output)
    
    video_id = get_video_id(args.url)
    if not video_id: 
        logging.error("❌ 유효한 YouTube 비디오 ID를 찾을 수 없습니다."); return
        
    # 각 단계별 파일 경로 정의
    audio_path = os.path.join(args.output, f"{video_id}.mp3")
    transcription_filepath = os.path.join(args.output, f"{video_id}.json")
    translation_filepath = os.path.join(args.output, f"{video_id}_{args.lang}.json")
    
    title = ""

    try:
        # --- 1. 오디오 다운로드 ---
        if not os.path.exists(audio_path):
            logging.info("--- 1. 오디오 다운로드 시작 ---")
            audio_path, title = download_youtube_audio(args.url, args.output)
        else: 
            logging.info(f"✔️ [1/4] 오디오 파일이 이미 존재합니다: {audio_path}")
            title = video_id
            
        # --- 2. 음성 인식 ---
        if not os.path.exists(transcription_filepath):
            logging.info("\n--- 2. 음성 인식 시작 ---")
            transcription_result = transcribe_audio_elevenlabs(audio_path)
            transcription_result['title'] = title 
            save_transcription_result(transcription_result, transcription_filepath)
        else: 
            logging.info(f"✔️ [2/4] 전사 결과 파일이 이미 존재합니다: {transcription_filepath}")
        
        # --- 3. 텍스트 번역 (translated 또는 both 일 경우에만 실행) ---
        if args.srt_type in ["translated", "both"]:
            if not os.path.exists(translation_filepath):
                logging.info("\n--- 3. 텍스트 번역 시작 ---")
                with open(transcription_filepath, 'r', encoding='utf-8') as f:
                    transcription_result = json.load(f)
                translated_segments = translate_text_gpt(transcription_result, args.lang, args.history)
                save_translated_segments(translated_segments, video_id, args.lang, translation_filepath)
            else: 
                logging.info(f"✔️ [3/4] 번역 파일이 이미 존재합니다: {translation_filepath}")
        else:
             logging.info("\n--- 3. 텍스트 번역 건너뜀 ---")

        # --- 4. SRT 자막 파일 생성 ---
        logging.info("\n--- 4. SRT 자막 파일 생성 시작 ---")
        
        # 원본 자막 생성
        if args.srt_type in ["source", "both"]:
            with open(transcription_filepath, 'r', encoding='utf-8') as f:
                transcription_result = json.load(f)
            create_srt_file(
                data=transcription_result,
                mode="source",
                video_id=video_id,
                lang_code=transcription_result.get('language_code', 'en'),
                output_dir=args.output,
                max_line_length=args.max_line_length,
                pause_threshold=args.pause_threshold
            )

        # 번역 자막 생성
        if args.srt_type in ["translated", "both"]:
            with open(translation_filepath, 'r', encoding='utf-8') as f:
                translation_data = json.load(f)
            create_srt_file(
                data=translation_data['segments'],
                mode="translated",
                video_id=video_id,
                lang_code=args.lang,
                output_dir=args.output,
                max_line_length=args.max_line_length
            )

    except Exception as e:
        logging.error(f"\n[ 파이프라인 실패! ] 에러: {e}", exc_info=True)
    finally:
        logging.info(f"\n--- 작업 종료 ---")

if __name__ == "__main__":
    main()

