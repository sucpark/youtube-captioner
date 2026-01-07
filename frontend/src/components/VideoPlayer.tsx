'use client';

import { useRef, useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { SubtitleSegment } from './SubtitleEditor';

interface VideoPlayerProps {
  videoId: string;
  segments: SubtitleSegment[];
  onTimeUpdate: (time: number) => void;
}

export interface VideoPlayerRef {
  seek: (time: number) => void;
  play: () => void;
  pause: () => void;
}

// Simple YouTube thumbnail as placeholder (we don't have actual video)
function getYouTubeThumbnail(videoId: string): string {
  return `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
}

const VideoPlayer = forwardRef<VideoPlayerRef, VideoPlayerProps>(
  ({ videoId, segments, onTimeUpdate }, ref) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    // Find current subtitle
    const currentSubtitle = segments.find(
      (seg) => currentTime >= seg.start && currentTime < seg.end
    );

    // Calculate duration from segments
    useEffect(() => {
      if (segments.length > 0) {
        const maxEnd = Math.max(...segments.map((s) => s.end));
        setDuration(maxEnd);
      }
    }, [segments]);

    // Playback simulation
    useEffect(() => {
      if (isPlaying) {
        intervalRef.current = setInterval(() => {
          setCurrentTime((prev) => {
            const newTime = prev + 0.1;
            if (newTime >= duration) {
              setIsPlaying(false);
              return duration;
            }
            return newTime;
          });
        }, 100);
      } else {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      }

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }, [isPlaying, duration]);

    // Notify parent of time updates
    useEffect(() => {
      onTimeUpdate(currentTime);
    }, [currentTime, onTimeUpdate]);

    // Expose methods to parent
    useImperativeHandle(ref, () => ({
      seek: (time: number) => {
        setCurrentTime(Math.max(0, Math.min(time, duration)));
      },
      play: () => setIsPlaying(true),
      pause: () => setIsPlaying(false),
    }));

    const formatTime = (seconds: number): string => {
      const m = Math.floor(seconds / 60);
      const s = Math.floor(seconds % 60);
      return `${m}:${s.toString().padStart(2, '0')}`;
    };

    const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
      const time = parseFloat(e.target.value);
      setCurrentTime(time);
    };

    return (
      <div className="bg-black rounded-lg overflow-hidden">
        {/* Video Area */}
        <div className="relative aspect-video bg-gray-900">
          {/* Thumbnail/Placeholder */}
          <img
            src={getYouTubeThumbnail(videoId)}
            alt="Video thumbnail"
            className="w-full h-full object-cover opacity-50"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '/placeholder-video.png';
            }}
          />

          {/* Subtitle Overlay */}
          {currentSubtitle && (
            <div className="absolute bottom-16 left-0 right-0 flex justify-center px-4">
              <div className="bg-black/80 text-white px-4 py-2 rounded text-center max-w-[80%]">
                <p className="text-lg leading-relaxed">{currentSubtitle.text}</p>
              </div>
            </div>
          )}

          {/* Center Play Button */}
          {!isPlaying && (
            <button
              onClick={() => setIsPlaying(true)}
              className="absolute inset-0 flex items-center justify-center"
            >
              <div className="w-16 h-16 bg-white/90 rounded-full flex items-center justify-center hover:bg-white transition-colors">
                <svg className="w-8 h-8 text-gray-900 ml-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
            </button>
          )}
        </div>

        {/* Controls */}
        <div className="p-3 bg-gray-900">
          {/* Progress Bar */}
          <input
            type="range"
            min={0}
            max={duration || 100}
            step={0.1}
            value={currentTime}
            onChange={handleSeek}
            className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />

          {/* Control Buttons */}
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-2 text-white hover:bg-gray-700 rounded"
              >
                {isPlaying ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                )}
              </button>
              <span className="text-sm text-gray-400 font-mono">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>

            <div className="text-xs text-gray-500">
              Subtitle Preview Mode
            </div>
          </div>
        </div>
      </div>
    );
  }
);

VideoPlayer.displayName = 'VideoPlayer';

export default VideoPlayer;
