'use client';

import { getDownloadUrl } from '@/lib/api';

interface DownloadPanelProps {
  jobId: string;
  hasSourceSrt: boolean;
  hasTranslatedSrt: boolean;
  sourceLanguage?: string;
  targetLanguage?: string;
}

export default function DownloadPanel({
  jobId,
  hasSourceSrt,
  hasTranslatedSrt,
  sourceLanguage,
  targetLanguage,
}: DownloadPanelProps) {
  const downloads = [
    {
      key: 'source_srt',
      label: `Source SRT (${sourceLanguage?.toUpperCase() || 'Original'})`,
      available: hasSourceSrt,
    },
    {
      key: 'translated_srt',
      label: `Translated SRT (${targetLanguage?.toUpperCase() || 'Target'})`,
      available: hasTranslatedSrt,
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <h3 className="font-medium text-gray-900 mb-3">Download Files</h3>
      <div className="space-y-2">
        {downloads.map((item) => (
          <a
            key={item.key}
            href={item.available ? getDownloadUrl(jobId, item.key) : '#'}
            download
            className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${
              item.available
                ? 'border-gray-200 hover:border-blue-300 hover:bg-blue-50 cursor-pointer'
                : 'border-gray-100 bg-gray-50 cursor-not-allowed opacity-50'
            }`}
          >
            <div className="flex items-center gap-3">
              <svg
                className={`w-5 h-5 ${item.available ? 'text-blue-600' : 'text-gray-400'}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
              <span className={`text-sm ${item.available ? 'text-gray-900' : 'text-gray-500'}`}>
                {item.label}
              </span>
            </div>
            {item.available && (
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
            )}
          </a>
        ))}
      </div>
    </div>
  );
}
