import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { useCopilotWebSocket } from '../hooks/useCopilotWebSocket';
import { ChatInterface } from './ChatInterface';
import { BrainStatePanel } from './BrainStatePanel';
import { BreathingExercise } from './BreathingExercise';

interface AICopilotProps {
  isEEGConnected: boolean;
}

export function AICopilot({ isEEGConnected }: AICopilotProps) {
  const {
    messages,
    brainState,
    textFeatures,
    incongruence,
    shouldIntervene,
    isConnected,
    isTyping,
    isListening,
    error,
    connect,
    disconnect,
    sendMessage,
  } = useCopilotWebSocket();

  const [showBreathing, setShowBreathing] = useState(false);

  // Auto-open breathing exercise when intervention is needed
  useEffect(() => {
    if (shouldIntervene && isConnected) {
      setShowBreathing(true);
    }
  }, [shouldIntervene, isConnected]);

  const handleStart = async () => {
    if (!isEEGConnected) {
      alert('Please connect to Muse EEG device first');
      return;
    }

    try {
      // Call backend API to initialize copilot
      const response = await fetch('http://localhost:8000/api/copilot/start', {
        method: 'POST',
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to start copilot');
      }

      // Connect WebSocket
      connect();
    } catch (err) {
      console.error('Error starting copilot:', err);
      alert(`Error: ${err instanceof Error ? err.message : 'Failed to start copilot'}`);
    }
  };

  const handleStop = async () => {
    try {
      // Disconnect WebSocket first
      disconnect();

      // Call backend API to stop and export session
      const response = await fetch('http://localhost:8000/api/copilot/stop', {
        method: 'POST',
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to stop copilot');
      }

      const data = await response.json();
      console.log('Session exported to:', data.export_path);
    } catch (err) {
      console.error('Error stopping copilot:', err);
      alert(`Error: ${err instanceof Error ? err.message : 'Failed to stop copilot'}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-zinc-900">AI Mental Health Co-Pilot</h2>
            <p className="text-zinc-600 mt-1">
              Real-time conversation analysis with EEG brain monitoring
            </p>
          </div>

          <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-3">
              {/* Connection Status */}
              <div className="flex items-center gap-2">
                <div
                  className={`w-3 h-3 rounded-full ${
                    isConnected ? 'bg-green-500 animate-pulse' : 'bg-zinc-300'
                  }`}
                ></div>
                <span className="text-sm text-zinc-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {/* Start/Stop Button */}
              {!isConnected ? (
                <Button
                  onClick={handleStart}
                  disabled={!isEEGConnected}
                  className="bg-green-500 hover:bg-green-600 text-white"
                >
                  Start Session
                </Button>
              ) : (
                <Button
                  onClick={handleStop}
                  className="bg-red-500 hover:bg-red-600 text-white"
                >
                  Stop Session
                </Button>
              )}
            </div>

            {/* Breathing Exercise Button - Below Start/Stop */}
            {isConnected && (
              <Button
                onClick={() => setShowBreathing(true)}
                variant="outline"
                className="border-blue-500 text-blue-500 hover:bg-blue-50"
              >
                🫁 Breathing Exercise
              </Button>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* EEG Warning */}
        {!isEEGConnected && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-sm">
            <strong>⚠️ EEG not connected:</strong> Please connect to Muse device in the EEG
            Dashboard tab first
          </div>
        )}

        {/* Instructions */}
        {!isConnected && isEEGConnected && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-2">How it works:</h3>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>Click "Start Session" to begin AI co-pilot conversation</li>
              <li>Speak naturally into your microphone</li>
              <li>AI analyzes your speech + brain activity in real-time</li>
              <li>Detects incongruence (e.g., saying "I'm fine" with high stress)</li>
              <li>Provides supportive responses and breathing exercises when needed</li>
            </ul>
          </div>
        )}
      </div>

      {/* Main Content Grid */}
      {isConnected && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Interface (2/3 width on large screens) */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-md h-[600px]">
            <ChatInterface
              messages={messages}
              isTyping={isTyping}
              isListening={isListening}
              onSendMessage={sendMessage}
            />
          </div>

          {/* Brain State Panel (1/3 width on large screens) */}
          <div className="lg:col-span-1">
            <BrainStatePanel
              brainState={brainState}
              textFeatures={textFeatures}
              incongruence={incongruence}
              shouldIntervene={shouldIntervene}
            />
          </div>
        </div>
      )}

      {/* Breathing Exercise Modal */}
      <BreathingExercise isOpen={showBreathing} onClose={() => setShowBreathing(false)} />
    </div>
  );
}
