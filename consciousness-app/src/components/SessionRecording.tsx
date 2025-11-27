import { useState, useEffect, useCallback } from 'react';
import { Button } from './ui/button';

const API_BASE = 'http://localhost:8000';

interface SessionStatus {
  is_recording: boolean;
  session_id: string | null;
  duration_seconds: number;
  samples_recorded: number;
  events_count: number;
}

interface SessionRecordingProps {
  isConnected: boolean;
  // These come from WebSocket now
  isRecording?: boolean;
  sessionId?: string | null;
}

export const SessionRecording = ({ isConnected, isRecording: wsIsRecording, sessionId: wsSessionId }: SessionRecordingProps) => {
  const [localRecording, setLocalRecording] = useState(false);
  const [localSessionId, setLocalSessionId] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Use WebSocket data if available, otherwise local state
  const isRecording = wsIsRecording ?? localRecording;
  const sessionId = wsSessionId ?? localSessionId;

  // Update duration while recording
  useEffect(() => {
    if (!isRecording) {
      return;
    }

    const startTime = Date.now();
    const interval = setInterval(() => {
      setDuration(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [isRecording]);

  const startRecording = useCallback(async (tags: string = "", notes: string = "") => {
    if (!isConnected) {
      setError('Connect to Muse first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/session/start?tags=${encodeURIComponent(tags)}&notes=${encodeURIComponent(notes)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      const data = await response.json();

      if (data.status === 'recording') {
        setLocalRecording(true);
        setLocalSessionId(data.session_id);
        setDuration(0);
      } else {
        setError(data.message || 'Failed to start recording');
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error('Start recording error:', err);
    } finally {
      setLoading(false);
    }
  }, [isConnected]);

  const stopRecording = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/session/stop`, {
        method: 'POST',
      });

      const data = await response.json();

      if (data.status === 'stopped') {
        setLocalRecording(false);
        setLocalSessionId(null);
        // Show success message briefly
        setError(`Session saved: ${data.session_path}`);
        setTimeout(() => setError(null), 3000);
      } else {
        setError(data.message || 'Failed to stop recording');
      }
    } catch (err) {
      setError('Failed to connect to server');
      console.error('Stop recording error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const addMarker = useCallback(async (label: string) => {
    if (!isRecording) return;

    try {
      await fetch(`${API_BASE}/api/session/marker?label=${encodeURIComponent(label)}`, {
        method: 'POST',
      });
    } catch (err) {
      console.error('Add marker error:', err);
    }
  }, [isRecording]);

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-zinc-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-zinc-900">Session Recording</h2>
        {isRecording && (
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
            <span className="text-sm font-mono text-red-600">{formatDuration(duration)}</span>
          </div>
        )}
      </div>

      <div className="space-y-4">
        {/* Recording Status */}
        <div className="space-y-3">
          <div className="flex flex-col gap-3">
            {!isRecording ? (
              <>
                <Button
                  onClick={() => startRecording()}
                  disabled={!isConnected || loading}
                  className="bg-red-600 hover:bg-red-700 text-white w-full"
                >
                  {loading ? 'Starting...' : '🔴 Start Recording'}
                </Button>
                <Button
                  onClick={() => startRecording('meditation', 'Meditation session')}
                  disabled={!isConnected || loading}
                  variant="outline"
                  className="border-purple-600 text-purple-600 hover:bg-purple-50 w-full"
                >
                  {loading ? 'Starting...' : '🧘 Start Meditation'}
                </Button>
              </>
            ) : (
              <Button
                onClick={stopRecording}
                disabled={loading}
                variant="outline"
                className="border-red-600 text-red-600 hover:bg-red-50 w-full"
              >
                {loading ? 'Stopping...' : '⏹️ Stop Recording'}
              </Button>
            )}

            {!isConnected && (
              <div className="text-sm text-zinc-500 text-center">Connect to Muse first</div>
            )}
          </div>
        </div>

        {/* Session Info */}
        {sessionId && (
          <div className="text-sm text-zinc-600">
            <span className="font-medium">Session:</span> {sessionId}
          </div>
        )}

        {/* Quick Markers */}
        {isRecording && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-zinc-700">Quick Markers:</div>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => addMarker('eyes_closed')}
              >
                👁️ Eyes Closed
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => addMarker('talking')}
              >
                🗣️ Talking
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => addMarker('focused')}
              >
                🎯 Focused
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => addMarker('relaxed')}
              >
                😌 Relaxed
              </Button>
            </div>
          </div>
        )}

        {/* Error/Success Message */}
        {error && (
          <div className={`text-sm ${error.includes('saved') ? 'text-green-600' : 'text-red-600'}`}>
            {error}
          </div>
        )}
      </div>
    </div>
  );
};
