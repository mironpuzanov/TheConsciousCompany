# Phase 3: Frontend UI Implementation Plan

**Date**: 2025-11-23
**Status**: 📋 Planning
**Estimated Time**: 6-8 hours

---

## Overview

Build React frontend for AI Co-Pilot with real-time brain state awareness and streaming conversation interface.

---

## Current Frontend Structure

```
consciousness-app/src/
├── App.tsx                  # Main app with view switching
├── components/
│   ├── MuseConnection.tsx   # EEG connection UI
│   ├── SessionRecording.tsx # Session recording controls
│   ├── LiveEEGDisplay.tsx   # Raw EEG display
│   ├── BandPowerDisplay.tsx # Band power metrics
│   └── ...                  # Other EEG components
├── hooks/
│   └── useWebSocket.tsx     # WebSocket hook for /ws
└── types/
    └── muse.ts              # EEG types
```

**Current Views**:
1. `eeg` - EEG Dashboard (existing)
2. `conversation` - Conversation Insights (existing)
3. `copilot` - **AI Co-Pilot (NEW - to be added)**

---

## Phase 3 Components to Build

### 1. Main Copilot Component
**File**: `src/components/AICopilot.tsx`

**Purpose**: Main container for AI Co-Pilot tab

**Structure**:
```tsx
<div className="ai-copilot-container">
  {/* Top Bar */}
  <div className="copilot-header">
    <CopilotControls
      onStart={startCopilot}
      onStop={stopCopilot}
      isActive={isActive}
      eegConnected={eegConnected}
    />
  </div>

  {/* Main Content - 2 Column Layout */}
  <div className="grid grid-cols-3 gap-6">
    {/* Left: Chat Interface (2/3 width) */}
    <div className="col-span-2">
      <ChatInterface
        messages={messages}
        isTyping={isTyping}
      />
    </div>

    {/* Right: Brain State Panel (1/3 width) */}
    <div className="col-span-1">
      <BrainStatePanel
        brainState={brainState}
        incongruence={incongruence}
      />
    </div>
  </div>

  {/* Breathing Exercise Overlay (conditional) */}
  {showBreathing && (
    <BreathingExercise onClose={() => setShowBreathing(false)} />
  )}
</div>
```

**Dependencies**:
- `useCopilotWebSocket()` hook
- `ChatInterface` component
- `BrainStatePanel` component
- `BreathingExercise` component

---

### 2. Copilot WebSocket Hook
**File**: `src/hooks/useCopilotWebSocket.ts`

**Purpose**: Manage WebSocket connection to `/ws/copilot`

**API**:
```typescript
interface CopilotMessage {
  type: 'ai_message' | 'transcript' | 'state_update' |
        'ai_typing' | 'ai_message_chunk' | 'ai_message_complete' |
        'error' | 'reconnecting';
  text?: string;
  brain_state?: BrainState;
  text_features?: TextFeatures;
  incongruence?: boolean;
  timestamp: number;
}

interface BrainState {
  stress: number;
  hr: number;
  emotion: string;
  cognitive_load: number;
}

interface TextFeatures {
  sentiment: string;
  emotion: string;
  topics: string[];
}

const useCopilotWebSocket = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isActive, setIsActive] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [brainState, setBrainState] = useState<BrainState | null>(null);
  const [incongruence, setIncongruence] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connect = () => {
    // 1. POST /api/copilot/start
    // 2. Connect WebSocket /ws/copilot
    // 3. Handle incoming messages
  };

  const disconnect = () => {
    // POST /api/copilot/stop
    // Close WebSocket
  };

  return {
    messages,
    isActive,
    isTyping,
    brainState,
    incongruence,
    error,
    connect,
    disconnect
  };
};
```

**Message Handling**:
```typescript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch(message.type) {
    case 'ai_message':
      setMessages(prev => [...prev, {
        role: 'ai',
        text: message.text,
        timestamp: message.timestamp
      }]);
      break;

    case 'transcript':
      setMessages(prev => [...prev, {
        role: 'user',
        text: message.text,
        confidence: message.confidence,
        timestamp: message.timestamp
      }]);
      break;

    case 'state_update':
      setBrainState(message.brain_state);
      setIncongruence(message.incongruence);
      break;

    case 'ai_typing':
      setIsTyping(true);
      break;

    case 'ai_message_chunk':
      // Append to last AI message or create new one
      break;

    case 'ai_message_complete':
      setIsTyping(false);
      break;

    case 'error':
      setError(message.message);
      break;

    case 'reconnecting':
      // Show reconnection UI
      break;
  }
};
```

---

### 3. Chat Interface Component
**File**: `src/components/ChatInterface.tsx`

**Purpose**: Display conversation with streaming support

**UI Structure**:
```tsx
<Card className="chat-interface h-[600px] flex flex-col">
  {/* Header */}
  <div className="chat-header p-4 border-b">
    <h3>Conversation</h3>
  </div>

  {/* Messages Area (scrollable) */}
  <div className="messages flex-1 overflow-y-auto p-4 space-y-4">
    {messages.map((msg, i) => (
      <MessageBubble
        key={i}
        role={msg.role}
        text={msg.text}
        timestamp={msg.timestamp}
      />
    ))}
    {isTyping && <TypingIndicator />}
  </div>

  {/* Input Area (disabled - voice only) */}
  <div className="chat-footer p-4 border-t bg-zinc-50">
    <div className="text-sm text-zinc-500 text-center">
      🎤 Speak naturally - AI is listening
    </div>
  </div>
</Card>
```

**Message Bubble Design**:
```tsx
const MessageBubble = ({ role, text, timestamp }) => (
  <div className={`message ${role === 'user' ? 'user' : 'ai'}`}>
    {role === 'user' ? (
      // User message (right-aligned, blue)
      <div className="flex justify-end">
        <div className="bg-blue-500 text-white rounded-2xl px-4 py-2 max-w-[80%]">
          <p>{text}</p>
          <span className="text-xs opacity-75">
            {new Date(timestamp * 1000).toLocaleTimeString()}
          </span>
        </div>
      </div>
    ) : (
      // AI message (left-aligned, gray)
      <div className="flex justify-start">
        <div className="bg-zinc-200 text-zinc-900 rounded-2xl px-4 py-2 max-w-[80%]">
          <p>{text}</p>
          <span className="text-xs text-zinc-500">
            {new Date(timestamp * 1000).toLocaleTimeString()}
          </span>
        </div>
      </div>
    )}
  </div>
);
```

---

### 4. Brain State Panel Component
**File**: `src/components/BrainStatePanel.tsx`

**Purpose**: Real-time brain + text analysis visualization

**UI Structure**:
```tsx
<div className="brain-state-panel space-y-4">
  {/* Stress Meter */}
  <Card className="p-4">
    <h4 className="text-sm font-medium mb-2">Stress Level</h4>
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-zinc-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${getStressColor(brainState.stress)}`}
          style={{ width: `${brainState.stress * 100}%` }}
        />
      </div>
      <span className="text-lg font-semibold">
        {(brainState.stress * 100).toFixed(0)}%
      </span>
    </div>
    {brainState.stress > 0.7 && (
      <p className="text-xs text-red-600 mt-2">⚠️ High stress detected</p>
    )}
  </Card>

  {/* Heart Rate */}
  <Card className="p-4">
    <h4 className="text-sm font-medium mb-2">Heart Rate</h4>
    <div className="text-3xl font-bold">
      {brainState.hr} <span className="text-sm text-zinc-500">bpm</span>
    </div>
  </Card>

  {/* Emotion */}
  <Card className="p-4">
    <h4 className="text-sm font-medium mb-2">Detected Emotion</h4>
    <div className="text-xl">
      {getEmotionEmoji(brainState.emotion)} {brainState.emotion}
    </div>
  </Card>

  {/* Incongruence Alert */}
  {incongruence && (
    <Card className="p-4 bg-yellow-50 border-yellow-200">
      <div className="flex items-start gap-3">
        <span className="text-2xl">⚠️</span>
        <div>
          <h4 className="font-medium text-yellow-900">Incongruence Detected</h4>
          <p className="text-sm text-yellow-700 mt-1">
            Your words don't match your brain activity
          </p>
        </div>
      </div>
    </Card>
  )}

  {/* Cognitive Load */}
  <Card className="p-4">
    <h4 className="text-sm font-medium mb-2">Cognitive Load</h4>
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-zinc-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-purple-500"
          style={{ width: `${brainState.cognitive_load * 100}%` }}
        />
      </div>
      <span className="text-sm">
        {(brainState.cognitive_load * 100).toFixed(0)}%
      </span>
    </div>
  </Card>
</div>
```

**Helper Functions**:
```typescript
const getStressColor = (stress: number) => {
  if (stress < 0.3) return 'bg-green-500';
  if (stress < 0.7) return 'bg-yellow-500';
  return 'bg-red-500';
};

const getEmotionEmoji = (emotion: string) => {
  const emojiMap = {
    'joy': '😊',
    'sadness': '😢',
    'anger': '😠',
    'fear': '😨',
    'anxiety': '😰',
    'neutral': '😐',
  };
  return emojiMap[emotion] || '😐';
};
```

---

### 5. Breathing Exercise Overlay
**File**: `src/components/BreathingExercise.tsx`

**Purpose**: Guided breathing when stress >0.7

**UI Structure**:
```tsx
<div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
  <Card className="p-8 max-w-md">
    <div className="text-center space-y-6">
      <h2 className="text-2xl font-bold">Let's Breathe Together</h2>

      {/* Animated Circle */}
      <div className="relative w-48 h-48 mx-auto">
        <div
          className={`absolute inset-0 rounded-full bg-blue-500 ${
            phase === 'inhale' ? 'scale-100' : 'scale-50'
          } transition-transform duration-4000 ease-in-out`}
        />
      </div>

      {/* Instructions */}
      <div className="text-xl font-medium">
        {phase === 'inhale' && '🌬️ Breathe in slowly...'}
        {phase === 'hold' && '⏸️ Hold...'}
        {phase === 'exhale' && '💨 Breathe out slowly...'}
      </div>

      {/* Progress */}
      <div className="text-sm text-zinc-500">
        Cycle {currentCycle} of 3
      </div>

      {/* Close Button */}
      <Button variant="outline" onClick={onClose}>
        Close
      </Button>
    </div>
  </Card>
</div>
```

**Breathing Cycle**:
```typescript
const useBreathingCycle = () => {
  const [phase, setPhase] = useState<'inhale' | 'hold' | 'exhale'>('inhale');
  const [currentCycle, setCurrentCycle] = useState(1);

  useEffect(() => {
    const timer = setInterval(() => {
      if (phase === 'inhale') {
        setPhase('hold');
        setTimeout(() => setPhase('exhale'), 4000); // Hold 4s
      } else if (phase === 'exhale') {
        if (currentCycle < 3) {
          setCurrentCycle(prev => prev + 1);
          setPhase('inhale');
        } else {
          // Complete
          onComplete();
        }
      }
    }, phase === 'inhale' ? 4000 : 6000); // Inhale 4s, exhale 6s

    return () => clearInterval(timer);
  }, [phase, currentCycle]);

  return { phase, currentCycle };
};
```

---

### 6. Copilot Controls Component
**File**: `src/components/CopilotControls.tsx`

**Purpose**: Start/Stop controls with status indicator

**UI Structure**:
```tsx
<Card className="p-4">
  <div className="flex items-center justify-between">
    <div>
      <h3 className="font-semibold">AI Co-Pilot</h3>
      <p className="text-sm text-zinc-500">
        {isActive ? '🟢 Active - Listening' : '⚪ Inactive'}
      </p>
    </div>

    <div className="flex gap-2">
      {!isActive ? (
        <Button
          onClick={onStart}
          disabled={!eegConnected}
        >
          Start Session
        </Button>
      ) : (
        <Button
          onClick={onStop}
          variant="destructive"
        >
          Stop Session
        </Button>
      )}
    </div>
  </div>

  {!eegConnected && (
    <p className="text-xs text-yellow-600 mt-2">
      ⚠️ Connect Muse EEG first
    </p>
  )}
</Card>
```

---

## App.tsx Integration

### Add Copilot View

**File**: `src/App.tsx`

**Changes**:

**1. Add copilot to view type**:
```typescript
const [view, setView] = useState<'eeg' | 'conversation' | 'copilot'>('eeg');
```

**2. Add button to navigation**:
```tsx
<div className="flex rounded-full bg-zinc-200 p-1">
  <Button
    variant={view === 'eeg' ? 'default' : 'ghost'}
    size="sm"
    onClick={() => setView('eeg')}
  >
    EEG Dashboard
  </Button>
  <Button
    variant={view === 'conversation' ? 'default' : 'ghost'}
    size="sm"
    onClick={() => setView('conversation')}
  >
    Conversation Insights
  </Button>
  <Button
    variant={view === 'copilot' ? 'default' : 'ghost'}  {/* NEW */}
    size="sm"
    onClick={() => setView('copilot')}
  >
    AI Co-Pilot
  </Button>
</div>
```

**3. Add view rendering**:
```tsx
{view === 'eeg' ? (
  <div className="space-y-6">
    {/* EEG Dashboard */}
  </div>
) : view === 'conversation' ? (
  <ConversationInsights />
) : (
  <AICopilot eegConnected={status === ConnectionStatus.CONNECTED} />  {/* NEW */}
)}
```

---

## File Structure (Phase 3)

```
consciousness-app/src/
├── App.tsx                         # MODIFIED: Add copilot view
├── components/
│   ├── AICopilot.tsx              # NEW: Main copilot container
│   ├── ChatInterface.tsx          # NEW: Chat UI
│   ├── BrainStatePanel.tsx        # NEW: Brain metrics display
│   ├── BreathingExercise.tsx      # NEW: Breathing overlay
│   ├── CopilotControls.tsx        # NEW: Start/stop controls
│   └── ...                        # Existing components
├── hooks/
│   ├── useWebSocket.tsx           # Existing: /ws hook
│   └── useCopilotWebSocket.ts     # NEW: /ws/copilot hook
└── types/
    ├── muse.ts                    # Existing: EEG types
    └── copilot.ts                 # NEW: Copilot types
```

---

## Types Definition

**File**: `src/types/copilot.ts`

```typescript
export interface CopilotMessage {
  type: 'ai_message' | 'transcript' | 'state_update' |
        'ai_typing' | 'ai_message_chunk' | 'ai_message_complete' |
        'error' | 'reconnecting';
  text?: string;
  brain_state?: BrainState;
  text_features?: TextFeatures;
  incongruence?: boolean;
  timestamp: number;
  confidence?: number;
}

export interface BrainState {
  stress: number;
  hr: number;
  emotion: string;
  cognitive_load: number;
}

export interface TextFeatures {
  sentiment: string;
  emotion: string;
  topics: string[];
}

export interface ChatMessage {
  role: 'user' | 'ai';
  text: string;
  timestamp: number;
  confidence?: number;
}
```

---

## Implementation Order

### Day 1 (3-4 hours)
1. ✅ Create types (`copilot.ts`)
2. ✅ Create WebSocket hook (`useCopilotWebSocket.ts`)
3. ✅ Create CopilotControls component
4. ✅ Add copilot view to App.tsx

### Day 2 (3-4 hours)
5. ✅ Create ChatInterface component
6. ✅ Create BrainStatePanel component
7. ✅ Create BreathingExercise component
8. ✅ Create main AICopilot component
9. ✅ Integration testing

---

## Testing Plan

### 1. Unit Testing
- [ ] WebSocket connection/disconnection
- [ ] Message handling for all 8 types
- [ ] Breathing cycle timing
- [ ] Stress threshold triggering

### 2. Integration Testing
- [ ] Start copilot session
- [ ] Speak and see transcript
- [ ] See AI response streaming
- [ ] See brain state updates
- [ ] See incongruence alert
- [ ] Trigger breathing exercise
- [ ] Stop session and export

### 3. UI/UX Testing
- [ ] Chat bubbles display correctly
- [ ] Timestamps formatted properly
- [ ] Typing indicator shows
- [ ] Brain metrics update smoothly
- [ ] Breathing animation smooth
- [ ] Responsive design (mobile/desktop)

---

## Dependencies

### NPM Packages (likely already installed)
- `react` (existing)
- `@types/react` (existing)
- Tailwind CSS (existing)
- shadcn/ui components (existing)

### No New Dependencies Required! ✅

---

## Estimated Metrics

### Lines of Code
- `useCopilotWebSocket.ts`: ~150 lines
- `AICopilot.tsx`: ~100 lines
- `ChatInterface.tsx`: ~120 lines
- `BrainStatePanel.tsx`: ~150 lines
- `BreathingExercise.tsx`: ~100 lines
- `CopilotControls.tsx`: ~60 lines
- `copilot.ts`: ~40 lines
- `App.tsx` changes: ~20 lines

**Total**: ~740 lines of new code

### File Count
- 6 new components
- 1 new hook
- 1 new types file
- 1 modified file (App.tsx)

**Total**: 9 files (7 new + 1 modified)

---

## Success Criteria

✅ User can start copilot session from UI
✅ User sees real-time transcription of their speech
✅ User sees AI responses streaming in
✅ User sees brain state metrics updating
✅ User sees incongruence alert when detected
✅ Breathing exercise triggers when stress >0.7
✅ User can stop session and see export confirmation
✅ All 8 WebSocket message types handled correctly
✅ UI is responsive and polished

---

**Status**: 📋 Ready for Implementation
**Next Step**: Begin building components
**Estimated Completion**: 6-8 hours total
