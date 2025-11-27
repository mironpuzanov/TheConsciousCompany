# Implementation Overview - Consciousness OS

## Current Architecture

### Data Flow
```
Muse 2 Headband
  ↓ (Bluetooth)
muselsl (LSL streams)
  ↓ (EEG, PPG, ACC, GYRO)
Python Backend (FastAPI)
  ↓ (WebSocket)
React Frontend
```

## Libraries & Technologies

### Backend (Python)

#### 1. **Signal Processing**
- **MNE-Python (v1.6.0)** - Primary artifact removal
  - ICA (Independent Component Analysis) for artifact removal
  - Built-in filtering (bandpass, notch)
  - Signal quality metrics (SNR, bad channel detection)
  - Real-time capable
  
- **scipy (v1.11.4)** - Scientific computing
  - `signal.butter()` - Butterworth bandpass filter
  - `signal.iirnotch()` - Notch filter (60 Hz)
  - `signal.welch()` - Power spectral density (band powers)
  
- **numpy (v1.26.2)** - Numerical operations
  - FFT, array operations, signal processing

#### 2. **Muse Connection**
- **muselsl (v2.2.1)** - Muse device connection
  - Connects to Muse 2 via Bluetooth
  - Streams EEG (256 Hz), PPG (64 Hz), ACC (52 Hz), GYRO (52 Hz)
  - Uses LSL (Lab Streaming Layer) protocol
  
- **pylsl (v1.16.2)** - LSL stream handling
  - Pulls data from LSL streams
  - Synchronizes multi-sensor data

#### 3. **Web Server**
- **FastAPI (v0.104.1)** - REST API + WebSocket server
- **uvicorn** - ASGI server
- **websockets** - WebSocket protocol

### Frontend (React/TypeScript)

- **React + Vite** - UI framework
- **Recharts** - Data visualization (waveforms, band powers)
- **TailwindCSS** - Styling
- **lucide-react** - Icons

## Current Implementation Status (Updated: Nov 20, 2025)

### ✅ Fully Working
1. **Muse Connection** - ✅ Connects to all sensors (EEG, PPG, ACC, GYRO)
2. **WebSocket Streaming** - ✅ Real-time data to frontend (stable, no crashes)
3. **MNE-Python Integration** - ✅ ICA artifact removal implemented (30s calibration)
4. **HRV Calculation** - ⚠️ Heart rate works, but RMSSD shows incorrect values (300-500ms)
5. **Live EEG Display** - ✅ Raw waveform visualization (smoothed)
6. **ICA Calibration** - ✅ 30-second calibration with progress bar
7. **Band Power Calculation** - ✅ Delta, Theta, Alpha, Beta, Gamma (Welch's method)
8. **Brain State Classification** - ✅ Ratio-based classification (30s smoothing, state locking)
9. **Multi-Sensor Artifact Detection** - ✅ Eye blink, muscle, motion, bad channel detection
10. **Bad Channel Detection** - ✅ Detects channels with extreme values (>200μV), excludes from averaging
11. **Posture Detection** - ⚠️ Works but inaccurate (too sensitive, UI jumps)
12. **Mental State Interpretation** - ✅ HRV/posture/band change explanations

### ⚠️ Partially Working / Needs Tuning
1. **ICA Artifact Removal** - ✅ Fits correctly, artifacts removed, but verification needed
2. **Motion Detection** - ✅ Detects movement, thresholds tuned
3. **Signal Quality Scoring** - ✅ SNR and confidence calculated, thresholds tuned
4. **HRV RMSSD** - ❌ Showing incorrect values (300-500ms instead of 20-100ms) - **CRITICAL BUG**
5. **Posture Detection** - ⚠️ Works but too sensitive, shows false positives when still
6. **Talking Artifact Detection** - ⚠️ Basic detection works, but not reliable enough
7. **Heart Rate Stability** - ⚠️ Appears/disappears, likely related to talking artifacts

### 🔧 Recent Fixes (Nov 20, 2025)
1. ✅ Fixed HRV/PPG data handling - Heart rate displays (but RMSSD has bug)
2. ✅ Fixed ICA progress UI - Progress bar and countdown timer added
3. ✅ Fixed MNE filter API - Notch filter using scipy instead of MNE
4. ✅ Fixed band power message parsing - Data now reaches frontend
5. ✅ Fixed JSON serialization - All numpy types converted to Python types
6. ✅ Improved motion detection - Lowered thresholds for better sensitivity
7. ✅ Added ICA status broadcasting - Progress updates in real-time
8. ✅ Added bad channel detection - Detects and excludes channels with extreme values
9. ✅ Added temporal smoothing - 30-second window, state locking (10s minimum)
10. ✅ Removed duplicate "Overall Mental State" - Only shows "Current State"
11. ✅ Improved posture smoothing - 60-second history, state locking
12. ✅ Consistent artifact detection - Combines MNE + artifact detector + bad channels

## Signal Processing Pipeline

### Current Flow:
```
Raw EEG (256 Hz)
  ↓
Bandpass Filter (0.5-50 Hz) - scipy
  ↓
Notch Filter (60 Hz) - scipy
  ↓
ICA Calibration (30 seconds) - MNE-Python
  ↓
ICA Artifact Removal (if fitted) - MNE-Python
  ↓
Band Power Calculation (Welch's method) - scipy
  ↓
Brain State Classification (simple threshold)
  ↓
WebSocket → Frontend
```

### Artifact Detection Methods:

1. **Eye Blink Detection** (`artifact_detector.py`)
   - EEG spike pattern (>150 μV in frontal channels)
   - Gyroscope Z-axis rotation (>200 deg/s)
   - Duration check (80-320ms)

2. **Muscle Artifact** (`artifact_detector.py`)
   - EMG frequency analysis (50-100 Hz power)
   - Accelerometer jaw movement detection
   - Threshold: 15% power in EMG range

3. **Motion Detection** (`artifact_detector.py`)
   - Accelerometer magnitude change (>0.15g)
   - Gyroscope rotation change (>100 deg/s)
   - Buffer variance analysis

4. **ICA Artifact Removal** (`mne_processor.py`)
   - Learns artifact patterns from 30s calibration
   - Automatically removes eye blinks, muscle artifacts
   - Uses MNE's `find_bads_eog()` and `find_bads_muscle()`

## File Structure

```
backend/
  ├── main.py                 # FastAPI server, WebSocket, data flow
  ├── muse_stream.py          # LSL stream connection (EEG, PPG, ACC, GYRO)
  ├── signal_processor.py     # Basic filtering + band power calculation
  ├── mne_processor.py        # MNE-Python ICA artifact removal
  ├── artifact_detector.py    # Multi-sensor artifact detection
  └── hrv_calculator.py       # Heart rate variability from PPG

consciousness-app/src/
  ├── hooks/
  │   └── useWebSocket.ts     # WebSocket connection hook
  ├── components/
  │   ├── BandPowerDisplay.tsx    # Frequency band visualization
  │   ├── HRVDisplay.tsx          # Heart rate & HRV
  │   ├── ArtifactStatus.tsx     # Artifact detection status
  │   ├── ICAStatus.tsx           # ICA calibration progress
  │   └── EEGWaveform.tsx         # Raw EEG waveforms
  └── App.tsx                 # Main application
```

## Known Issues & Limitations (Updated: Nov 20, 2025)

### Critical Issues

1. **HRV RMSSD Calculation Bug** ⚠️
   - RMSSD showing 300-500ms (should be 20-100ms for healthy adults)
   - Likely issue: Timestamp calculation or peak detection in `hrv_calculator.py`
   - **Status**: Needs investigation - check RR interval calculation and peak detection algorithm

2. **Posture UI Layout Shifts** ⚠️
   - UI jumps when posture state changes
   - Text changes cause layout reflow
   - **Fix Needed**: Fixed-height containers with absolute positioning or CSS Grid to prevent layout shifts
   - **Status**: Partially fixed with min-height, but still needs improvement

3. **Posture Detection Inaccuracy** ⚠️
   - Shows "good" then "bad" when user is sitting still
   - Detection too sensitive to minor movements
   - **Fix Needed**: 
     - Increase smoothing window (currently 15 samples, need 30+)
     - Increase state lock duration (currently 10s, may need 15-20s)
     - Better variance threshold for "unstable" detection
   - **Status**: Needs tuning

4. **Heart Rate Disappearing** ⚠️
   - Heart rate appears then disappears
   - May be related to talking (muscle artifacts affecting PPG)
   - **Fix Needed**: 
     - Better artifact detection for talking/chewing
     - Exclude PPG samples during muscle artifacts
     - Smoother HRV calculation with longer buffer
   - **Status**: Needs improvement

5. **TP9 Channel Always Problematic** ⚠️
   - TP9 (left ear) consistently shows extreme values (thousands of μV)
   - Other channels normal (<100 μV)
   - Likely causes:
     - Poor electrode contact (glasses interference)
     - How device is worn
     - Electrode placement issue
   - **Current Fix**: Bad channel detection excludes TP9 from averaging
   - **Status**: Working but needs better handling - maybe auto-exclude if consistently bad

6. **Talking Artifact Detection** ⚠️
   - Talking/chewing not reliably detected as artifact
   - Affects heart rate and brain state classification
   - **Fix Needed**: 
     - Improve muscle artifact detection (jaw movement)
     - Lower EMG frequency threshold
     - Use accelerometer for jaw movement detection
     - Mark as artifact during talking to exclude from analysis
   - **Status**: Needs enhancement

### Minor Issues

1. **ICA Calibration Required** - Must wait 30 seconds before artifact removal is active (by design)
2. **Artifact Detection Inconsistency** - Sometimes shows "clean" when brain state shows "artifact_detected"
   - **Status**: Partially fixed - now combines MNE + artifact detector + bad channels
3. **Brain State Classification** - Still shows "mixed" sometimes (reduced but not eliminated)

## Next Steps & Improvements

### Immediate (High Priority - Next Session)

1. **Fix HRV RMSSD Calculation** 🔴
   - Investigate why RMSSD shows 300-500ms (should be 20-100ms)
   - Check `hrv_calculator.py` peak detection and RR interval calculation
   - Verify timestamp handling (LSL timestamps vs real-time)
   - Test with known good PPG data

2. **Fix Posture UI Layout Shifts** 🔴
   - Use CSS Grid or Flexbox with fixed dimensions
   - Prevent text changes from causing layout reflow
   - Use absolute positioning for status text
   - Add CSS `will-change: contents` or similar optimizations

3. **Improve Posture Detection Stability** 🔴
   - Increase smoothing window from 15 to 30+ samples
   - Increase state lock duration from 10s to 15-20s
   - Better variance calculation (use rolling window)
   - Only change status if sustained change for 15+ seconds

4. **Enhance Talking Artifact Detection** 🔴
   - Improve muscle artifact detection in `artifact_detector.py`
   - Lower EMG frequency threshold (currently 50-100 Hz, try 40-120 Hz)
   - Use accelerometer for jaw movement (Y-axis changes)

5. **Better TP9 Handling** 🟡
   - Auto-exclude if consistently bad (>50% of time)
   - Show persistent warning if TP9 is always bad
   - Suggest electrode placement adjustments
   - Maybe use only 3 channels if TP9 is unreliable

6. **Stabilize Heart Rate Display** 🟡
   - Longer HRV buffer (currently 30s, try 60s)
   - Smooth heart rate over 5-10 second window
   - Don't show "0" or "--" if data is just calibrating
   - Show "Calibrating..." instead of disappearing

### Short-term (Medium Priority)
1. **ASR (Artifact Subspace Reconstruction)** - Add MNE's ASR for real-time artifact removal
2. **Adaptive thresholds** - Learn user-specific artifact thresholds over time
3. **Artifact timeline** - Show artifact history in UI
4. **Export functionality** - Save sessions with artifact annotations

### Long-term (Future)
1. **Machine learning classification** - Train model on user's brain states
2. **Multi-session baseline** - Learn user's baseline brain activity patterns
3. **Real-time feedback** - Audio/visual feedback for focus/relaxation states
4. **Integration with other apps** - API for other applications to use brain state data

## Trust & Verification

### How to Verify It's Working:
1. **Check backend logs**: `tail -f backend/backend.log`
2. **Check WebSocket messages**: Browser DevTools → Network → WS
3. **Test artifact removal**: Blink during ICA calibration, then after - should see difference
4. **Verify band powers**: Should see Delta/Theta/Alpha/Beta/Gamma percentages

### How to Improve:
1. **Tune thresholds** in `artifact_detector.py`
2. **Adjust ICA components** in `mne_processor.py` (currently 3 components)
3. **Improve classification** in `signal_processor.py` `get_brain_state()`
4. **Add more MNE features**: ASR (Artifact Subspace Reconstruction)

