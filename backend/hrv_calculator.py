"""
Heart Rate Variability (HRV) Calculator
Calculates HRV metrics from PPG (photoplethysmography) data

FIXED: Using scipy.signal.find_peaks for robust peak detection
"""

import numpy as np
from scipy import signal
from typing import List, Optional, Dict
from collections import deque
import logging

logger = logging.getLogger(__name__)


class HRVCalculator:
    """
    Calculate HRV metrics from PPG sensor data
    """

    def __init__(self, sample_rate: int = 64):
        self.sample_rate = sample_rate
        # Muse PPG is actually ~64 samples/sec but via LSL often comes slower
        # Use large buffer to accommodate various rates
        self.ppg_buffer = deque(maxlen=2000)  # ~30+ seconds at any rate
        self.peak_times: List[float] = []
        self.last_peak_time: Optional[float] = None
        self.last_valid_heart_rate: float = 0.0  # Cache last valid heart rate

    def update_ppg(self, ppg_data: np.ndarray, timestamp: float):
        """
        Update PPG buffer with new data

        Args:
            ppg_data: PPG data [ambient, infrared, red] or single value
            timestamp: Timestamp of the data
        """
        try:
            # Handle different input formats
            if isinstance(ppg_data, (int, float)):
                # Single value
                infrared = float(ppg_data)
            elif len(ppg_data.shape) == 0:
                # Scalar numpy array
                infrared = float(ppg_data.item())
            elif len(ppg_data) == 1:
                # Single element array
                infrared = float(ppg_data[0])
            else:
                # Multiple channels, use infrared (index 1) or red (index 2) as fallback
                if len(ppg_data) >= 2:
                    infrared = float(ppg_data[1])
                elif len(ppg_data) >= 1:
                    infrared = float(ppg_data[0])
                else:
                    return  # Invalid data
            
            self.ppg_buffer.append((infrared, timestamp))
        except Exception as e:
            # Silently handle errors to avoid spam
            pass

    def detect_peaks(self) -> List[float]:
        """
        Detect peaks in PPG signal (heartbeats) using scipy.signal.find_peaks

        Returns:
            List of timestamps where peaks were detected
        """
        if len(self.ppg_buffer) < 10:  # Need some data
            return []

        # Check if we have at least 3 seconds of data based on timestamps
        timestamps_check = [item[1] for item in self.ppg_buffer]
        duration = timestamps_check[-1] - timestamps_check[0]
        if duration < 3.0:  # Need at least 3 seconds for reliable detection
            return []

        # Extract infrared channel values and timestamps
        values = np.array([item[0] for item in self.ppg_buffer])
        timestamps = np.array([item[1] for item in self.ppg_buffer])

        if len(values) < 5:  # Need minimum samples
            return []

        # Calculate actual sample rate from timestamps
        if len(timestamps) > 10:
            actual_duration = timestamps[-1] - timestamps[0]
            if actual_duration > 0:
                actual_rate = len(timestamps) / actual_duration
                if abs(actual_rate - self.sample_rate) > 10:
                    # Sample rate mismatch - use actual rate
                    self.sample_rate = int(actual_rate)
                    logger.info(f"PPG actual sample rate: {actual_rate:.1f} Hz")

        # Normalize signal (remove DC offset and scale)
        values_normalized = values - np.mean(values)
        std_val = np.std(values_normalized)

        # Debug: log signal characteristics
        if len(self.ppg_buffer) % 200 == 0:
            logger.info(f"PPG signal: mean={np.mean(values):.0f}, std={std_val:.1f}, min={np.min(values):.0f}, max={np.max(values):.0f}")
        if std_val > 0:
            values_normalized = values_normalized / std_val

        # Apply bandpass filter for PPG (0.5-4 Hz = 30-240 BPM)
        # But only if sample rate is high enough (Nyquist > 4 Hz means fs > 8 Hz)
        try:
            if self.sample_rate >= 10:
                sos = signal.butter(
                    N=2,
                    Wn=[0.5, 4],  # 0.5-4 Hz
                    btype='bandpass',
                    fs=self.sample_rate,
                    output='sos'
                )
                filtered = signal.sosfilt(sos, values_normalized)
            else:
                # Low sample rate - just use normalized signal (already smooth)
                logger.debug(f"PPG sample rate too low for bandpass filter: {self.sample_rate} Hz")
                filtered = values_normalized
        except Exception as e:
            logger.debug(f"Filter error: {e}")
            filtered = values_normalized

        # Use scipy.signal.find_peaks with physiologically reasonable constraints
        # Minimum distance: 0.4s (150 BPM max), Maximum distance: 2s (30 BPM min)
        min_distance_samples = max(1, int(self.sample_rate * 0.4))  # ~150 BPM max, min 1

        # Find peaks using scipy (much more robust)
        peak_indices, properties = signal.find_peaks(
            filtered,
            distance=min_distance_samples,
            prominence=0.3,  # Require some prominence to avoid noise
            height=None  # Don't filter by height
        )

        if len(peak_indices) < 2:
            # Try with lower prominence
            peak_indices, _ = signal.find_peaks(
                filtered,
                distance=min_distance_samples,
                prominence=0.1,
            )

        # Convert indices to timestamps
        peak_timestamps = []
        for idx in peak_indices:
            if 0 <= idx < len(timestamps):
                peak_timestamps.append(timestamps[idx])
        
        # Update peak_times for partial data fallback
        self.peak_times = peak_timestamps

        # Debug: log peak detection results periodically
        if len(self.ppg_buffer) % 200 == 0:
            logger.info(f"Peak detection: found {len(peak_indices)} peaks, sample_rate={self.sample_rate}, buffer_size={len(self.ppg_buffer)}")
            if len(filtered) > 0:
                logger.info(f"Filtered signal: min={np.min(filtered):.3f}, max={np.max(filtered):.3f}")

        return peak_timestamps

    def calculate_hrv(self) -> Dict:
        """
        Calculate HRV metrics from detected peaks

        Returns:
            Dictionary with HRV metrics
        """
        # Debug: log buffer state periodically
        if len(self.ppg_buffer) > 0 and len(self.ppg_buffer) % 100 == 0:
            values = [item[0] for item in list(self.ppg_buffer)[-10:]]
            logger.info(f"HRV buffer: {len(self.ppg_buffer)} samples, recent values: {values[:3]}")

        peaks = self.detect_peaks()

        if len(peaks) < 3:  # Need at least 3 peaks for 2 RR intervals
            return {
                'heart_rate': 0,
                'hrv_rmssd': 0,
                'hrv_sdnn': 0,
                'rr_intervals': [],
                'valid': False,
                'debug': {'peaks_found': len(peaks), 'buffer_size': len(self.ppg_buffer), 'reason': 'insufficient_peaks'}
            }

        # Calculate RR intervals (time between peaks)
        # Peaks are timestamps in seconds, convert to milliseconds
        rr_intervals = []
        outliers = 0
        for i in range(1, len(peaks)):
            rr_seconds = peaks[i] - peaks[i-1]
            rr_ms = rr_seconds * 1000  # Convert to milliseconds
            # Valid RR interval: 400-2000ms (30-150 bpm)
            if 400 <= rr_ms <= 2000:
                rr_intervals.append(rr_ms)
            else:
                outliers += 1
                # Only log occasionally to avoid spam
                if outliers <= 3:
                    logger.debug(f"Outlier RR: {rr_ms:.0f}ms")

        if len(rr_intervals) < 2:
            return {
                'heart_rate': 0,
                'hrv_rmssd': 0,
                'hrv_sdnn': 0,
                'rr_intervals': [],
                'valid': False,
                'debug': {'peaks_found': len(peaks), 'valid_rr': len(rr_intervals), 'outliers': outliers}
            }

        # Calculate heart rate (bpm)
        avg_rr = np.mean(rr_intervals)
        heart_rate = 60000 / avg_rr if avg_rr > 0 else 0

        # Calculate RMSSD (Root Mean Square of Successive Differences)
        # This is a measure of short-term HRV
        # RMSSD should typically be 20-100ms for healthy adults at rest
        successive_diffs = np.diff(rr_intervals)
        rmssd = np.sqrt(np.mean(successive_diffs ** 2))

        # Calculate SDNN (Standard Deviation of NN intervals)
        # This is a measure of overall HRV
        sdnn = np.std(rr_intervals)

        # Sanity check - if RMSSD is way too high, something is wrong
        # Only log occasionally to avoid spam
        if rmssd > 200 and len(self.ppg_buffer) % 500 == 0:
            logger.warning(f"RMSSD unusually high: {rmssd:.1f}ms - low PPG sample rate may cause inaccurate HRV")
            logger.debug(f"RR intervals: {rr_intervals}")

        # Cache the valid heart rate
        self.last_valid_heart_rate = float(heart_rate)
        
        return {
            'heart_rate': float(heart_rate),
            'hrv_rmssd': float(rmssd),
            'hrv_sdnn': float(sdnn),
            'rr_intervals': [float(rr) for rr in rr_intervals[-10:]],  # Last 10 intervals
            'valid': True,
            'debug': {'peaks_found': len(peaks), 'valid_rr': len(rr_intervals), 'avg_rr_ms': avg_rr}
        }

    def get_current_metrics(self) -> Dict:
        """
        Get current HRV metrics (called periodically)

        Returns:
            Dictionary with current HRV metrics
        """
        metrics = self.calculate_hrv()
        
        # If not fully valid but we have a cached heart rate, use it (better than showing 0)
        if not metrics.get('valid', False) and self.last_valid_heart_rate > 0:
            metrics['heart_rate'] = self.last_valid_heart_rate
            metrics['valid'] = True  # Allow display
            metrics['cached'] = True  # Mark as cached/estimated
        
        # If we have some peaks but not enough for full validation, try to estimate
        elif not metrics.get('valid', False) and len(self.peak_times) >= 2:
            # Calculate basic heart rate from last two peaks
            rr_seconds = self.peak_times[-1] - self.peak_times[-2]
            if 0.4 <= rr_seconds <= 2.0:  # Valid RR range (30-150 bpm)
                heart_rate = 60.0 / rr_seconds
                if 30 <= heart_rate <= 150:  # Physiologically reasonable
                    metrics['heart_rate'] = float(heart_rate)
                    metrics['valid'] = True  # Mark as valid for display
                    metrics['partial'] = True  # But mark as partial data
                    self.last_valid_heart_rate = float(heart_rate)
        
        return metrics

