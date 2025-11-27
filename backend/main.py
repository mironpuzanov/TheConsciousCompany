"""
Consciousness OS - Python Backend
FastAPI server with WebSocket for real-time EEG streaming
"""

import asyncio
import logging
import numpy as np
import time
from collections import deque
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json

from muse_stream import MuseStreamer
from signal_processor import SignalProcessor, get_brain_state
from artifact_detector import ArtifactDetector
from hrv_calculator import HRVCalculator
from mne_processor import MNEProcessor
from state_smoother import StateSmoother
from mental_state_interpreter import MentalStateInterpreter
from session_recorder import session_recorder
from talking_detector import TalkingDetector
try:
    from conversation_analyzer.backend.routes import router as conversation_router
    HAS_CONVERSATION_ANALYZER = True
except ImportError:
    conversation_router = None
    HAS_CONVERSATION_ANALYZER = False

# AI Co-Pilot imports (optional - disable if dependencies not installed)
try:
    from copilot_session import CopilotSession
    COPILOT_AVAILABLE = True
except ImportError as e:
    COPILOT_AVAILABLE = False
    CopilotSession = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Consciousness OS Backend")
if HAS_CONVERSATION_ANALYZER:
    app.include_router(conversation_router)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
muse_streamer = MuseStreamer()
signal_processor = SignalProcessor()  # Keep for band power calculation
mne_processor = MNEProcessor()  # MNE-based artifact removal
artifact_detector = ArtifactDetector()
hrv_calculator = HRVCalculator()
state_smoother = StateSmoother(window_size=10)  # 10-second smoothing for better responsiveness to cognitive changes
mental_state_interpreter = MentalStateInterpreter()
talking_detector = TalkingDetector()  # Gyroscope-based talking detection

# Cognitive metrics smoothing (shorter window for responsiveness)
from collections import deque
cognitive_load_history = deque(maxlen=8)  # 8-second window for cognitive load
stress_history = deque(maxlen=8)  # 8-second window for stress

# AI Co-Pilot instance
copilot_session: Optional[CopilotSession] = None
copilot_brain_state: Optional[dict] = None  # Latest brain state for copilot

# Posture smoothing buffer with state locking
posture_history: deque = deque(maxlen=60)  # 60 seconds of posture data
posture_current_status: Optional[str] = None
posture_change_time: float = 0.0
POSTURE_MIN_DURATION: float = 10.0  # Minimum 10 seconds before posture status can change

# Stream monitoring
_last_data_received = 0.0  # Timestamp of last data received
STREAM_TIMEOUT = 5.0  # Consider stream dead if no data for 5 seconds

# ICA fitting state
ica_fitted = False
ica_fit_buffer = []  # Buffer for initial ICA fitting
ica_fit_progress = 0  # Progress percentage (0-100)

# Buffer to accumulate samples for processing
# We'll process every 1 second (256 samples)
BUFFER_SIZE = 256
eeg_buffer = {
    0: deque(maxlen=BUFFER_SIZE),  # TP9
    1: deque(maxlen=BUFFER_SIZE),  # AF7
    2: deque(maxlen=BUFFER_SIZE),  # AF8
    3: deque(maxlen=BUFFER_SIZE),  # TP10
}

# Throttle EEG data sends to frontend (20 Hz instead of 256 Hz)
_last_eeg_send_time = 0.0
EEG_SEND_INTERVAL = 0.05  # 50ms = 20 Hz


def get_session_context() -> Dict[str, bool]:
    """
    Get current session context (meditation vs conversation)
    
    Returns:
        Dict with 'is_meditation' and 'is_conversation' flags
    """
    if not session_recorder.is_recording or not session_recorder.current_session:
        return {'is_meditation': False, 'is_conversation': False}
    
    tags = session_recorder.current_session.tags or []
    is_meditation = 'meditation' in [t.lower() for t in tags]
    is_conversation = 'conversation' in [t.lower() for t in tags] or 'chat' in [t.lower() for t in tags]
    
    return {
        'is_meditation': is_meditation,
        'is_conversation': is_conversation
    }


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        import numpy as np
        
        # Convert numpy types to Python native types for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            return obj
        
        try:
            json_message = convert_numpy(message)
        except Exception as e:
            logger.error(f"Error converting message to JSON: {e}", exc_info=True)
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(json_message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}", exc_info=True)
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)


manager = ConnectionManager()


async def process_sensor_data(eeg_samples: np.ndarray, eeg_timestamp: float,
                              ppg_data: Optional[np.ndarray] = None,
                              acc_data: Optional[np.ndarray] = None,
                              gyro_data: Optional[np.ndarray] = None):
    """
    Process incoming sensor data from all sources and broadcast to clients

    Args:
        eeg_samples: EEG samples [n_samples, n_channels]
        eeg_timestamp: LSL timestamp for EEG
        ppg_data: PPG data [ambient, infrared, red] or None
        acc_data: Accelerometer data [x, y, z] or None
        gyro_data: Gyroscope data [x, y, z] or None
    """
    try:
        # Validate input
        if eeg_samples is None or eeg_samples.shape[0] == 0:
            logger.warning("Received empty EEG samples, skipping...")
            return
        
        # Update stream monitoring (use current time, not LSL timestamp)
        global _last_data_received
        _last_data_received = time.time()
        
        # Update HRV calculator with PPG data (PPG comes at 64 Hz)
        if ppg_data is not None:
            try:
                # Log periodically to debug
                if not hasattr(process_sensor_data, '_ppg_log_counter'):
                    process_sensor_data._ppg_log_counter = 0
                process_sensor_data._ppg_log_counter += 1
                
                if process_sensor_data._ppg_log_counter % 500 == 0:
                    logger.info(f"PPG data received: shape={ppg_data.shape if hasattr(ppg_data, 'shape') else type(ppg_data)}, data={ppg_data}")
                
                hrv_calculator.update_ppg(ppg_data, eeg_timestamp)
            except Exception as e:
                logger.warning(f"Error updating PPG: {e}", exc_info=True)
        else:
            if not hasattr(process_sensor_data, '_ppg_log_counter'):
                process_sensor_data._ppg_log_counter = 0
            process_sensor_data._ppg_log_counter += 1
            if process_sensor_data._ppg_log_counter % 1000 == 0:
                logger.warning("PPG data is None - check if Muse PPG stream is connected")

        # Add EEG samples to buffers
        for i in range(eeg_samples.shape[0]):
            for ch in range(min(4, eeg_samples.shape[1])):  # Handle variable channel count
                if ch < len(eeg_buffer):
                    eeg_buffer[ch].append(eeg_samples[i, ch])

    # Send raw data (last sample from each channel)
        # Throttle to ~20 Hz (every 50ms) to avoid overwhelming the frontend
        # We still process all samples for band power calculation
        global _last_eeg_send_time
        if eeg_samples.shape[0] > 0:
            last_sample = eeg_samples[-1, :]
            # Ensure we only send 4 channels
            data_to_send = last_sample[:4].tolist() if len(last_sample) >= 4 else last_sample.tolist()
            
            # Only send if enough time has passed (throttle to ~20 Hz)
            current_time = eeg_timestamp
            if current_time - _last_eeg_send_time >= EEG_SEND_INTERVAL:
                _last_eeg_send_time = current_time
                
                # Get HRV metrics (updated every second)
                hrv_metrics = hrv_calculator.get_current_metrics()
                
                # Include HRV in EEG data if we have any heart rate value
                eeg_broadcast = {
                    'type': 'eeg_data',
                    'timestamp': float(eeg_timestamp),
                    'data': [float(x) for x in data_to_send],  # Ensure all floats
                }
                
                # Add HRV if we have heart rate > 0 (even if partial/cached)
                if hrv_metrics.get('heart_rate', 0) > 0:
                    eeg_broadcast['heart_rate'] = float(hrv_metrics.get('heart_rate', 0))
                    eeg_broadcast['hrv_rmssd'] = float(hrv_metrics.get('hrv_rmssd', 0))
                    eeg_broadcast['hrv_sdnn'] = float(hrv_metrics.get('hrv_sdnn', 0))
                
                await manager.broadcast(eeg_broadcast)

        # Process band powers every BUFFER_SIZE samples (1 second)
        if len(eeg_buffer[0]) >= BUFFER_SIZE:
            try:
                # Get session context early for use throughout processing
                session_context = get_session_context()

                # Prepare data for MNE processing [n_channels, n_samples]
                eeg_for_mne = np.array([list(eeg_buffer[ch]) for ch in range(4)])  # [4, 256]
                
                # Detect bad channels (extreme values = poor contact)
                bad_channels = artifact_detector.detect_bad_channels(eeg_for_mne.T, threshold=200)  # 200μV threshold
                
                # Log channel amplitudes periodically for diagnostics
                if not hasattr(process_sensor_data, '_channel_log_counter'):
                    process_sensor_data._channel_log_counter = 0
                process_sensor_data._channel_log_counter += 1
                
                if process_sensor_data._channel_log_counter % 60 == 0:  # Every 60 seconds
                    channel_amplitudes = np.max(np.abs(eeg_for_mne), axis=1)  # Max abs value per channel
                    channel_names = ['TP9', 'AF7', 'AF8', 'TP10']
                    logger.info(f"Channel amplitudes (max abs): {dict(zip(channel_names, [f'{a:.1f}μV' for a in channel_amplitudes]))}")
                    if np.max(channel_amplitudes) > 150:
                        logger.warning(f"High channel amplitude detected! Max: {np.max(channel_amplitudes):.1f}μV at {channel_names[np.argmax(channel_amplitudes)]}")
                
                # Exclude bad channels from averaging
                good_channels = [ch for ch in range(4) if ch not in bad_channels]
                if len(good_channels) == 0:
                    # All channels bad - use all but mark as artifact
                    good_channels = list(range(4))
                    logger.warning("All channels have extreme values - using all channels but marking as artifact")
                elif len(bad_channels) > 0:
                    logger.warning(f"Bad channels detected: {bad_channels} (TP9={0 in bad_channels}, AF7={1 in bad_channels}, AF8={2 in bad_channels}, TP10={3 in bad_channels})")
                
                # Average across good channels only
                avg_signal = np.mean([list(eeg_buffer[ch]) for ch in good_channels], axis=0)
                
                # Fit ICA on first 30 seconds of data
                global ica_fitted, ica_fit_buffer, ica_fit_progress
                if not ica_fitted:
                    # We're already in the block where buffer is full, so add to ICA buffer
                    ica_fit_buffer.append(eeg_for_mne.copy())
                    ica_fit_progress = min(100, int((len(ica_fit_buffer) / 30) * 100))
                    
                    # Log progress every 5 seconds
                    if len(ica_fit_buffer) % 5 == 0:
                        logger.info(f"ICA calibration: {ica_fit_progress}% ({len(ica_fit_buffer)}/30 seconds)")
                    
                    if len(ica_fit_buffer) >= 30:  # 30 seconds
                        try:
                            # Concatenate and fit ICA
                            ica_data = np.concatenate(ica_fit_buffer, axis=1)
                            logger.info(f"Fitting ICA with {ica_data.shape[1]} samples ({ica_data.shape[1]/256:.1f} seconds)...")
                            mne_processor.fit_ica(ica_data, n_components=3)
                            ica_fitted = True
                            ica_fit_progress = 100
                            logger.info("✅ ICA fitted - ready for artifact removal")
                            ica_fit_buffer = []  # Clear buffer
                        except Exception as e:
                            logger.error(f"Error fitting ICA: {e}", exc_info=True)
                            # Reset and try again
                            ica_fit_buffer = []
                            ica_fit_progress = 0
                
                # Process with MNE (applies filters + ICA if fitted)
                try:
                    mne_result = mne_processor.process_window(eeg_for_mne, apply_ica=ica_fitted)
                except Exception as e:
                    logger.error(f"Error in MNE processing: {e}", exc_info=True)
                    # Fallback to basic processing without MNE
                    avg_signal = np.mean([list(eeg_buffer[ch]) for ch in range(4)], axis=0)
                    result = signal_processor.process_window(avg_signal)
                    mne_result = {
                        'filtered_data': [avg_signal.tolist()],
                        'quality': {'confidence': 50, 'snr': 0, 'bad_channels': []},
                        'has_artifact': True
                    }
                    # Continue processing with fallback
                
                # Get cleaned data for band power calculation
                try:
                    cleaned_data = np.array(mne_result['filtered_data']).T  # Back to [n_channels, n_samples]
                    if cleaned_data.shape[0] > 0 and cleaned_data.shape[1] > 0:
                        avg_cleaned = np.mean(cleaned_data, axis=0)  # Average across channels
                    else:
                        # Fallback to original signal
                        avg_cleaned = avg_signal
                    
                    # Calculate band powers from cleaned signal (using good channels only)
                    result = signal_processor.process_window(avg_cleaned)
                    
                    # If we excluded bad channels, note it in the result
                    if len(bad_channels) > 0:
                        logger.debug(f"Excluded {len(bad_channels)} bad channel(s) from averaging: {bad_channels}")
                except Exception as e:
                    logger.error(f"Error processing cleaned data: {e}", exc_info=True)
                    # Fallback to basic processing
                    result = signal_processor.process_window(avg_signal)
                    mne_result = {
                        'quality': {'confidence': 30, 'snr': 0, 'bad_channels': []},
                        'has_artifact': True
                    }
                
                # Use MNE quality metrics
                signal_quality_score = mne_result['quality']['confidence']

                # Get session context for is_meditation flag
                is_meditation = session_context.get('is_meditation', False)

                # Check artifact detector for consistency (with context-aware handling)
                artifact_result = artifact_detector.detect_all(
                    eeg_for_mne.T,  # [n_samples, n_channels]
                    acc_data,
                    gyro_data,
                    is_meditation=is_meditation
                )
                
                # Combine artifact detection: MNE + artifact detector + bad channels
                has_artifact = (
                    mne_result['has_artifact'] or 
                    signal_quality_score < 50 or 
                    artifact_result.get('has_artifact', False) or
                    len(bad_channels) > 0  # Bad channels = artifact
                )
                
                # Determine brain state (context-aware: for meditation, use band powers directly)
                # For meditation: ignore artifact classification, use band powers
                # For conversation: use artifact-aware classification
                if is_meditation:
                    # Meditation: Always use band powers, ignore artifact classification
                    raw_brain_state = get_brain_state(result['band_powers'], is_meditation=True)
                elif not has_artifact and signal_quality_score > 50:
                    # Conversation: Standard artifact-aware classification
                    raw_brain_state = get_brain_state(result['band_powers'], is_meditation=False)
                else:
                    raw_brain_state = 'artifact_detected' if has_artifact else 'low_confidence'
                
                # Add to smoothing buffer
                try:
                    state_smoother.add_sample(
                        result['band_powers'],
                        signal_quality_score,
                        raw_brain_state,
                        has_artifact
                    )
                    
                    # Get smoothed values
                    smoothed_band_powers = state_smoother.get_smoothed_band_powers() or result['band_powers']
                    smoothed_quality = state_smoother.get_smoothed_signal_quality()
                    smoothed_brain_state = state_smoother.get_smoothed_brain_state()
                    artifact_ratio = state_smoother.get_artifact_ratio()
                    
                    # Always use smoothed brain state (it has built-in stability checks)
                    brain_state = smoothed_brain_state
                    
                    # Only recalculate if we have a stable, clean signal
                    if state_smoother.is_stable() and artifact_ratio < 0.3 and smoothed_quality > 60:
                        # Recalculate from smoothed band powers for better accuracy
                        if smoothed_brain_state not in ['artifact_detected', 'low_confidence', 'unknown', 'mixed']:
                            recalculated_state = get_brain_state(smoothed_band_powers, is_meditation=is_meditation)
                            # Only use recalculated if it's more specific than current
                            if recalculated_state != 'mixed':
                                brain_state = recalculated_state
                    
                    # Update has_artifact based on artifact ratio
                    has_artifact = artifact_ratio > 0.5  # More than 50% of samples have artifacts
                    
                    # Update previous band powers for change detection
                    state_smoother.update_previous_band_powers(smoothed_band_powers)
                except Exception as e:
                    logger.error(f"Error in state smoothing: {e}", exc_info=True)
                    # Use raw values if smoothing fails
                    smoothed_band_powers = result['band_powers']
                    smoothed_quality = signal_quality_score
                    brain_state = raw_brain_state
                    artifact_ratio = 0.0

                # Get HRV metrics (calculate every second)
                try:
                    hrv_metrics = hrv_calculator.get_current_metrics()
                    # Log HRV status periodically for debugging
                    if not hasattr(process_sensor_data, '_hrv_log_counter'):
                        process_sensor_data._hrv_log_counter = 0
                    process_sensor_data._hrv_log_counter += 1
                    
                    if process_sensor_data._hrv_log_counter % 60 == 0:  # Every 60 seconds
                        logger.info(f"HRV metrics: valid={hrv_metrics.get('valid', False)}, heart_rate={hrv_metrics.get('heart_rate', 0):.1f}, buffer_size={len(hrv_calculator.ppg_buffer)}, peaks={len(hrv_calculator.peak_times)}")
                    
                    # If not valid but we have a heart rate, use it
                    if not hrv_metrics.get('valid', False) and hrv_metrics.get('heart_rate', 0) > 0:
                        # Allow showing heart rate even if not fully valid (partial data is better than nothing)
                        hrv_metrics['valid'] = True
                except Exception as e:
                    logger.warning(f"Error calculating HRV: {e}", exc_info=True)
                    hrv_metrics = {'heart_rate': 0, 'hrv_rmssd': 0, 'hrv_sdnn': 0, 'valid': False}
                
                # Interpret HRV
                hrv_interpretation = mental_state_interpreter.interpret_hrv(
                    hrv_metrics.get('hrv_rmssd', 0),
                    hrv_metrics.get('hrv_sdnn', 0),
                    hrv_metrics.get('heart_rate', 0)
                )
                
                # Interpret posture with smoothing and state locking
                global posture_history, posture_current_status, posture_change_time
                
                # Log ACC/GYRO data periodically for debugging
                if not hasattr(process_sensor_data, '_acc_log_counter'):
                    process_sensor_data._acc_log_counter = 0
                process_sensor_data._acc_log_counter += 1
                
                if process_sensor_data._acc_log_counter % 500 == 0:
                    logger.info(f"ACC data: {acc_data is not None}, GYRO data: {gyro_data is not None}, posture_history size: {len(posture_history)}")
                
                # Always try to get posture data (don't skip if acc_data is None - use history)
                if acc_data is not None and len(acc_data) >= 3:
                    # Calculate current posture
                    x, y, z = acc_data[0], acc_data[1], acc_data[2]
                    magnitude = np.sqrt(x**2 + y**2 + z**2)
                    if magnitude > 0.5:
                        x_norm = x / magnitude
                        y_norm = y / magnitude
                        pitch = np.arcsin(-x_norm) * 180 / np.pi
                        roll = np.arcsin(y_norm) * 180 / np.pi
                        posture_history.append({'pitch': pitch, 'roll': roll, 'timestamp': eeg_timestamp})
                
                # Get raw posture interpretation (will use history if acc_data is None)
                raw_posture = mental_state_interpreter.interpret_posture(
                    gyro_data, acc_data, list(posture_history)
                )
                
                # Apply state locking (similar to brain state)
                current_time = time.time()
                new_status = raw_posture.get('status', 'Analyzing...')
                
                # Never show "No posture data" once we have any history - show "Analyzing..." instead
                if new_status == 'No posture data' and len(posture_history) > 0:
                    new_status = 'Analyzing...'
                    raw_posture['status'] = 'Analyzing...'
                    raw_posture['meaning'] = 'Calibrating posture detection...'
                
                if posture_current_status is None:
                    # First reading - wait for more data before showing
                    if len(posture_history) >= 5:
                        posture_current_status = new_status
                        posture_change_time = current_time
                        posture_interpretation = raw_posture
                    else:
                        # Not enough data yet - show analyzing
                        posture_interpretation = {
                            'status': 'Analyzing...',
                            'meaning': 'Calibrating posture detection...',
                            'recommendation': ''
                        }
                elif new_status != posture_current_status:
                    # Status changed - check if enough time has passed
                    time_since_change = current_time - posture_change_time
                    if time_since_change >= POSTURE_MIN_DURATION:
                        # Enough time passed - allow change
                        posture_current_status = new_status
                        posture_change_time = current_time
                        posture_interpretation = raw_posture
                    else:
                        # Not enough time - keep current status but update values
                        posture_interpretation = raw_posture.copy()
                        posture_interpretation['status'] = posture_current_status
                else:
                    # Same status - update values
                    posture_interpretation = raw_posture
                
                # Interpret band changes
                previous_band_powers = state_smoother.get_previous_band_powers()
                band_change_interpretation = mental_state_interpreter.interpret_band_changes(
                    smoothed_band_powers,
                    previous_band_powers
                )
                
                # Skip comprehensive state - it's redundant with current state
                comprehensive_state = None

                # Get session context for context-aware processing
                session_context = get_session_context()
                is_meditation = session_context.get('is_meditation', False)
                
                # Detect talking using gyroscope (with context-aware threshold)
                talking_result = talking_detector.update(gyro_data, acc_data, eeg_timestamp, is_meditation=is_meditation)
                is_talking = talking_result.get('is_talking', False)

                # If talking detected, mark as talking artifact but KEEP brain activity data
                # This allows us to analyze brain activity during speech later
                if is_talking:
                    # Add event to session if recording
                    if session_recorder.is_recording and not getattr(talking_detector, '_last_talking_event', False):
                        session_recorder.add_event('talking', 'Talking detected', {
                            'confidence': talking_result.get('confidence', 0),
                            'duration': talking_result.get('duration', 0)
                        })
                        talking_detector._last_talking_event = True
                elif getattr(talking_detector, '_last_talking_event', False):
                    if session_recorder.is_recording:
                        session_recorder.add_event('talking_stopped', 'Talking stopped', {
                            'duration': talking_result.get('duration', 0)
                        })
                    talking_detector._last_talking_event = False

                # Update AI Co-Pilot brain state (every second)
                global copilot_brain_state

                # Extract band powers with bounds checking
                beta = max(0.0, min(100.0, smoothed_band_powers.get('beta', 0)))
                gamma = max(0.0, min(100.0, smoothed_band_powers.get('gamma', 0)))
                alpha = max(0.0, min(100.0, smoothed_band_powers.get('alpha', 0)))
                theta = max(0.0, min(100.0, smoothed_band_powers.get('theta', 0)))
                delta = max(0.0, min(100.0, smoothed_band_powers.get('delta', 0)))

                # Calculate raw cognitive load from EEG
                raw_cognitive_load = min(max((beta + gamma) / 200.0, 0.0), 1.0)
                cognitive_load_history.append(raw_cognitive_load)
                smoothed_cognitive_load = float(np.mean(cognitive_load_history))  # 8-second average

                # Calculate stress from beta waves + heart rate
                # Stress = 60% beta waves + 40% heart rate deviation from resting (70 bpm)
                beta_stress = beta / 100.0  # 0-1
                hr = hrv_metrics.get('heart_rate', 70)
                hr_stress = min(max((hr - 70) / 50.0, 0.0), 1.0)  # Normalized: 70=0%, 120+=100%
                raw_stress = min(max(0.6 * beta_stress + 0.4 * hr_stress, 0.0), 1.0)
                stress_history.append(raw_stress)
                smoothed_stress = float(np.mean(stress_history))  # 8-second average

                copilot_brain_state = {
                    'stress': smoothed_stress,  # Smoothed stress with HR component
                    'cognitive_load': smoothed_cognitive_load,  # Smoothed cognitive load
                    'hr': int(max(40, min(200, hr))),  # Realistic HR range
                    'emotion_arousal': float(min(max(gamma / 100.0, 0.0), 1.0)),  # Clamped to 0-1
                    'beta': float(beta),
                    'alpha': float(alpha),
                    'theta': float(theta),
                    'gamma': float(gamma),
                    'delta': float(delta),
                    'brain_state': str(brain_state),
                    'signal_quality': float(smoothed_quality),
                    'emg_intensity': float(min(max(artifact_result.get('emg_intensity', 0.0), 0.0), 1.0))  # Clamped to 0-1
                }

                # Update copilot if active (with null-safety)
                if copilot_session and copilot_session.is_active:
                    try:
                        copilot_session.update_brain_state(copilot_brain_state)
                    except Exception as e:
                        logger.warning(f"Failed to update copilot brain state: {e}")

                # Record session data
                if session_recorder.is_recording:
                    # Record processed sample (1/second)
                    # Convert numpy types to Python native for JSON serialization
                    session_recorder.add_processed_sample(
                        timestamp=float(eeg_timestamp),
                        band_powers={k: float(v) for k, v in smoothed_band_powers.items()},
                        brain_state=str(brain_state),
                        signal_quality=float(smoothed_quality),
                        heart_rate=float(hrv_metrics.get('heart_rate', 0)) if hrv_metrics.get('heart_rate', 0) > 0 else 0.0,  # Save if > 0, even if partial
                        hrv_rmssd=float(hrv_metrics.get('hrv_rmssd', 0)) if hrv_metrics.get('valid', False) else 0.0,
                        # NEW: Artifact features (continuous 0-1)
                        emg_intensity=float(artifact_result.get('emg_intensity', 0.0)),
                        forehead_emg=float(artifact_result.get('forehead_emg', 0.0)),
                        blink_intensity=float(artifact_result.get('blink_intensity', 0.0)),
                        movement_intensity=float(artifact_result.get('movement_intensity', 0.0)),
                        data_quality=float(artifact_result.get('data_quality', 1.0)),
                        # Legacy
                        has_artifact=bool(has_artifact),
                        artifact_type=str(artifact_result.get('artifact_type', 'clean')),
                        acc_data=[float(x) for x in acc_data.tolist()] if acc_data is not None else None,
                        gyro_data=[float(x) for x in gyro_data.tolist()] if gyro_data is not None else None,
                        is_talking=bool(is_talking)
                    )

                # Broadcast band powers with smoothed values
                try:
                    broadcast_data = {
            'type': 'band_powers',
                        'timestamp': float(eeg_timestamp),
                        'band_powers': {k: float(v) for k, v in smoothed_band_powers.items()},  # Ensure all floats
                        'brain_state': str(brain_state),
                        'has_artifact': bool(has_artifact),  # Explicitly convert to Python bool
                        'artifact_type': str(artifact_result.get('artifact_type', 'poor_contact' if len(bad_channels) > 0 else 'low_quality') if has_artifact else 'clean'),
                        'bad_channels': [int(ch) for ch in bad_channels],  # List of bad channel indices
                        'artifact_details': {
                            'bad_channels': [int(ch) for ch in bad_channels],
                            'channel_names': ['TP9', 'AF7', 'AF8', 'TP10'],
                            'poor_contact': len(bad_channels) > 0,
                            **{k: bool(v) for k, v in artifact_result.items() if k != 'artifact_type' and k != 'has_artifact'}
                        },
            'signal_quality': {
                            'mean': float(result.get('mean', 0)),
                            'std': float(result.get('std', 0)),
                            'snr': float(mne_result.get('quality', {}).get('snr', 0)),
                            'confidence': float(smoothed_quality),  # Use smoothed quality
                            'bad_channels': [int(ch) for ch in mne_result.get('quality', {}).get('bad_channels', [])],
                            'stability': bool(state_smoother.is_stable() if hasattr(state_smoother, 'is_stable') else False),
                            'artifact_ratio': float(artifact_ratio),
                        },
                        'ica_status': {
                            'fitted': bool(ica_fitted),  # Explicitly convert
                            'progress': int(ica_fit_progress),
                        },
                        # Send heart rate even if partial/cached (better than 0)
                        'heart_rate': float(hrv_metrics.get('heart_rate', 0)) if hrv_metrics.get('heart_rate', 0) > 0 else 0,
                        'hrv_rmssd': float(hrv_metrics.get('hrv_rmssd', 0)) if hrv_metrics.get('valid', False) else 0,
                        'hrv_sdnn': float(hrv_metrics.get('hrv_sdnn', 0)) if hrv_metrics.get('valid', False) else 0,
                        # Mental state interpretations
                        'hrv_interpretation': hrv_interpretation,
                        'posture_interpretation': posture_interpretation,
                        'band_change_interpretation': band_change_interpretation,
                        # Talking detection
                        'is_talking': bool(is_talking),
                        'talking_confidence': float(talking_result.get('confidence', 0)),
                        'talking_duration': float(talking_result.get('duration', 0)),
                        # Session recording status
                        'is_recording': bool(session_recorder.is_recording),
                        'session_id': session_recorder.current_session.session_id if session_recorder.current_session else None,
                    }
                    
                    # Log for debugging (less verbose)
                    if hasattr(state_smoother, 'band_power_history') and len(state_smoother.band_power_history) % 5 == 0:
                        logger.debug(f"State: {brain_state}, Quality: {smoothed_quality:.1f}, Artifacts: {artifact_ratio:.1%}")
                    
                    await manager.broadcast(broadcast_data)
                except Exception as e:
                    logger.error(f"Error broadcasting data: {e}", exc_info=True)
                    # Don't let broadcast errors stop the stream
            except Exception as e:
                logger.error(f"Error processing band powers: {e}", exc_info=True)
                # Continue streaming even if processing fails
                import traceback
                logger.debug(f"Traceback: {traceback.format_exc()}")
    except Exception as e:
        logger.error(f"Error in process_sensor_data: {e}", exc_info=True)
        import traceback
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        # Don't let processing errors stop the stream - just log and continue


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Health check endpoint
    """
    return {
        "status": "ok",
        "service": "Consciousness OS Backend",
        "version": "1.0.0"
    }


@app.get("/api/device-info")
async def get_device_info() -> Dict[str, Any]:
    """
    Get information about connected Muse device
    """
    info = muse_streamer.get_device_info()
    return info


@app.post("/api/connect")
async def connect_muse() -> Dict[str, Any]:
    """
    Connect to Muse device via LSL
    """
    try:
        logger.info("Received /api/connect request")
        # Stop any existing stream first
        if muse_streamer.is_streaming:
            logger.info("Stopping existing stream before reconnecting...")
            muse_streamer.disconnect()
            await asyncio.sleep(0.5)  # Give it time to stop
        
        logger.info("Attempting to connect to Muse via LSL...")
        success = muse_streamer.connect(timeout=10.0)
        logger.info(f"Muse connection result: {success}")

        if success:
            # Reset ICA state on new connection
            global ica_fitted, ica_fit_buffer, ica_fit_progress, state_smoother, hrv_calculator
            ica_fitted = False
            ica_fit_buffer = []
            ica_fit_progress = 0
            
            # Reset EEG buffers
            for ch in range(4):
                eeg_buffer[ch].clear()
            
            # Reset state smoother
            state_smoother = StateSmoother(window_size=30)  # 30 seconds for stability
            global posture_history
            posture_history = deque(maxlen=30)
            
            # Reset HRV calculator
            hrv_calculator = HRVCalculator()
            
            # Reset send time and stream monitoring
            global _last_eeg_send_time, _last_data_received
            _last_eeg_send_time = 0.0
            _last_data_received = 0.0
            
            logger.info("✅ All state reset for new connection - ICA will calibrate")
            
            # Start streaming in background with multi-sensor callback
            # Use create_task to run in background - it will continue even if errors occur
            async def start_stream():
                try:
                    await muse_streamer.stream_data(process_sensor_data)
                except Exception as e:
                    logger.error(f"Stream function exited: {e}", exc_info=True)
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
            
            stream_task = asyncio.create_task(start_stream())
            logger.info(f"Stream task created: {stream_task}")
            
            # Add error handler to task (non-blocking)
            def handle_stream_error(task):
                try:
                    task.result()  # This will raise if task failed
                    logger.info("Stream task completed normally")
                except Exception as e:
                    logger.error(f"Stream task completed with error: {e}", exc_info=True)
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    # Task completed - check if we should restart
                    if muse_streamer.is_streaming:
                        logger.warning("Stream task ended but is_streaming is still True - this is unexpected")
                    
            stream_task.add_done_callback(handle_stream_error)
            
            # Start monitoring task to detect if stream stops
            async def monitor_stream():
                while True:
                    await asyncio.sleep(2.0)  # Check every 2 seconds
                    if _last_data_received > 0:
                        time_since_data = time.time() - _last_data_received
                        if time_since_data > STREAM_TIMEOUT and muse_streamer.is_streaming:
                            logger.warning(f"⚠️ Stream appears stopped - no data for {time_since_data:.1f}s (is_streaming={muse_streamer.is_streaming})")
                            # Don't auto-restart, just log
                    elif muse_streamer.is_streaming:
                        # Stream started but no data received yet
                        pass
            
            asyncio.create_task(monitor_stream())

            return {
                "status": "connected",
                "device_info": muse_streamer.get_device_info()
            }
        else:
            return {
                "status": "error",
                "message": "Failed to connect to Muse. Make sure 'muselsl stream' is running."
            }

    except Exception as e:
        logger.error(f"Connection error: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/api/disconnect")
async def disconnect_muse() -> Dict[str, str]:
    """
    Disconnect from Muse device
    """
    muse_streamer.disconnect()

    # Reset all state
    global ica_fitted, ica_fit_buffer, ica_fit_progress, state_smoother
    ica_fitted = False
    ica_fit_buffer = []
    ica_fit_progress = 0

    # Clear buffers
    for ch in range(4):
        eeg_buffer[ch].clear()
    
    # Reset state smoother
    state_smoother = StateSmoother(window_size=5)
    
    logger.info("Disconnected - all state cleared")

    return {"status": "disconnected"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time EEG data streaming
    """
    await manager.connect(websocket)

    try:
        # Keep connection alive and listen for client messages
        while True:
            # Wait for any message from client (e.g., commands)
            data = await websocket.receive_text()

            # Parse command
            try:
                command = json.loads(data)
                logger.info(f"Received command: {command}")

                # Handle commands if needed
                if command.get('type') == 'ping':
                    await websocket.send_json({'type': 'pong'})

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")


# =============================================================================
# Session Recording Endpoints
# =============================================================================

@app.post("/api/session/start")
async def start_session(notes: str = "", tags: str = "") -> Dict[str, str]:
    """
    Start recording a new session

    Args:
        notes: Optional session notes
        tags: Comma-separated tags
    """
    try:
        # Input validation
        if len(notes) > 10000:
            raise HTTPException(status_code=400, detail="Notes too long (max 10KB)")
        if len(tags) > 1000:
            raise HTTPException(status_code=400, detail="Tags too long (max 1KB)")

        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        session_id = session_recorder.start_session(notes=notes, tags=tag_list)
        return {
            "status": "recording",
            "session_id": session_id,
            "message": f"Started recording session: {session_id}"
        }
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/api/session/stop")
async def stop_session() -> Dict[str, str]:
    """
    Stop current recording session and save data
    """
    try:
        session_path = session_recorder.stop_session()
        if session_path:
            return {
                "status": "stopped",
                "session_path": session_path,
                "message": "Session saved successfully"
            }
        else:
            return {"status": "error", "message": "No active session to stop"}
    except Exception as e:
        logger.error(f"Error stopping session: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/session/status")
async def get_session_status() -> Dict[str, Any]:
    """
    Get current recording status
    """
    return session_recorder.get_session_status()


@app.post("/api/session/marker")
async def add_session_marker(label: str, notes: str = "") -> Dict[str, str]:
    """
    Add a marker to current session (e.g., "started talking", "eyes closed")
    """
    if not session_recorder.is_recording:
        return {"status": "error", "message": "No active recording session"}

    session_recorder.add_marker(label, notes)
    return {"status": "ok", "message": f"Marker added: {label}"}


@app.get("/api/sessions")
async def list_sessions() -> Dict[str, List]:
    """
    List all saved sessions
    """
    sessions = session_recorder.list_sessions()
    return {"sessions": sessions}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """
    Load a specific session
    """
    session_data = session_recorder.load_session(session_id)
    if session_data:
        return session_data
    else:
        return {"status": "error", "message": f"Session not found: {session_id}"}


@app.post("/api/sessions/{session_id}/rename")
async def rename_session(session_id: str, name: str) -> Dict[str, str]:
    """
    Add a friendly name to a session
    """
    # Input validation
    if len(name) > 200:
        raise HTTPException(status_code=400, detail="Name too long (max 200 chars)")
    success = session_recorder.rename_session(session_id, name)
    if success:
        return {"status": "ok", "message": f"Session renamed to: {name}"}
    else:
        return {"status": "error", "message": f"Failed to rename session {session_id}"}


@app.post("/api/sessions/{session_id}/update")
async def update_session(session_id: str, notes: str = None, tags: str = None, name: str = None) -> Dict[str, str]:
    """
    Update session metadata (notes, tags, or name)
    """
    # Input validation
    if notes and len(notes) > 10000:
        raise HTTPException(status_code=400, detail="Notes too long (max 10KB)")
    if tags and len(tags) > 1000:
        raise HTTPException(status_code=400, detail="Tags too long (max 1KB)")
    if name and len(name) > 200:
        raise HTTPException(status_code=400, detail="Name too long (max 200 chars)")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    success = session_recorder.update_session_metadata(session_id, notes=notes, tags=tag_list, name=name)
    if success:
        return {"status": "ok", "message": f"Session {session_id} updated"}
    else:
        return {"status": "error", "message": f"Failed to update session {session_id}"}


# =============================================================================
# AI Co-Pilot Endpoints
# =============================================================================

@app.post("/api/copilot/start")
async def start_copilot() -> Dict[str, str]:
    """
    Start AI Co-Pilot session

    This will initialize the copilot and begin audio recording/transcription.
    Brain state updates will be fed automatically from the EEG processing.
    """
    global copilot_session

    try:
        # Check if copilot dependencies are available
        if not COPILOT_AVAILABLE:
            raise HTTPException(status_code=503, detail="Copilot dependencies not installed. Install requirements_copilot.txt")

        # Check if Muse is connected
        if not muse_streamer.is_streaming:
            raise HTTPException(status_code=400, detail="Muse device not connected. Please connect EEG first.")

        # Check if already running
        if copilot_session and copilot_session.is_active:
            raise HTTPException(status_code=409, detail="Copilot session already active")

        # Initialize copilot if needed
        if copilot_session is None:
            logger.info("Initializing AI Co-Pilot...")
            copilot_session = CopilotSession()

        logger.info("AI Co-Pilot session start requested")

        return {
            "status": "ready",
            "message": "Copilot initialized. Connect via WebSocket at /ws/copilot to start."
        }

    except Exception as e:
        logger.error(f"Error starting copilot: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/api/copilot/stop")
async def stop_copilot() -> Dict[str, str]:
    """
    Stop AI Co-Pilot session
    """
    global copilot_session

    try:
        if copilot_session is None or not copilot_session.is_active:
            raise HTTPException(status_code=400, detail="No active copilot session")

        copilot_session.stop_session()

        # Export session data
        from pathlib import Path
        output_dir = Path("sessions") / "copilot" / f"session_{int(time.time())}"

        try:
            copilot_session.export_session(output_dir)
        except Exception as export_error:
            logger.error(f"Failed to export session: {export_error}")
            raise HTTPException(status_code=500, detail=f"Session stopped but export failed: {str(export_error)}")

        logger.info(f"AI Co-Pilot session stopped and exported to {output_dir}")

        return {
            "status": "stopped",
            "message": "Copilot session stopped",
            "export_path": str(output_dir)
        }

    except Exception as e:
        logger.error(f"Error stopping copilot: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/api/copilot/status")
async def get_copilot_status() -> Dict[str, Any]:
    """
    Get current copilot status
    """
    global copilot_session

    if copilot_session is None:
        return {
            "status": "inactive",
            "is_active": False,
            "models_loaded": False
        }

    return {
        "status": "active" if copilot_session.is_active else "inactive",
        "is_active": copilot_session.is_active,
        "models_loaded": copilot_session.ml_analyzer.models_loaded,
        "session_duration": time.time() - copilot_session.session_start_time if copilot_session.is_active else 0
    }


@app.websocket("/ws/copilot")
async def copilot_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for AI Co-Pilot real-time conversation

    Messages sent to frontend:
    - type: 'ai_message' - Initial greeting or complete AI message
    - type: 'transcript' - User speech transcription
    - type: 'state_update' - Brain + text analysis state
    - type: 'ai_typing' - AI is generating response
    - type: 'ai_message_chunk' - Streaming AI response chunk
    - type: 'ai_message_complete' - AI response finished
    - type: 'error' - Error occurred
    - type: 'reconnecting' - Session reconnecting after error
    - type: 'recording_start' - Microphone recording started
    - type: 'recording_end' - Microphone recording ended

    Messages received from frontend:
    - type: 'user_text' - User typed message
    """
    global copilot_session

    await websocket.accept()
    logger.info("Copilot WebSocket client connected")

    try:
        # Initialize copilot if needed
        if copilot_session is None:
            logger.info("Initializing AI Co-Pilot from WebSocket...")
            copilot_session = CopilotSession()

        # WebSocket callback to send messages to frontend
        async def websocket_callback(message: dict):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to copilot WebSocket: {e}")
                raise  # Re-raise to stop session if WebSocket fails

        # Create tasks for bidirectional communication
        async def receive_messages():
            """Handle incoming messages from frontend"""
            logger.info("[DEBUG] receive_messages task started")
            try:
                # Wait for session to become active (with timeout)
                logger.info(f"[DEBUG] Waiting for session to become active. copilot_session: {copilot_session is not None}, is_active: {copilot_session.is_active if copilot_session else 'N/A'}")

                for _ in range(10):  # Wait up to 5 seconds
                    if copilot_session and copilot_session.is_active:
                        break
                    await asyncio.sleep(0.5)

                logger.info(f"[DEBUG] Starting receive loop. copilot_session: {copilot_session is not None}, is_active: {copilot_session.is_active if copilot_session else 'N/A'}")

                while copilot_session and copilot_session.is_active:
                    try:
                        logger.info("[DEBUG] Waiting for WebSocket message...")
                        data = await websocket.receive_json()
                        logger.info(f"[DEBUG] Received WebSocket message: {data}")
                        logger.info(f"Received WebSocket message: {data.get('type')}")

                        if data.get('type') == 'user_text':
                            # Process text message from user
                            text = data.get('text', '').strip()
                            logger.info(f"[DEBUG] Extracted text: '{text}'")
                            if text and copilot_session:
                                logger.info(f"Processing user text: {text}")
                                await copilot_session.process_text_message(text, websocket_callback)
                                logger.info(f"[DEBUG] Finished processing user text")
                            else:
                                logger.warning(f"[DEBUG] Skipped processing: text='{text}', copilot_session={copilot_session is not None}")
                    except asyncio.CancelledError:
                        logger.info("Receive task cancelled")
                        break
                    except RuntimeError as e:
                        # WebSocket disconnected
                        if "disconnect message has been received" in str(e):
                            logger.info("WebSocket disconnected, stopping receive loop")
                            break
                        logger.error(f"Runtime error processing message: {e}", exc_info=True)
                        break
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        # Send error to frontend but keep connection alive
                        try:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Error processing message: {str(e)}",
                                "timestamp": time.time()
                            })
                        except:
                            pass

                logger.info(f"[DEBUG] Exited receive loop. copilot_session: {copilot_session is not None}, is_active: {copilot_session.is_active if copilot_session else 'N/A'}")
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected during receive")
            except Exception as e:
                logger.error(f"Fatal error in receive_messages: {e}", exc_info=True)
            finally:
                logger.info("[DEBUG] receive_messages task ending")

        async def run_session():
            """Run the copilot session"""
            try:
                logger.info("Starting AI Co-Pilot session...")
                await copilot_session.start_session(websocket_callback)
            except Exception as e:
                logger.error(f"Error in copilot session: {e}", exc_info=True)
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Session error: {str(e)}",
                        "timestamp": time.time()
                    })
                except:
                    pass

        # Run both tasks concurrently with asyncio.gather
        # This allows audio recording and text message receiving to work simultaneously
        receive_task = asyncio.create_task(receive_messages())
        session_task = asyncio.create_task(run_session())

        # Wait for either task to complete (session ends or disconnect)
        done, pending = await asyncio.wait(
            [receive_task, session_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except WebSocketDisconnect:
        logger.info("Copilot WebSocket client disconnected")
        if copilot_session:
            copilot_session.stop_session()
    except Exception as e:
        logger.error(f"Copilot WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
                "timestamp": time.time()
            })
        except:
            pass
        if copilot_session:
            copilot_session.stop_session()


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Consciousness OS Backend...")
    logger.info("Make sure to run 'muselsl stream' in another terminal first!")
    logger.info("")
    logger.info("Steps to connect:")
    logger.info("1. Turn on Muse headband")
    logger.info("2. Run: muselsl stream")
    logger.info("3. Open browser to http://localhost:8000")
    logger.info("4. Click 'Connect' in the web interface")
    logger.info("")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
