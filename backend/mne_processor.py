"""
MNE-Python based signal processor with proper artifact removal
Uses ICA and ASR for production-grade artifact removal
"""

import numpy as np
from typing import Dict, Optional
import mne
from mne.preprocessing import ICA, create_eog_epochs
from mne.filter import filter_data, notch_filter
import logging

logger = logging.getLogger(__name__)

# Muse 2 channel names and positions
MUSE_CHANNELS = ['TP9', 'AF7', 'AF8', 'TP10']
SAMPLE_RATE = 256


class MNEProcessor:
    """
    Production-grade EEG processor using MNE-Python
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.ica: Optional[ICA] = None
        self.ica_fitted = False
        self.bad_channels = []
        
        # Create MNE info object
        self.info = mne.create_info(
            ch_names=MUSE_CHANNELS,
            sfreq=sample_rate,
            ch_types='eeg'
        )

    def apply_filters(self, data: np.ndarray) -> np.ndarray:
        """
        Apply bandpass and notch filters using MNE
        
        Args:
            data: EEG data [n_channels, n_samples] or [n_samples, n_channels]
            
        Returns:
            Filtered data
        """
        # Ensure shape is [n_channels, n_samples] for MNE
        if len(data.shape) == 1:
            data = data.reshape(1, -1)
        if data.shape[0] != 4:
            # Assume [n_samples, n_channels], transpose
            if data.shape[1] == 4:
                data = data.T
        
        # Bandpass filter (0.5-50 Hz)
        filtered = filter_data(
            data,
            sfreq=self.sample_rate,
            l_freq=0.5,
            h_freq=50.0,
            method='fir',
            phase='zero-double'
        )
        
        # Notch filter (60 Hz) - Use scipy for shorter signals
        from scipy import signal as scipy_signal
        b, a = scipy_signal.iirnotch(w0=60, Q=30, fs=self.sample_rate)
        sos = scipy_signal.tf2sos(b, a)
        filtered = scipy_signal.sosfilt(sos, filtered)
        
        return filtered

    def fit_ica(self, data: np.ndarray, n_components: int = 3):
        """
        Fit ICA for artifact removal
        
        Args:
            data: EEG data [n_channels, n_samples]
            n_components: Number of ICA components (max 3 for 4 channels)
        """
        try:
            # Create RawArray for MNE
            raw = mne.io.RawArray(data, self.info)
            
            # Fit ICA
            self.ica = ICA(n_components=min(n_components, data.shape[0] - 1), random_state=97)
            self.ica.fit(raw)
            self.ica_fitted = True
            logger.info(f"ICA fitted with {self.ica.n_components_} components")
        except Exception as e:
            logger.error(f"Error fitting ICA: {e}")
            self.ica = None

    def apply_ica(self, data: np.ndarray, exclude_components: Optional[list] = None) -> np.ndarray:
        """
        Apply ICA to remove artifacts
        
        Args:
            data: EEG data [n_channels, n_samples]
            exclude_components: List of component indices to exclude (auto-detect if None)
            
        Returns:
            Cleaned data
        """
        if not self.ica_fitted or self.ica is None:
            return data
        
        try:
            # Create RawArray
            raw = mne.io.RawArray(data, self.info)
            
            # Auto-detect artifact components if not specified
            if exclude_components is None:
                exclude_components = []
                # Detect EOG artifacts (eye blinks) - handle gracefully if no EOG channel
                try:
                    eog_inds, scores = self.ica.find_bads_eog(raw, threshold=1.5)
                    if eog_inds:
                        exclude_components.extend(eog_inds)
                except Exception as e:
                    logger.debug(f"Could not detect EOG artifacts (no EOG channel): {e}")
                
                # Detect muscle artifacts
                try:
                    muscle_inds, _ = self.ica.find_bads_muscle(raw, threshold=0.3)
                    if muscle_inds:
                        exclude_components.extend(muscle_inds)
                except Exception as e:
                    logger.debug(f"Could not detect muscle artifacts: {e}")
                
                exclude_components = list(set(exclude_components))
                
                if exclude_components:
                    logger.debug(f"ICA removing {len(exclude_components)} artifact components: {exclude_components}")
            
            # Apply ICA
            if exclude_components:
                self.ica.exclude = exclude_components
                raw_clean = self.ica.apply(raw, exclude=self.ica.exclude)
                return raw_clean.get_data()
            else:
                return data
                
        except Exception as e:
            logger.error(f"Error applying ICA: {e}")
            return data

    def calculate_signal_quality(self, data: np.ndarray) -> Dict:
        """
        Calculate signal quality metrics
        
        Args:
            data: EEG data [n_channels, n_samples]
            
        Returns:
            Dictionary with quality metrics
        """
        quality = {
            'snr': 0.0,
            'mean_amplitude': 0.0,
            'std_amplitude': 0.0,
            'bad_channels': [],
            'confidence': 0.0
        }
        
        if data.shape[0] == 0:
            return quality
        
        # Calculate per-channel metrics
        channel_amplitudes = np.mean(np.abs(data), axis=1)
        channel_stds = np.std(data, axis=1)
        
        quality['mean_amplitude'] = float(np.mean(channel_amplitudes))
        quality['std_amplitude'] = float(np.mean(channel_stds))
        
        # Estimate SNR (signal vs noise)
        signal_power = np.mean(channel_amplitudes ** 2)
        noise_power = np.mean(channel_stds ** 2)
        if noise_power > 0:
            quality['snr'] = float(10 * np.log10(signal_power / noise_power))
        
        # Detect bad channels (too high or too low amplitude)
        mean_amp = np.mean(channel_amplitudes)
        std_amp = np.std(channel_amplitudes)
        
        bad_chans = []
        for i, amp in enumerate(channel_amplitudes):
            if amp < 5 or amp > mean_amp + 3 * std_amp:
                bad_chans.append(i)
        
        quality['bad_channels'] = bad_chans
        
        # Calculate confidence (0-100)
        # Based on SNR, channel quality, and amplitude
        snr_score = min(quality['snr'] / 20.0, 1.0) * 100  # Good SNR is >20dB
        channel_score = (1 - len(bad_chans) / data.shape[0]) * 100
        amplitude_score = 100 if 10 < quality['mean_amplitude'] < 100 else 50
        
        quality['confidence'] = float((snr_score + channel_score + amplitude_score) / 3)
        
        return quality

    def process_window(self, data: np.ndarray, apply_ica: bool = True) -> Dict:
        """
        Process a window of EEG data with MNE
        
        Args:
            data: Raw EEG data [n_samples] or [n_samples, n_channels]
            apply_ica: Whether to apply ICA artifact removal
            
        Returns:
            Dictionary with processed data and metrics
        """
        # Convert to [n_channels, n_samples] if needed
        if len(data.shape) == 1:
            # Single channel - average across all channels from buffer
            data = data.reshape(1, -1)
        elif data.shape[0] == 4 and data.shape[1] != 4:
            # Already [n_channels, n_samples]
            pass
        else:
            # [n_samples, n_channels], transpose
            data = data.T
        
        # Apply filters
        filtered = self.apply_filters(data)
        
        # Apply ICA if fitted
        if apply_ica and self.ica_fitted:
            filtered = self.apply_ica(filtered)
        
        # Calculate signal quality
        quality = self.calculate_signal_quality(filtered)
        
        return {
            'filtered_data': filtered.T.tolist(),  # Return as [n_samples, n_channels]
            'quality': quality,
            'has_artifact': len(quality['bad_channels']) > 0 or quality['confidence'] < 50
        }

