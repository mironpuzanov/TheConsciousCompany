export interface EEGReading {
  timestamp: number;
  data: number[]; // 4 channels: TP9, AF7, AF8, TP10
}

export interface MuseDeviceInfo {
  name: string;
  connected: boolean;
  batteryLevel?: number;
}

export interface BandPowers {
  delta: number;
  theta: number;
  alpha: number;
  beta: number;
  gamma: number;
}

export interface HRVMetrics {
  heart_rate: number;
  hrv_rmssd: number;
  hrv_sdnn: number;
  valid: boolean;
}

export interface ArtifactInfo {
  has_artifact: boolean;
  artifact_type: string;
  artifact_details?: {
    eye_blink?: boolean;
    muscle?: boolean;
    motion?: boolean;
    em_interference?: boolean;
    poor_contact?: boolean;
    statistical?: boolean;
  };
}

export enum ConnectionStatus {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  ERROR = 'error',
}
