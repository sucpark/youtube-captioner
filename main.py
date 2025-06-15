import os
import json
import logging
import argparse
from src import config
from src.modules import metadata_manager
from src.modules.downloader import get_video_id, fetch_video_info, download_youtube_audio, download_youtube_video
from src.modules.transcriber import transcribe_audio_elevenlabs, save_transcription_result
from src.modules.translator import translate_text_gpt
from src.modules.formatter import save_translated_segments
from src.modules.captioner import create_srt_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description="YouTube Caption Generator")
    parser.add_argument("--url", default="https://www.youtube.com/watch?v=FsUMdkCYluc", help="YouTube 비디오 URL")
    parser.add_argument("--lang", default="ko", choices=config.get_supported_codes(), help="번역할 목표 언어의 ISO 639-1 코드")
    parser.add_argument("--download-video", action='store_true', help="오디오와 함께 비디오도 다운로드합니다.")
    parser.add_argument("--quality", default='high', choices=['high', 'medium', 'low'], help="비디오 다운로드 시 화질")
    parser.add_argument("--srt-type", default="both", choices=["source", "translated", "both"], help="생성할 자막의 종류")
    parser.add_argument("--history", type=int, default=3, help="번역 문맥으로 기억할 이전 대화 청크 수")
    parser.add_argument("--output", default="output", help="결과물 저장 디렉터리")
    parser.add_argument("--max-line-length", type=int, default=80, help="자막 한 줄의 최대 길이")
    parser.add_argument("--pause-threshold", type=float, default=1.0, help="원본 자막 생성 시, 문장으로 간주할 쉼 간격(초)")
    args = parser.parse_args()


    if not os.path.exists(args.output): os.makedirs(args.output)
    metadata = metadata_manager.load_metadata(args.output)

    try:
        video_id = get_video_id(args.url)
        
        # [개선] 각 비디오 ID에 대한 하위 폴더 경로 생성
        video_output_dir = os.path.join(args.output, video_id)
        if not os.path.exists(video_output_dir):
            os.makedirs(video_output_dir)
            logging.info(f"'{video_output_dir}' 폴더를 생성했습니다.")

        if video_id not in metadata:
            info_dict = fetch_video_info(args.url)
            metadata_manager.update_video_entry(metadata, video_id, info_dict)
        
        video_entry = metadata[video_id]
        logging.info(f"--- 작업 시작: {video_entry.get('title', video_id)} ---")

        # [개선] 모든 파일 경로와 존재 유무 확인 시, video_output_dir 사용
        
        if args.download_video:
            if not metadata_manager.file_exists_in_metadata(video_entry, 'video', video_output_dir):
                logging.info("\n--- 비디오 다운로드 시작 ---")
                video_path = download_youtube_video(args.url, video_output_dir, video_id, args.quality)
                metadata_manager.add_file_to_entry(metadata, video_id, 'video', video_path)
            else: logging.info(f"✔️ 비디오 파일이 이미 존재합니다: {video_entry['files']['video']}")

        if not metadata_manager.file_exists_in_metadata(video_entry, 'audio', video_output_dir):
            logging.info("\n--- 오디오 다운로드 시작 ---")
            audio_path = download_youtube_audio(args.url, video_output_dir, video_id)
            metadata_manager.add_file_to_entry(metadata, video_id, 'audio', audio_path)
        else: logging.info(f"✔️ 오디오 파일이 이미 존재합니다: {video_entry['files']['audio']}")
        audio_path = os.path.join(video_output_dir, video_entry['files']['audio'])

        if not metadata_manager.file_exists_in_metadata(video_entry, 'transcription', video_output_dir):
            logging.info("\n--- 음성 인식 시작 ---")
            transcription_result = transcribe_audio_elevenlabs(audio_path)
            transcription_filename = f"{video_id}_transcription.json"
            transcription_filepath = os.path.join(video_output_dir, transcription_filename)
            save_transcription_result(transcription_result, transcription_filepath)
            metadata_manager.add_file_to_entry(metadata, video_id, 'transcription', transcription_filepath)
        else: logging.info(f"✔️ 전사 결과 파일이 이미 존재합니다.")
        transcription_filepath = os.path.join(video_output_dir, video_entry['files']['transcription'])
        metadata_manager.ensure_source_language(metadata, video_id, transcription_filepath)

        target_lang_code = args.lang
        translation_key = f'translation_{target_lang_code}'
        if args.srt_type in ["translated", "both"] and not metadata_manager.file_exists_in_metadata(video_entry, translation_key, video_output_dir):
            target_lang_name = config.get_language_name(target_lang_code)
            logging.info(f"\n--- 텍스트 번역 시작 ({target_lang_name}) ---")
            with open(transcription_filepath, 'r', encoding='utf-8') as f:
                transcription_result = json.load(f)
            translated_segments = translate_text_gpt(transcription_result, target_lang_name, args.history)
            translation_filename = f"{video_id}_{target_lang_code}_translation.json"
            translation_filepath = os.path.join(video_output_dir, translation_filename)
            save_translated_segments(translated_segments, video_id, target_lang_code, translation_filepath)
            metadata_manager.add_file_to_entry(metadata, video_id, translation_key, translation_filepath)
        elif metadata_manager.file_exists_in_metadata(video_entry, translation_key, video_output_dir): logging.info(f"✔️ 번역 파일이 이미 존재합니다.")
        else: logging.info("\n--- 텍스트 번역 건너뜀 ---")

        logging.info("\n--- SRT 자막 파일 생성 시작 ---")
        source_lang_code = video_entry.get('source_language_code', 'en')
        srt_source_key = f'srt_source_{source_lang_code}'
        if args.srt_type in ["source", "both"] and not metadata_manager.file_exists_in_metadata(video_entry, srt_source_key, video_output_dir):
            with open(transcription_filepath, 'r', encoding='utf-8') as f:
                transcription_result = json.load(f)
            srt_path = create_srt_file(data=transcription_result, mode="source", video_id=video_id, lang_code=source_lang_code,
                                       output_dir=video_output_dir, max_line_length=args.max_line_length, pause_threshold=args.pause_threshold)
            metadata_manager.add_file_to_entry(metadata, video_id, srt_source_key, srt_path)
        
        srt_translated_key = f'srt_translated_{target_lang_code}'
        if args.srt_type in ["translated", "both"] and not metadata_manager.file_exists_in_metadata(video_entry, srt_translated_key, video_output_dir):
            translation_filepath = os.path.join(video_output_dir, video_entry['files'][translation_key])
            with open(translation_filepath, 'r', encoding='utf-8') as f:
                translation_data = json.load(f)
            srt_path = create_srt_file(data=translation_data['segments'], mode="translated", video_id=video_id, lang_code=target_lang_code,
                                       output_dir=video_output_dir, max_line_length=args.max_line_length)
            metadata_manager.add_file_to_entry(metadata, video_id, srt_translated_key, srt_path)
            
    except Exception as e:
        logging.error(f"\n[ 파이프라인 실패! ] 에러: {e}", exc_info=True)
    finally:
        metadata_manager.save_metadata(args.output, metadata)
        logging.info(f"\n--- 작업 종료 ---")

if __name__ == "__main__":
    main()

