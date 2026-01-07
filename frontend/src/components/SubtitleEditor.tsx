'use client';

import { useState, useRef, useEffect } from 'react';

export interface SubtitleSegment {
  start: number;
  end: number;
  text: string;
}

interface SubtitleEditorProps {
  segments: SubtitleSegment[];
  currentTime: number;
  onSeek: (time: number) => void;
  onSegmentsChange: (segments: SubtitleSegment[]) => void;
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
}

function parseTime(timeStr: string): number {
  const match = timeStr.match(/(\d{2}):(\d{2}):(\d{2}),(\d{3})/);
  if (!match) return 0;
  const [, h, m, s, ms] = match;
  return parseInt(h) * 3600 + parseInt(m) * 60 + parseInt(s) + parseInt(ms) / 1000;
}

export default function SubtitleEditor({
  segments,
  currentTime,
  onSeek,
  onSegmentsChange,
}: SubtitleEditorProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLDivElement>(null);

  // Find active segment
  const activeIndex = segments.findIndex(
    (seg) => currentTime >= seg.start && currentTime < seg.end
  );

  // Auto-scroll to active segment
  useEffect(() => {
    if (activeRef.current && listRef.current) {
      const container = listRef.current;
      const element = activeRef.current;
      const containerRect = container.getBoundingClientRect();
      const elementRect = element.getBoundingClientRect();

      if (elementRect.top < containerRect.top || elementRect.bottom > containerRect.bottom) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [activeIndex]);

  const handleTextChange = (index: number, newText: string) => {
    const newSegments = [...segments];
    newSegments[index] = { ...newSegments[index], text: newText };
    onSegmentsChange(newSegments);
  };

  const handleTimeChange = (index: number, field: 'start' | 'end', value: string) => {
    const time = parseTime(value);
    if (isNaN(time)) return;

    const newSegments = [...segments];
    newSegments[index] = { ...newSegments[index], [field]: time };
    onSegmentsChange(newSegments);
  };

  const handleDelete = (index: number) => {
    const newSegments = segments.filter((_, i) => i !== index);
    onSegmentsChange(newSegments);
    setEditingIndex(null);
  };

  const handleSplit = (index: number) => {
    const segment = segments[index];
    const midTime = (segment.start + segment.end) / 2;
    const newSegments = [
      ...segments.slice(0, index),
      { ...segment, end: midTime },
      { start: midTime, end: segment.end, text: '' },
      ...segments.slice(index + 1),
    ];
    onSegmentsChange(newSegments);
  };

  const handleMerge = (index: number) => {
    if (index >= segments.length - 1) return;
    const current = segments[index];
    const next = segments[index + 1];
    const newSegments = [
      ...segments.slice(0, index),
      { start: current.start, end: next.end, text: `${current.text} ${next.text}` },
      ...segments.slice(index + 2),
    ];
    onSegmentsChange(newSegments);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-700">
          Subtitles ({segments.length} segments)
        </h3>
        <div className="text-xs text-gray-500">
          Click to edit, double-click to jump
        </div>
      </div>

      {/* Segments List */}
      <div ref={listRef} className="flex-1 overflow-y-auto">
        {segments.map((segment, index) => {
          const isActive = index === activeIndex;
          const isEditing = index === editingIndex;

          return (
            <div
              key={index}
              ref={isActive ? activeRef : undefined}
              className={`border-b border-gray-100 transition-colors ${
                isActive ? 'bg-blue-50' : 'hover:bg-gray-50'
              } ${isEditing ? 'bg-yellow-50' : ''}`}
              onClick={() => setEditingIndex(isEditing ? null : index)}
              onDoubleClick={() => onSeek(segment.start)}
            >
              {/* Collapsed View */}
              {!isEditing && (
                <div className="px-4 py-3 cursor-pointer">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-gray-400 w-20 flex-shrink-0">
                      {formatTime(segment.start).slice(3, -4)}
                    </span>
                    <p className={`text-sm flex-1 truncate ${isActive ? 'text-blue-900 font-medium' : 'text-gray-700'}`}>
                      {segment.text}
                    </p>
                  </div>
                </div>
              )}

              {/* Expanded Edit View */}
              {isEditing && (
                <div className="px-4 py-3 space-y-3" onClick={(e) => e.stopPropagation()}>
                  {/* Time inputs */}
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={formatTime(segment.start)}
                      onChange={(e) => handleTimeChange(index, 'start', e.target.value)}
                      className="w-28 px-2 py-1 text-xs font-mono border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                    <span className="text-gray-400">→</span>
                    <input
                      type="text"
                      value={formatTime(segment.end)}
                      onChange={(e) => handleTimeChange(index, 'end', e.target.value)}
                      className="w-28 px-2 py-1 text-xs font-mono border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                    <span className="text-xs text-gray-400">
                      ({(segment.end - segment.start).toFixed(1)}s)
                    </span>
                  </div>

                  {/* Text input */}
                  <textarea
                    value={segment.text}
                    onChange={(e) => handleTextChange(index, e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
                    rows={2}
                  />

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onSeek(segment.start)}
                      className="px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded"
                    >
                      Play
                    </button>
                    <button
                      onClick={() => handleSplit(index)}
                      className="px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded"
                    >
                      Split
                    </button>
                    {index < segments.length - 1 && (
                      <button
                        onClick={() => handleMerge(index)}
                        className="px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded"
                      >
                        Merge Next
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(index)}
                      className="px-2 py-1 text-xs text-red-600 hover:bg-red-50 rounded ml-auto"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
