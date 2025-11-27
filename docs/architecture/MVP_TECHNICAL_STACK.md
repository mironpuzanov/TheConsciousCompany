# Consciousness OS - MVP Technical Stack & Product Requirements

# Project Overview

**Mission:** Build the operating system for human consciousness - combining EEG brain sensing with AI coaching to make inner mental states measurable, understandable, and optimizable.

**Product Vision:** "Whoop for consciousness" - a system that detects emotional triggers, cognitive patterns, and mental states during conversations and intentional practice sessions.

**Current Phase:** Research & Validation (not product building yet)

**Target Market:** B2C consciousness seekers - psychedelic integrators, meditators, biohackers, high-performers actively working on self-development.

**Hardware:** Starting with Muse 2 EEG headband ($250), then custom hardware later.

**Core Value Proposition:**

- Objective metrics for subjective experiences
- Find correlations between conversation topics and brain states
- Break self-delusion with biofeedback
- Personalized insights based on YOUR brain data

---

# Phase 1 Strategy: Validate Before Building

## The Key Question

**Do brain states actually correlate with conversation content in meaningful ways?**

Before building multi-user infrastructure, we need to prove:

1. We can get clean EEG data from Muse 2
2. Brain states change detectably during conversations
3. These changes correlate with specific topics/emotions
4. AI can extract useful insights from this correlation

**If YES → Build web platform, scale to users**

**If NO → Pivot or iterate on approach**

## Architecture Decision: Electron-Only First

**Why NOT build web app yet:**

- You're the only user (no need for cloud/multi-user)
- Faster iteration (1 week vs 4 weeks)
- All data stays local (better for experimentation)
- Can still use OpenAI, Claude APIs from Electron
- Build web infrastructure AFTER validating concept

**Tech Stack:**

- Electron app (TypeScript)
- Local file storage
- System audio recording
- Real-time EEG streaming
- API calls to OpenAI/Claude

---

# Electron App Architecture

## What the App Does

**Main Window:**

```
┌────────────────────────────────────────┐
│  Consciousness OS - Research Tool      │
├────────────────────────────────────────┤
│                                        │
│  Muse Status: ● Connected              │
│  Battery: 87%                          │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │  [Start New Session]             │  │
│  └──────────────────────────────────┘  │
│                                        │
│  Recent Sessions:                      │
│  - Nov 20, 3:42pm (15m) - Analyzed     │
│  - Nov 19, 2:15pm (23m) - Analyzed     │
│  - Nov 18, 10:30am (18m) - Analyzed    │
│                                        │
└────────────────────────────────────────┘
```

**During Session:**

```
┌────────────────────────────────────────┐
│  Recording Session...        ⏺ 03:42   │
├────────────────────────────────────────┤
│                                        │
│  Brain State: Focused 🟢               │
│  Alpha: ████████░░ 78%                 │
│  Beta:  ██████████ 92%                 │
│  Theta: ████░░░░░░ 45%                 │
│                                        │
│  Audio: Recording...                   │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │  [Stop Session]                  │  │
│  └──────────────────────────────────┘  │
│                                        │
└────────────────────────────────────────┘
```

## Data Flow

```
┌──────────────┐
│   Muse 2     │
│  Headband    │
└──────┬───────┘
       │ Bluetooth
       ↓
┌──────────────────────────────────┐
│    Electron App (Main Process)   │
│                                  │
│  1. Connect to Muse (muse-js)    │
│  2. Stream EEG data              │
│  3. Record system audio          │
│  4. Process in real-time:        │
│     - Filter noise               │
│     - Extract band powers        │
│     - Calculate HRV              │
│  5. Save to local files          │
│  6. After session:               │
│     - Transcribe audio (Whisper) │
│     - Analyze with Claude API    │
│     - Generate insights          │
└──────────────────────────────────┘
       ↓
┌──────────────────────────────────┐
│   Local File System              │
│                                  │
│  /sessions                       │
│    /2024-11-20_1542              │
│      - raw_eeg.csv               │
│      - features.json             │
│      - audio.wav                 │
│      - transcript.json           │
│      - analysis.json             │
└──────────────────────────────────┘
```

---

# Complete Tech Stack

## Electron App

**Core Framework:**

```bash
npm create @quick-start/electron consciousness-research
cd consciousness-research
npm install
```

**Key Dependencies:**

```json
{
  "dependencies": {
    "muse-js": "^4.0.0",           // Muse connection
    "@xenova/transformers": "^2.0.0", // Whisper (local)
    "mic": "^2.1.2",                // System audio
    "csv-writer": "^1.6.0",         // Save EEG data
    "@anthropic-ai/sdk": "^0.9.0",  // Claude API
    "recharts": "^2.10.0"           // Visualizations
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "typescript": "^5.0.0",
    "electron-builder": "^24.0.0"
  }
}
```

## Key Electron Capabilities

**1. Bluetooth Connection (muse-js):**

- Scan for Muse devices
- Connect via Web Bluetooth API (works in Electron)
- Stream 256 samples/sec per channel

**2. System Audio Recording:**

- Record what you hear (like Granola)
- No need for separate microphone
- Captures Zoom/calls/music/everything

**3. Local Processing:**

- Real-time filtering (50Hz notch, bandpass)
- FFT for band power extraction
- HRV from PPG sensor

**4. API Integration:**

- OpenAI Whisper (can run locally or API)
- Claude API for analysis
- All from JavaScript/TypeScript

**5. File System Access:**

- Save sessions to disk
- Load past sessions
- Export data

---

# Development Phases

## Week 1: Connect & Stream

**Goal:** See live EEG data from Muse

**Monday-Tuesday:**

- Set up Electron project
- Install muse-js
- Create "Connect to Muse" button
- Display raw EEG values updating in real-time

**Wednesday-Thursday:**

- Add signal processing (filtering)
- Calculate band powers (alpha, beta, theta, delta, gamma)
- Show live band power charts
- Verify data quality

**Friday:**

- Test 3+ sessions wearing Muse
- Validate: Can we get clean, consistent data?
- Document: What causes artifacts? (movement, eye blinks, jaw clenching)

**Deliverable:** Electron app showing live brain data

---

## Week 2: Record & Process

**Goal:** Record full sessions with audio

**Monday-Tuesday:**

- Add system audio recording
- Start/Stop session buttons
- Save EEG data to CSV files
- Save audio to WAV files

**Wednesday-Thursday:**

- Integrate Whisper (local model)
- Transcribe audio after session
- Add timestamps to transcript
- Sync transcript with EEG timeline

**Friday:**

- Record 5 test sessions (conversations, meetings, solo thinking)
- Verify transcription accuracy
- Check EEG-audio synchronization

**Deliverable:** Can record + transcribe sessions with brain data

---

## Week 3: Analysis & Insights

**Goal:** Generate AI insights from data

**Monday-Tuesday:**

- Integrate Claude API
- Build analysis pipeline:
    1. Load transcript + EEG features
    2. Identify moments of high beta (stress/focus)
    3. Match with transcript text
    4. Send to Claude: "What patterns do you see?"

**Wednesday-Thursday:**

- Build insights UI
- Show analysis results in app
- Add "Key Moments" timeline
- Example: "3:42 - Discussing budget → Beta +45%, possible anxiety"

**Friday:**

- Analyze all past sessions
- Look for patterns across sessions
- Document findings

**Deliverable:** Working insight generation

---

## Week 4: Validation

**Goal:** Determine if this actually works

**Monday-Thursday:**

- Record 10+ diverse sessions:
    - Difficult conversations
    - Creative work
    - Meditation
    - Problem-solving
    - Social calls
    - Stressful tasks

**Friday:**

- Review all insights
- Answer: Are correlations meaningful?
- Answer: Can AI extract useful patterns?
- Answer: Would this help people?

**Decision Point:**

- ✅ If YES → Plan web app architecture
- ❌ If NO → Iterate on approach or pivot

---

# File Structure

```
consciousness-research/
├── src/
│   ├── main/                    # Main process
│   │   ├── index.ts            # App entry
│   │   ├── muse.ts             # Muse connection
│   │   ├── audio.ts            # Audio recording
│   │   ├── processing.ts       # EEG processing
│   │   └── analysis.ts         # AI analysis
│   ├── renderer/               # UI (React)
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── MuseConnect.tsx
│   │   │   ├── SessionControl.tsx
│   │   │   ├── LiveCharts.tsx
│   │   │   └── InsightsView.tsx
│   └── shared/
│       └── types.ts            # TypeScript types
├── data/                       # Local data storage
│   └── sessions/
│       └── YYYY-MM-DD_HHmm/
│           ├── raw_eeg.csv
│           ├── features.json
│           ├── audio.wav
│           ├── transcript.json
│           └── analysis.json
├── models/                     # Local AI models
│   └── whisper-base/          # If using local Whisper
└── package.json
```

---

# Data Formats

## EEG Features (features.json)

```json
[
  {
    "timestamp": 1700493720,
    "delta": 0.23,
    "theta": 0.45,
    "alpha": 0.78,
    "beta": 0.92,
    "gamma": 0.34,
    "heart_rate": 72,
    "hrv_rmssd": 45.2
  }
]
```

## Transcript (transcript.json)

```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 3.2,
      "text": "So I've been thinking about the budget..."
    },
    {
      "start": 3.2,
      "end": 7.1,
      "text": "And honestly it's making me pretty anxious."
    }
  ]
}
```

## Analysis (analysis.json)

```json
{
  "session_id": "2024-11-20_1542",
  "duration_minutes": 15.2,
  "overall_state": "High cognitive load with anxiety spikes",
  "key_moments": [
    {
      "timestamp": 192,
      "transcript": "discussing budget",
      "brain_state": "Beta +45%, Alpha -23%",
      "interpretation": "Anxiety response to financial topic",
      "confidence": 0.87
    }
  ],
  "patterns": [
    "Financial topics trigger consistent stress response",
    "Alpha increases during creative problem-solving",
    "Theta spike when discussing relationships"
  ],
  "ai_insights": "Full Claude analysis here..."
}
```

---

# Whisper Integration Options

## Option A: Local (Recommended for MVP)

```bash
npm install @xenova/transformers
```

**Pros:**

- Free
- Private (data never leaves laptop)
- Fast enough for post-session

**Cons:**

- Needs ~2GB disk space
- Slower than API

## Option B: OpenAI API

```bash
npm install openai
```

**Pros:**

- Faster
- More accurate

**Cons:**

- Costs ~$0.006/minute
- Audio sent to OpenAI

**Recommendation:** Start with local, switch to API if needed

---

# Claude API Integration

## Analysis Prompt Template

```tsx
const analysisPrompt = `
You are analyzing a conversation paired with real-time brain data (EEG).

## Brain Data:
- Delta (0.5-4 Hz): Deep sleep, unconscious
- Theta (4-8 Hz): Meditation, creativity, memory
- Alpha (8-13 Hz): Relaxation, calm focus
- Beta (13-30 Hz): Active thinking, problem-solving, anxiety
- Gamma (30-100 Hz): Peak concentration, information processing

## Session Transcript:
${transcript}

## EEG Features (simplified):
${eegSummary}

## Your Task:
1. Identify moments where brain state changed significantly
2. Match these with transcript content
3. Interpret what the brain data suggests
4. Look for patterns (e.g., "Beta spikes when discussing work")
5. Provide actionable insights

Be specific. Reference timestamps. Explain confidence level.
`;
```

---

# Success Criteria

## Week 1:

- [ ]  Electron app runs on MacOS
- [ ]  Successfully connects to Muse 2
- [ ]  Displays live EEG data
- [ ]  Charts update in real-time
- [ ]  Data looks clean (no constant artifacts)

## Week 2:

- [ ]  Can record full sessions
- [ ]  Audio captures system sound
- [ ]  Transcription works accurately
- [ ]  EEG and audio stay synchronized
- [ ]  5+ test sessions recorded

## Week 3:

- [ ]  Claude API integration working
- [ ]  Generates analysis for each session
- [ ]  Insights displayed in UI
- [ ]  Can review past sessions
- [ ]  At least 3 meaningful correlations found

## Week 4:

- [ ]  10+ diverse sessions recorded
- [ ]  Consistent patterns identified
- [ ]  AI insights feel useful (not generic)
- [ ]  Clear answer: Does this concept work?
- [ ]  Documentation of findings

---

# Research Questions to Answer

## Data Quality:

1. How clean is Muse 2 data during normal activities?
2. What causes most artifacts?
3. Can we detect meaningful state changes?
4. How much does movement affect readings?

## Correlations:

1. Do emotional topics change brain states?
2. Are these changes consistent across sessions?
3. Can we predict state from conversation?
4. Can we predict conversation from state?

## AI Analysis:

1. Does Claude extract useful patterns?
2. Are insights actionable?
3. What works better: real-time or post-session?
4. How much context does AI need?

## User Experience:

1. Is wearing Muse distracting?
2. Does knowing about monitoring change behavior?
3. How long are useful sessions?
4. What would make this more valuable?

---

# After Validation: Web Platform Plan

**If research phase succeeds, build:**

1. **Cloud Backend (FastAPI)**
    - User accounts
    - Session storage
    - API for Electron app
2. **Web Dashboard (Next.js)**
    - View sessions from anywhere
    - Mobile-friendly
    - Share insights
3. **Enhanced Electron App**
    - Uploads to cloud
    - Downloads analysis
    - System tray mode
4. **Mobile App (React Native)**
    - View insights on phone
    - Light version of dashboard
    - Push notifications

**But don't build ANY of this until validation complete.**

---

# Immediate Next Steps

## Today:

1. Install Electron + TypeScript
2. Set up project structure
3. Create basic window with "Connect" button

## Tomorrow (When Muse Arrives):

1. Install muse-js
2. Test Bluetooth connection
3. Display raw EEG values
4. Verify data streaming

## This Week:

1. Add signal processing
2. Create live charts
3. Record first test session
4. Validate data quality

**Focus:** Get data flowing. Everything else is secondary.

---

# Why This Approach Works

**Fast Iteration:**

- 1 week to working prototype
- No cloud complexity
- No deployment hassle

**Lower Risk:**

- Validate before building infrastructure
- Fail fast if concept doesn't work
- Learn what users actually need

**Privacy:**

- All data stays local
- No server vulnerabilities
- Full control

**Flexibility:**

- Easy to pivot
- Can still add web later
- Electron works as bridge anyway

**Learning:**

- Deep understanding of EEG data
- Real patterns vs. noise
- What actually matters

---

# Remember

**You're not building a product yet.**

**You're answering: "Should this product exist?"**

Spend 4 weeks validating, not 4 months building.

If it works → you'll know exactly what to build.

If it doesn't → you saved months of wasted effort.

**Start hacking tomorrow when Muse arrives. 🧠**