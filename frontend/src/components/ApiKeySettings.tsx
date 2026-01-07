'use client';

import { useState, useEffect } from 'react';

interface ApiKeySettingsProps {
  onKeysChange: (keys: { openai: string }) => void;
}

export default function ApiKeySettings({ onKeysChange }: ApiKeySettingsProps) {
  const [openaiKey, setOpenaiKey] = useState('');
  const [showKeys, setShowKeys] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  // Load keys from localStorage on mount
  useEffect(() => {
    const savedOpenai = localStorage.getItem('openai_api_key') || '';
    setOpenaiKey(savedOpenai);
    onKeysChange({ openai: savedOpenai });

    // Auto-expand if key is not set
    if (!savedOpenai) {
      setIsExpanded(true);
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem('openai_api_key', openaiKey);
    onKeysChange({ openai: openaiKey });
    setIsExpanded(false);
  };

  const hasKeys = !!openaiKey;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-50"
      >
        <div className="flex items-center gap-2">
          <svg
            className="w-5 h-5 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
            />
          </svg>
          <span className="font-medium text-gray-900">API Key</span>
          {hasKeys ? (
            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
              Configured
            </span>
          ) : (
            <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
              Required
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          <p className="text-sm text-gray-500 mt-3 mb-4">
            Your API key is stored locally in your browser and sent directly to the API.
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                OpenAI API Key
              </label>
              <input
                type={showKeys ? 'text' : 'password'}
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder="Enter your OpenAI API key"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Used for transcription (STT) and translation
              </p>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={showKeys}
                  onChange={(e) => setShowKeys(e.target.checked)}
                  className="rounded border-gray-300"
                />
                Show key
              </label>

              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Save Key
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
