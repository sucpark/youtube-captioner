'use client';

import { useState, useEffect } from 'react';
import { getLanguages, Language } from '@/lib/api';

interface ProcessFormProps {
  onSubmit: (data: {
    youtube_url: string;
    target_language: string;
    srt_type: 'source' | 'translated' | 'both';
  }) => void;
  isLoading: boolean;
  disabled: boolean;
}

export default function ProcessForm({ onSubmit, isLoading, disabled }: ProcessFormProps) {
  const [url, setUrl] = useState('');
  const [language, setLanguage] = useState('ko');
  const [srtType, setSrtType] = useState<'source' | 'translated' | 'both'>('both');
  const [languages, setLanguages] = useState<Language[]>([]);

  useEffect(() => {
    getLanguages()
      .then((data) => setLanguages(data.languages))
      .catch((err) => {
        console.error('Failed to load languages:', err);
        // Fallback languages
        setLanguages([
          { code: 'ko', name: 'Korean' },
          { code: 'en', name: 'English' },
          { code: 'ja', name: 'Japanese' },
          { code: 'zh', name: 'Chinese' },
        ]);
      });
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    onSubmit({ youtube_url: url.trim(), target_language: language, srt_type: srtType });
  };

  const isValidUrl = url.includes('youtube.com/watch') || url.includes('youtu.be/');

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          YouTube URL
        </label>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.youtube.com/watch?v=..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isLoading}
        />
        {url && !isValidUrl && (
          <p className="mt-1 text-sm text-red-500">Please enter a valid YouTube URL</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Target Language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading}
          >
            {languages.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Subtitle Type
          </label>
          <select
            value={srtType}
            onChange={(e) => setSrtType(e.target.value as 'source' | 'translated' | 'both')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading}
          >
            <option value="both">Both (Source + Translated)</option>
            <option value="source">Source Only</option>
            <option value="translated">Translated Only</option>
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading || disabled || !isValidUrl}
        className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Processing...
          </>
        ) : (
          <>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Generate Subtitles
          </>
        )}
      </button>
    </form>
  );
}
