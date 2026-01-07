'use client';

interface ProgressTrackerProps {
  status: string;
  progress: number;
  message: string;
  error?: string | null;
}

const STEPS = [
  { key: 'downloading', label: 'Download' },
  { key: 'transcribing', label: 'Transcribe' },
  { key: 'translating', label: 'Translate' },
  { key: 'captioning', label: 'Caption' },
];

export default function ProgressTracker({ status, progress, message, error }: ProgressTrackerProps) {
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center gap-2 text-red-700">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span className="font-medium">Error</span>
        </div>
        <p className="mt-2 text-sm text-red-600">{error}</p>
      </div>
    );
  }

  const getCurrentStepIndex = () => {
    const idx = STEPS.findIndex((s) => s.key === status);
    return idx >= 0 ? idx : 0;
  };

  const currentStepIndex = getCurrentStepIndex();

  return (
    <div className="space-y-4">
      {/* Progress Bar */}
      <div className="relative">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="mt-1 flex justify-between text-xs text-gray-500">
          <span>{message || 'Processing...'}</span>
          <span>{progress}%</span>
        </div>
      </div>

      {/* Steps */}
      <div className="flex items-center justify-between">
        {STEPS.map((step, index) => {
          const isComplete = index < currentStepIndex || status === 'completed';
          const isCurrent = index === currentStepIndex && status !== 'completed';

          return (
            <div key={step.key} className="flex flex-col items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors ${
                  isComplete
                    ? 'bg-green-500 text-white'
                    : isCurrent
                    ? 'bg-blue-600 text-white animate-pulse'
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {isComplete ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>
              <span
                className={`mt-1 text-xs ${
                  isComplete || isCurrent ? 'text-gray-900 font-medium' : 'text-gray-500'
                }`}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Completed */}
      {status === 'completed' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-green-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="font-medium">Processing Complete!</span>
          </div>
        </div>
      )}
    </div>
  );
}
