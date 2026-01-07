# YouTube Caption Generator

Generate and translate subtitles for YouTube videos with a web-based interface.

![Screenshot](docs/screenshot.png)

## Features

- **Speech-to-Text**: Uses OpenAI gpt-4o-transcribe with speaker diarization
- **Translation**: OpenAI GPT-4o-mini for natural translations
- **Subtitle Editor**: Edit subtitles with video preview and timeline
- **Multi-language**: Support for 8 languages (Korean, English, Japanese, Chinese, Spanish, French, German, Russian)
- **Real-time Progress**: WebSocket-based progress tracking
- **Local Deployment**: Docker Compose for easy local setup

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd youtube-captioner

# Start the application
docker-compose up -d

# Open http://localhost:3000 in your browser
```

### Manual Setup

#### Backend (FastAPI)

```bash
cd backend

# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the server
uv run uvicorn app.main:app --reload --port 8000
```

#### Frontend (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. **Configure API Key**: Enter your OpenAI API key in the settings panel
2. **Enter YouTube URL**: Paste a YouTube video URL
3. **Select Options**: Choose target language and subtitle type
4. **Generate**: Click "Generate Subtitles" and wait for processing
5. **Download/Edit**: Download the SRT files or open the subtitle editor

## API Key

You need to provide your own API key:

- **OpenAI**: [Get API Key](https://platform.openai.com/) - For transcription (STT) and translation

API key is stored in your browser's localStorage and sent directly to the API.

## Project Structure

```
youtube-captioner/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── jobs.py          # In-memory job management
│   │   ├── routers/
│   │   │   ├── process.py   # Processing API
│   │   │   └── websocket.py # Real-time progress
│   │   └── core/            # Core modules
│   │       ├── downloader.py
│   │       ├── transcriber.py
│   │       ├── translator.py
│   │       └── captioner.py
│   └── Dockerfile
│
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   └── lib/             # API client
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.12, uv |
| APIs | OpenAI (STT + Translation) |
| Deployment | Docker, Docker Compose |

## License

MIT
