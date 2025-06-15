import logging
import argparse
from src import pipeline, config

def main():
    """
    이 파일은 이제 커맨드 라인 인터페이스(CLI)의 진입점(Entrypoint) 역할만 합니다.
    모든 핵심 로직은 `pipeline.py`의 `run_pipeline` 함수에 위임됩니다.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = argparse.ArgumentParser(
        description="YouTube 다국어 자막 생성기",
        formatter_class=argparse.RawTextHelpFormatter # help 메시지 포맷 개선
    )
    
    # --- 인자 정의 ---
    parser.add_argument("--url", default="https://www.youtube.com/watch?v=FsUMdkCYluc", help="YouTube 비디오 URL")
    parser.add_argument("--lang", default="ko", choices=config.get_supported_codes(), help="번역할 목표 언어의 ISO 639-1 코드")
    parser.add_argument("--download-video", action='store_true', help="오디오와 함께 비디오도 다운로드합니다.")
    parser.add_argument("--quality", default='high', choices=['high', 'medium', 'low'], help="비디오 다운로드 시 화질")
    parser.add_argument("--srt-type", default="both", choices=["source", "translated", "both"], help="생성할 자막의 종류 (source|translated|both)")
    parser.add_argument("--history", type=int, default=3, help="번역 시 문맥으로 기억할 이전 대화 청크 수")
    parser.add_argument("--output", default="output", help="결과물 저장 디렉터리")
    parser.add_argument("--max-line-length", type=int, default=80, help="자막 한 줄의 최대 길이 (권장: 35~42)")
    parser.add_argument("--pause-threshold", type=float, default=1.0, help="원본 자막 생성 시, 문장으로 간주할 쉼 간격(초)")
    args = parser.parse_args()

    # --- 핵심 로직 실행 ---
    # 파싱된 인자들을 그대로 `run_pipeline` 함수에 전달합니다.
    pipeline.run_pipeline(
        url=args.url,
        output_dir=args.output,
        lang_code=args.lang,
        should_download_video=args.download_video,
        video_quality=args.quality,
        srt_type=args.srt_type,
        gpt_history_size=args.history,
        max_line_length=args.max_line_length,
        pause_threshold=args.pause_threshold,
    )

if __name__ == "__main__":
    main()

