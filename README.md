# YouTube 다국어 자막 생성기

유튜브 영상 URL만으로 음성을 인식하고, 원하는 언어로 번역하여 SRT 자막 파일을 자동으로 생성하는 파이프라인 프로젝트입니다.

---

## 🚀 주요 기능

- **다단계 자동화 파이프라인**: 오디오/비디오 다운로드, 음성 인식, 번역, 자막 파일 생성이 모두 자동으로 처리됩니다.
- **다국어 번역**: **OpenAI (GPT-4o-mini)** API를 사용하여 지정된 언어로 자연스러운 번역을 제공합니다. (지원 언어는 `src/config.py`에서 관리)
- **정교한 음성 인식**: **ElevenLabs** API를 사용하여 화자 분리(`Diarization`) 기능이 포함된 정확한 텍스트를 추출합니다.
- **지능적인 자막 생성**: 단순 길이 제한이 아닌, 문맥, 문장 부호, 실제 대화의 쉼(pause)을 종합적으로 고려하여 가독성 높은 SRT 자막을 생성합니다.
- **메타데이터 기반 관리**: 처리된 모든 영상의 정보와 생성된 파일 목록을 `metadata.json`에 저장하여, 불필요한 API 호출 및 파일 재생성을 방지합니다.
- **체계적인 파일 관리**: 각 영상 ID별로 하위 폴더를 생성하여 관련된 모든 결과물을 깔끔하게 관리합니다.
- **비디오 다운로드 (선택 사항)**: 고화질(1080p), 중간(720p), 저화질(480p) 옵션을 선택하여 원본 영상을 함께 다운로드할 수 있습니다.
- **유연한 자막 선택**: 원본 언어 자막, 번역된 언어 자막 또는 두 가지 모두를 선택하여 생성할 수 있습니다.

---

## 🛠️ 기술 스택

- **언어**: Python 3.11+
- **패키지 및 의존성 관리**: Poetry
- **핵심 라이브러리**:
  - `yt-dlp`: YouTube 오디오 및 비디오 다운로드
  - `elevenlabs`: 음성 인식 (STT)
  - `openai`: 텍스트 번역
  - `python-dotenv`: API 키 등 환경 변수 관리
- **테스트**: Pytest

---

## ⚙️ 설치 및 설정

**사전 요구사항**:
- Python 3.11 이상
- Poetry
- [FFmpeg](https://ffmpeg.org/download.html) (yt-dlp가 오디오/비디오 변환 시 필요)

1.  **프로젝트 클론**
    ```bash
    git clone <your-repository-url>
    cd youtube-caption-generator
    ```

2.  **의존성 설치**
    ```bash
    poetry install
    ```

3.  **환경 변수 설정**
    프로젝트 루트 디렉터리에 `.env` 파일을 생성하고 아래와 같이 API 키를 입력합니다.

    ```.env
    ELEVENLABS_API_KEY="sk_..."
    OPENAI_API_KEY="sk_..."
    ```

---

## ▶️ 사용 방법

모든 작업은 `main.py`를 통해 실행됩니다.

**기본 사용법 (한국어로 번역된 자막과 원본 자막 모두 생성):**
```bash
poetry run python main.py --url "[https://www.youtube.com/watch?v=VIDEO_ID](https://www.youtube.com/watch?v=VIDEO_ID)" --lang ko

주요 옵션:

--url: 대상 유튜브 비디오의 전체 URL (필수)

--lang: 번역할 목표 언어의 ISO 639-1 코드 (기본값: ko)

--download-video: 비디오를 함께 다운로드합니다.

--quality: 다운로드할 비디오의 화질 (high, medium, low, 기본값: high)

--srt-type: 생성할 자막의 종류 (source, translated, both, 기본값: both)

--output: 결과물이 저장될 폴더 (기본값: output)

사용 예시:

일본어로 번역된 자막만 생성:

poetry run python main.py --url "URL" --lang ja --srt-type translated

1080p 영상과 함께 원본(영어) 자막만 생성:

poetry run python main.py --url "URL" --download-video --quality high --srt-type source

📂 프로젝트 구조
youtube-caption-generator/
├── output/
│   ├── metadata.json
│   └── (video_id)/
│       ├── (video_id).mp3
│       ├── (video_id).mp4
│       ├── (video_id)_transcription.json
│       ├── (video_id)_(lang_code)_translation.json
│       └── (video_id)_(lang_code).srt
├── src/
│   ├── modules/
│   │   ├── captioner.py
│   │   ├── downloader.py
│   │   ├── formatter.py
│   │   ├── metadata_manager.py
│   │   ├── transcriber.py
│   │   └── translator.py
│   └── config.py
├── tests/
├── .env
├── main.py
├── poetry.lock
└── pyproject.toml
