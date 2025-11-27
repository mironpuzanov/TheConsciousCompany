/**
 * AI Co-Pilot TypeScript Types
 * Matches backend WebSocket message types from main.py
 */

export interface BrainState {
  stress: number; // 0-1
  cognitive_load: number; // 0-1
  hr: number; // bpm
  emotion: string; // emotion label from text analysis
  emotion_arousal: number; // 0-1
  alpha: number; // 0-100 (band power percentage)
  beta: number; // 0-100 (band power percentage)
  gamma: number; // 0-100 (band power percentage)
  theta: number; // 0-100 (band power percentage)
  delta: number; // 0-100 (band power percentage)
  emg_intensity: number; // 0-1
}

export interface TextFeatures {
  sentiment: {
    label: 'positive' | 'negative' | 'neutral';
    score: number;
  };
  emotion: {
    label: string;
    score: number;
  };
  topics: string[];
  is_question?: boolean;
  stress_indicators?: Record<string, number>;
  psychological_labels?: Record<string, number>;
}

export interface FusedState {
  brain_state: BrainState;
  text_features: TextFeatures;
  raw_text: string;
  incongruence: boolean;
  should_intervene: boolean;
  timestamp: number;
}

export type CopilotMessageType =
  | 'ai_message'
  | 'transcript'
  | 'state_update'
  | 'ai_typing'
  | 'ai_message_chunk'
  | 'ai_message_complete'
  | 'error'
  | 'reconnecting'
  | 'recording_start'
  | 'recording_end';

export interface CopilotMessage {
  type: CopilotMessageType;
  text?: string;
  brain_state?: BrainState;
  text_features?: TextFeatures;
  incongruence?: boolean;
  should_intervene?: boolean;
  timestamp: number;
  attempt?: number; // For reconnecting messages
  message?: string; // For error messages
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'ai';
  text: string;
  timestamp: number;
  emotion?: string;
  isStreaming?: boolean;
}

export interface CopilotStatus {
  status: 'active' | 'inactive';
  is_active: boolean;
  models_loaded: boolean;
  session_duration?: number;
}
