# Consciousness OS - Technical Implementation Plan

## Overview
This document outlines the step-by-step implementation plan for building the web app to connect to Muse 2, stream EEG data, process it, and extract meaningful insights.

**Current Status:** ✅ Web app successfully streaming live EEG data from Muse 2
**Architecture Change:** Switched from Electron to simple web app using muse-js + Web Bluetooth API
**Goal:** Build web app for real-time EEG data collection, visualization, and analysis

---

## Phase 1: Foundation & Muse Connection (Days 1-2)

### 1.1 Project Setup
- [ ] Initialize Electron project with TypeScript
  ```bash
  npm create @quick-start/electron consciousness-os
  cd consciousness-os
  npm install
  ```
- [ ] Configure TypeScript for both main and renderer processes
- [ ] Set up project structure:
  ```
  src/
  ├── main/           # Electron main process
  ├── renderer/       # React UI
  └── shared/         # Types and utilities
  ```
- [ ] Install ESLint and Prettier for code quality

### 1.2 Core Dependencies Installation
```json
{
  "dependencies": {
    "muse-js": "^4.0.0",              // Muse 2 Bluetooth connection
    "rxjs": "^7.8.0",                 // Reactive streams (used by muse-js)
    "web-bluetooth": "^1.0.0",        // Bluetooth API polyfill
    "react": "^18.2.0",               // UI framework
    "recharts": "^2.10.0"             // Charts for visualization
  },
  "devDependencies": {
    "electron": "^28.0.0",
    "typescript": "^5.0.0",
    "electron-builder": "^24.0.0",
    "@types/react": "^18.2.0"
  }
}
```

### 1.3 Basic UI Setup
- [ ] Create main window (800x600px)
- [ ] Build basic layout:
  - Header with app title
  - Connection status indicator
  - Device info display (battery, signal quality)
  - Main content area for data display
- [ ] Add "Connect to Muse" button
- [ ] Style with CSS (dark theme for better readability)

### 1.4 Muse 2 Bluetooth Connection
- [ ] Enable Web Bluetooth in Electron
  ```typescript
  // In main process
  webPreferences: {
    nodeIntegration: false,
    contextIsolation: true,
    enableBluetoothAPI: true
  }
  ```
- [ ] Implement device scanning
  - Scan for Muse devices
  - Display available devices in UI
  - Show device name and signal strength
- [ ] Implement connection logic
  - Connect to selected Muse device
  - Handle connection success/failure
  - Show connection status in UI
- [ ] Implement disconnect logic
  - Clean disconnect on user action
  - Handle unexpected disconnections
  - Show reconnection UI
- [ ] Add connection persistence
  - Remember last connected device
  - Auto-reconnect on app start (optional)

**Milestone:** Click "Connect" → See "Muse-XXXX Connected ✓"

---

## Phase 2: Real-Time Data Streaming (Days 3-4)

### 2.1 EEG Data Stream Setup
- [ ] Subscribe to EEG channels from muse-js
  ```typescript
  // 4 channels: TP9, AF7, AF8, TP10
  client.eegReadings.subscribe(reading => {
    // Process raw EEG data (256 samples/sec per channel)
  })
  ```
- [ ] Implement data buffer
  - Create circular buffer for each channel
  - Store last 10 seconds of data
  - Handle buffer overflow
- [ ] Add timestamp synchronization
  - Timestamp each sample
  - Handle clock drift
  - Sync with system time

### 2.2 Auxiliary Sensors
- [ ] Subscribe to PPG (heart rate) data
  ```typescript
  client.ppgReadings.subscribe(reading => {
    // Process PPG for heart rate
  })
  ```
- [ ] Subscribe to accelerometer data (for motion artifacts)
  ```typescript
  client.accelerometerData.subscribe(data => {
    // Detect head movement
  })
  ```
- [ ] Subscribe to gyroscope data
- [ ] Get battery level and update UI

### 2.3 Display Raw Data
- [ ] Create real-time data display component
- [ ] Show raw EEG values for all 4 channels
  - TP9 (left ear)
  - AF7 (left forehead)
  - AF8 (right forehead)
  - TP10 (right ear)
- [ ] Display as scrolling numbers (updating ~4 times/sec)
- [ ] Add signal quality indicator per channel
  - Green: Good signal (< 10% packet loss)
  - Yellow: Fair signal (10-25% packet loss)
  - Red: Poor signal (> 25% packet loss)
- [ ] Show sampling rate (should be 256 Hz)
- [ ] Display PPG heart rate if available

**Milestone:** See live numbers updating for all 4 EEG channels

---

## Phase 3: Signal Processing & Cleaning (Days 5-7)

### 3.1 Signal Processing Dependencies
```bash
npm install dsp.js fili mathjs
```
- [ ] Install DSP libraries
- [ ] Create signal processing module (`src/main/processing.ts`)

### 3.2 Noise Filtering
- [ ] Implement notch filter (50/60 Hz powerline noise)
  ```typescript
  // Remove electrical interference
  const notchFilter = createNotchFilter(60, 256); // 60Hz, 256Hz sample rate
  ```
- [ ] Implement bandpass filter (0.5-50 Hz)
  ```typescript
  // Keep only relevant EEG frequencies
  const bandpassFilter = createBandpassFilter(0.5, 50, 256);
  ```
- [ ] Apply filters to each channel in real-time
- [ ] Add filter bypass option (for debugging)

### 3.3 Artifact Detection & Removal
- [ ] Detect eye blink artifacts
  - High amplitude spikes (> 100 μV)
  - Duration < 500ms
  - Mark as artifact, don't delete
- [ ] Detect jaw clench artifacts
  - High frequency noise in all channels
  - Use EMG frequency range (> 50 Hz)
- [ ] Detect motion artifacts
  - Use accelerometer data
  - Correlate with sudden EEG changes
  - Flag sections with excessive movement
- [ ] Create artifact timeline
  - Mark artifact periods in data stream
  - Display in UI
  - Allow user to review

### 3.4 Data Quality Metrics
- [ ] Calculate signal-to-noise ratio (SNR) per channel
- [ ] Calculate electrode impedance (contact quality)
- [ ] Track packet loss rate
- [ ] Display quality metrics in UI
  - Overall quality score (0-100)
  - Per-channel quality
  - Artifact percentage
  - Recommendations for improvement

**Milestone:** See filtered data with quality indicators and artifact detection

---

## Phase 4: Feature Extraction & Understanding (Days 8-10)

### 4.1 Frequency Band Analysis
- [ ] Implement Fast Fourier Transform (FFT)
  ```typescript
  // Use 1-second windows with 50% overlap
  const fft = new FFT(256); // 256 samples = 1 second at 256 Hz
  ```
- [ ] Extract power in each frequency band:
  - **Delta (0.5-4 Hz):** Deep sleep, unconscious processing
  - **Theta (4-8 Hz):** Meditation, creativity, memory
  - **Alpha (8-13 Hz):** Relaxed, calm focus
  - **Beta (13-30 Hz):** Active thinking, anxiety, problem-solving
  - **Gamma (30-50 Hz):** Peak focus, information processing
- [ ] Calculate relative band power (% of total)
- [ ] Calculate absolute band power (μV²)
- [ ] Average across channels (or analyze per hemisphere)

### 4.2 Advanced Metrics
- [ ] Calculate band power ratios
  - Beta/Alpha ratio (stress indicator)
  - Theta/Beta ratio (relaxation indicator)
  - Alpha asymmetry (left vs right hemisphere)
- [ ] Calculate engagement score
  ```typescript
  engagement = beta / (alpha + theta)
  ```
- [ ] Calculate relaxation score
  ```typescript
  relaxation = alpha / beta
  ```
- [ ] Calculate mental workload
  ```typescript
  workload = (theta + alpha) / beta
  ```

### 4.3 Heart Rate Variability (HRV)
- [ ] Extract heart rate from PPG sensor
- [ ] Calculate inter-beat intervals (IBI)
- [ ] Calculate RMSSD (HRV metric)
  ```typescript
  // Root Mean Square of Successive Differences
  rmssd = sqrt(mean((IBI[i+1] - IBI[i])²))
  ```
- [ ] Display heart rate and HRV in UI

### 4.4 Live Visualization
- [ ] Create live band power charts (line chart)
  - X-axis: Time (last 60 seconds)
  - Y-axis: Power (0-100%)
  - 5 lines (one per band)
- [ ] Create frequency spectrum chart (bar chart)
  - Current frequency distribution
  - Update every 1 second
- [ ] Create brain state indicator
  - "Focused" - High beta, low alpha
  - "Relaxed" - High alpha, low beta
  - "Creative" - High theta, moderate alpha
  - "Drowsy" - High delta, low beta
  - Use color coding and emoji
- [ ] Add historical timeline
  - Scrollable view of past states
  - Show state changes over time

**Milestone:** See live brain state with band powers updating in real-time

---

## Phase 5: Session Recording (Days 11-12)

### 5.1 Session Management
- [ ] Add "Start Session" button
- [ ] Create session data structure
  ```typescript
  interface Session {
    id: string;                    // timestamp-based
    startTime: number;
    endTime: number;
    duration: number;
    rawEEG: number[][];           // [channel][samples]
    features: FeaturePoint[];      // band powers over time
    artifacts: ArtifactPeriod[];
    quality: QualityMetrics;
  }
  ```
- [ ] Implement session recording
  - Start collecting data on button press
  - Store in memory during session
  - Show recording indicator (time elapsed)
- [ ] Add "Stop Session" button
- [ ] Save session data on stop

### 5.2 Data Storage
- [ ] Create local storage directory
  ```
  ~/ConsciousnessOS/sessions/
    └── YYYY-MM-DD_HHmm/
        ├── raw_eeg.csv
        ├── features.json
        └── metadata.json
  ```
- [ ] Save raw EEG data to CSV
  ```csv
  timestamp,TP9,AF7,AF8,TP10
  1700493720.001,123.4,98.2,101.5,115.3
  ```
- [ ] Save processed features to JSON
  ```json
  {
    "timestamp": 1700493720,
    "delta": 0.23,
    "theta": 0.45,
    "alpha": 0.78,
    "beta": 0.92,
    "gamma": 0.34
  }
  ```
- [ ] Save session metadata (duration, quality, notes)

### 5.3 Session History
- [ ] Create sessions list UI
- [ ] Display past sessions
  - Date/time
  - Duration
  - Quality score
  - Brief summary
- [ ] Implement session loading
  - Load and display past session data
  - Show charts from past sessions
  - Compare multiple sessions

**Milestone:** Record a 5-minute session, stop it, see it saved and viewable

---

## Phase 6: Testing & Validation (Days 13-14)

### 6.1 Data Quality Validation
- [ ] Record 5+ test sessions with different conditions:
  - Eyes open vs closed
  - Sitting still vs moving
  - Focused work vs relaxation
  - Talking vs silent
- [ ] Analyze data quality
  - Check artifact detection accuracy
  - Verify band power calculations
  - Compare with known EEG patterns
- [ ] Document artifacts and their causes
  - What triggers eye blink detection?
  - What causes signal loss?
  - How does movement affect data?

### 6.2 Feature Validation
- [ ] Test known mental states
  - Meditation (should show high alpha)
  - Math problems (should show high beta)
  - Closing eyes (should show alpha increase)
  - Relaxation (should show low beta)
- [ ] Verify band power changes
  - Do values match expected patterns?
  - Are changes consistent across sessions?
  - Can you reproduce results?

### 6.3 UI/UX Polish
- [ ] Add keyboard shortcuts
  - Spacebar: Start/Stop session
  - C: Connect/Disconnect
  - R: Refresh device list
- [ ] Add error handling and user feedback
  - Connection errors
  - Data quality warnings
  - Storage errors
- [ ] Add loading states
- [ ] Improve visual design
- [ ] Add tooltips and help text

**Milestone:** Reliable app that consistently captures clean EEG data

---

## File Structure

```
consciousness-os/
├── src/
│   ├── main/
│   │   ├── index.ts              # Electron main process
│   │   ├── muse.ts               # Muse connection logic
│   │   ├── processing.ts         # Signal processing
│   │   ├── features.ts           # Feature extraction
│   │   ├── storage.ts            # File system operations
│   │   └── ipc-handlers.ts       # IPC communication
│   ├── renderer/
│   │   ├── App.tsx               # Main React component
│   │   ├── components/
│   │   │   ├── MuseConnect.tsx   # Connection UI
│   │   │   ├── LiveData.tsx      # Raw data display
│   │   │   ├── BandPowerCharts.tsx # Visualizations
│   │   │   ├── SessionControl.tsx  # Start/stop recording
│   │   │   ├── SessionHistory.tsx  # Past sessions
│   │   │   └── QualityIndicator.tsx # Signal quality
│   │   ├── hooks/
│   │   │   ├── useMuse.ts        # Muse connection hook
│   │   │   └── useSession.ts     # Session management hook
│   │   └── styles/
│   └── shared/
│       ├── types.ts              # TypeScript interfaces
│       └── constants.ts          # App constants
├── data/
│   └── sessions/                 # Local session storage
├── package.json
├── tsconfig.json
└── electron-builder.json
```

---

## Key Technical Decisions

### 1. Muse-JS Library
- Use `muse-js` for Bluetooth connectivity
- Works with Web Bluetooth API (supported in Electron)
- Actively maintained, good documentation
- RxJS-based reactive streams

### 2. Signal Processing
- Real-time processing (not batch)
- Use 1-second FFT windows with 50% overlap
- Apply filters before FFT
- Keep raw data separate from processed data

### 3. Data Storage
- Local files only (no database yet)
- CSV for raw data (easy to export/analyze)
- JSON for processed features (easy to parse)
- One folder per session

### 4. UI Framework
- React for renderer process
- Recharts for visualizations
- IPC for main/renderer communication
- Real-time updates via event emitters

---

## Current Progress (Updated: 2025-01-20)

### ✅ Completed
- [x] Web app architecture (Vite + React + TypeScript)
- [x] Muse 2 Bluetooth connection via Web Bluetooth API
- [x] Live EEG data streaming (256 Hz, 4 channels)
- [x] Real-time waveform visualization (with debug toggle)
- [x] Basic UI with connection status

### 🚧 In Progress
- [ ] Signal filtering (notch + bandpass filters)
- [ ] Frequency band analysis (delta, theta, alpha, beta, gamma)
- [ ] Band power extraction and visualization

### 📋 Next Up
- [ ] Artifact detection (eye blinks, jaw clenches, motion)
- [ ] Data quality metrics
- [ ] Session recording and storage
- [ ] Audio recording integration
- [ ] Transcription with Whisper
- [ ] AI analysis with Claude

---

## Success Criteria

### Phase 1-2: Connection & Streaming ✅ COMPLETED
- [x] App connects to Muse 2 via Bluetooth (Web Bluetooth)
- [x] Raw EEG data streams at 256 Hz
- [x] All 4 channels display live values
- [x] Connection working and verified with official Muse app

### Phase 3: Signal Processing 🚧 IN PROGRESS
- [ ] Filters remove noise effectively
- [ ] Artifacts detected accurately
- [ ] Data quality metrics displayed
- [ ] Signal quality indicators working

### Phase 4: Feature Extraction 📋 NEXT
- [ ] Band powers calculated correctly
- [ ] Charts update in real-time
- [ ] Brain state indicator makes sense
- [ ] Values change with mental state

### Phase 5-6: Recording & Testing 📋 FUTURE
- [ ] Can record 15+ minute sessions
- [ ] Sessions save and load correctly
- [ ] Recorded 10+ diverse test sessions
- [ ] Data quality consistently good

---

## Next Steps After Phase 6

1. **Audio Recording Integration**
   - Add system audio capture
   - Sync audio with EEG timeline
   - Save audio files with sessions

2. **Transcription**
   - Integrate Whisper (local or API)
   - Transcribe audio after session
   - Add timestamps to transcript

3. **AI Analysis**
   - Integrate Claude API
   - Match transcript with brain states
   - Generate insights

4. **Full Validation**
   - 10+ sessions with conversations
   - Analyze correlations
   - Determine if concept works

---

## Getting Started

### Today:
1. Set up Electron project
2. Install dependencies
3. Create basic UI
4. Test app launches

### Tomorrow:
1. Implement Muse connection
2. Test with your Muse 2
3. Display raw data
4. Verify streaming works

### This Week:
1. Complete Phases 1-4
2. Get clean, processed data
3. Build visualizations
4. Record first test sessions

---

## Notes & Considerations

### Bluetooth Permissions
- MacOS requires Bluetooth permissions
- Add to Info.plist:
  ```xml
  <key>NSBluetoothAlwaysUsageDescription</key>
  <string>This app needs Bluetooth to connect to Muse EEG headband</string>
  ```

### Performance
- EEG at 256 Hz = ~1000 samples/sec (4 channels)
- FFT every 1 second (manageable)
- Use Web Workers if UI becomes laggy
- Throttle chart updates to 30 FPS max

### Data Privacy
- All data stays local
- No network requests (except AI APIs later)
- User owns all data files
- Easy to export/delete

### Testing Tips
- Test with Muse properly positioned on head
- Ensure good electrode contact (use moisture)
- Minimize movement during recording
- Close eyes briefly to test alpha detection
- Do mental math to test beta detection

---

## Resources

- Muse-JS Docs: https://github.com/urish/muse-js
- EEG Band Powers: https://en.wikipedia.org/wiki/Electroencephalography
- DSP Guide: https://www.dspguide.com/
- Electron Docs: https://www.electronjs.org/docs/latest/

---

**Ready to start building! 🧠**
