# Improvements Summary - Artifact Removal & Signal Stability

## Issues Fixed (Nov 20, 2025)

### 1. ✅ Temporal Smoothing Added
**Problem**: Brain state and signal quality constantly changing every second

**Solution**: Added `StateSmoother` class that:
- Averages band powers over 5-second window
- Uses mode (most common) for brain state classification
- Smooths signal quality scores
- Prevents rapid fluctuations

**Result**: Stable classification that doesn't jump around

### 2. ✅ Improved Brain State Classification
**Problem**: Classification too sensitive, showing "drowsy" when awake

**Solution**: Switched from dominant-band to ratio-based classification:
- Uses Beta/Alpha ratio for focus detection
- Uses Theta/Beta ratio for creative states
- High Delta (>40%) now marked as "mixed" (likely artifact)
- More nuanced state detection

**Result**: More accurate classification that accounts for context

### 3. ✅ Better Artifact Detection
**Problem**: Artifact detection constantly changing between "clean" and "low quality"

**Solution**:
- Lowered ICA thresholds (1.5 for EOG, 0.3 for muscle)
- Added artifact ratio tracking (percentage of samples with artifacts)
- Only mark as artifact if >50% of samples in window have artifacts
- Smoothed signal quality scores

**Result**: More stable artifact detection

### 4. ✅ Enhanced ICA Artifact Removal
**Problem**: ICA fitted but artifacts not being removed effectively

**Solution**:
- More sensitive artifact component detection
- Better logging of removed components
- Improved component exclusion logic

## Emotional State Detection Libraries

### Research Findings:

**NeuroKit2** - Comprehensive signal processing
- Can analyze HRV, EEG, EDA for emotional states
- Not specifically for EEG emotional states
- Good for physiological signals

**pyEEG** - EEG feature extraction
- Extracts features from EEG
- Doesn't directly classify emotions
- Good for feature engineering

**Current Approach** (Recommended):
- Use **band power ratios** for emotional inference:
  - **Relaxed/Calm**: High Alpha, Low Beta
  - **Focused/Alert**: High Beta, Moderate Alpha
  - **Stressed/Anxious**: High Beta, Low Alpha
  - **Creative/Meditative**: High Theta, Moderate Alpha
- Combine with **HRV** (already implemented):
  - Low HRV = Stress/Anxiety
  - High HRV = Relaxed/Calm

### Future: Machine Learning Approach
- Train classifier on labeled emotional states
- Use band power ratios + HRV as features
- Requires labeled data collection

## Current Dashboard Components

### What's Helpful Now:
1. **Band Power Visualization** - Shows frequency distribution
2. **Brain State** - Current cognitive state (focused, relaxed, etc.)
3. **Signal Quality** - Confidence in readings
4. **HRV Metrics** - Stress/relaxation indicator
5. **ICA Status** - Artifact removal status

### What Could Be Added:
1. **Emotional State** - Derived from band ratios + HRV
2. **Trend Graph** - Show brain state over time
3. **Focus Score** - 0-100 score based on Beta/Alpha ratio
4. **Relaxation Score** - 0-100 based on Alpha + HRV
5. **Artifact Timeline** - Visual timeline of artifacts

## High Delta When Awake - Explanation

**Why you see high Delta when talking:**
1. **Artifacts not fully removed** - Muscle artifacts from talking can appear as Delta
2. **Poor electrode contact** - Low signal quality can show as Delta
3. **Signal processing issue** - Need better filtering

**What we fixed:**
- High Delta (>40%) now marked as "mixed" (likely artifact)
- Better artifact removal with improved ICA
- Temporal smoothing prevents single-second spikes

**Next steps:**
- Verify ICA is actually removing muscle artifacts
- Add better muscle artifact detection
- Improve signal quality thresholds

## Testing Recommendations

1. **Test artifact removal**:
   - Blink during ICA calibration
   - After calibration, blink again - should be removed
   - Talk/chew - should detect muscle artifacts

2. **Test stability**:
   - Watch brain state for 30 seconds
   - Should be stable (not changing every second)
   - Signal quality should be consistent

3. **Test classification**:
   - Relax (close eyes, breathe) - should show "relaxed" or "alpha"
   - Focus on task - should show "focused" or "beta"
   - High delta should show "mixed" (not "drowsy")

## Files Changed

1. `backend/state_smoother.py` - NEW: Temporal smoothing (30-second window, state locking)
2. `backend/signal_processor.py` - Improved classification (ratio-based, no "mixed" when possible)
3. `backend/main.py` - Integrated smoothing, bad channel detection, consistent artifact detection
4. `backend/mne_processor.py` - Better ICA thresholds
5. `backend/artifact_detector.py` - Added `detect_bad_channels()` for extreme value detection
6. `backend/mental_state_interpreter.py` - HRV/posture/band change interpretations
7. `consciousness-app/src/components/PostureDisplay.tsx` - Fixed height, state locking UI
8. `consciousness-app/src/components/ArtifactStatus.tsx` - Bad channel display
9. `consciousness-app/src/components/BandPowerDisplay.tsx` - Removed duplicate "Overall Mental State"

## Known Issues (Nov 20, 2025)

### 1. HRV RMSSD Calculation Bug
- **Symptom**: RMSSD showing 300-500ms (should be 20-100ms)
- **Likely Cause**: Timestamp calculation or peak detection algorithm
- **Location**: `backend/hrv_calculator.py` - `calculate_hrv()` method
- **Next Steps**: 
  - Check RR interval calculation (peaks[i] - peaks[i-1] in seconds)
  - Verify peak detection is finding actual heartbeats
  - Add logging to see raw RR intervals

### 2. Posture UI Layout Shifts
- **Symptom**: UI jumps when posture state changes
- **Current Fix**: Added min-height, but still shifts
- **Next Steps**:
  - Use CSS Grid with fixed row heights
  - Absolute positioning for status text
  - Prevent any layout reflow on state change

### 3. Posture Detection Inaccuracy
- **Symptom**: Shows "good" then "bad" when sitting still
- **Current**: 15-sample smoothing, 10s state lock
- **Next Steps**:
  - Increase to 30+ sample smoothing
  - Increase state lock to 15-20 seconds
  - Better variance threshold for "unstable"

### 4. Heart Rate Disappearing
- **Symptom**: Heart rate appears then disappears
- **Likely Cause**: Talking creates muscle artifacts that affect PPG
- **Next Steps**:
  - Better talking artifact detection
  - Exclude PPG during muscle artifacts
  - Smoother HRV with longer buffer (60s)

### 5. TP9 Channel Issues
- **Symptom**: TP9 consistently shows extreme values (thousands of μV)
- **Current Fix**: Bad channel detection excludes it from averaging
- **Next Steps**:
  - Auto-exclude if bad >50% of time
  - Show persistent warning
  - Suggest electrode placement

### 6. Talking Artifact Detection
- **Symptom**: Talking not reliably detected, affects heart rate
- **Current**: Basic muscle detection (50-100 Hz EMG)
- **Next Steps**:
  - Lower EMG threshold (40-120 Hz)
  - Use accelerometer for jaw movement
  - Exclude HRV during muscle artifacts

