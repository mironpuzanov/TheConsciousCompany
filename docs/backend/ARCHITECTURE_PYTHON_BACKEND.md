# Consciousness OS - Python Backend Architecture

## Overview
Switching from pure JavaScript to **Python backend + Web frontend** for proper scientific EEG signal processing.

## Why Python Backend?
- ✅ **muselsl** - Industry-standard library for Muse devices
- ✅ **scipy** - Proper bandpass/notch filters (Butterworth)
- ✅ **mne-python** - Research-grade EEG analysis
- ✅ **numpy** - Fast numerical processing
- ❌ JavaScript FFT libraries - Not rigorous enough for research

---

## Architecture

```
┌──────────────────────────────────────┐
│         WEB BROWSER                  │
│  ┌────────────────────────────────┐  │
│  │   React Frontend (Vite)        │  │
│  │   - UI Controls                │  │
│  │   - Visualizations             │  │
│  │   - Connection Status          │  │
│  └────────────────────────────────┘  │
│              │                        │
│              │ WebSocket              │
│              │ (ws://localhost:8000)  │
└──────────────┼────────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│      PYTHON BACKEND (FastAPI)        │
│  ┌────────────────────────────────┐  │
│  │  FastAPI Server (port 8000)    │  │
│  │  - WebSocket endpoint          │  │
│  │  - Serves React build          │  │
│  └────────────────────────────────┘  │
│  ┌────────────────────────────────┐  │
│  │  Signal Processing Pipeline    │  │
│  │  - muselsl (Muse connection)   │  │
│  │  - scipy (filters)             │  │
│  │  - numpy (FFT, band powers)    │  │
│  └────────────────────────────────┘  │
└──────────────┼────────────────────────┘
               │
               │ Bluetooth
               ▼
         ┌──────────┐
         │  Muse 2  │
         └──────────┘
```

---

## How It Works

### Connection Flow:
1. **Start Python backend**: `python backend/main.py`
2. **Backend connects to Muse**: Uses `muselsl` to connect via Bluetooth
3. **Open browser**: Go to `http://localhost:8000`
4. **Frontend connects**: WebSocket to backend
5. **Real-time data**: Backend streams processed EEG data to frontend

### Important: Connection happens in Python, not browser!
- ❌ **Old way**: Browser Web Bluetooth → Muse
- ✅ **New way**: Python muselsl → Muse → WebSocket → Browser

---

## Tech Stack

### Backend (Python)
```
backend/
├── main.py              # FastAPI server + WebSocket
├── muse_stream.py       # muselsl connection & streaming
├── signal_processor.py  # Filters, FFT, band powers
├── requirements.txt     # Python dependencies
└── static/             # Serves React build
```

**Dependencies:**
- `fastapi` - Web server
- `uvicorn` - ASGI server
- `websockets` - Real-time communication
- `muselsl` - Muse connection
- `numpy` - Numerical processing
- `scipy` - Signal filtering
- `pylsl` - Lab Streaming Layer

### Frontend (React)
```
frontend/
├── src/
│   ├── hooks/
│   │   └── useWebSocket.ts    # Connect to Python backend
│   ├── components/
│   │   ├── BandPowerDisplay.tsx
│   │   └── ConnectionStatus.tsx
│   └── App.tsx
└── package.json
```

---

## Implementation Steps

### Phase 1: Python Backend Setup
1. Create `backend/` directory
2. Install Python dependencies
3. Set up FastAPI server
4. Implement muselsl Muse connection
5. Test: Can Python connect to Muse?

### Phase 2: Signal Processing
1. Implement Butterworth bandpass filter (0.5-50 Hz)
2. Implement notch filter (60 Hz powerline noise)
3. Implement FFT + band power extraction
4. Test: Are band powers accurate?

### Phase 3: WebSocket Communication
1. Create WebSocket endpoint in FastAPI
2. Stream processed data to frontend
3. Test: Does data reach browser?

### Phase 4: Frontend Updates
1. Remove `muse-js` and Web Bluetooth code
2. Add WebSocket connection
3. Update UI to show backend status
4. Display real-time band powers

### Phase 5: Integration Testing
1. Full flow: Python → Muse → Process → WebSocket → Browser
2. Verify band powers change with mental states
3. Compare with research-grade tools

---

## Running the Application

### Development:
```bash
# Terminal 1: Python backend
cd backend
pip install -r requirements.txt
python main.py

# Terminal 2: React frontend (dev mode)
cd frontend
npm run dev
```

### Production:
```bash
# Build frontend
cd frontend
npm run build
# Copy build to backend/static/

# Run backend only (serves frontend too)
cd backend
python main.py

# Open browser
open http://localhost:8000
```

---

## Benefits of This Architecture

1. **Scientific Rigor**
   - muselsl is used by research labs
   - scipy filters are validated
   - Proper signal processing pipeline

2. **Simplicity**
   - One connection point (Python → Muse)
   - No browser Bluetooth complexity
   - Easier debugging

3. **Future-Ready**
   - Can add ML models in Python
   - Easy to save sessions to disk
   - Can integrate with other Python tools

4. **Performance**
   - Python handles heavy processing
   - Browser just displays results
   - Lower CPU usage in browser

---

## Current Status vs New Plan

### ✅ What We Keep:
- React frontend UI
- Recharts visualizations
- Component structure

### ❌ What We Replace:
- `muse-js` → `muselsl`
- Browser Web Bluetooth → Python Bluetooth
- JavaScript FFT → numpy FFT
- Custom filters → scipy Butterworth filters

### ➕ What We Add:
- FastAPI backend
- WebSocket real-time communication
- Research-grade signal processing
- Proper data validation

---

## Next Steps

1. Create `backend/` directory structure
2. Set up Python virtual environment
3. Install dependencies
4. Implement muselsl connection
5. Test Muse connection in Python
6. Build signal processing pipeline
7. Set up WebSocket streaming
8. Update React frontend

**Ready to start building the Python backend?** 🐍
