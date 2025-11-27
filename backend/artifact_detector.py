"""
Artifact Feature Extractor Module (Refactored)
Uses multiple sensors (EEG, ACC, GYRO) to extract physiological features.

PHILOSOPHY: Artifacts are psychological signals, not noise!
- Jaw tension = stress
- Forehead EMG = cognitive effort
- Blink bursts = overwhelm
- Movement = emotional activation

We extract continuous intensity values (0-1), not binary flags.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import deque
from scipy import signal
import logging

logger = logging.getLogger(__name__)

# Artifact types (now features, not errors)
ARTIFACT_FEATURES = {
    'emg_intensity': 'Muscle Activity (jaw/face)',
    'forehead_emg': 'Forehead Tension (cognitive effort)',
    'blink_intensity': 'Blink Activity (overwhelm indicator)',
    'movement_intensity': 'Movement (emotional activation)',
    'data_quality': 'Signal Quality (0=garbage, 1=clean)'
}


class ArtifactDetector:
    """
    Multi-sensor artifact detection for EEG data
    """

    def __init__(self, eeg_sample_rate: int = 256, acc_sample_rate: int = 52, gyro_sample_rate: int = 52):
        self.eeg_sample_rate = eeg_sample_rate
        self.acc_sample_rate = acc_sample_rate
        self.gyro_sample_rate = gyro_sample_rate

        # Buffers for temporal analysis
        self.eeg_buffer = deque(maxlen=256)  # 1 second of EEG
        self.acc_buffer = deque(maxlen=52)  # 1 second of accelerometer
        self.gyro_buffer = deque(maxlen=52)  # 1 second of gyroscope

        # Previous values for change detection
        self.prev_acc_magnitude = 0.0
        self.prev_gyro_magnitude = 0.0

        # Baseline for statistical detection
        self.eeg_baseline_mean = 0.0
        self.eeg_baseline_std = 10.0
        self.baseline_samples = 0
        self.baseline_window_size = 256 * 5  # 5 seconds for baseline

    def update_eeg(self, eeg_data: np.ndarray):
        """
        Update EEG buffer with new data

        Args:
            eeg_data: EEG samples [n_samples, n_channels] or [n_channels]
        """
        if len(eeg_data.shape) == 1:
            # Single sample, add to buffer
            self.eeg_buffer.append(eeg_data)
        else:
            # Multiple samples, add all
            for sample in eeg_data:
                self.eeg_buffer.append(sample)

        # Update baseline (running average)
        if self.baseline_samples < self.baseline_window_size:
            self.baseline_samples += len(eeg_data) if len(eeg_data.shape) > 1 else 1
            if len(self.eeg_buffer) > 0:
                all_samples = np.array(list(self.eeg_buffer))
                self.eeg_baseline_mean = np.mean(all_samples)
                self.eeg_baseline_std = np.std(all_samples)

    def update_acc(self, acc_data: np.ndarray):
        """
        Update accelerometer buffer

        Args:
            acc_data: Accelerometer data [x, y, z] or [n_samples, 3]
        """
        if len(acc_data.shape) == 1:
            self.acc_buffer.append(acc_data)
        else:
            for sample in acc_data:
                self.acc_buffer.append(sample)

    def update_gyro(self, gyro_data: np.ndarray):
        """
        Update gyroscope buffer

        Args:
            gyro_data: Gyroscope data [x, y, z] or [n_samples, 3]
        """
        if len(gyro_data.shape) == 1:
            self.gyro_buffer.append(gyro_data)
        else:
            for sample in gyro_data:
                self.gyro_buffer.append(sample)

    def detect_eye_blink(self, eeg_data: np.ndarray, gyro_data: Optional[np.ndarray] = None) -> bool:
        """
        Detect eye blink using EEG spike pattern and gyroscope

        Eye blinks create:
        - High amplitude spike (>150 μV) in frontal channels (AF7, AF8)
        - Upward rotation in gyroscope Z-axis
        - Duration: 200-500ms

        Args:
            eeg_data: EEG data [n_channels] or [n_samples, n_channels]
            gyro_data: Gyroscope data [x, y, z] or None

        Returns:
            True if eye blink detected
        """
        # Use buffer for better detection (need temporal context)
        if len(self.eeg_buffer) < 64:  # Need at least 250ms of data
            return False

        # Get recent EEG data from buffer
        recent_eeg = np.array(list(self.eeg_buffer))[-64:]  # Last 250ms
        
        # Check frontal channels (AF7=1, AF8=2)
        if recent_eeg.shape[1] >= 3:
            frontal_channels = recent_eeg[:, [1, 2]]  # AF7 and AF8
            frontal_max = np.max(np.abs(frontal_channels))

            # Check for characteristic spike (>150 μV in frontal channels)
            if frontal_max > 150:
                # Check if it's a spike pattern (sudden increase then decrease)
                # Look for peak in the middle of the window
                frontal_abs = np.abs(frontal_channels)
                max_idx = np.argmax(frontal_abs)
                
                # Check if peak is in middle portion (not at edges)
                if 10 < max_idx < len(frontal_abs) - 10:
                    # Check duration - should be relatively short
                    above_threshold = np.sum(frontal_abs > 100)
                    if 20 <= above_threshold <= 80:  # ~80-320ms at 256Hz
                        # Check gyroscope if available
                        if gyro_data is not None and len(self.gyro_buffer) > 0:
                            recent_gyro = np.array(list(self.gyro_buffer))[-10:]
                            if recent_gyro.shape[1] >= 3:
                                gyro_z = np.abs(recent_gyro[:, 2])
                                # Upward rotation threshold (lowered for better detection)
                                if np.max(gyro_z) > 200:  # degrees/second
                                    return True
                        # Without gyro, rely on EEG pattern only (lower threshold)
                        return True

        return False

    def detect_muscle_artifact(self, eeg_data: np.ndarray, acc_data: Optional[np.ndarray] = None) -> bool:
        """
        Detect muscle artifacts (chewing, talking) using EMG frequency analysis

        Muscle artifacts create:
        - High power in EMG range (50-100 Hz)
        - Sustained high-frequency noise
        - Jaw movement in accelerometer

        Args:
            eeg_data: EEG data [n_channels] or [n_samples, n_channels]
            acc_data: Accelerometer data [x, y, z] or None

        Returns:
            True if muscle artifact detected
        """
        if len(eeg_data.shape) == 1:
            # Need multiple samples for frequency analysis
            if len(self.eeg_buffer) < 128:
                return False
            eeg_window = np.array(list(self.eeg_buffer))[-128:]
            # Average across channels
            if eeg_window.shape[1] >= 4:
                eeg_signal = np.mean(eeg_window, axis=1)
            else:
                eeg_signal = eeg_window[:, 0]
        else:
            # Average across channels
            if eeg_data.shape[1] >= 4:
                eeg_signal = np.mean(eeg_data, axis=1)
            else:
                eeg_signal = eeg_data[:, 0]

        # Calculate power in EMG range (50-100 Hz)
        if len(eeg_signal) >= 128:
            frequencies, psd = signal.welch(
                eeg_signal,
                fs=self.eeg_sample_rate,
                nperseg=min(128, len(eeg_signal)),
                noverlap=64
            )

            # Find EMG frequency range
            emg_idx = np.logical_and(frequencies >= 50, frequencies <= 100)
            emg_power = np.trapz(psd[emg_idx], frequencies[emg_idx])

            # Total power for normalization
            total_power = np.trapz(psd, frequencies)

            if total_power > 0:
                emg_ratio = emg_power / total_power

                # High EMG ratio indicates muscle artifact
                if emg_ratio > 0.15:  # 15% of power in EMG range
                    # Check accelerometer for jaw movement
                    if acc_data is not None:
                        if len(acc_data.shape) == 1:
                            acc_magnitude = np.linalg.norm(acc_data)
                        else:
                            acc_magnitude = np.mean([np.linalg.norm(a) for a in acc_data])
                        # Jaw movement creates small but sustained acceleration
                        if acc_magnitude > 0.5:  # g units
                            return True
                    else:
                        # Without accelerometer, rely on EMG ratio only
                        return True

        return False

    def detect_motion_artifact(self, acc_data: Optional[np.ndarray] = None,
                               gyro_data: Optional[np.ndarray] = None,
                               eeg_data: Optional[np.ndarray] = None) -> bool:
        """
        Detect head movement using accelerometer and gyroscope

        Motion artifacts create:
        - Sudden changes in accelerometer magnitude
        - Rotation changes in gyroscope
        - Correlated changes in all EEG channels

        Args:
            acc_data: Accelerometer data [x, y, z] or None
            gyro_data: Gyroscope data [x, y, z] or None
            eeg_data: EEG data for correlation check

        Returns:
            True if motion artifact detected
        """
        motion_detected = False

        # Check accelerometer (more sensitive)
        if acc_data is not None:
            try:
                if len(acc_data.shape) == 0:
                    # Scalar
                    acc_magnitude = abs(float(acc_data))
                elif len(acc_data.shape) == 1:
                    if len(acc_data) >= 3:
                        acc_magnitude = np.linalg.norm(acc_data)
                    else:
                        acc_magnitude = np.linalg.norm(acc_data) if len(acc_data) > 0 else 0
                else:
                    acc_magnitude = np.mean([np.linalg.norm(a) for a in acc_data])

                # Check for sudden change (lowered threshold for better detection)
                if self.prev_acc_magnitude > 0:
                    change = abs(acc_magnitude - self.prev_acc_magnitude)
                    if change > 0.15:  # 0.15g change (more sensitive)
                        motion_detected = True
                self.prev_acc_magnitude = acc_magnitude
            except:
                pass

        # Check gyroscope (more sensitive)
        if gyro_data is not None:
            try:
                if len(gyro_data.shape) == 0:
                    # Scalar
                    gyro_magnitude = abs(float(gyro_data))
                elif len(gyro_data.shape) == 1:
                    if len(gyro_data) >= 3:
                        gyro_magnitude = np.linalg.norm(gyro_data)
                    else:
                        gyro_magnitude = np.linalg.norm(gyro_data) if len(gyro_data) > 0 else 0
                else:
                    gyro_magnitude = np.mean([np.linalg.norm(g) for g in gyro_data])

                # Check for sudden rotation (lowered threshold)
                if self.prev_gyro_magnitude > 0:
                    change = abs(gyro_magnitude - self.prev_gyro_magnitude)
                    if change > 100:  # 100 degrees/second (more sensitive)
                        motion_detected = True
                self.prev_gyro_magnitude = gyro_magnitude
            except:
                pass

        # Also check buffer for sustained movement
        if len(self.acc_buffer) > 10:
            recent_acc = np.array(list(self.acc_buffer))[-10:]
            if recent_acc.shape[1] >= 3:
                acc_magnitudes = [np.linalg.norm(a) for a in recent_acc]
                acc_variance = np.var(acc_magnitudes)
                # High variance indicates movement
                if acc_variance > 0.1:
                    motion_detected = True

        return motion_detected

    def detect_em_interference(self, eeg_data: np.ndarray) -> bool:
        """
        Detect electromagnetic interference (60 Hz powerline noise)

        Args:
            eeg_data: EEG data [n_channels] or [n_samples, n_channels]

        Returns:
            True if EM interference detected
        """
        if len(eeg_data.shape) == 1:
            if len(self.eeg_buffer) < 128:
                return False
            eeg_window = np.array(list(self.eeg_buffer))[-128:]
            eeg_signal = np.mean(eeg_window, axis=1) if eeg_window.shape[1] >= 4 else eeg_window[:, 0]
        else:
            eeg_signal = np.mean(eeg_data, axis=1) if eeg_data.shape[1] >= 4 else eeg_data[:, 0]

        if len(eeg_signal) >= 128:
            # Calculate power at 60 Hz
            frequencies, psd = signal.welch(
                eeg_signal,
                fs=self.eeg_sample_rate,
                nperseg=min(128, len(eeg_signal)),
                noverlap=64
            )

            # Find 60 Hz power
            freq_60_idx = np.argmin(np.abs(frequencies - 60))
            power_60hz = psd[freq_60_idx]

            # Average power in surrounding frequencies
            surrounding_idx = np.logical_and(frequencies >= 55, frequencies <= 65)
            surrounding_power = np.mean(psd[surrounding_idx])

            # If 60 Hz is significantly higher than surrounding, likely interference
            if surrounding_power > 0 and power_60hz > surrounding_power * 2:
                return True

        return False

    def detect_statistical_artifacts(self, eeg_data: np.ndarray) -> bool:
        """
        Detect artifacts using statistical methods (z-score)

        More robust than fixed threshold - adapts to signal characteristics

        Args:
            eeg_data: EEG data [n_channels] or [n_samples, n_channels]

        Returns:
            True if statistical artifact detected
        """
        if len(eeg_data.shape) == 1:
            eeg_data = eeg_data.reshape(1, -1)

        # Use baseline statistics
        if self.baseline_samples < self.baseline_window_size:
            # Still building baseline, use simple threshold (less sensitive)
            return np.max(np.abs(eeg_data)) > 150  # Increased threshold

        # Calculate z-scores
        z_scores = np.abs((eeg_data - self.eeg_baseline_mean) / (self.eeg_baseline_std + 1e-6))

        # Flag if any sample > 4 standard deviations (more conservative)
        # Only flag if multiple samples are outliers (not just one spike)
        outliers = np.sum(z_scores > 4)
        return outliers > 3  # Need at least 3 outliers to be considered artifact

    def detect_bad_channels(self, eeg_data: np.ndarray, threshold: float = 200) -> List[int]:
        """
        Detect channels with extreme values (likely poor contact or artifacts)
        
        Args:
            eeg_data: EEG data [n_channels] or [n_samples, n_channels]
            threshold: Maximum allowed amplitude in microvolts (default: 200μV)
        
        Returns:
            List of channel indices that are bad
        """
        if len(eeg_data.shape) == 1:
            # Single sample [n_channels]
            bad_channels = []
            for ch in range(len(eeg_data)):
                if abs(eeg_data[ch]) > threshold:
                    bad_channels.append(ch)
            return bad_channels
        else:
            # Multiple samples [n_samples, n_channels]
            bad_channels = []
            for ch in range(eeg_data.shape[1]):
                channel_data = eeg_data[:, ch]
                # Check if max absolute value exceeds threshold
                if np.max(np.abs(channel_data)) > threshold:
                    bad_channels.append(ch)
            return bad_channels

    def detect_poor_contact(self, eeg_data: np.ndarray) -> bool:
        """
        Detect poor electrode contact (low signal amplitude)

        Args:
            eeg_data: EEG data [n_channels] or [n_samples, n_channels]

        Returns:
            True if poor contact detected
        """
        if len(eeg_data.shape) == 1:
            eeg_data = eeg_data.reshape(1, -1)

        # Check signal amplitude (too low = poor contact)
        signal_amplitude = np.mean(np.abs(eeg_data))

        # Very low amplitude (< 5 μV) suggests poor contact
        if signal_amplitude < 5:
            return True

        return False

    def extract_emg_intensity(self, eeg_data: np.ndarray) -> float:
        """
        Extract EMG intensity as continuous 0-1 value.
        High values = jaw/face muscle activity = stress/talking/emotional activation
        """
        if len(self.eeg_buffer) < 128:
            return 0.0

        eeg_window = np.array(list(self.eeg_buffer))[-128:]
        if eeg_window.shape[1] >= 4:
            eeg_signal = np.mean(eeg_window, axis=1)
        else:
            eeg_signal = eeg_window[:, 0]

        try:
            frequencies, psd = signal.welch(
                eeg_signal,
                fs=self.eeg_sample_rate,
                nperseg=min(128, len(eeg_signal)),
                noverlap=64
            )

            # EMG power (30-100 Hz)
            emg_idx = np.logical_and(frequencies >= 30, frequencies <= 100)
            emg_power = np.trapz(psd[emg_idx], frequencies[emg_idx]) if np.any(emg_idx) else 0
            total_power = np.trapz(psd, frequencies)

            if total_power > 0:
                emg_ratio = emg_power / total_power
                # Map to 0-1 (0.15 ratio = 0.5 intensity, 0.3+ = 1.0)
                return float(min(1.0, emg_ratio / 0.3))
        except:
            pass
        return 0.0

    def extract_forehead_emg(self, eeg_data: np.ndarray) -> float:
        """
        Extract forehead EMG specifically from AF7/AF8 channels.
        High values = cognitive effort/concentration
        """
        if len(self.eeg_buffer) < 64:
            return 0.0

        recent_eeg = np.array(list(self.eeg_buffer))[-64:]
        if recent_eeg.shape[1] < 3:
            return 0.0

        # AF7 and AF8 are frontal channels (indices 1, 2)
        frontal = recent_eeg[:, [1, 2]]
        frontal_power = np.mean(np.abs(frontal))

        # Normalize (50μV = 0.5, 100μV+ = 1.0)
        return float(min(1.0, frontal_power / 100.0))

    def extract_blink_intensity(self, eeg_data: np.ndarray) -> float:
        """
        Extract blink intensity. High values = overwhelm/fatigue
        """
        if len(self.eeg_buffer) < 64:
            return 0.0

        recent_eeg = np.array(list(self.eeg_buffer))[-64:]
        if recent_eeg.shape[1] < 3:
            return 0.0

        frontal = recent_eeg[:, [1, 2]]
        frontal_max = np.max(np.abs(frontal))

        # Blinks are >150μV spikes
        if frontal_max > 150:
            return float(min(1.0, (frontal_max - 150) / 150.0 + 0.5))
        return 0.0

    def extract_movement_intensity(self, acc_data: Optional[np.ndarray],
                                    gyro_data: Optional[np.ndarray]) -> float:
        """
        Extract movement intensity from IMU. High values = emotional activation
        """
        intensity = 0.0

        if acc_data is not None:
            try:
                if len(acc_data.shape) == 1 and len(acc_data) >= 3:
                    acc_magnitude = np.linalg.norm(acc_data)
                    # Baseline is ~1g (gravity), movement adds variance
                    if len(self.acc_buffer) > 10:
                        recent = np.array(list(self.acc_buffer))[-10:]
                        if recent.shape[1] >= 3:
                            variance = np.var([np.linalg.norm(a) for a in recent])
                            intensity = min(1.0, variance / 0.5)  # 0.5 variance = 1.0
            except:
                pass

        if gyro_data is not None:
            try:
                if len(gyro_data.shape) == 1 and len(gyro_data) >= 3:
                    gyro_magnitude = np.linalg.norm(gyro_data)
                    # High rotation = movement
                    gyro_intensity = min(1.0, gyro_magnitude / 500.0)
                    intensity = max(intensity, gyro_intensity)
            except:
                pass

        return float(intensity)

    def extract_data_quality(self, eeg_data: np.ndarray) -> float:
        """
        Extract data quality score. Only penalize true garbage:
        - Signal clipping (>500μV)
        - Very low signal (<5μV = poor contact)
        - 60Hz interference
        """
        quality = 1.0

        if len(eeg_data.shape) == 1:
            eeg_data = eeg_data.reshape(1, -1)

        max_amp = np.max(np.abs(eeg_data))
        mean_amp = np.mean(np.abs(eeg_data))

        # Clipping penalty
        if max_amp > 500:
            quality -= 0.5

        # Poor contact penalty
        if mean_amp < 5:
            quality -= 0.3

        # 60Hz interference check
        if self.detect_em_interference(eeg_data):
            quality -= 0.2

        return float(max(0.0, quality))

    def detect_all(self, eeg_data: np.ndarray,
                   acc_data: Optional[np.ndarray] = None,
                   gyro_data: Optional[np.ndarray] = None,
                   is_meditation: bool = False) -> Dict:
        """
        Extract all physiological features (continuous 0-1 values).

        Context-aware artifact handling:
        - Meditation: Only mark as artifact if signal quality is poor (clipping, poor contact, 60Hz)
        - Conversation: Track all physiological signals (blinks, movements, muscle) as behavioral data

        Args:
            eeg_data: EEG data [n_samples, n_channels]
            acc_data: Accelerometer data [x, y, z] or None
            gyro_data: Gyroscope data [x, y, z] or None
            is_meditation: If True, only mark true signal artifacts, not physiological features

        Returns:
            Features that represent psychological state, NOT errors to discard.
        """
        # Update buffers
        self.update_eeg(eeg_data)
        if acc_data is not None:
            self.update_acc(acc_data)
        if gyro_data is not None:
            self.update_gyro(gyro_data)

        # Extract continuous features (always track these - they're physiological data)
        emg_intensity = self.extract_emg_intensity(eeg_data)
        forehead_emg = self.extract_forehead_emg(eeg_data)
        blink_intensity = self.extract_blink_intensity(eeg_data)
        movement_intensity = self.extract_movement_intensity(acc_data, gyro_data)
        data_quality = self.extract_data_quality(eeg_data)

        # Context-aware artifact detection
        # For meditation: only mark as artifact if signal quality is truly poor (clipping, poor contact, 60Hz)
        # For conversation: track all physiological signals as behavioral data
        if is_meditation:
            # Meditation: Only true signal artifacts (poor contact, clipping, interference)
            has_artifact = data_quality < 0.5  # Only true garbage
            artifact_type = 'clean'
            if data_quality < 0.5:
                artifact_type = 'poor_quality'
            # Don't mark muscle tension or movement as artifacts - they're physiological data
        else:
            # Conversation: Track everything as behavioral data
            # Only mark as artifact if signal quality is poor
            has_artifact = data_quality < 0.5
            artifact_type = 'clean'
            if data_quality < 0.5:
                artifact_type = 'poor_quality'
            elif emg_intensity > 0.7:
                artifact_type = 'muscle'  # Informational, not discard
            elif movement_intensity > 0.7:
                artifact_type = 'motion'  # Informational
            elif blink_intensity > 0.5:
                artifact_type = 'eye_blink'  # Informational

        return {
            # New continuous features (THE IMPORTANT ONES)
            'emg_intensity': float(emg_intensity),
            'forehead_emg': float(forehead_emg),
            'blink_intensity': float(blink_intensity),
            'movement_intensity': float(movement_intensity),
            'data_quality': float(data_quality),
            # Legacy (backward compatibility) - only for truly bad data
            'has_artifact': bool(has_artifact),
            'artifact_type': str(artifact_type),
            'details': {
                'eye_blink': blink_intensity > 0.5,
                'muscle': emg_intensity > 0.5,
                'motion': movement_intensity > 0.5,
                'em_interference': data_quality < 0.8,
                'poor_contact': data_quality < 0.7,
                'statistical': False
            }
        }

