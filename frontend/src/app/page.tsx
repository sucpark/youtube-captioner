'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ApiKeySettings from '@/components/ApiKeySettings';
import ProcessForm from '@/components/ProcessForm';
import ProgressTracker from '@/components/ProgressTracker';
import DownloadPanel from '@/components/DownloadPanel';
import { startProcessing, getJobStatus, JobStatus } from '@/lib/api';
import { useWebSocket, ProgressMessage } from '@/hooks/useWebSocket';

export default function Home() {
  const router = useRouter();
  const [apiKeys, setApiKeys] = useState({ elevenlabs: '', openai: '' });
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [targetLanguage, setTargetLanguage] = useState('ko');

  const { lastMessage } = useWebSocket(jobId);

  // Update job status from WebSocket
  useEffect(() => {
    if (lastMessage) {
      setJobStatus((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          status: lastMessage.status,
          progress: lastMessage.progress,
          message: lastMessage.message || '',
          error: lastMessage.error || null,
          result: lastMessage.result || prev.result,
        };
      });

      if (lastMessage.type === 'completed' || lastMessage.type === 'error') {
        setIsProcessing(false);
      }
    }
  }, [lastMessage]);

  // Poll job status as backup
  useEffect(() => {
    if (!jobId || !isProcessing) return;

    const interval = setInterval(async () => {
      try {
        const status = await getJobStatus(jobId);
        setJobStatus(status);

        if (status.status === 'completed' || status.status === 'failed') {
          setIsProcessing(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Failed to get job status:', err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId, isProcessing]);

  const handleSubmit = async (data: {
    youtube_url: string;
    target_language: string;
    srt_type: 'source' | 'translated' | 'both';
  }) => {
    if (!apiKeys.elevenlabs || !apiKeys.openai) {
      alert('Please configure your API keys first');
      return;
    }

    setIsProcessing(true);
    setJobStatus(null);
    setTargetLanguage(data.target_language);

    try {
      const result = await startProcessing(data, apiKeys.elevenlabs, apiKeys.openai);
      setJobId(result.job_id);
      setJobStatus({
        id: result.job_id,
        youtube_url: data.youtube_url,
        target_language: data.target_language,
        srt_type: data.srt_type,
        status: result.status,
        progress: 0,
        message: 'Starting...',
        error: null,
        result: {},
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    } catch (err) {
      setIsProcessing(false);
      alert(err instanceof Error ? err.message : 'Failed to start processing');
    }
  };

  const hasApiKeys = apiKeys.elevenlabs && apiKeys.openai;
  const isCompleted = jobStatus?.status === 'completed';

  return (
    <main className="min-h-screen py-8 px-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">YouTube Caption Generator</h1>
          <p className="mt-2 text-gray-600">
            Generate and translate subtitles for YouTube videos
          </p>
        </div>

        {/* API Keys */}
        <ApiKeySettings onKeysChange={setApiKeys} />

        {/* Process Form */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Generate Subtitles</h2>
          <ProcessForm
            onSubmit={handleSubmit}
            isLoading={isProcessing}
            disabled={!hasApiKeys}
          />
        </div>

        {/* Progress */}
        {jobStatus && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Progress</h2>
            <ProgressTracker
              status={jobStatus.status}
              progress={jobStatus.progress}
              message={jobStatus.message}
              error={jobStatus.error}
            />
          </div>
        )}

        {/* Download */}
        {isCompleted && jobId && (
          <>
            <DownloadPanel
              jobId={jobId}
              hasSourceSrt={jobStatus?.result?.has_source_srt || false}
              hasTranslatedSrt={jobStatus?.result?.has_translated_srt || false}
              sourceLanguage={jobStatus?.result?.source_language}
              targetLanguage={targetLanguage}
            />

            {/* Edit Button */}
            <button
              onClick={() => router.push(`/result/${jobId}`)}
              className="w-full py-3 px-4 bg-gray-900 text-white font-medium rounded-lg hover:bg-gray-800 flex items-center justify-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Open Subtitle Editor
            </button>
          </>
        )}

        {/* Footer */}
        <footer className="text-center text-sm text-gray-500">
          <p>
            Powered by{' '}
            <a href="https://elevenlabs.io" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
              ElevenLabs
            </a>{' '}
            &{' '}
            <a href="https://openai.com" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
              OpenAI
            </a>
          </p>
        </footer>
      </div>
    </main>
  );
}
