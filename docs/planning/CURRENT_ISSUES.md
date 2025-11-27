# Current Issues & Next Steps - Consciousness OS

**Last Updated:** November 21, 2025

## Recently Fixed (Nov 21)

### ✅ Session Recording Implemented
- **New file**: `backend/session_recorder.py`
- API endpoints: `/api/session/start`, `/api/session/stop`, `/api/session/status`, `/api/session/marker`
- Saves: raw EEG (CSV), processed data (JSON), events, summary
- Sessions stored in `backend/sessions/` directory

### ✅ Talking Detector Implemented
- **New file**: `backend/talking_detector.py`
- Uses gyroscope to detect jaw movement (speech rhythm 2-5 Hz)
- Separate from EEG artifacts - allows recording brain activity during speech
- Added `is_talking`, `talking_confidence`, `talking_duration` to WebSocket broadcast

### ✅ HRV RMSSD Calculation Fixed
- Now uses `scipy.signal.find_peaks` for robust peak detection
- Added bandpass filter (0.5-4 Hz) to PPG signal
- Added debug logging for troubleshooting
- Expected values now: 20-100ms for healthy adults at rest

---

## Remaining Issues

### 1. HRV RMSSD Calculation Bug 🔴
**Problem:** RMSSD showing 300-500ms (should be 20-100ms for healthy adults)

**Symptoms:**
- RMSSD values way too high
- SDNN may also be incorrect
- Heart rate seems correct

**Likely Causes:**
- Timestamp calculation error in `hrv_calculator.py`
- Peak detection finding wrong peaks (not heartbeats)
- RR interval calculation using wrong units
- LSL timestamp vs real-time timestamp mismatch

**Investigation Steps:**
1. Check `hrv_calculator.py` `detect_peaks()` - verify it's finding actual heartbeats
2. Check `calculate_hrv()` - verify RR intervals are in milliseconds
3. Add logging to see raw RR intervals
4. Verify PPG data is valid (infrared channel extraction)
5. Test with known good PPG data

**Files to Check:**
- `backend/hrv_calculator.py` - Lines 58-100 (peak detection), 101-157 (HRV calculation)

---

### 2. Posture UI Layout Shifts 🔴
**Problem:** UI jumps/flickers when posture state changes

**Symptoms:**
- Layout shifts when text changes
- Cards resize when status updates
- "Waiting for sensor data" → "Good" causes jump

**Current Fix:**
- Added `min-h-[140px]` to posture card
- Still shifts slightly

**Better Fix Needed:**
- Use CSS Grid with fixed row heights
- Absolute positioning for status text
- Prevent any layout reflow
- Use `will-change: contents` or similar
- Fixed-width containers

**Files to Fix:**
- `consciousness-app/src/components/PostureDisplay.tsx`

---

### 3. Posture Detection Inaccuracy 🔴
**Problem:** Shows "good" then "bad" when sitting completely still

**Symptoms:**
- Posture status changes every few seconds
- False positives for movement
- Not detecting actual posture correctly

**Current Implementation:**
- 60-second history buffer
- 15-sample smoothing (15 seconds)
- 10-second state lock
- Variance detection (pitch_std > 10 or roll_std > 10)

**Fix Needed:**
- Increase smoothing window to 30+ samples (30 seconds)
- Increase state lock to 15-20 seconds
- Better variance threshold (maybe 15-20 instead of 10)
- Only change if sustained for longer period
- Better baseline establishment

**Files to Fix:**
- `backend/mental_state_interpreter.py` - `interpret_posture()` method
- `backend/main.py` - Posture state locking logic

---

### 4. Heart Rate Disappearing 🟡
**Problem:** Heart rate appears then disappears

**Symptoms:**
- Heart rate shows for a few seconds, then goes to "--"
- May be related to talking
- HRV also disappears

**Likely Causes:**
- Talking creates muscle artifacts
- Muscle artifacts affect PPG signal
- HRV calculation requires clean PPG data
- Buffer too short (30 seconds)

**Fix Needed:**
- Better talking artifact detection (see #5)
- Exclude PPG samples during muscle artifacts
- Longer HRV buffer (60 seconds instead of 30)
- Smoother heart rate display (don't show 0, show "Calibrating...")
- Don't mark as invalid if just one bad sample

**Files to Fix:**
- `backend/hrv_calculator.py` - Buffer size, validation logic
- `backend/main.py` - PPG exclusion during artifacts
- `consciousness-app/src/components/HRVDisplay.tsx` - Better "waiting" state

---

### 5. Talking Artifact Detection 🟡
**Problem:** Talking/chewing not reliably detected, affects heart rate and brain state

**Symptoms:**
- Heart rate disappears when talking
- Brain state shows artifacts when talking
- Not consistently detected as muscle artifact

**Current Implementation:**
- EMG frequency analysis (50-100 Hz power)
- Accelerometer jaw movement
- Threshold: 15% power in EMG range

**Fix Needed:**
- Lower EMG frequency range (40-120 Hz instead of 50-100 Hz)
- Lower EMG threshold (10% instead of 15%)
- Better accelerometer jaw detection (Y-axis changes)
- Use gyroscope for jaw movement
- Mark entire window as artifact when talking detected
- Exclude HRV/PPG during muscle artifacts

**Files to Fix:**
- `backend/artifact_detector.py` - `detect_muscle_artifact()` method
- `backend/main.py` - Exclude HRV during muscle artifacts

---

### 6. TP9 Channel Always Problematic 🟡
**Problem:** TP9 (left ear) consistently shows extreme values (thousands of μV)

**Symptoms:**
- TP9 values in thousands
- Other channels normal (<100 μV)
- Affects averaging and classification

**Likely Causes:**
- Poor electrode contact
- Glasses interference
- How device is worn
- Electrode placement

**Current Fix:**
- Bad channel detection (>200μV threshold)
- Excludes from averaging
- Shows in artifact status

**Better Fix Needed:**
- Auto-exclude if bad >50% of time
- Show persistent warning if TP9 consistently bad
- Suggest electrode placement adjustments
- Maybe use only 3 channels if TP9 unreliable
- User setting to permanently exclude TP9

**Files to Fix:**
- `backend/main.py` - Bad channel detection logic
- `consciousness-app/src/components/ArtifactStatus.tsx` - Persistent warnings

---

## Implementation Notes

### Posture UI Fix Strategy
```css
/* Use fixed grid layout */
.posture-card {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 200px; /* Fixed height */
}

.status-text {
  position: absolute; /* Or fixed height container */
  min-height: 60px;
}
```

### HRV RMSSD Debug Strategy
1. Log raw PPG values
2. Log detected peaks
3. Log RR intervals before calculation
4. Verify timestamps are in seconds
5. Check if peaks are actual heartbeats (should be ~0.8-1.2 seconds apart)

### Talking Detection Strategy
1. Lower EMG threshold to 10%
2. Expand frequency range to 40-120 Hz
3. Add accelerometer Y-axis variance (jaw movement)
4. Combine with gyroscope for better detection
5. Mark as artifact for entire 1-second window

---

## Priority Order

1. **HRV RMSSD Bug** - Critical, affects data accuracy
2. **Posture UI Layout** - Critical, affects UX
3. **Posture Detection** - High, affects trust in system
4. **Talking Detection** - High, affects heart rate stability
5. **TP9 Handling** - Medium, already partially working
6. **Heart Rate Stability** - Medium, related to #4

---

## Testing Checklist

After fixes, test:
- [ ] HRV RMSSD shows reasonable values (20-100ms)
- [ ] Posture UI doesn't jump when state changes
- [ ] Posture stays stable when sitting still
- [ ] Heart rate doesn't disappear when talking
- [ ] Talking is detected as artifact
- [ ] TP9 bad channel warning appears if consistently bad

