'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getJobStatus, getDownloadUrl, JobStatus } from '@/lib/api';
import VideoPlayer, { VideoPlayerRef } from '@/components/VideoPlayer';
import SubtitleEditor, { SubtitleSegment } from '@/components/SubtitleEditor';

// Generate SRT content from segments
function generateSRT(segments: SubtitleSegment[]): string {
  return segments
    .map((seg, i) => {
      const formatTime = (s: number) => {
        const h = Math.floor(s / 3600);
        const m = Math.floor((s % 3600) / 60);
        const sec = Math.floor(s % 60);
        const ms = Math.floor((s % 1) * 1000);
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
      };
      return `${i + 1}\n${formatTime(seg.start)} --> ${formatTime(seg.end)}\n${seg.text}\n`;
    })
    .join('\n');
}

export default function ResultPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;

  const [job, setJob] = useState<JobStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [activeTab, setActiveTab] = useState<'source' | 'translated'>('translated');
  const [segments, setSegments] = useState<SubtitleSegment[]>([]);

  const playerRef = useRef<VideoPlayerRef>(null);

  // Load job data
  useEffect(() => {
    async function loadJob() {
      try {
        const data = await getJobStatus(jobId);
        setJob(data);

        // Extract segments from job result
        if (data.result) {
          const segs = activeTab === 'translated'
            ? data.result.translated_segments
            : data.result.source_segments;
          if (segs) {
            setSegments(segs);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load job');
      } finally {
        setLoading(false);
      }
    }

    loadJob();
  }, [jobId, activeTab]);

  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentTime(time);
  }, []);

  const handleSeek = useCallback((time: number) => {
    playerRef.current?.seek(time);
  }, []);

  const handleDownloadEdited = () => {
    const srtContent = generateSRT(segments);
    const blob = new Blob([srtContent], { type: 'text/srt' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${job?.result?.video_id || 'subtitles'}_edited.srt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-xl font-bold text-gray-900">Error</h1>
          <p className="mt-2 text-gray-600">{error || 'Job not found'}</p>
          <button
            onClick={() => router.push('/')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  if (job.status !== 'completed') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-xl font-bold text-gray-900">Processing...</h1>
          <p className="mt-2 text-gray-600">Job is still processing. Please wait.</p>
          <button
            onClick={() => router.push('/')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  const videoId = job.result?.video_id || '';

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/')}
              className="p-2 hover:bg-gray-100 rounded-md"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h1 className="text-lg font-semibold text-gray-900">Subtitle Editor</h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownloadEdited}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
            >
              Download Edited SRT
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-[calc(100vh-120px)]">
          {/* Video Panel */}
          <div className="flex flex-col">
            <VideoPlayer
              ref={playerRef}
              videoId={videoId}
              segments={segments}
              onTimeUpdate={handleTimeUpdate}
            />

            {/* Download Links */}
            <div className="mt-4 bg-white rounded-lg border border-gray-200 p-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Original Files</h3>
              <div className="flex gap-2">
                {job.result?.has_source_srt && (
                  <a
                    href={getDownloadUrl(jobId, 'source_srt')}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Source SRT
                  </a>
                )}
                {job.result?.has_translated_srt && (
                  <a
                    href={getDownloadUrl(jobId, 'translated_srt')}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Translated SRT
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* Editor Panel */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden flex flex-col">
            {/* Tabs */}
            <div className="flex border-b border-gray-200">
              {job.result?.has_source_srt && (
                <button
                  onClick={() => setActiveTab('source')}
                  className={`px-4 py-2 text-sm font-medium ${
                    activeTab === 'source'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Source ({job.result?.source_language?.toUpperCase()})
                </button>
              )}
              {job.result?.has_translated_srt && (
                <button
                  onClick={() => setActiveTab('translated')}
                  className={`px-4 py-2 text-sm font-medium ${
                    activeTab === 'translated'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Translated ({job.target_language.toUpperCase()})
                </button>
              )}
            </div>

            {/* Editor */}
            <div className="flex-1 overflow-hidden">
              <SubtitleEditor
                segments={segments}
                currentTime={currentTime}
                onSeek={handleSeek}
                onSegmentsChange={setSegments}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
