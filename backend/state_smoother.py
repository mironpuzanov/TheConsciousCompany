"""
Temporal smoothing for brain state and signal quality
Prevents rapid fluctuations in classification
"""

from collections import deque
from typing import Dict, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class StateSmoother:
    """
    Smooths brain state and signal quality over time to prevent rapid fluctuations
    """

    def __init__(self, window_size: int = 30):
        """
        Args:
            window_size: Number of seconds to average over (default: 30 seconds for stability)
        """
        self.window_size = window_size
        self.band_power_history: deque = deque(maxlen=window_size)
        self.signal_quality_history: deque = deque(maxlen=window_size)
        self.brain_state_history: deque = deque(maxlen=window_size)
        self.has_artifact_history: deque = deque(maxlen=window_size)
        self.previous_band_powers: Optional[Dict[str, float]] = None
        self.current_stable_state: Optional[str] = None
        self.state_change_time: float = 0.0
        self.min_state_duration: float = 10.0  # Minimum 10 seconds before state can change

    def add_sample(self, band_powers: Dict[str, float], signal_quality: float,
                   brain_state: str, has_artifact: bool):
        """Add a new sample to the smoothing buffer"""
        self.band_power_history.append(band_powers.copy())
        self.signal_quality_history.append(signal_quality)
        self.brain_state_history.append(brain_state)
        self.has_artifact_history.append(has_artifact)

    def get_smoothed_band_powers(self) -> Optional[Dict[str, float]]:
        """Get averaged band powers over the window"""
        if len(self.band_power_history) == 0:
            return None

        # Average band powers over time
        avg_powers = {}
        for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
            values = [bp.get(band, 0) for bp in self.band_power_history if band in bp]
            if values:
                avg_powers[band] = float(np.mean(values))
            else:
                avg_powers[band] = 0.0

        return avg_powers

    def get_smoothed_signal_quality(self) -> float:
        """Get averaged signal quality over the window"""
        if len(self.signal_quality_history) == 0:
            return 0.0
        return float(np.mean(list(self.signal_quality_history)))

    def get_smoothed_brain_state(self) -> str:
        """Get most common brain state over the window (mode) with stability check and minimum duration"""
        import time
        
        if len(self.brain_state_history) == 0:
            return 'unknown'

        # Count occurrences of each state
        state_counts = {}
        for state in self.brain_state_history:
            state_counts[state] = state_counts.get(state, 0) + 1

        if not state_counts:
            return 'unknown'
        
        # Get most common state
        most_common = max(state_counts.items(), key=lambda x: x[1])
        new_state, count = most_common
        
        # Only return state if it appears in at least 70% of samples (more stable)
        confidence = count / len(self.brain_state_history)
        if confidence < 0.7:
            # If no clear majority, check for artifact states (they take priority)
            if 'artifact_detected' in state_counts and state_counts['artifact_detected'] > len(self.brain_state_history) * 0.3:
                new_state = 'artifact_detected'
            elif 'low_confidence' in state_counts and state_counts['low_confidence'] > len(self.brain_state_history) * 0.3:
                new_state = 'low_confidence'
            elif self.current_stable_state:
                # Keep current state if no clear new state
                return self.current_stable_state
        
        # Enforce minimum duration before state change
        current_time = time.time()
        if self.current_stable_state is None:
            # First state - set it
            self.current_stable_state = new_state
            self.state_change_time = current_time
            return new_state
        
        # Check if state actually changed
        if new_state != self.current_stable_state:
            # State changed - check if enough time has passed
            time_since_change = current_time - self.state_change_time
            if time_since_change >= self.min_state_duration:
                # Enough time passed - allow change
                self.current_stable_state = new_state
                self.state_change_time = current_time
                return new_state
            else:
                # Not enough time - keep current state
                return self.current_stable_state
        
        # Same state - update time if needed
        return self.current_stable_state
    
    def get_previous_band_powers(self) -> Optional[Dict[str, float]]:
        """Get previous band powers for change detection"""
        return self.previous_band_powers
    
    def update_previous_band_powers(self, band_powers: Dict[str, float]):
        """Update previous band powers"""
        self.previous_band_powers = band_powers.copy()

    def get_artifact_ratio(self) -> float:
        """Get ratio of samples with artifacts (0-1)"""
        if len(self.has_artifact_history) == 0:
            return 0.0
        return float(np.mean([1 if x else 0 for x in self.has_artifact_history]))

    def is_stable(self) -> bool:
        """Check if the signal is stable (low variance in quality)"""
        if len(self.signal_quality_history) < 3:
            return False
        quality_std = np.std(list(self.signal_quality_history))
        return quality_std < 10  # Low variance = stable

