import { useState, useCallback, useRef, useEffect } from 'react';
import { ConnectionStatus } from '../types/muse';
import type { EEGReading, MuseDeviceInfo } from '../types/muse';

const WS_URL = 'ws://localhost:8000/ws';
const API_BASE = 'http://localhost:8000';

const HISTORY_LENGTH = 128; // Keep last 0.5 seconds of data for waveform (reduced for performance)
const EEG_UPDATE_THROTTLE_MS = 50; // Update UI at 20 Hz instead of 256 Hz
const BAND_POWER_HISTORY_LENGTH = 60; // Keep 60 seconds of band power data

interface WebSocketMessage {
  type: 'eeg_data' | 'band_powers';
  timestamp: number;
  data?: number[]; // For eeg_data
  heart_rate?: number;
  hrv_rmssd?: number;
  hrv_sdnn?: number;
  band_powers?: {
    delta: number;
    theta: number;
    alpha: number;
    beta: number;
    gamma: number;
  };
  brain_state?: string;
  has_artifact?: boolean;
  artifact_type?: string;
  artifact_details?: {
    eye_blink?: boolean;
    muscle?: boolean;
    motion?: boolean;
    em_interference?: boolean;
    poor_contact?: boolean;
    statistical?: boolean;
  };
  signal_quality?: {
    mean: number;
    std: number;
  };
}

interface BandPowers {
  delta: number;
  theta: number;
  alpha: number;
  beta: number;
  gamma: number;
}

export const useWebSocket = () => {
  const [status, setStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  const [deviceInfo, setDeviceInfo] = useState<MuseDeviceInfo | null>(null);
  const [eegData, setEegData] = useState<EEGReading | null>(null);
  const [eegHistory, setEegHistory] = useState<EEGReading[]>([]);
  const [bandPowers, setBandPowers] = useState<BandPowers | null>(null);
  const [bandPowerHistory, setBandPowerHistory] = useState<Array<BandPowers & { timestamp: number }>>([]);
  const [brainState, setBrainState] = useState<string>('');
  const [heartRate, setHeartRate] = useState<number>(0);
  const [hrvRmssd, setHrvRmssd] = useState<number>(0);
  const [hrvSdnn, setHrvSdnn] = useState<number>(0);
  const [icaStatus, setIcaStatus] = useState<{ fitted: boolean; progress: number } | null>(null);
  const [artifactInfo, setArtifactInfo] = useState<{
    has_artifact: boolean;
    artifact_type: string;
    artifact_details?: any;
  } | null>(null);
  const [hrvInterpretation, setHrvInterpretation] = useState<any>(null);
  const [postureInterpretation, setPostureInterpretation] = useState<any>(null);
  const [bandChangeInterpretation, setBandChangeInterpretation] = useState<string>('');
  const [comprehensiveState, setComprehensiveState] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const shouldReconnect = useRef(true);
  const lastEegUpdateRef = useRef<number>(0);
  const pendingEegDataRef = useRef<EEGReading | null>(null);

  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setStatus(ConnectionStatus.CONNECTED);
        setError(null);

        // Send ping to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          } else {
            clearInterval(pingInterval);
          }
        }, 30000); // Ping every 30 seconds

        // Store interval ID for cleanup
        (ws as any).pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === 'eeg_data' && message.data) {
            const reading: EEGReading = {
              timestamp: message.timestamp * 1000, // Convert to milliseconds
              data: message.data,
            };

            // Store the latest reading
            pendingEegDataRef.current = reading;

            // Update HRV metrics if available
            if (message.heart_rate !== undefined) {
              setHeartRate(message.heart_rate);
            }
            if (message.hrv_rmssd !== undefined) {
              setHrvRmssd(message.hrv_rmssd);
            }

            // Throttle UI updates to avoid overwhelming React
            const now = Date.now();
            if (now - lastEegUpdateRef.current >= EEG_UPDATE_THROTTLE_MS) {
              lastEegUpdateRef.current = now;
              
              // Update state with throttled frequency
              setEegData(reading);

              // Add to history and keep last HISTORY_LENGTH readings
              setEegHistory(prev => {
                const updated = [...prev, reading];
                return updated.slice(-HISTORY_LENGTH);
              });
            }
          } else if (message.type === 'band_powers') {
            // Band powers come at 1 Hz, so no throttling needed
            if (message.band_powers) {
              setBandPowers(message.band_powers);
              // Add to history for graph
              setBandPowerHistory(prev => {
                const newEntry = { ...message.band_powers!, timestamp: message.timestamp };
                const updated = [...prev, newEntry];
                return updated.slice(-BAND_POWER_HISTORY_LENGTH);
              });
            }
            if (message.brain_state) {
              setBrainState(message.brain_state);
            }
            // Update HRV metrics
            if (message.heart_rate !== undefined) {
              setHeartRate(message.heart_rate);
            }
            if (message.hrv_rmssd !== undefined) {
              setHrvRmssd(message.hrv_rmssd);
            }
            if (message.hrv_sdnn !== undefined) {
              setHrvSdnn(message.hrv_sdnn);
            }
            // Update ICA status
            if ((message as any).ica_status) {
              setIcaStatus((message as any).ica_status);
            }
            // Update artifact info
            if (message.has_artifact !== undefined || (message as any).bad_channels) {
              const msg = message as any;
              setArtifactInfo({
                has_artifact: message.has_artifact || false,
                artifact_type: message.artifact_type || 'clean',
                artifact_details: {
                  ...(msg.artifact_details || {}),
                  bad_channels: msg.bad_channels || [],
                  channel_names: msg.artifact_details?.channel_names || ['TP9', 'AF7', 'AF8', 'TP10'],
                },
              });
            }
            // Update mental state interpretations
            if ((message as any).hrv_interpretation) {
              setHrvInterpretation((message as any).hrv_interpretation);
            }
            if ((message as any).posture_interpretation) {
              setPostureInterpretation((message as any).posture_interpretation);
            }
            if ((message as any).band_change_interpretation) {
              setBandChangeInterpretation((message as any).band_change_interpretation);
            }
            if ((message as any).comprehensive_state) {
              setComprehensiveState((message as any).comprehensive_state);
            }
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        const pingInterval = (ws as any).pingInterval;
        if (pingInterval) {
          clearInterval(pingInterval);
        }

        if (shouldReconnect.current && status !== ConnectionStatus.DISCONNECTED) {
          // Attempt to reconnect after 2 seconds
          reconnectTimeoutRef.current = window.setTimeout(() => {
            console.log('Attempting to reconnect...');
            connectWebSocket();
          }, 2000);
        }
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to connect to backend');
      setStatus(ConnectionStatus.ERROR);
    }
  }, [status]);

  const connect = useCallback(async () => {
    try {
      setStatus(ConnectionStatus.CONNECTING);
      setError(null);

      // First, connect to Muse via API
      const connectResponse = await fetch(`${API_BASE}/api/connect`, {
        method: 'POST',
      });

      if (!connectResponse.ok) {
        const errorData = await connectResponse.json();
        throw new Error(errorData.message || 'Failed to connect to Muse');
      }

      const connectData = await connectResponse.json();

      if (connectData.status === 'error') {
        throw new Error(connectData.message || 'Failed to connect to Muse');
      }

      // Update device info
      if (connectData.device_info) {
        setDeviceInfo({
          name: connectData.device_info.name || 'Muse',
          connected: true,
        });
      }

      // Then connect WebSocket
      connectWebSocket();

    } catch (err) {
      setStatus(ConnectionStatus.ERROR);
      setError(err instanceof Error ? err.message : 'Failed to connect to Muse');
      console.error('❌ Connection error:', err);
    }
  }, [connectWebSocket]);

  const disconnect = useCallback(async () => {
    shouldReconnect.current = false;

    // Disconnect from Muse
    try {
      await fetch(`${API_BASE}/api/disconnect`, {
        method: 'POST',
      });
    } catch (err) {
      console.error('Error disconnecting from Muse:', err);
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setStatus(ConnectionStatus.DISCONNECTED);
    setDeviceInfo(null);
    setEegData(null);
    setEegHistory([]);
    setBandPowers(null);
    setBandPowerHistory([]);
    setBrainState('');
    setHeartRate(0);
    setHrvRmssd(0);
    setHrvSdnn(0);
    setIcaStatus(null);
    setArtifactInfo(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shouldReconnect.current = false;
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    status,
    deviceInfo,
    eegData,
    eegHistory,
    bandPowers,
    bandPowerHistory,
    brainState,
    heartRate,
    hrvRmssd,
    hrvSdnn,
    icaStatus,
    artifactInfo,
    hrvInterpretation,
    postureInterpretation,
    bandChangeInterpretation,
    comprehensiveState,
    error,
    connect,
    disconnect,
  };
};

