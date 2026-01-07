'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { createWebSocket } from '@/lib/api';

export interface ProgressMessage {
  type: 'progress' | 'completed' | 'error';
  status: string;
  progress: number;
  message?: string;
  error?: string;
  result?: {
    video_id: string;
    source_language: string;
    has_source_srt: boolean;
    has_translated_srt: boolean;
  };
}

export function useWebSocket(jobId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<ProgressMessage | null>(null);

  const connect = useCallback(() => {
    if (!jobId || wsRef.current) return;

    const ws = createWebSocket(jobId);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ProgressMessage;
        setLastMessage(data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, [jobId]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (jobId) {
      connect();
    }
    return () => disconnect();
  }, [jobId, connect, disconnect]);

  return { isConnected, lastMessage, connect, disconnect };
}
