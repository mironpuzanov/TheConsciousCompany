# Integration Testing Guide

## Prerequisites

1. **Python Backend Setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or: venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```

2. **React Frontend Setup:**
   ```bash
   cd consciousness-app
   npm install
   ```

3. **Muse Device:**
   - Turn on your Muse 2 headband
   - Ensure Bluetooth is enabled on your computer

## Testing Steps

### Step 1: Start muselsl Stream

In Terminal 1:
```bash
muselsl stream
```

You should see output like:
```
Connecting to Muse...
Connected to Muse-XXXX
Streaming EEG data...
```

### Step 2: Start Python Backend

In Terminal 2:
```bash
cd backend
source venv/bin/activate  # If not already activated
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 3: Start React Frontend

In Terminal 3:
```bash
cd consciousness-app
npm run dev
```

You should see:
```
VITE v5.x.x ready in xxx ms
➜  Local:   http://localhost:5173/
```

### Step 4: Test Connection

1. Open browser to `http://localhost:5173`
2. Click "Connect to Muse" button
3. Verify:
   - Connection status changes to "Connected"
   - Device name appears
   - "Live" indicator appears
   - Raw EEG data starts updating
   - Band powers appear after ~1 second
   - Brain state indicator shows current state

### Step 5: Verify Data Flow

**Check Backend Logs (Terminal 2):**
- Should see: "Client connected. Total: 1"
- Should see periodic log messages about data processing

**Check Frontend:**
- Live EEG Display: Should show 4 channels updating in real-time
- Band Power Display: Should show bar chart with percentages
- Brain State: Should show one of: Relaxed, Focused, Creative, Drowsy, Peak Focus, Mixed
- EEG Waveform (if debug enabled): Should show 4 lines scrolling

### Step 6: Test Disconnection

1. Click "Disconnect" button
2. Verify:
   - Connection status returns to "Disconnected"
   - Data stops updating
   - WebSocket closes cleanly

## Expected Behavior

### WebSocket Messages

The backend sends two types of messages:

1. **EEG Data** (high frequency, ~256 Hz):
   ```json
   {
     "type": "eeg_data",
     "timestamp": 1234567890.123,
     "data": [123.4, 98.2, 101.5, 115.3]
   }
   ```

2. **Band Powers** (1 Hz, every second):
   ```json
   {
     "type": "band_powers",
     "timestamp": 1234567890.123,
     "band_powers": {
       "delta": 12.3,
       "theta": 18.5,
       "alpha": 35.2,
       "beta": 28.1,
       "gamma": 5.9
     },
     "brain_state": "relaxed",
     "has_artifact": false,
     "signal_quality": {
       "mean": 0.5,
       "std": 12.3
     }
   }
   ```

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Verify all Python dependencies are installed
- Check Python version (3.8+ required)

### "No EEG stream found" error
- Make sure `muselsl stream` is running BEFORE starting backend
- Check Muse headband is on and connected
- Try restarting muselsl stream

### Frontend can't connect
- Verify backend is running on port 8000
- Check browser console for WebSocket errors
- Verify CORS is enabled in backend (should be for localhost:5173)

### No data appearing
- Wait at least 1 second after connection (band powers need 256 samples)
- Check browser console for errors
- Verify WebSocket connection is open (check Network tab in DevTools)

### Data looks wrong
- Check signal quality in backend logs
- Verify Muse headband is properly positioned
- Check for artifacts (movement, eye blinks)

## Manual API Testing

You can test the backend API directly:

```bash
# Health check
curl http://localhost:8000/

# Get device info (before connecting)
curl http://localhost:8000/api/device-info

# Connect to Muse
curl -X POST http://localhost:8000/api/connect

# Disconnect
curl -X POST http://localhost:8000/api/disconnect
```

## Success Criteria

✅ All steps complete without errors
✅ Real-time EEG data visible in frontend
✅ Band powers updating every second
✅ Brain state indicator working
✅ No console errors in browser
✅ Clean disconnect works
✅ Reconnection works after disconnect

## Next Steps After Integration

1. Test with actual Muse device during different activities:
   - Meditation (should show high alpha/theta)
   - Focused work (should show high beta)
   - Relaxation (should show high alpha)
   - Movement (should detect artifacts)

2. Verify signal processing accuracy:
   - Compare with known EEG patterns
   - Test artifact detection
   - Validate band power calculations

3. Performance testing:
   - Long sessions (15+ minutes)
   - Multiple clients connected
   - Network stability

