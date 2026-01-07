const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export interface ProcessRequest {
  youtube_url: string;
  target_language: string;
  srt_type: 'source' | 'translated' | 'both';
  max_line_length?: number;
  pause_threshold?: number;
}

export interface SubtitleSegment {
  start: number;
  end: number;
  text: string;
}

export interface JobResult {
  video_id?: string;
  source_language?: string;
  has_source_srt?: boolean;
  has_translated_srt?: boolean;
  source_segments?: SubtitleSegment[];
  translated_segments?: SubtitleSegment[];
}

export interface JobStatus {
  id: string;
  youtube_url: string;
  target_language: string;
  srt_type: string;
  status: string;
  progress: number;
  message: string;
  error: string | null;
  result: JobResult;
  created_at: string;
  updated_at: string;
}

export interface Language {
  code: string;
  name: string;
}

export async function startProcessing(
  request: ProcessRequest,
  openaiKey: string
): Promise<{ job_id: string; status: string }> {
  const response = await fetch(`${API_URL}/api/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-OpenAI-Key': openaiKey,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start processing');
  }

  return response.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${API_URL}/api/jobs/${jobId}`);

  if (!response.ok) {
    throw new Error('Failed to get job status');
  }

  return response.json();
}

export async function getLanguages(): Promise<{ languages: Language[] }> {
  const response = await fetch(`${API_URL}/api/languages`);

  if (!response.ok) {
    throw new Error('Failed to get languages');
  }

  return response.json();
}

export function getDownloadUrl(jobId: string, fileType: string): string {
  return `${API_URL}/api/jobs/${jobId}/download/${fileType}`;
}

export function createWebSocket(jobId: string): WebSocket {
  return new WebSocket(`${WS_URL}/ws/${jobId}`);
}
