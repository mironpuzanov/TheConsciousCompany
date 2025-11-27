import { useState, useCallback, useRef, useEffect } from 'react';
import { MuseClient } from 'muse-js';
import { ConnectionStatus } from '../types/muse';
import type { EEGReading, MuseDeviceInfo } from '../types/muse';

const HISTORY_LENGTH = 256; // Keep last 1 second of data (256 Hz sampling rate)

export const useMuse = () => {
  const [status, setStatus] = useState<ConnectionStatus>(ConnectionStatus.DISCONNECTED);
  const [deviceInfo, setDeviceInfo] = useState<MuseDeviceInfo | null>(null);
  const [eegData, setEegData] = useState<EEGReading | null>(null);
  const [eegHistory, setEegHistory] = useState<EEGReading[]>([]);
  const [error, setError] = useState<string | null>(null);

  const clientRef = useRef<MuseClient | null>(null);

  const connect = useCallback(async () => {
    try {
      setStatus(ConnectionStatus.CONNECTING);
      setError(null);

      const client = new MuseClient();
      await client.connect();
      await client.start();

      clientRef.current = client;

      setDeviceInfo({
        name: client.deviceName || 'Muse',
        connected: true,
      });

      setStatus(ConnectionStatus.CONNECTED);

      // Buffer to collect readings from all 4 electrodes
      const channelBuffer: number[] = [0, 0, 0, 0];

      // Subscribe to EEG readings
      client.eegReadings.subscribe({
        next: (reading) => {
          const electrode = reading.electrode;
          const value = reading.samples[0] || 0;

          channelBuffer[electrode] = value;

          const newReading: EEGReading = {
            timestamp: Date.now(),
            data: [...channelBuffer],
          };

          setEegData(newReading);

          // Add to history and keep last HISTORY_LENGTH readings
          setEegHistory(prev => {
            const updated = [...prev, newReading];
            return updated.slice(-HISTORY_LENGTH);
          });
        },
      });

    } catch (err) {
      setStatus(ConnectionStatus.ERROR);
      setError(err instanceof Error ? err.message : 'Failed to connect to Muse');
      console.error('❌ Muse connection error:', err);
    }
  }, []);

  const disconnect = useCallback(async () => {
    if (clientRef.current) {
      await clientRef.current.disconnect();
      clientRef.current = null;
      setStatus(ConnectionStatus.DISCONNECTED);
      setDeviceInfo(null);
      setEegData(null);
      setEegHistory([]);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (clientRef.current) {
        clientRef.current.disconnect();
      }
    };
  }, []);

  return {
    status,
    deviceInfo,
    eegData,
    eegHistory,
    error,
    connect,
    disconnect,
  };
};
