# YouTube Caption Generator - Web Application Development Plan

## Project Overview

Transform the CLI-based YouTube Caption Generator into a **full-stack web application** with a user-friendly interface.

### Current State
- Python CLI tool using Poetry
- ElevenLabs STT + OpenAI GPT translation
- SRT subtitle file generation

### Target State
- Web-based UI with real-time progress tracking
- Subtitle editor with video preview
- Docker-based local deployment

---

## Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Frontend | Next.js + TypeScript | App Router, Tailwind CSS |
| Backend | FastAPI (Python) | Reuse existing code, async support |
| Package Manager | **uv** | 10-100x faster than Poetry |
| Database | **None** | Session-based, no persistence needed |
| Task Queue | **In-memory** | Simple dict, no Redis needed |
| API Keys | **localStorage** | Browser storage, sent via headers |
| Deployment | Docker Compose | One-click local execution |

---

## Project Structure

```
youtube-caption-generator/
├── docker-compose.yml
├── .env.example
│
├── backend/                      # FastAPI
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── routers/
│   │   │   ├── process.py       # Processing API
│   │   │   └── websocket.py     # Real-time progress
│   │   ├── jobs.py              # In-memory job management
│   │   └── core/                # Migrated modules
│   │       ├── downloader.py
│   │       ├── transcriber.py
│   │       ├── translator.py
│   │       └── captioner.py
│   └── storage/                 # Temporary file storage
│
├── frontend/                     # Next.js
│   ├── Dockerfile
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # Main (URL input + settings)
│   │   │   └── result/[jobId]/  # Result + editor
│   │   ├── components/
│   │   │   ├── ProcessForm.tsx
│   │   │   ├── ProgressTracker.tsx
│   │   │   ├── VideoPlayer.tsx
│   │   │   ├── SubtitleEditor.tsx
│   │   │   └── ApiKeySettings.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   └── lib/
│   │       └── api.ts
│
└── src/                          # Original CLI code (reference)
```

---

## Core Features

### 1. API Key Management
- Stored in browser **localStorage**
- Sent via request headers
- No authentication required

### 2. Video Processing
- YouTube URL input
- Language selection (8 languages)
- Quality/option settings
- **Real-time progress** via WebSocket

### 3. Subtitle Editor
```
┌─────────────────────────────────────────────┐
│  VideoPlayer (with subtitle overlay)        │
├─────────────────────────────────────────────┤
│  SubtitleTimeline (drag to adjust time)     │
│  ┌────┐ ┌────────┐ ┌────┐ ┌──────┐        │
│  │ S1 │ │   S2   │ │ S3 │ │  S4  │ ...    │
├─────────────────────────────────────────────┤
│  SubtitleEditor (text editing)              │
│  [00:00:05,000] --> [00:00:08,500]         │
│  [Editable subtitle text___________]        │
└─────────────────────────────────────────────┘
```

---

## API Design

### Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/process` | Start processing (API keys in headers) |
| GET | `/api/jobs/{id}` | Get job status |
| GET | `/api/jobs/{id}/download/{type}` | Download file (srt/audio) |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/{job_id}` | Real-time progress updates |

### Request/Response Example
```python
# POST /api/process
# Headers: X-ElevenLabs-Key, X-OpenAI-Key
{
    "youtube_url": "https://youtube.com/watch?v=...",
    "target_language": "ko",
    "srt_type": "both"  # source/translated/both
}

# Response
{
    "job_id": "uuid-xxx",
    "status": "pending"
}
```

### In-memory Job Management
```python
# jobs.py
jobs: dict[str, JobInfo] = {}

class JobInfo:
    id: str
    status: str  # pending/downloading/transcribing/translating/completed/failed
    progress: int  # 0-100
    result: dict | None
```

---

## Implementation Phases

### Phase 1: Backend (3-4 days)
1. FastAPI project setup (uv)
2. Copy existing modules (`src/modules/` → `backend/app/core/`)
3. Parameterize API keys (env vars → function args)
4. `/api/process` endpoint + background task
5. WebSocket progress broadcasting

### Phase 2: Frontend (3-4 days)
6. Next.js project + Tailwind CSS
7. API key input form (localStorage)
8. Processing form (URL, language, options)
9. Progress tracker (WebSocket connection)
10. Result page (download buttons)

### Phase 3: Subtitle Editor (3-4 days)
11. Video player + subtitle overlay
12. Subtitle editor (text editing)
13. Time adjustment (drag or input)

### Phase 4: Finalization (1-2 days)
14. Docker Compose setup
15. README documentation

---

## Docker Configuration

### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes:
      - ./storage:/app/storage

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Execution
```bash
docker-compose up -d
# Access http://localhost:3000
```

---

## Files to Modify

| Original File | Changes |
|---------------|---------|
| `src/modules/transcriber.py` | Add `api_key` parameter |
| `src/modules/translator.py` | Add `api_key` parameter + progress callback |
| `src/pipeline.py` | Async wrapper + WebSocket progress |

---

## Data Flow

```
[Frontend]                    [Backend]
    │                             │
    │ 1. Save API keys to         │
    │    localStorage             │
    │                             │
    │ 2. POST /api/process ───────▶│ 3. Create job (UUID)
    │    (URL + API Keys)         │    jobs[id] = JobInfo
    │                             │
    │ 4. WebSocket connect ───────▶│ 5. Start background task
    │    /ws/{job_id}             │    - Download (0-25%)
    │                             │    - Transcribe (25-50%)
    │◀──────────────── 6. Progress│    - Translate (50-75%)
    │    {"progress": 50}         │    - Caption (75-100%)
    │                             │
    │◀──────────────── 7. Complete│
    │    {"status": "completed"}  │
    │                             │
    │ 8. GET /download/srt ───────▶│ 9. Return file
    │◀────────────────────────────│
```

---

## Backend Setup (uv)

```bash
cd backend
uv init
uv add fastapi "uvicorn[standard]"
uv add yt-dlp elevenlabs openai python-dotenv
uv add python-multipart

# Dev dependencies
uv add --dev pytest pytest-asyncio httpx
```

---

## Supported Languages

| Code | Language |
|------|----------|
| ko | Korean |
| en | English |
| ja | Japanese |
| zh | Chinese |
| es | Spanish |
| fr | French |
| de | German |
| ru | Russian |

---

## Summary

This plan transforms the YouTube Caption Generator from a CLI tool into a modern web application while maintaining simplicity:

- **No database** - Session-based, files stored temporarily
- **No Redis** - In-memory job tracking
- **No authentication** - Users provide their own API keys
- **Docker-based** - Easy local deployment

Total estimated development time: **10-14 days**
