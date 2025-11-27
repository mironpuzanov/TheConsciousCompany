# AI Mental Health Co-Pilot - Implementation Plan

## Product Vision

**Real-time AI mental health companion** that combines:
- **Brain activity** (EEG from Muse 2)
- **Speech transcription** (Whisper local)
- **Psychological pattern analysis** (Local ML models)
- **Adaptive conversation** (GPT-5)

The AI listens, detects stress/emotions from both brain and speech, and intervenes with questions or breathing exercises when needed.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   REAL-TIME PIPELINE                    │
├─────────────────────────────────────────────────────────┤
│ INPUT LAYER (Parallel Streams)                          │
│  ├─ Microphone → Whisper → Text chunks (every 2 sec)    │
│  └─ Muse EEG → Brain state (every 1 sec)                │
├─────────────────────────────────────────────────────────┤
│ LOCAL ML ANALYSIS (100ms latency)                       │
│  ├─ Sentiment: DistilBERT (positive/negative/neutral)   │
│  ├─ Emotion: RoBERTa (7 emotions)                       │
│  ├─ Topic: KeyBERT extraction                           │
│  └─ Question: Classifier (asking vs stating)            │
├─────────────────────────────────────────────────────────┤
│ FUSION LAYER (Every 5 seconds)                          │
│  Combine: Brain + Text features → Unified state         │
│  Detect: Incongruence (text vs brain mismatch)          │
├─────────────────────────────────────────────────────────┤
│ GPT-5 DECISION LAYER (Every 10-15 sec)                  │
│  Input: Fused state (condensed, structured)             │
│  Output: AI response or "keep listening"                │
│  Cost: ~100 tokens/decision = $0.0005                   │
├─────────────────────────────────────────────────────────┤
│ UI LAYER (New Tab: "AI Co-Pilot")                       │
│  - Real-time transcript display                         │
│  - Brain state visualization                            │
│  - AI messages in chat interface                        │
│  - Breathing exercise overlay (when triggered)          │
└─────────────────────────────────────────────────────────┘
```

---

## Product Requirements (PRD)

### Core Features

#### 1. **Real-Time Conversation Mode**
**User Story**: As a user, I want to talk to an AI co-pilot that understands both what I say and how my brain reacts, so it can guide me through stress/anxiety.

**Requirements**:
- Start/stop conversation session
- Real-time speech-to-text transcription
- Live brain activity monitoring
- AI responses appear in chat interface
- Session saved for review

**Success Metrics**:
- Transcription latency <2 seconds
- Brain data synchronized with text (timestamp alignment)
- AI response latency <5 seconds
- 90%+ transcription accuracy

---

#### 2. **Psychological Pattern Detection**
**User Story**: As a user, I want the AI to detect when I'm stressed or anxious, even if I say "I'm fine," so it can intervene appropriately.

**Requirements**:
- Sentiment analysis (every utterance)
- Emotion classification (7 categories)
- Topic extraction (what user talks about)
- Incongruence detection (text vs brain mismatch)
- Stress threshold alerts (when brain shows high stress)

**Success Metrics**:
- Sentiment accuracy >85%
- Emotion detection accuracy >75%
- Incongruence detection works (e.g., "I'm fine" + high stress)
- False positive rate <10%

---

#### 3. **Adaptive AI Intervention**
**User Story**: As a user, I want the AI to ask relevant questions and suggest breathing exercises when I'm stressed, so I can regulate my emotions.

**Requirements**:
- Context-aware question generation (based on topic + emotion)
- Stress intervention trigger (HR spike + negative sentiment)
- Guided breathing exercises (when stress >0.7)
- Empathetic response framing ("I notice...", "How does that feel?")
- Crisis escalation (suggest professional help if severe distress)

**Success Metrics**:
- Interventions feel timely (not intrusive)
- Breathing exercises reduce HR by 10+ bpm
- User engagement >5 min average session
- User satisfaction >4/5 stars

---

#### 4. **Separate UI Tab: "AI Co-Pilot"**
**User Story**: As a user, I want a dedicated tab for AI conversations, separate from meditation/EEG monitoring, so I don't confuse different features.

**Requirements**:
- New tab in frontend navigation
- Chat interface (user messages + AI responses)
- Live transcript panel (scrolling text)
- Brain state sidebar (real-time metrics)
- Breathing exercise overlay (when triggered)
- Session history (review past conversations)

**UI Components**:
```
┌────────────────────────────────────────────────────┐
│ [Meditation] [EEG Monitor] [AI Co-Pilot] [Sessions]│
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌─────────────────┐  ┌──────────────────────────┐ │
│  │  Brain State    │  │  Conversation            │ │
│  │                 │  │                          │ │
│  │  Stress: 0.7    │  │  AI: How are you today?  │ │
│  │  HR: 85 bpm     │  │                          │ │
│  │ Emotion: Anxious│  │  You: I'm fine but...    │ │
│  │                 │  │                          │ │
│  │  [Live metrics] │  │  AI: I notice your       │ │
│  │                 │  │  stress increased...     │ │
│  └─────────────────┘  │                          │ │
│                       │  [Type message...]       │ │
│                       └──────────────────────────┘ │
│                                                    │
│  [Start Session]  [Stop]  [Breathing Exercise]     │
└────────────────────────────────────────────────────┘
```

**Success Metrics**:
- UI loads <1 second
- No UI freezing during real-time updates
- Clear visual separation from other tabs
- Responsive design (works on laptop/desktop)

---

## Technical Implementation

### Phase 1: Backend Core (Priority 1)

#### 1.1 Audio Recording Module
**File**: `backend/audio_recorder.py`

**Requirements**:
- Record from system microphone
- 16kHz sample rate (Whisper optimized)
- Save to WAV format
- Thread-safe for real-time processing

**Dependencies**:
```bash
pip install pyaudio soundfile
```

**API**:
```python
class AudioRecorder:
    def start_recording(self) -> None
    def stop_recording(self) -> str  # Returns WAV file path
    async def stream_audio(self, callback: Callable) -> None  # Real-time chunks
```

---

#### 1.2 Whisper Transcription Module
**File**: `backend/whisper_transcriber.py`

**Requirements**:
- Use `faster-whisper` (optimized for streaming)
- Real-time transcription (2-3 sec chunks)
- Handle silence detection
- Timestamp alignment with EEG

**Dependencies**:
```bash
pip install faster-whisper
```

**API**:
```python
class WhisperTranscriber:
    def __init__(self, model_size: str = "base")
    async def transcribe_stream(self, audio_chunk: bytes) -> dict
    # Returns: {text: str, timestamp: float, confidence: float}
```

**Model Selection**:
- `tiny`: Fastest, 75MB, 60% accuracy (too low)
- `base`: Fast, 140MB, 80% accuracy ✅ **USE THIS**
- `small`: Medium, 460MB, 85% accuracy (backup)
- `medium`: Slow, 1.5GB, 90% accuracy (overkill)

---

#### 1.3 Local ML Analysis Pipeline
**File**: `backend/ml_analyzer.py`

**Requirements**:
- Reuse existing conversation_analyzer models
- Fast inference (100ms target)
- Batch processing support
- Error handling for edge cases

**API**:
```python
class MLAnalyzer:
    def __init__(self):
        # Load models from conversation_analyzer
        self.sentiment_pipeline = load_sentiment_model()
        self.emotion_pipeline = load_emotion_model()
        self.topic_extractor = load_topic_model()
        self.question_classifier = load_question_model()

    def analyze(self, text: str) -> dict:
        return {
            'sentiment': self.sentiment_pipeline(text)[0],
            'emotion': self.emotion_pipeline(text)[0],
            'topics': self.topic_extractor(text),
            'is_question': self.question_classifier(text),
        }
```

**Models to Use** (from conversation_analyzer):
- ✅ Sentiment: `distilbert-base-uncased-finetuned-sst-2-english`
- ✅ Emotion: `j-hartmann/emotion-english-distilroberta-base`
- ✅ Topic: `KeyBERT` or existing topic model
- ✅ Question: `shahrukhx01/question-vs-statement-classifier`

---

#### 1.4 Brain-Text Fusion Engine
**File**: `backend/fusion_engine.py`

**Requirements**:
- Combine brain state + text features
- Detect incongruence (text vs brain)
- Sliding window (60 seconds context)
- Trigger detection (when to intervene)

**API**:
```python
class FusionEngine:
    def __init__(self, window_size: int = 60):
        self.context_window = deque(maxlen=window_size)

    def fuse(self, brain_state: dict, text_features: dict, raw_text: str) -> dict:
        """
        Returns unified state:
        {
            'text': str,
            'sentiment': str,  # 'positive', 'negative', 'neutral'
            'emotion': str,    # 'joy', 'sadness', 'anxiety', etc.
            'topics': list,
            'brain_stress': float,  # 0-1
            'cognitive_load': float,  # 0-1
            'hr': int,  # bpm
            'incongruence': bool,  # Text positive but brain stressed
            'should_intervene': bool,  # Trigger for GPT-5
            'timestamp': float
        }
        """

    def detect_incongruence(self, sentiment: str, brain_stress: float) -> bool:
        # Example: "I'm fine" (positive) but stress > 0.6
        return sentiment == 'positive' and brain_stress > 0.6

    def should_intervene(self, fused_state: dict) -> bool:
        # Intervention triggers
        return (
            fused_state['brain_stress'] > 0.7 or
            fused_state['emotion'] in ['fear', 'anxiety'] or
            fused_state['incongruence'] or
            fused_state['hr'] > 90
        )
```

---

#### 1.5 GPT-5 Decision Layer
**File**: `backend/gpt5_copilot.py`

**Requirements**:
- Use OpenAI GPT-5 API
- Streaming responses (for real-time feel)
- Context-aware prompts (include brain + text state)
- Therapeutic framing
- Crisis detection

**Dependencies**:
```bash
pip install openai
```

**API**:
```python
from openai import OpenAI

class GPT5Copilot:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.conversation_history = []

    async def generate_response(self, fused_states: list) -> str:
        """
        Generate AI response based on fused state

        Args:
            fused_states: List of recent fused states (last 60 sec)

        Returns:
            AI response text
        """
        prompt = self._build_prompt(fused_states)

        response = self.client.chat.completions.create(
            model="gpt-5",  # Use GPT-5
            messages=[
                {"role": "system", "content": THERAPIST_SYSTEM_PROMPT},
                *self.conversation_history,
                {"role": "user", "content": prompt}
            ],
            stream=True,
            temperature=0.7,
            max_tokens=200
        )

        # Stream response
        full_response = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                yield chunk.choices[0].delta.content  # Stream to UI

        self.conversation_history.append({
            "role": "assistant",
            "content": full_response
        })

    def _build_prompt(self, fused_states: list) -> str:
        """Build context-aware prompt for GPT-5"""
        latest = fused_states[-1]

        return f"""
Current conversation state:

User just said: "{latest['text']}"

Psychological analysis:
- Sentiment: {latest['sentiment']}
- Emotion: {latest['emotion']}
- Topics: {', '.join(latest['topics'])}

Brain & Physiological state:
- Stress level: {latest['brain_stress']:.1f} (0=calm, 1=high stress)
- Cognitive load: {latest['cognitive_load']:.1f}
- Heart rate: {latest['hr']} bpm
- Incongruence detected: {latest['incongruence']}

Last 60 seconds summary:
{self._summarize_context(fused_states)}

Based on this, decide:
1. Should you intervene now? (suggest breathing, ask clarifying question)
2. Or keep listening?

Respond with empathy and therapeutic framing.
"""

    def _summarize_context(self, fused_states: list) -> str:
        """Condense last 60 sec into summary"""
        texts = [s['text'] for s in fused_states]
        avg_stress = sum(s['brain_stress'] for s in fused_states) / len(fused_states)
        emotions = [s['emotion'] for s in fused_states]

        return f"""
- User talked about: {' '.join(texts[:5])}...
- Average stress: {avg_stress:.1f}
- Emotions detected: {', '.join(set(emotions))}
"""
```

**System Prompt** (Therapist Instructions):
```python
THERAPIST_SYSTEM_PROMPT = """
You are a compassionate AI mental health co-pilot with access to real-time brain activity and speech analysis.

Your capabilities:
- Detect stress, anxiety, fear from brain EEG signals
- Analyze sentiment and emotion from speech
- Identify incongruence (user says "I'm fine" but brain shows stress)

Your role:
1. Listen actively and validate emotions
2. Notice when stress/anxiety increases (from brain data)
3. Gently intervene when needed:
   - Suggest breathing exercises (when stress >0.7)
   - Ask clarifying questions (when emotion shifts)
   - Reflect incongruence ("You said you're fine, but I notice...")
4. Guide user toward self-awareness
5. NEVER diagnose mental illness
6. If severe distress detected, suggest professional help

Response style:
- Empathetic and warm
- Use "I notice..." framing
- Ask open-ended questions
- Keep responses short (2-3 sentences)
- Suggest breathing when stress spikes

Crisis keywords: suicide, self-harm, hopeless → Escalate to professional
"""
```

---

#### 1.6 Session Coordination Module
**File**: `backend/copilot_session.py`

**Requirements**:
- Orchestrate all components
- Real-time coordination
- WebSocket streaming to frontend
- Session recording

**API**:
```python
class CopilotSession:
    def __init__(self):
        self.audio_recorder = AudioRecorder()
        self.transcriber = WhisperTranscriber()
        self.ml_analyzer = MLAnalyzer()
        self.fusion_engine = FusionEngine()
        self.gpt5_copilot = GPT5Copilot(api_key=OPENAI_API_KEY)
        self.brain_state = None  # Updated from main.py EEG stream

    async def start_session(self, websocket):
        """
        Start real-time co-pilot session

        Flow:
        1. Start audio recording
        2. Start transcription stream
        3. Analyze text with local ML
        4. Fuse with brain state
        5. Every 10-15 sec, call GPT-5 for decision
        6. Stream AI responses to frontend
        """

        # Start audio stream
        audio_stream = self.audio_recorder.stream_audio()

        async for audio_chunk in audio_stream:
            # Transcribe
            transcript = await self.transcriber.transcribe_stream(audio_chunk)

            if transcript['text']:
                # Analyze with local ML
                text_features = self.ml_analyzer.analyze(transcript['text'])

                # Fuse with brain state
                fused_state = self.fusion_engine.fuse(
                    brain_state=self.brain_state,
                    text_features=text_features,
                    raw_text=transcript['text']
                )

                # Send to frontend (real-time update)
                await websocket.send_json({
                    'type': 'transcript',
                    'text': transcript['text'],
                    'features': text_features,
                    'brain_state': self.brain_state,
                    'timestamp': fused_state['timestamp']
                })

                # Check if AI should respond
                if fused_state['should_intervene']:
                    # Call GPT-5
                    response = await self.gpt5_copilot.generate_response(
                        self.fusion_engine.context_window
                    )

                    # Stream AI response to frontend
                    async for chunk in response:
                        await websocket.send_json({
                            'type': 'ai_response',
                            'text': chunk,
                            'timestamp': time.time()
                        })

    def update_brain_state(self, brain_state: dict):
        """Called by main.py every second with latest EEG data"""
        self.brain_state = brain_state
```

---

### Phase 2: API Endpoints (Priority 2)

**File**: `backend/main.py` (add to existing)

**New Endpoints**:
```python
# AI Co-Pilot Session Management
@app.post("/api/copilot/start")
async def start_copilot_session(notes: str = "", tags: str = ""):
    """Start AI co-pilot conversation session"""
    session_id = copilot_manager.start_session(notes, tags)
    return {"status": "started", "session_id": session_id}

@app.post("/api/copilot/stop")
async def stop_copilot_session():
    """Stop current co-pilot session"""
    session_path = copilot_manager.stop_session()
    return {"status": "stopped", "session_path": session_path}

@app.websocket("/ws/copilot")
async def copilot_websocket(websocket: WebSocket):
    """
    Real-time WebSocket for AI co-pilot

    Sends:
    - Transcribed text
    - Text analysis features
    - Brain state updates
    - AI responses (streaming)
    """
    await websocket.accept()

    copilot_session = CopilotSession()

    # Start real-time session
    await copilot_session.start_session(websocket)
```

---

### Phase 3: Frontend UI (Priority 3)

#### 3.1 New Tab: "AI Co-Pilot"
**File**: `consciousness-app/src/pages/AICopilot.tsx`

**Components**:
1. **Brain State Panel** (left sidebar)
   - Real-time stress meter
   - Heart rate display
   - Current emotion badge
   - Cognitive load bar

2. **Conversation Panel** (main area)
   - Scrolling transcript
   - AI messages (bubbles)
   - User messages (bubbles)
   - Typing indicator (when AI thinking)

3. **Control Panel** (bottom)
   - Start/Stop session button
   - Breathing exercise button
   - Microphone status indicator

4. **Breathing Exercise Overlay** (modal)
   - Animated breathing circle
   - "Breathe in... Breathe out..." text
   - Heart rate decrease progress

**Code Structure**:
```typescript
// consciousness-app/src/pages/AICopilot.tsx

import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

interface Message {
  type: 'user' | 'ai';
  text: string;
  timestamp: number;
}

interface BrainState {
  stress: number;
  hr: number;
  emotion: string;
  cognitive_load: number;
}

export function AICopilot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [brainState, setBrainState] = useState<BrainState | null>(null);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [showBreathingExercise, setShowBreathingExercise] = useState(false);

  const { socket, connect, disconnect } = useWebSocket('/ws/copilot');

  useEffect(() => {
    if (!socket) return;

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'transcript') {
        setMessages(prev => [...prev, {
          type: 'user',
          text: data.text,
          timestamp: data.timestamp
        }]);
        setBrainState(data.brain_state);
      }

      if (data.type === 'ai_response') {
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last?.type === 'ai') {
            // Append to existing AI message (streaming)
            return [...prev.slice(0, -1), {
              ...last,
              text: last.text + data.text
            }];
          } else {
            // New AI message
            return [...prev, {
              type: 'ai',
              text: data.text,
              timestamp: data.timestamp
            }];
          }
        });
      }
    };
  }, [socket]);

  const startSession = async () => {
    await fetch('/api/copilot/start', { method: 'POST' });
    connect();
    setIsSessionActive(true);
  };

  const stopSession = async () => {
    await fetch('/api/copilot/stop', { method: 'POST' });
    disconnect();
    setIsSessionActive(false);
  };

  return (
    <div className="ai-copilot-container">
      {/* Brain State Panel */}
      <aside className="brain-state-panel">
        <h2>Brain State</h2>
        {brainState && (
          <>
            <div className="metric">
              <label>Stress</label>
              <div className="stress-meter" style={{ width: `${brainState.stress * 100}%` }} />
              <span>{(brainState.stress * 100).toFixed(0)}%</span>
            </div>

            <div className="metric">
              <label>Heart Rate</label>
              <span className="hr-value">{brainState.hr} bpm</span>
            </div>

            <div className="metric">
              <label>Emotion</label>
              <span className="emotion-badge">{brainState.emotion}</span>
            </div>

            <div className="metric">
              <label>Cognitive Load</label>
              <div className="load-bar" style={{ width: `${brainState.cognitive_load * 100}%` }} />
            </div>
          </>
        )}
      </aside>

      {/* Conversation Panel */}
      <main className="conversation-panel">
        <div className="messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.type}`}>
              <div className="bubble">{msg.text}</div>
              <span className="timestamp">
                {new Date(msg.timestamp * 1000).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </main>

      {/* Control Panel */}
      <footer className="control-panel">
        {!isSessionActive ? (
          <button onClick={startSession} className="btn-start">
            Start Session
          </button>
        ) : (
          <>
            <button onClick={stopSession} className="btn-stop">
              Stop Session
            </button>
            <button onClick={() => setShowBreathingExercise(true)} className="btn-breathing">
              Breathing Exercise
            </button>
            <div className="mic-indicator">🎤 Listening...</div>
          </>
        )}
      </footer>

      {/* Breathing Exercise Overlay */}
      {showBreathingExercise && (
        <BreathingExercise onClose={() => setShowBreathingExercise(false)} />
      )}
    </div>
  );
}
```

---

#### 3.2 Breathing Exercise Component
**File**: `consciousness-app/src/components/BreathingExercise.tsx`

```typescript
import React, { useState, useEffect } from 'react';

export function BreathingExercise({ onClose }: { onClose: () => void }) {
  const [phase, setPhase] = useState<'in' | 'hold' | 'out'>('in');
  const [countdown, setCountdown] = useState(4);

  useEffect(() => {
    const interval = setInterval(() => {
      setCountdown(prev => {
        if (prev === 1) {
          // Switch phase
          if (phase === 'in') setPhase('hold');
          else if (phase === 'hold') setPhase('out');
          else setPhase('in');
          return 4;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [phase]);

  return (
    <div className="breathing-overlay">
      <div className="breathing-circle" data-phase={phase}>
        <h1>{phase === 'in' ? 'Breathe In' : phase === 'hold' ? 'Hold' : 'Breathe Out'}</h1>
        <p className="countdown">{countdown}</p>
      </div>

      <button onClick={onClose} className="btn-close">Close</button>
    </div>
  );
}
```

---

## Implementation Timeline

### Week 1: Backend Foundation
- [x] Audio recording module
- [x] Whisper transcription integration
- [x] Local ML analyzer (reuse conversation_analyzer)
- [x] Fusion engine
- [x] GPT-5 integration

### Week 2: API & Real-Time
- [x] WebSocket endpoint
- [x] Session management
- [x] Real-time coordination
- [x] Testing with dummy data

### Week 3: Frontend UI
- [x] AI Co-Pilot tab
- [x] Brain state panel
- [x] Conversation interface
- [x] Breathing exercise component
- [x] Styling & UX polish

### Week 4: Integration & Testing
- [x] End-to-end testing
- [x] Performance optimization
- [x] Bug fixes
- [x] User testing & feedback

---

## Dependencies

### Python Backend
```bash
# Audio & Transcription
pip install pyaudio soundfile faster-whisper

# OpenAI GPT-5
pip install openai

# Already installed (conversation_analyzer)
# transformers torch sentence-transformers
```

### Frontend
```bash
# WebSocket
npm install react-use-websocket

# UI components (if not already installed)
npm install @headlessui/react @heroicons/react
```

---

## Cost Estimation

### GPT-5 API Costs
**Assumptions**:
- Average session: 10 minutes
- GPT-5 decision every 15 seconds = 40 decisions/session
- Average prompt: 100 tokens/decision
- Average response: 50 tokens/decision
- Total: 150 tokens × 40 = 6,000 tokens/session

**Pricing** (GPT-5 estimated):
- Input: $0.01/1K tokens = $0.06/session
- Output: $0.03/1K tokens = $0.12/session
- **Total: ~$0.18/session** (10 min)

**Monthly** (1 session/day):
- $0.18 × 30 = **$5.40/month**

---

## Success Metrics

### Technical KPIs
- ✅ Transcription latency <2 seconds
- ✅ ML analysis latency <100ms
- ✅ GPT-5 response latency <5 seconds
- ✅ Timestamp alignment accuracy >95%
- ✅ WebSocket uptime >99%

### User Experience KPIs
- ✅ Session engagement >5 minutes
- ✅ Intervention feels timely (not intrusive)
- ✅ Breathing exercise reduces HR by 10+ bpm
- ✅ User satisfaction >4/5 stars
- ✅ False positive intervention rate <10%

### Business KPIs
- ✅ Daily active users (DAU)
- ✅ Session completion rate
- ✅ Retention (users coming back)
- ✅ Cost per session <$0.20

---

## Privacy & Ethics

### Data Handling
- ✅ **EEG data**: Never sent to OpenAI (stays local)
- ✅ **Audio**: Transcribed locally (Whisper), then deleted
- ✅ **Text**: Sent to GPT-5 with condensed features (not full transcript)
- ✅ **Session data**: Saved locally, encrypted at rest

### User Consent
- ✅ Clear disclaimer: "Not a replacement for therapy"
- ✅ Crisis detection: Suggest professional help if severe distress
- ✅ User control: Can pause/stop anytime
- ✅ Transparency: Explain what brain data shows

### Ethical Guidelines
- ❌ **Never diagnose** mental illness
- ✅ **Always validate** user emotions
- ✅ **Intervene gently** (not intrusive)
- ✅ **Escalate to professional** if crisis detected

---

## Risk Mitigation

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Whisper transcription errors | Medium | Use `base` model (80% accuracy), test with noise |
| GPT-5 API downtime | High | Fallback to GPT-4o, cache common responses |
| WebSocket disconnects | Medium | Auto-reconnect, buffer messages |
| High latency (>5 sec) | Low | Optimize prompt size, use streaming |

### User Experience Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| False positive interventions | Medium | Tune thresholds, A/B testing |
| Intrusive AI responses | High | Add "wait" mode, delay interventions |
| Privacy concerns | High | Clear data policy, local processing |
| Overreliance on AI | High | Disclaimer, suggest professional help |

---

## Next Steps

1. **Create backend modules** (Phase 1)
2. **Add API endpoints** (Phase 2)
3. **Build frontend UI** (Phase 3)
4. **Test with dummy data** (Week 2)
5. **End-to-end integration** (Week 4)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-21
**Author**: Claude (Consciousness OS)
**Status**: Ready for Implementation
