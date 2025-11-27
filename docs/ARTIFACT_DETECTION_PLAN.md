# Enhanced Artifact Detection Plan

## Current Issues

1. **Simple amplitude threshold** - Only checks if amplitude > 100 μV
2. **No multi-sensor detection** - Not using accelerometer, gyroscope, or PPG
3. **No temporal pattern detection** - Can't detect eye blinks (characteristic spike pattern)
4. **No muscle artifact detection** - Chewing/talking creates high-frequency noise
5. **Electromagnetic interference** - Touching laptop causes 60Hz noise

## Available Sensors

Muse 2 provides:
- **EEG** (256 Hz, 4 channels): Brain activity
- **PPG** (64 Hz, 3 channels): Heart rate variability
- **ACC** (52 Hz, 3 channels): Accelerometer (motion detection)
- **GYRO** (52 Hz, 3 channels): Gyroscope (head movement, blinks)

## Enhanced Artifact Detection Strategy

### 1. Eye Blink Detection
**Method**: Use gyroscope + EEG pattern
- **Gyroscope**: Sharp rotation on Z-axis (upward head movement)
- **EEG Pattern**: High-amplitude spike (>200 μV) in frontal channels (AF7, AF8)
- **Duration**: 200-500ms
- **Shape**: Characteristic V-shaped spike

**Implementation**:
```python
def detect_eye_blink(eeg_data, gyro_data, timestamp_window):
    # Check gyroscope for upward rotation
    if gyro_z > threshold:
        # Check EEG for spike in frontal channels
        if max(abs(eeg_data[AF7]), abs(eeg_data[AF8])) > 200:
            # Check duration
            if 200 < duration < 500:
                return True
    return False
```

### 2. Muscle Artifact Detection (Chewing/Talking)
**Method**: High-frequency analysis + accelerometer
- **EEG**: High power in >50 Hz range (EMG frequency)
- **Accelerometer**: Jaw movement detected
- **Pattern**: Sustained high-frequency noise across channels

**Implementation**:
```python
def detect_muscle_artifact(eeg_data, acc_data, sample_rate):
    # Calculate power in EMG range (50-100 Hz)
    emg_power = calculate_band_power(eeg_data, 50, 100, sample_rate)
    
    # Check accelerometer for jaw movement
    jaw_movement = detect_jaw_movement(acc_data)
    
    if emg_power > threshold and jaw_movement:
        return True
    return False
```

### 3. Motion Artifact Detection
**Method**: Accelerometer + gyroscope correlation
- **Accelerometer**: Sudden acceleration changes
- **Gyroscope**: Rotation changes
- **EEG**: Correlated sudden changes in all channels

**Implementation**:
```python
def detect_motion_artifact(eeg_data, acc_data, gyro_data):
    # Calculate motion magnitude
    acc_magnitude = np.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
    gyro_magnitude = np.sqrt(gyro_x**2 + gyro_y**2 + gyro_z**2)
    
    # Check for sudden changes
    if abs(acc_magnitude - prev_acc) > threshold:
        # Check if EEG changes correlate
        if eeg_variance > threshold:
            return True
    return False
```

### 4. Electromagnetic Interference (60 Hz)
**Method**: Enhanced notch filtering + detection
- **Current**: Basic 60 Hz notch filter
- **Enhancement**: Adaptive notch filter that tracks interference
- **Detection**: Monitor 60 Hz power before/after filtering

**Implementation**:
```python
def detect_em_interference(eeg_data, sample_rate):
    # Calculate power at 60 Hz
    power_60hz = calculate_frequency_power(eeg_data, 59, 61, sample_rate)
    
    # If 60 Hz power is unusually high, likely interference
    if power_60hz > baseline_60hz * 2:
        return True
    return False
```

### 5. Statistical Artifact Detection
**Method**: Z-score based detection (more robust than fixed threshold)
- Calculate mean and std of signal
- Flag samples > 3 standard deviations
- More adaptive than fixed 100 μV threshold

**Implementation**:
```python
def detect_statistical_artifacts(eeg_data):
    mean = np.mean(eeg_data)
    std = np.std(eeg_data)
    
    # Z-score based detection
    z_scores = np.abs((eeg_data - mean) / std)
    
    # Flag if any sample > 3 std (99.7% confidence)
    if np.any(z_scores > 3):
        return True
    return False
```

## Implementation Steps

### Phase 1: Enable Multi-Sensor Streaming
1. Update muselsl command to include `--ppg --acc --gyro`
2. Create separate stream inlets for ACC, GYRO, PPG
3. Buffer data from all sensors with timestamp synchronization

### Phase 2: Basic Multi-Sensor Detection
1. Implement eye blink detection (gyroscope + EEG)
2. Implement motion detection (accelerometer)
3. Replace simple amplitude threshold with statistical detection

### Phase 3: Advanced Detection
1. Implement muscle artifact detection (EMG frequency analysis)
2. Implement electromagnetic interference detection
3. Combine all detection methods with confidence scores

### Phase 4: Artifact Handling
1. Mark artifact periods (don't delete, just flag)
2. Exclude artifacts from band power calculation
3. Show artifact timeline in UI
4. Allow user to review and adjust

## Artifact Classification

Instead of binary (artifact/no artifact), classify types:
- `eye_blink`: Eye blink detected
- `muscle`: Muscle artifact (chewing, talking)
- `motion`: Head movement
- `em_interference`: Electromagnetic interference
- `poor_contact`: Poor electrode contact (low signal)
- `clean`: No artifacts detected

## Integration with Brain State Classification

1. **Don't classify during artifacts** - Return "unknown" or "artifact_detected"
2. **Use artifact-free periods only** - Only calculate band powers from clean data
3. **Show confidence** - Lower confidence if artifacts were recently detected
4. **Temporal smoothing** - Use longer windows (3-5 seconds) to reduce artifact impact

## Next Steps

1. ✅ Fix web page crash (reduce debug data)
2. ⏭️ Enable multi-sensor streaming in muselsl
3. ⏭️ Create artifact detection module
4. ⏭️ Integrate with signal processing pipeline
5. ⏭️ Update UI to show artifact status

