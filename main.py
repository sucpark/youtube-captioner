import os
import logging
import argparse
from src.modules.downloader import download_youtube_audio
from src.modules.transcriber import transcribe_audio_elevenlabs, save_transcription_result

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description="YouTube Caption Generator")
    parser.add_argument("--url", default="https://www.youtube.com/watch?v=FsUMdkCYluc", help="다운로드할 YouTube 비디오 URL")
    parser.add_argument("--output", default="output", help="오디오 파일을 저장할 디렉터리 (기본값: output)")
    args = parser.parse_args()

    test_url = args.url
    output_directory = args.output

    # 출력 폴더가 없으면 생성
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    try:
        # 1단계: 오디오 다운로드
        print("--- 1. 오디오 다운로드 시작 ---")
        audio_path, title = download_youtube_audio(test_url, output_directory)
        print(f"✔️ 다운로드 완료: {audio_path}")

        # 2단계: 오디오 전사 (ElevenLabs 사용)
        print("\n--- 2. 음성 인식 시작 ---")
        transcription_result = transcribe_audio_elevenlabs(audio_path)
        
        # 3단계: 결과 저장
        print("\n--- 3. 결과 파일로 저장 ---")
        result_filename = os.path.splitext(os.path.basename(audio_path))[0] + ".json"
        result_filepath = os.path.join(output_directory, result_filename)
        save_transcription_result(transcription_result, result_filepath)
        
        print("\n[ 최종 결과 ]")
        print(f"영상 제목: {title}")
        print(f"감지된 언어: {transcription_result.get('language_code')}")
        print("전체 텍스트:")
        print(transcription_result.get('text'))
        
        # 4단계: 화자별 타임스탬프 일부 출력
        print("\n--- 4. 화자별 타임스탬프 확인 (첫 5개 단어) ---")
        words = transcription_result.get('words', [])
        if words:
            for i, word_data in enumerate(words[:5]):
                start = word_data.get('start', 'N/A')
                end = word_data.get('end', 'N/A')
                word = word_data.get('text', 'N/A')
                speaker = word_data.get('speaker_id', 'N/A')
                
                if isinstance(start, float) and isinstance(end, float):
                    print(f"  {i+1}. 화자[{speaker}]: \"{word}\" ({start:.2f}s ~ {end:.2f}s)")
                else:
                    print(f"  {i+1}. 화자[{speaker}]: \"{word}\"")
        else:
            print("  단어 정보를 찾을 수 없습니다.")

    except Exception as e:
        print(f"\n[ 파이프라인 실패! ] 에러: {e}")

    
    logging.info(f"--- 작업 종료 ---")

if __name__ == "__main__":
    main()