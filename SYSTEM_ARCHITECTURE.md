# Consciousness OS - Complete System Architecture

## Overview

Real-time EEG + AI mental health co-pilot system combining Muse 2 brain monitoring with GPT-5 conversation analysis.

---

## Full Stack Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Meditation  │  │ EEG Monitor  │  │  AI Co-Pilot (NEW!)      │  │
│  │     Tab      │  │     Tab      │  │                          │  │
│  │              │  │              │  │  - Chat Interface        │  │
│  │  - Guided    │  │  - Live EEG  │  │  - Brain State Panel     │  │
│  │  - Timer     │  │  - Band Pwr  │  │  - Incongruence Alert    │  │
│  │  - History   │  │  - Artifacts │  │  - Breathing Exercise    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│                                                                    │
│                    WebSocket: /ws  |  /ws/copilot                  │
└────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/WS
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND (Python FastAPI)                         │
│                        main.py (Port 8000)                          │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    EEG PROCESSING PIPELINE                     │ │
│  │                                                                │ │
│  │  Muse LSL Stream (256 Hz)                                      │ │
│  │       ↓                                                        │ │
│  │  Signal Processor (MNE + ICA artifact removal)                 │ │
│  │       ↓                                                        │ │
│  │  Band Powers (delta, theta, alpha, beta, gamma)                │ │
│  │       ↓                                                        │ │
│  │  Brain State Classification (meditation, focus, stress, etc.)  │ │
│  │       ↓                                                        │ │
│  │  State Smoother (30-second window)                             │ │
│  │       ↓                                                        │ │
│  │  WebSocket /ws → Frontend (20 Hz)                              │ │
│  │       ↓                                                        │ │
│  │  Brain State → copilot_session.update_brain_state() (1 Hz)     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                 AI CO-PILOT PIPELINE (NEW!)                    │ │
│  │                    copilot_session.py                          │ │
│  │                                                                │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │ 1. AUDIO RECORDER (audio_recorder.py)                    │  │ │
│  │  │    - Microphone → 16 kHz chunks (2 sec)                  │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                            ↓                                   │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │ 2. WHISPER TRANSCRIBER (whisper_transcriber.py)          │  │ │
│  │  │    - faster-whisper (base model)                         │  │ │
│  │  │    - Voice activity detection                            │  │ │
│  │  │    - Output: text + confidence                           │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                            ↓                                   │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │ 3. ML ANALYZER (ml_analyzer.py)                          │  │ │
│  │  │    - ExpertRunner (from conversation_analyzer)           │  │ │
│  │  │    - Emotions: joy, sadness, anger, fear, anxiety        │  │ │
│  │  │    - Sentiment: positive/negative/neutral                │  │ │
│  │  │    - Psychological labels: stress, avoidance, etc.       │  │ │
│  │  │    - Topics: work, family, health                        │  │ │
│  │  │    - NER triggers                                        │  │ │
│  │  │    - Latency: ~100ms                                     │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                            ↓                                   │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │ 4. FUSION ENGINE (fusion_engine.py)                      │  │ │
│  │  │    - Combines: brain_state + text_features               │  │ │
│  │  │    - Detects incongruence:                               │  │ │
│  │  │      * Says "I'm fine" but stress = 0.8                  │  │ │
│  │  │    - Intervention triggers:                              │  │ │
│  │  │      * Stress >0.7                                       │  │ │
│  │  │      * HR >90 bpm                                        │  │ │
│  │  │      * Negative emotions (fear, anxiety)                 │  │ │
│  │  │      * Incongruence detected                             │  │ │
│  │  │    - Context window: 60 seconds                          │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                            ↓                                   │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │ 5. GPT-5 COPILOT (gpt5_copilot.py)                       │  │ │
│  │  │    - Therapeutic system prompt                           │  │ │
│  │  │    - Context-aware (60-sec window)                       │  │ │
│  │  │    - Streaming responses                                 │  │ │
│  │  │    - Frequency: Every 10-15 seconds                      │  │ │
│  │  │    - Crisis detection (suicide, self-harm keywords)      │  │ │
│  │  │    - Cost: ~$0.0005 per decision                         │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                            ↓                                   │ │
│  │  WebSocket /ws/copilot → Frontend                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   SESSION RECORDING                            │ │
│  │  - EEG data (1 Hz): band powers, brain state, artifacts        │ │
│  │  - HRV data: heart rate, RMSSD, SDNN                           │ │
│  │  - Copilot data: conversation, brain+text fusion               │ │
│  │  - Export: sessions/<type>/session_<timestamp>/                │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
                                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│                          HARDWARE LAYER                              │
│                                                                      │
│  ┌──────────────────┐         ┌─────────────────────────────────┐    │
│  │   Muse 2 EEG     │         │  Computer Microphone            │    │
│  │                  │         │                                 │    │
│  │  - 4 channels    │         │  - 16 kHz sampling              │    │
│  │  - 256 Hz        │         │  - Default system mic           │    │
│  │  - PPG (64 Hz)   │         │  - pyaudio capture              │    │
│  │  - ACC/GYRO      │         │                                 │    │
│  │                  │         │                                 │    │
│  │  via muselsl     │         │  via audio_recorder.py          │    │
│  └──────────────────┘         └─────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow (Complete)

### 1. EEG Data Flow (Every 1 Second)

```
Muse 2 Headband
    ↓
muselsl stream (Bluetooth → LSL)
    ↓
main.py: MuseStreamer.stream_data()
    ↓
process_sensor_data()
    ├─→ MNE Processing (ICA artifact removal)
    ├─→ Band Power Calculation (delta, theta, alpha, beta, gamma)
    ├─→ Brain State Classification
    ├─→ State Smoothing (30-second window)
    ├─→ WebSocket /ws → Frontend (EEG Monitor Tab)
    └─→ copilot_session.update_brain_state() → AI Co-Pilot
```

### 2. AI Co-Pilot Flow (Real-Time)

```
User Speaks
    ↓
audio_recorder.py (microphone, 16 kHz)
    ↓
whisper_transcriber.py (faster-whisper, 1-2 sec)
    ↓
ml_analyzer.py (ExpertRunner, 100ms)
    ├─→ Sentiment: positive/negative/neutral
    ├─→ Emotion: joy, sadness, anger, fear, anxiety
    ├─→ Topics: work, family, health, stress
    ├─→ Psychological labels: avoidance, self-criticism, etc.
    └─→ Question detection
    ↓
fusion_engine.py
    ├─→ Combine: text_features + brain_state
    ├─→ Detect incongruence
    ├─→ Trigger intervention if needed
    └─→ 60-second context window
    ↓
gpt5_copilot.py (every 10-15 sec)
    ├─→ Build context-aware prompt
    ├─→ Call GPT-5 API (streaming)
    ├─→ Generate empathetic response
    └─→ Crisis detection
    ↓
WebSocket /ws/copilot → Frontend (AI Co-Pilot Tab)
```

### 3. Incongruence Detection Example

```
User says: "I'm fine, just a bit tired"
    ↓
ML Analyzer detects:
    - Sentiment: positive (0.6)
    - Emotion: neutral (0.5)
    - Topics: [general]
    ↓
Brain State from EEG:
    - Stress: 0.85 (HIGH!)
    - HR: 95 bpm (ELEVATED!)
    - Beta: 60% (high cognitive load)
    ↓
Fusion Engine:
    - Incongruence: TRUE (text says "fine" but brain stressed)
    - should_intervene: TRUE
    - intervention_reason: "high stress (0.8), elevated HR (95 bpm), incongruence"
    ↓
GPT-5 Response:
    "I hear that you're tired. I'm noticing your stress levels are quite
     elevated right now, and your heart rate jumped to 95. What's really
     going on?"
```

---

## API Endpoints Summary

### EEG Endpoints (Existing)
- `POST /api/connect` - Connect to Muse via LSL
- `POST /api/disconnect` - Disconnect from Muse
- `GET /api/device-info` - Get Muse device info
- `WebSocket /ws` - Real-time EEG data stream

### Session Recording (Existing)
- `POST /api/session/start` - Start recording session
- `POST /api/session/stop` - Stop and save session
- `GET /api/session/status` - Get current recording status
- `POST /api/session/marker` - Add marker to session
- `GET /api/sessions` - List all sessions
- `GET /api/sessions/{id}` - Load specific session
- `POST /api/sessions/{id}/rename` - Rename session
- `POST /api/sessions/{id}/update` - Update session metadata

### AI Co-Pilot Endpoints (NEW - Phase 2)
- `POST /api/copilot/start` - Initialize AI Co-Pilot
- `POST /api/copilot/stop` - Stop AI Co-Pilot and export
- `GET /api/copilot/status` - Get copilot status
- `WebSocket /ws/copilot` - Real-time conversation stream

---

## Technology Stack

### Hardware
- **Muse 2 EEG Headband**: 4-channel EEG (TP9, AF7, AF8, TP10), PPG, ACC/GYRO
- **Computer Microphone**: 16 kHz audio recording

### Backend
- **Python 3.9+**: Main language
- **FastAPI**: Web server + WebSocket
- **muselsl**: Muse device streaming via LSL
- **MNE-Python**: EEG signal processing + ICA
- **faster-whisper**: Speech-to-text transcription
- **ExpertRunner**: ML model ensemble (from conversation_analyzer)
- **OpenAI GPT-5**: AI response generation

### ML Models (Local)
- **Emotion Models**:
  - emotion_distilroberta
  - emotion_distilbert
  - twitter_roberta_emotion
- **Stress Models**:
  - beto_emotion
  - hatexplain
- **Psychological Labels**:
  - zero_shot_psych (avoidance, self-criticism, reflection, decisiveness, support-seeking, stress)
- **NER**:
  - bert-base-NER

### Frontend (Phase 3)
- **React**: UI framework
- **WebSocket API**: Real-time communication
- **Chart.js**: Brain wave visualization

---

## Cost Analysis

### AI Co-Pilot (Per 10-Minute Session)
- **GPT-5 Decisions**: ~40
- **Tokens/Decision**: ~150
- **Total Tokens**: 6,000
- **Cost**: **$0.18/session**

### Monthly Usage (1 session/day)
- **Sessions**: 30
- **Total Cost**: **$5.40/month**

### Comparison
- **All-GPT Approach**: $0.72/hour = $0.12/min × 10 = **$1.20/session**
- **Hybrid (Local ML + GPT-5)**: **$0.18/session**
- **Savings**: 6× cheaper!

---

## Performance Metrics

### Latency
- **EEG Processing**: 1 second (batch processing)
- **Audio → Whisper**: 1-2 seconds
- **ML Analysis**: 100-200ms
- **Fusion**: <5ms
- **GPT-5 Response**: 1-3 seconds (streaming)
- **Total (Speech → AI Response)**: **3-5 seconds**

### Throughput
- **EEG Data**: 256 Hz raw → 1 Hz processed
- **Audio Data**: 16 kHz → 0.5 Hz (2-second chunks)
- **WebSocket Updates**:
  - EEG: 20 Hz (throttled)
  - Copilot: Real-time streaming

### Resource Usage
- **Memory**: ~2GB (with all ML models loaded)
- **CPU**: ~30% (2 cores)
- **Network**: <1 KB/s (WebSocket)

---

## File Structure

```
Consciousness OS/
├── backend/
│   ├── main.py                    # FastAPI server (EEG + Copilot endpoints)
│   ├── muse_stream.py             # Muse LSL streaming
│   ├── signal_processor.py        # Band power calculation
│   ├── mne_processor.py           # MNE + ICA artifact removal
│   ├── state_smoother.py          # 30-second smoothing
│   ├── mental_state_interpreter.py # Brain state classification
│   ├── session_recorder.py        # Session data export
│   │
│   ├── audio_recorder.py          # NEW: Microphone recording
│   ├── whisper_transcriber.py     # NEW: Speech-to-text
│   ├── ml_analyzer.py             # NEW: Text analysis (ExpertRunner)
│   ├── fusion_engine.py           # NEW: Brain + text fusion
│   ├── gpt5_copilot.py            # NEW: GPT-5 response generation
│   ├── copilot_session.py         # NEW: Session orchestrator
│   │
│   ├── requirements.txt           # Main dependencies
│   └── requirements_copilot.txt   # NEW: Copilot dependencies
│
├── conversation_analyzer/         # ML model repository
│   ├── backend/
│   │   └── expert_runner.py       # Model ensemble
│   ├── core/
│   │   └── preprocess.py          # Transcript processing
│   └── .env.local                 # OPENAI_API_KEY
│
├── frontend/                      # React UI (Phase 3)
│   └── src/
│       └── components/
│           └── AICopilot/         # NEW: AI Co-Pilot tab
│
├── sessions/                      # Recorded sessions
│   ├── eeg/                       # EEG recordings
│   └── copilot/                   # NEW: Copilot conversations
│
└── docs/
    ├── AI_COPILOT_IMPLEMENTATION_PLAN.md
    ├── PHASE1_COMPLETE.md
    ├── PHASE1_FINAL_REVIEW.md
    ├── PHASE2_COMPLETE.md
    ├── PHASE2_SUMMARY.md
    └── SYSTEM_ARCHITECTURE.md     # This file
```

---

## Development Status

### ✅ Phase 1 Complete (Backend Core)
- [x] Audio Recorder
- [x] Whisper Transcriber
- [x] ML Analyzer (ExpertRunner integration)
- [x] Fusion Engine
- [x] GPT-5 Copilot
- [x] Session Coordinator

### ✅ Phase 2 Complete (API Integration)
- [x] Copilot imports in main.py
- [x] Real-time brain state updates
- [x] API endpoints: start, stop, status
- [x] WebSocket endpoint /ws/copilot
- [x] Session export

### ✅ Phase 3 In Progress (Frontend UI)
- [x] "AI Co-Pilot" tab in React
- [x] Chat interface
- [x] Brain state visualization panel
- [x] Breathing exercise overlay
- [x] WebSocket connection

### 📋 Phase 4 Planned (Testing & Polish)
- [x] End-to-end testing with real EEG + text
- [x] Performance optimization
- [x] Bug fixes
- [x] User testing

---

**Last Updated**: 2025-11-23
**System Version**: 2.0 (with AI Co-Pilot)
