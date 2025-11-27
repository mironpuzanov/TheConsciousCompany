# WebSocket Integration - Complete

## Summary

The React frontend has been successfully updated to use WebSocket communication with the Python backend instead of direct Web Bluetooth connection via `muse-js`.

## Changes Made

### 1. New WebSocket Hook (`useWebSocket.ts`)
- Replaces `useMuse.ts` hook
- Connects to Python backend via WebSocket (`ws://localhost:8000/ws`)
- Handles connection lifecycle (connect, disconnect, reconnect)
- Processes two message types:
  - `eeg_data`: Raw EEG samples (4 channels) at ~256 Hz
  - `band_powers`: Processed frequency band powers and brain state at 1 Hz
- Automatic reconnection on disconnect
- Ping/pong keepalive mechanism

### 2. Updated Types (`types/muse.ts`)
- Added `BandPowers` interface to match backend format

### 3. Updated Components

**BandPowerDisplay.tsx:**
- Now receives `bandPowers` and `brainState` as props from backend
- Removed local FFT calculation (now done in Python backend)
- Displays brain state from backend classification

**MuseConnection.tsx:**
- Updated connection instructions to mention Python backend requirements

**App.tsx:**
- Switched from `useMuse` to `useWebSocket` hook
- Passes `bandPowers` and `brainState` to BandPowerDisplay

### 4. Backend Integration
- Frontend calls `/api/connect` to initiate Muse connection
- Frontend connects to `/ws` WebSocket endpoint for real-time data
- Backend handles all signal processing (filtering, FFT, band powers)
- Backend sends processed data via WebSocket

## Architecture Flow

```
Muse Headband
    ↓ (Bluetooth)
muselsl stream (LSL)
    ↓
Python Backend (FastAPI)
    ├─ Signal Processing (scipy, numpy)
    ├─ Band Power Calculation
    └─ WebSocket Broadcast
        ↓
React Frontend (WebSocket)
    ├─ Live EEG Display
    ├─ Band Power Charts
    └─ Brain State Indicator
```

## Data Flow

1. **Connection:**
   - User clicks "Connect" → Frontend calls `POST /api/connect`
   - Backend connects to Muse via LSL
   - Frontend opens WebSocket connection to `/ws`

2. **Data Streaming:**
   - Backend receives EEG data from LSL stream
   - Processes in 1-second windows (256 samples)
   - Broadcasts two message types:
     - Raw EEG data (high frequency)
     - Processed band powers (1 Hz)

3. **Display:**
   - Frontend receives messages and updates UI
   - Live EEG display shows raw values
   - Band power chart shows frequency distribution
   - Brain state shows current classification

## Benefits

1. **Scientific Accuracy:**
   - Python backend uses research-grade libraries (scipy, numpy)
   - Proper Butterworth filters and Welch's method for PSD
   - More accurate than JavaScript FFT implementations

2. **Separation of Concerns:**
   - Backend handles all heavy processing
   - Frontend focuses on visualization
   - Easier to debug and maintain

3. **Future-Ready:**
   - Can add ML models in Python backend
   - Can save sessions to disk
   - Can integrate with other Python tools

4. **Performance:**
   - Lower CPU usage in browser
   - Better for long sessions
   - Can handle multiple clients

## Testing

See `INTEGRATION_TEST.md` for detailed testing instructions.

Quick test:
1. Start `muselsl stream`
2. Start backend: `cd backend && python main.py`
3. Start frontend: `cd consciousness-app && npm run dev`
4. Open browser to `http://localhost:5173`
5. Click "Connect to Muse"
6. Verify data is flowing

## Removed Dependencies

The following are no longer needed (but kept for now):
- `muse-js` - Replaced by Python backend
- `rxjs` - Was used by muse-js
- `fft.js` - FFT now done in Python

Note: These can be removed from `package.json` in a future cleanup, but keeping them for now doesn't hurt.

## Next Steps

1. ✅ WebSocket integration complete
2. ✅ Components updated
3. ✅ Integration testing guide created
4. ⏭️ Test with actual Muse device
5. ⏭️ Verify signal processing accuracy
6. ⏭️ Performance testing with long sessions

