import os
import json
import logging
from src import config
from src.modules import metadata_manager
from src.modules.downloader import get_video_id, fetch_video_info, download_youtube_audio, download_youtube_video
from src.modules.transcriber import transcribe_audio_elevenlabs, save_transcription_result
from src.modules.translator import translate_text_gpt
from src.modules.formatter import save_translated_segments
from src.modules.captioner import create_srt_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_pipeline(
    url: str,
    output_dir: str,
    lang_code: str,
    should_download_video: bool,
    video_quality: str,
    srt_type: str,
    gpt_history_size: int,
    max_line_length: int,
    pause_threshold: float,
):
    """
    자막 생성의 전체 과정을 처리하는 핵심 파이프라인 함수.
    이 함수는 UI와 독립적으로 실행됩니다.
    """
    # 1. 메타데이터 로드
    metadata = metadata_manager.load_metadata(output_dir)
    
    try:
        # 2. 비디오 정보 확인 및 폴더 생성
        video_id = get_video_id(url)
        video_output_dir = os.path.join(output_dir, video_id)
        if not os.path.exists(video_output_dir):
            os.makedirs(video_output_dir)
            logging.info(f"'{video_output_dir}' 폴더를 생성했습니다.")

        if video_id not in metadata:
            info_dict = fetch_video_info(url)
            metadata_manager.update_video_entry(metadata, video_id, info_dict)
        
        video_entry = metadata[video_id]
        metadata_manager.create_info_file(video_id, video_entry, video_output_dir)
        logging.info(f"\n--- 작업 시작: {video_entry.get('title', video_id)} ---")

        # 3. 각 단계별 작업 실행 (파일 존재 시 건너뜀)
        
        # 비디오 다운로드
        if should_download_video:
            if not metadata_manager.file_exists_in_metadata(video_entry, 'video', video_output_dir):
                logging.info("\n--- 비디오 다운로드 시작 ---")
                video_path = download_youtube_video(url, video_output_dir, video_id, video_quality)
                metadata_manager.add_file_to_entry(metadata, video_id, 'video', video_path)
            else: logging.info(f"✔️ 비디오 파일이 이미 존재합니다: {video_entry['files']['video']}")

        # 오디오 다운로드
        if not metadata_manager.file_exists_in_metadata(video_entry, 'audio', video_output_dir):
            logging.info("\n--- 오디오 다운로드 시작 ---")
            audio_path = download_youtube_audio(url, video_output_dir, video_id)
            metadata_manager.add_file_to_entry(metadata, video_id, 'audio', audio_path)
        else: logging.info(f"✔️ 오디오 파일이 이미 존재합니다: {video_entry['files']['audio']}")
        audio_path = os.path.join(video_output_dir, video_entry['files']['audio'])

        # 음성 인식
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

        # 텍스트 번역
        target_lang_name = config.get_language_name(lang_code)
        if not target_lang_name: raise ValueError(f"지원하지 않는 언어 코드입니다: {lang_code}")
        translation_key = f'translation_{lang_code}'
        if srt_type in ["translated", "both"] and not metadata_manager.file_exists_in_metadata(video_entry, translation_key, video_output_dir):
            logging.info(f"\n--- 텍스트 번역 시작 ({target_lang_name}) ---")
            with open(transcription_filepath, 'r', encoding='utf-8') as f:
                transcription_result = json.load(f)
            translated_segments = translate_text_gpt(transcription_result, target_lang_name, gpt_history_size)
            translation_filename = f"{video_id}_{lang_code}_translation.json"
            translation_filepath = os.path.join(video_output_dir, translation_filename)
            save_translated_segments(translated_segments, video_id, lang_code, translation_filepath)
            metadata_manager.add_file_to_entry(metadata, video_id, translation_key, translation_filepath)
        elif metadata_manager.file_exists_in_metadata(video_entry, translation_key, video_output_dir): logging.info(f"✔️ 번역 파일이 이미 존재합니다.")
        else: logging.info("\n--- 텍스트 번역 건너뜀 ---")

        # SRT 자막 생성
        logging.info("\n--- SRT 자막 파일 생성 시작 ---")
        source_lang_code = video_entry.get('source_language_code', 'en')
        srt_source_key = f'srt_source_{source_lang_code}'
        if srt_type in ["source", "both"] and not metadata_manager.file_exists_in_metadata(video_entry, srt_source_key, video_output_dir):
            with open(transcription_filepath, 'r', encoding='utf-8') as f:
                transcription_result = json.load(f)
            srt_path = create_srt_file(data=transcription_result, mode="source", video_id=video_id, lang_code=source_lang_code,
                                       output_dir=video_output_dir, max_line_length=max_line_length, pause_threshold=pause_threshold)
            metadata_manager.add_file_to_entry(metadata, video_id, srt_source_key, srt_path)
        
        srt_translated_key = f'srt_translated_{lang_code}'
        if srt_type in ["translated", "both"] and not metadata_manager.file_exists_in_metadata(video_entry, srt_translated_key, video_output_dir):
            translation_filepath = os.path.join(video_output_dir, video_entry['files'][translation_key])
            with open(translation_filepath, 'r', encoding='utf-8') as f:
                translation_data = json.load(f)
            srt_path = create_srt_file(data=translation_data['segments'], mode="translated", video_id=video_id, lang_code=lang_code,
                                       output_dir=video_output_dir, max_line_length=max_line_length)
            metadata_manager.add_file_to_entry(metadata, video_id, srt_translated_key, srt_path)

    except Exception as e:
        logging.error(f"\n[ 파이프라인 실패! ] 에러: {e}", exc_info=True)
    finally:
        # 4. 작업 종료 전, 항상 메타데이터 저장
        metadata_manager.save_metadata(output_dir, metadata)
        logging.info(f"\n--- 작업 종료 ---")