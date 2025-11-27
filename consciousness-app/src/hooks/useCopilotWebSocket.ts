import { useState, useEffect, useRef, useCallback } from 'react';
import type { CopilotMessage, BrainState, TextFeatures, ChatMessage } from '../types/copilot';

interface UseCopilotWebSocketReturn {
  messages: ChatMessage[];
  brainState: BrainState | null;
  textFeatures: TextFeatures | null;
  incongruence: boolean;
  shouldIntervene: boolean;
  isConnected: boolean;
  isTyping: boolean;
  isListening: boolean;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
  sendMessage: (text: string) => void;
}

export function useCopilotWebSocket(): UseCopilotWebSocketReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [brainState, setBrainState] = useState<BrainState | null>(null);
  const [textFeatures, setTextFeatures] = useState<TextFeatures | null>(null);
  const [incongruence, setIncongruence] = useState(false);
  const [shouldIntervene, setShouldIntervene] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const streamingMessageRef = useRef<string>('');
  const streamingMessageIdRef = useRef<string>('');

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const ws = new WebSocket('ws://localhost:8000/ws/copilot');
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('Copilot WebSocket connected');
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data: CopilotMessage = JSON.parse(event.data);

          switch (data.type) {
            case 'ai_message':
              // Complete AI message
              if (data.text) {
                setMessages((prev) => [
                  ...prev,
                  {
                    id: `ai-${Date.now()}`,
                    type: 'ai',
                    text: data.text,
                    timestamp: data.timestamp,
                  },
                ]);
              }
              setIsTyping(false);
              break;

            case 'transcript':
              // User speech transcription
              if (data.text) {
                setMessages((prev) => [
                  ...prev,
                  {
                    id: `user-${Date.now()}`,
                    type: 'user',
                    text: data.text,
                    timestamp: data.timestamp,
                    emotion: data.text_features?.emotion.label,
                  },
                ]);
              }
              setIsListening(false);
              break;

            case 'state_update':
              // Brain + text state update
              if (data.brain_state) {
                setBrainState(data.brain_state);
              }
              if (data.text_features) {
                setTextFeatures(data.text_features);
              }
              if (data.incongruence !== undefined) {
                setIncongruence(data.incongruence);
              }
              if (data.should_intervene !== undefined) {
                setShouldIntervene(data.should_intervene);
              }
              break;

            case 'ai_typing':
              // AI is generating response
              setIsTyping(true);
              streamingMessageRef.current = '';
              streamingMessageIdRef.current = `ai-${Date.now()}`;
              break;

            case 'ai_message_chunk':
              // Streaming AI response chunk
              if (data.text) {
                streamingMessageRef.current += data.text;

                // Update or add streaming message
                setMessages((prev) => {
                  const existing = prev.find((m) => m.id === streamingMessageIdRef.current);
                  if (existing) {
                    return prev.map((m) =>
                      m.id === streamingMessageIdRef.current
                        ? { ...m, text: streamingMessageRef.current, isStreaming: true }
                        : m
                    );
                  } else {
                    return [
                      ...prev,
                      {
                        id: streamingMessageIdRef.current,
                        type: 'ai',
                        text: streamingMessageRef.current,
                        timestamp: data.timestamp,
                        isStreaming: true,
                      },
                    ];
                  }
                });
              }
              break;

            case 'ai_message_complete':
              // AI response finished streaming
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === streamingMessageIdRef.current
                    ? { ...m, isStreaming: false }
                    : m
                )
              );
              setIsTyping(false);
              streamingMessageRef.current = '';
              streamingMessageIdRef.current = '';
              break;

            case 'error':
              // Error occurred
              console.error('Copilot error:', data.message);
              setError(data.message || 'An error occurred');
              setIsTyping(false);
              break;

            case 'reconnecting':
              // Session reconnecting
              console.log(`Reconnecting... attempt ${data.attempt}`);
              setError(`Reconnecting (attempt ${data.attempt})...`);
              break;

            case 'recording_start':
              // Microphone recording started
              setIsListening(true);
              break;

            case 'recording_end':
              // Microphone recording ended
              setIsListening(false);
              break;

            default:
              console.warn('Unknown message type:', data.type);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
          setError('Failed to parse message');
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error - Please try reconnecting');
        setIsConnected(false);
        setIsTyping(false);
        setIsListening(false);
      };

      ws.onclose = (event) => {
        console.log('Copilot WebSocket disconnected', event.code, event.reason);

        // Show user-friendly error message
        if (event.code === 1006) {
          setError('Connection lost - Click "Start Session" to reconnect');
        } else if (event.code !== 1000) {
          setError(`Disconnected (code: ${event.code}) - Click "Start Session" to reconnect`);
        }

        setIsConnected(false);
        setIsTyping(false);
        setIsListening(false);
      };
    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError('Failed to connect');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsTyping(false);
    setIsListening(false);
  }, []);

  const sendMessage = useCallback((text: string) => {
    console.log('[DEBUG] sendMessage called with:', text);
    console.log('[DEBUG] WebSocket state:', wsRef.current?.readyState,
                'OPEN =', WebSocket.OPEN,
                'CONNECTING =', WebSocket.CONNECTING,
                'CLOSING =', WebSocket.CLOSING,
                'CLOSED =', WebSocket.CLOSED);

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('Cannot send message: WebSocket not connected');
      console.error('WebSocket exists?', !!wsRef.current);
      console.error('Ready state:', wsRef.current?.readyState);
      return;
    }

    try {
      // Add user message to chat immediately
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        type: 'user',
        text,
        timestamp: Date.now() / 1000,
      };
      setMessages((prev) => [...prev, userMessage]);

      // Send to backend
      const payload = {
        type: 'user_text',
        text,
        timestamp: Date.now() / 1000,
      };
      console.log('[DEBUG] Sending WebSocket message:', payload);
      wsRef.current.send(JSON.stringify(payload));
      console.log('[DEBUG] Message sent successfully');
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message');
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
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
  };
}
