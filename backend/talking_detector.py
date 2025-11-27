"""
Talking/Jaw Movement Detector
Uses gyroscope and accelerometer to detect talking artifacts
without affecting brain activity detection.

Key insight: Talking creates characteristic jaw movements that can be
detected via gyroscope (rotation) and accelerometer (small movements),
allowing us to:
1. DETECT when user is talking
2. MARK the EEG data as talking-affected
3. Still RECORD brain activity for analysis
4. Apply DIFFERENT processing for talking periods
"""

import numpy as np
from collections import deque
from typing import Dict, Optional, Tuple, List
from scipy import signal
import logging

logger = logging.getLogger(__name__)


class TalkingDetector:
    """
    Detects talking/jaw movement using IMU sensors (gyroscope + accelerometer)

    Talking creates:
    - Rhythmic jaw movements at 2-5 Hz (speech rhythm)
    - Small but consistent gyroscope oscillations (Y-axis primarily)
    - Accelerometer micro-movements

    This is separate from EEG-based muscle artifact detection because:
    - Gyroscope is not affected by EEG noise
    - Allows detection even when EEG is corrupted
    - Can be used to train artifact removal models
    """

    def __init__(self, sample_rate: int = 52):
        """
        Args:
            sample_rate: IMU sample rate (Muse 2 is 52 Hz for ACC/GYRO)
        """
        self.sample_rate = sample_rate

        # Buffers for temporal analysis
        self.gyro_buffer: deque = deque(maxlen=sample_rate * 3)  # 3 seconds
        self.acc_buffer: deque = deque(maxlen=sample_rate * 3)   # 3 seconds

        # State tracking
        self.is_talking = False
        self.talking_confidence = 0.0
        self.talking_start_time: Optional[float] = None
        self.talking_duration = 0.0

        # Smoothing to prevent rapid state changes
        self.detection_history: deque = deque(maxlen=10)  # 10 samples = ~0.2s
        self.state_lock_time = 0.0
        self.MIN_STATE_DURATION = 0.5  # Minimum 0.5s before state can change

        # Thresholds (tuned for Muse 2)
        self.GYRO_VARIANCE_THRESHOLD = 5.0    # deg/s variance for talking
        self.GYRO_RHYTHM_THRESHOLD = 0.3      # Rhythm detection threshold
        self.ACC_VARIANCE_THRESHOLD = 0.01    # g variance for jaw movement
        self.CONFIDENCE_THRESHOLD = 0.6       # Required confidence to mark as talking (conversation)
        self.CONFIDENCE_THRESHOLD_MEDITATION = 0.75  # Higher threshold for meditation (reduce false positives)

    def update(self, gyro_data: Optional[np.ndarray],
               acc_data: Optional[np.ndarray],
               timestamp: float,
               is_meditation: bool = False) -> Dict:
        """
        Update detector with new sensor data

        Args:
            gyro_data: Gyroscope [x, y, z] in deg/s
            acc_data: Accelerometer [x, y, z] in g
            timestamp: Current timestamp

        Returns:
            Detection result dictionary
        """
        # Add to buffers
        if gyro_data is not None and len(gyro_data) >= 3:
            self.gyro_buffer.append(gyro_data)
        if acc_data is not None and len(acc_data) >= 3:
            self.acc_buffer.append(acc_data)

        # Need enough data for analysis
        if len(self.gyro_buffer) < self.sample_rate:
            return {
                'is_talking': False,
                'confidence': 0.0,
                'duration': 0.0,
                'reason': 'insufficient_data'
            }

        # Detect talking with context-aware threshold
        detection = self._detect_talking(is_meditation=is_meditation)

        # Add to history for smoothing
        self.detection_history.append(detection['is_talking'])

        # Apply smoothing - require majority of recent detections
        smoothed_talking = sum(self.detection_history) > len(self.detection_history) * 0.6

        # Apply state locking
        current_time = timestamp
        if smoothed_talking != self.is_talking:
            if current_time - self.state_lock_time >= self.MIN_STATE_DURATION:
                # State can change
                if smoothed_talking and not self.is_talking:
                    # Started talking
                    self.talking_start_time = current_time
                    logger.debug("🗣️ Talking detected")
                elif not smoothed_talking and self.is_talking:
                    # Stopped talking
                    self.talking_duration = current_time - (self.talking_start_time or current_time)
                    logger.debug(f"🤐 Talking stopped (duration: {self.talking_duration:.1f}s)")

                self.is_talking = smoothed_talking
                self.state_lock_time = current_time

        # Update duration if currently talking
        if self.is_talking and self.talking_start_time:
            self.talking_duration = current_time - self.talking_start_time

        self.talking_confidence = detection['confidence']

        return {
            'is_talking': self.is_talking,
            'confidence': self.talking_confidence,
            'duration': self.talking_duration,
            'reason': detection.get('reason', 'ok'),
            'gyro_variance': detection.get('gyro_variance', 0),
            'rhythm_score': detection.get('rhythm_score', 0),
        }

    def _detect_talking(self, is_meditation: bool = False) -> Dict:
        """
        Core talking detection algorithm

        Uses multiple features:
        1. Gyroscope variance (talking creates consistent oscillation)
        2. Speech rhythm detection (2-5 Hz oscillation)
        3. Accelerometer micro-movements
        4. Breathing pattern filter (for meditation - exclude 0.2-0.5 Hz)

        Args:
            is_meditation: If True, use higher threshold and filter breathing patterns
        """
        gyro_array = np.array(list(self.gyro_buffer))

        # Feature 1: Gyroscope variance (especially Y-axis for jaw)
        # Talking creates rhythmic jaw movement visible in gyroscope
        gyro_y = gyro_array[:, 1]  # Y-axis (pitch/jaw movement)
        gyro_variance = np.var(gyro_y)

        # Feature 2: Speech rhythm detection
        # Talking has characteristic 2-5 Hz rhythm
        rhythm_score = self._detect_speech_rhythm(gyro_y)

        # Feature 3: Breathing pattern detection (for meditation)
        # Breathing is 0.2-0.5 Hz, speech is 2-5 Hz - filter out breathing
        is_breathing = False
        if is_meditation and len(gyro_y) >= self.sample_rate * 2:  # Need 2+ seconds
            breathing_score = self._detect_breathing_pattern(gyro_y)
            if breathing_score > 0.5:  # Strong breathing pattern detected
                is_breathing = True
                # Reduce confidence if it's just breathing
                rhythm_score *= 0.3  # Heavily penalize if it's breathing rhythm

        # Feature 4: Accelerometer micro-movements (if available)
        acc_score = 0.0
        if len(self.acc_buffer) >= self.sample_rate:
            acc_array = np.array(list(self.acc_buffer))
            acc_variance = np.mean(np.var(acc_array, axis=0))
            acc_score = min(1.0, acc_variance / self.ACC_VARIANCE_THRESHOLD)

        # Combine features into confidence score
        # Gyroscope variance is primary indicator
        variance_score = min(1.0, gyro_variance / self.GYRO_VARIANCE_THRESHOLD)

        # Weight the features
        confidence = (
            variance_score * 0.4 +
            rhythm_score * 0.5 +
            acc_score * 0.1
        )

        # Use context-aware threshold
        threshold = self.CONFIDENCE_THRESHOLD_MEDITATION if is_meditation else self.CONFIDENCE_THRESHOLD
        
        # If breathing detected, require even higher confidence
        if is_breathing:
            threshold = max(threshold, 0.85)

        is_talking = confidence > threshold

        return {
            'is_talking': is_talking,
            'confidence': confidence,
            'gyro_variance': gyro_variance,
            'rhythm_score': rhythm_score,
            'acc_score': acc_score,
            'is_breathing': is_breathing,
            'reason': 'breathing' if is_breathing else ('detected' if is_talking else 'not_detected')
        }

    def _detect_speech_rhythm(self, signal_data: np.ndarray) -> float:
        """
        Detect speech rhythm in gyroscope signal

        Speech typically has rhythm at 2-5 Hz (syllable rate)

        Args:
            signal_data: 1D array of gyroscope data

        Returns:
            Rhythm score (0-1)
        """
        if len(signal_data) < self.sample_rate:
            return 0.0

        try:
            # Use Welch's method for power spectral density
            frequencies, psd = signal.welch(
                signal_data,
                fs=self.sample_rate,
                nperseg=min(self.sample_rate, len(signal_data)),
                noverlap=self.sample_rate // 2
            )

            # Find power in speech rhythm range (2-5 Hz)
            speech_range = np.logical_and(frequencies >= 2, frequencies <= 5)
            speech_power = np.sum(psd[speech_range])

            # Normalize by total power
            total_power = np.sum(psd)
            if total_power > 0:
                rhythm_ratio = speech_power / total_power
            else:
                rhythm_ratio = 0.0

            # Scale to 0-1 (typical speech has 30-50% power in this range)
            rhythm_score = min(1.0, rhythm_ratio / self.GYRO_RHYTHM_THRESHOLD)

            return rhythm_score

        except Exception as e:
            logger.debug(f"Error in rhythm detection: {e}")
            return 0.0

    def _detect_breathing_pattern(self, signal_data: np.ndarray) -> float:
        """
        Detect breathing pattern in gyroscope signal
        
        Breathing is typically 0.2-0.5 Hz (12-30 breaths per minute)
        This is much slower than speech (2-5 Hz)
        
        Args:
            signal_data: 1D array of gyroscope data
            
        Returns:
            Breathing pattern score (0-1)
        """
        if len(signal_data) < self.sample_rate * 2:  # Need at least 2 seconds
            return 0.0
        
        try:
            # Use Welch's method for power spectral density
            frequencies, psd = signal.welch(
                signal_data,
                fs=self.sample_rate,
                nperseg=min(self.sample_rate * 2, len(signal_data)),
                noverlap=None
            )
            
            # Breathing frequency range: 0.2-0.5 Hz
            breathing_mask = (frequencies >= 0.2) & (frequencies <= 0.5)
            breathing_power = np.sum(psd[breathing_mask])
            
            # Speech frequency range: 2-5 Hz (for comparison)
            speech_mask = (frequencies >= 2.0) & (frequencies <= 5.0)
            speech_power = np.sum(psd[speech_mask])
            
            # Total power in relevant range
            total_power = np.sum(psd[(frequencies >= 0.1) & (frequencies <= 10.0)])
            
            if total_power == 0:
                return 0.0
            
            # Breathing score: ratio of breathing power to total power
            # If breathing power is dominant and speech power is low, it's likely breathing
            breathing_ratio = breathing_power / total_power
            speech_ratio = speech_power / total_power
            
            # High breathing ratio + low speech ratio = strong breathing pattern
            if speech_ratio < 0.1:  # Very little speech activity
                return min(1.0, breathing_ratio * 2.0)  # Amplify breathing score
            else:
                # Some speech activity - reduce breathing score
                return max(0.0, breathing_ratio - speech_ratio)
                
        except Exception as e:
            logger.debug(f"Error in breathing detection: {e}")
            return 0.0

    def get_artifact_correction_factor(self) -> float:
        """
        Get a correction factor for EEG signal processing

        When talking is detected, we can use this to:
        - Weight the signal lower in averaging
        - Apply different filtering
        - Exclude from some calculations

        Returns:
            Factor from 0 (exclude completely) to 1 (full weight)
        """
        if not self.is_talking:
            return 1.0

        # Reduce weight based on confidence
        # High confidence talking = lower weight
        return max(0.2, 1.0 - self.talking_confidence * 0.8)

    def reset(self):
        """Reset detector state"""
        self.gyro_buffer.clear()
        self.acc_buffer.clear()
        self.detection_history.clear()
        self.is_talking = False
        self.talking_confidence = 0.0
        self.talking_start_time = None
        self.talking_duration = 0.0
        self.state_lock_time = 0.0


# Global instance
talking_detector = TalkingDetector()
