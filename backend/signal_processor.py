"""
Signal Processing Module for EEG Data
Uses scipy for scientific-grade filtering and numpy for FFT analysis
"""

import numpy as np
from scipy import signal
from typing import Dict, List, Tuple

# EEG frequency bands (Hz)
BANDS = {
    'delta': (0.5, 4),    # Deep sleep
    'theta': (4, 8),      # Meditation, creativity
    'alpha': (8, 13),     # Relaxed, calm
    'beta': (13, 30),     # Active thinking
    'gamma': (30, 50),    # Peak focus
}

# Muse 2 sampling rate
SAMPLE_RATE = 256  # Hz


class SignalProcessor:
    """
    Research-grade EEG signal processor using scipy filters
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate

        # Design Butterworth bandpass filter (0.5-50 Hz)
        # This removes DC offset and high-frequency noise
        self.bandpass_sos = signal.butter(
            N=4,  # 4th order filter
            Wn=[0.5, 50],  # Passband: 0.5-50 Hz
            btype='bandpass',
            fs=sample_rate,
            output='sos'  # Second-order sections for numerical stability
        )

        # Design notch filter for 60 Hz powerline noise
        # iirnotch returns (b, a) coefficients, convert to SOS format
        b, a = signal.iirnotch(
            w0=60,  # 60 Hz (US powerline frequency)
            Q=30,   # Quality factor
            fs=sample_rate
        )
        self.notch_sos = signal.tf2sos(b, a)

    def filter_signal(self, data: np.ndarray) -> np.ndarray:
        """
        Apply bandpass and notch filters to raw EEG data

        Args:
            data: Raw EEG samples (1D array)

        Returns:
            Filtered EEG samples
        """
        # Apply bandpass filter
        filtered = signal.sosfilt(self.bandpass_sos, data)

        # Apply notch filter for powerline noise
        filtered = signal.sosfilt(self.notch_sos, filtered)

        return filtered

    def calculate_band_powers(self, data: np.ndarray) -> Dict[str, float]:
        """
        Calculate power in each frequency band using Welch's method

        Args:
            data: Filtered EEG samples (should be at least 1 second)

        Returns:
            Dictionary with band powers as percentages
        """
        if len(data) < self.sample_rate:
            # Need at least 1 second of data
            return {band: 0.0 for band in BANDS.keys()}

        # Use Welch's method for power spectral density estimation
        # More robust than raw FFT for noisy signals
        frequencies, psd = signal.welch(
            data,
            fs=self.sample_rate,
            nperseg=min(256, len(data)),  # Window size
            noverlap=128,  # 50% overlap
            scaling='density'
        )

        # Calculate power in each band
        band_powers = {}
        for band_name, (low_freq, high_freq) in BANDS.items():
            # Find frequency bins within this band
            idx = np.logical_and(frequencies >= low_freq, frequencies <= high_freq)

            # Integrate power spectral density over frequency band
            # Using trapezoidal integration
            band_power = np.trapz(psd[idx], frequencies[idx])
            band_powers[band_name] = band_power

        # Normalize to percentages
        total_power = sum(band_powers.values())
        if total_power > 0:
            band_powers = {
                band: float((power / total_power) * 100)  # Ensure Python float, not numpy float
                for band, power in band_powers.items()
            }

        return band_powers

    def detect_artifacts(self, data: np.ndarray, threshold: float = 100) -> bool:
        """
        Simple artifact detection based on amplitude threshold

        Args:
            data: EEG samples
            threshold: Maximum allowed amplitude (microvolts)

        Returns:
            True if artifact detected, False otherwise
        """
        return np.max(np.abs(data)) > threshold

    def process_window(self, data: np.ndarray) -> Dict:
        """
        Process a window of EEG data and extract features

        Args:
            data: Raw EEG samples (should be at least 1 second)

        Returns:
            Dictionary containing filtered data, band powers, and quality metrics
        """
        # Filter the signal
        filtered = self.filter_signal(data)

        # Note: Artifact detection is now done in artifact_detector module
        # This simple check is kept as a fallback
        has_artifact = self.detect_artifacts(filtered)

        # Always calculate band powers (artifact detection happens separately)
        # We'll exclude artifacts in the classification step
        band_powers = self.calculate_band_powers(filtered)

        return {
            'filtered_data': filtered.tolist(),
            'band_powers': band_powers,
            'has_artifact': bool(has_artifact),  # Convert numpy bool to Python bool
            'mean': float(np.mean(filtered)),
            'std': float(np.std(filtered)),
        }


def get_brain_state(band_powers: Dict[str, float], is_meditation: bool = False) -> str:
    """
    Determine brain state using ratio-based classification (more stable)
    
    Uses band power ratios instead of just dominant band for better accuracy
    
    For meditation: Uses band powers directly, ignores EMG-based artifacts
    For conversation: Standard classification with artifact awareness

    Args:
        band_powers: Dictionary of band powers (percentages)
        is_meditation: If True, use meditation-specific state classification

    Returns:
        String describing the brain state
    """
    if not band_powers or sum(band_powers.values()) == 0:
        return 'unknown'

    delta = band_powers.get('delta', 0)
    theta = band_powers.get('theta', 0)
    alpha = band_powers.get('alpha', 0)
    beta = band_powers.get('beta', 0)
    gamma = band_powers.get('gamma', 0)

    # Calculate ratios (more stable than absolute values)
    total = delta + theta + alpha + beta + gamma
    if total == 0:
        return 'unknown'

    # Ratio-based classification (more reliable)
    beta_alpha_ratio = beta / (alpha + 1e-6)  # Avoid division by zero
    theta_beta_ratio = theta / (beta + 1e-6)
    alpha_delta_ratio = alpha / (delta + 1e-6)

    # Meditation-specific classification (use band powers directly)
    if is_meditation:
        # Deep meditation: High theta + alpha, low beta
        if theta > 20 and alpha > 25 and beta < 15:
            return 'deep_meditation'
        
        # Meditative state: High theta or high alpha
        if theta > 15 or alpha > 30:
            return 'meditative'
        
        # Entering meditation: Moderate theta/alpha, decreasing beta
        if (theta > 10 or alpha > 20) and beta < 20:
            return 'entering_meditation'
        
        # Returning: Beta increasing, alpha decreasing
        if beta > 20 and alpha < 20:
            return 'returning'
        
        # Default for meditation: use dominant frequency
        if alpha > delta and alpha > beta:
            return 'relaxed'
        elif theta > delta and theta > beta:
            return 'meditative'
        else:
            return 'mixed'

    # Standard classification (conversation/active states)
    # High delta (>40%) when awake is likely artifact or poor signal
    if delta > 40:
        return 'mixed'  # Likely artifact or poor signal quality

    # Focused state: High beta, moderate alpha
    if beta > 30 and beta_alpha_ratio > 1.5:
        return 'focused'

    # Peak focus: High gamma + beta
    if gamma > 15 and beta > 25:
        return 'peak_focus'

    # Relaxed: High alpha, low beta
    if alpha > 30 and beta < 20:
        return 'relaxed'

    # Creative/meditative: High theta, moderate alpha
    if theta > 25 and alpha > 20:
        return 'creative'

    # Drowsy: High delta + theta (but only if delta is reasonable)
    if delta > 30 and theta > 20 and delta < 40:
        return 'drowsy'

    # Instead of "mixed", try to determine the most likely state based on ratios
    # Even if not perfect, give a specific state rather than "mixed"
    
    # If we have some activity, prefer focused over mixed
    if beta > 20 or gamma > 10:
        return 'focused'
    
    # If we have relaxation, prefer relaxed
    if alpha > 20:
        return 'relaxed'
    
    # If we have theta, prefer creative
    if theta > 15:
        return 'creative'
    
    # Last resort - if delta is reasonable, assume relaxed
    if delta < 30:
        return 'relaxed'
    
    # Only use mixed as absolute last resort
    return 'mixed'
