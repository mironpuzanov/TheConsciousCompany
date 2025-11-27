"""
Session Recording Module
Records EEG data, band powers, and events for later analysis
Supports both local storage and cloud upload (Supabase)
"""

import json
import os
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque
import numpy as np
import logging
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class SessionMetadata:
    """Metadata for a recording session"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    device_name: str = "Muse 2"
    sample_rate: int = 256
    channels: List[str] = None
    notes: str = ""
    tags: List[str] = None

    def __post_init__(self):
        if self.channels is None:
            self.channels = ["TP9", "AF7", "AF8", "TP10"]
        if self.tags is None:
            self.tags = []


@dataclass
class EEGSample:
    """Single EEG sample with all channels"""
    timestamp: float  # LSL timestamp
    local_time: str   # Human readable
    channels: List[float]  # [TP9, AF7, AF8, TP10]


@dataclass
class ProcessedSample:
    """Processed data (1 per second)"""
    timestamp: float
    local_time: str
    band_powers: Dict[str, float]  # delta, theta, alpha, beta, gamma
    brain_state: str
    signal_quality: float
    heart_rate: float
    hrv_rmssd: float
    # NEW: Artifact features (continuous 0-1 values, NOT binary flags)
    emg_intensity: float = 0.0       # jaw/face muscle activity (stress/talking)
    forehead_emg: float = 0.0        # cognitive effort indicator
    blink_intensity: float = 0.0     # overwhelm/fatigue indicator
    movement_intensity: float = 0.0  # emotional activation
    data_quality: float = 1.0        # signal quality (only discard if <0.5)
    # Legacy fields (backward compat)
    has_artifact: bool = False       # Only true for garbage data
    artifact_type: str = "clean"     # Informational only
    # Sensor data
    acc_data: Optional[List[float]] = None  # [x, y, z]
    gyro_data: Optional[List[float]] = None  # [x, y, z]
    is_talking: bool = False


@dataclass
class SessionEvent:
    """Events during session (artifacts, state changes, markers)"""
    timestamp: float
    local_time: str
    event_type: str  # 'artifact', 'state_change', 'marker', 'talking'
    description: str
    data: Optional[Dict] = None


class SessionRecorder:
    """
    Records and saves EEG session data

    Data is stored in:
    - Raw EEG samples (high frequency, for detailed analysis)
    - Processed samples (1/second, band powers and states)
    - Events (artifacts, markers)
    """

    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = sessions_dir
        self.is_recording = False
        self.current_session: Optional[SessionMetadata] = None

        # Buffers for current session
        self.raw_samples: List[EEGSample] = []
        self.processed_samples: List[ProcessedSample] = []
        self.events: List[SessionEvent] = []

        # Buffer for real-time processing (don't save every sample)
        self.raw_buffer: deque = deque(maxlen=256 * 60)  # 60 seconds buffer
        self.save_raw = True  # Can disable to save space

        # Talking detection state
        self.talking_buffer: deque = deque(maxlen=30)  # 30 seconds of talking detection

        # Ensure sessions directory exists
        os.makedirs(sessions_dir, exist_ok=True)

    def start_session(self, notes: str = "", tags: List[str] = None) -> str:
        """
        Start a new recording session

        Returns:
            Session ID
        """
        if self.is_recording:
            logger.warning("Already recording - stopping previous session")
            self.stop_session()

        # Generate session ID
        now = datetime.now()
        session_id = now.strftime("%Y%m%d_%H%M%S")

        self.current_session = SessionMetadata(
            session_id=session_id,
            start_time=now.isoformat(),
            notes=notes,
            tags=tags or []
        )

        # Clear buffers
        self.raw_samples = []
        self.processed_samples = []
        self.events = []
        self.raw_buffer.clear()
        self.talking_buffer.clear()

        self.is_recording = True

        # Create session directory
        session_path = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_path, exist_ok=True)

        logger.info(f"🔴 Started recording session: {session_id}")

        # Add start event
        self.add_event("session_start", "Recording started")

        return session_id

    def stop_session(self) -> Optional[str]:
        """
        Stop current recording session and save data

        Returns:
            Path to saved session or None if no session
        """
        if not self.is_recording or not self.current_session:
            logger.warning("No active recording session")
            return None

        self.is_recording = False

        # Update metadata
        now = datetime.now()
        self.current_session.end_time = now.isoformat()

        # Calculate duration
        start = datetime.fromisoformat(self.current_session.start_time)
        self.current_session.duration_seconds = (now - start).total_seconds()

        # Add stop event
        self.add_event("session_stop", f"Recording stopped. Duration: {self.current_session.duration_seconds:.1f}s")

        # Save session
        session_path = self._save_session()

        logger.info(f"⏹️ Stopped recording session: {self.current_session.session_id}")
        logger.info(f"   Duration: {self.current_session.duration_seconds:.1f}s")
        logger.info(f"   Raw samples: {len(self.raw_samples)}")
        logger.info(f"   Processed samples: {len(self.processed_samples)}")
        logger.info(f"   Events: {len(self.events)}")
        logger.info(f"   Saved to: {session_path}")

        # Clear current session
        self.current_session = None

        return session_path

    def add_raw_sample(self, timestamp: float, channels: List[float]):
        """
        Add raw EEG sample (called at 256 Hz)

        Args:
            timestamp: LSL timestamp
            channels: [TP9, AF7, AF8, TP10] values
        """
        if not self.is_recording:
            return

        # Always add to buffer for analysis
        self.raw_buffer.append((timestamp, channels))

        # Only save raw if enabled (can generate large files)
        if self.save_raw:
            sample = EEGSample(
                timestamp=timestamp,
                local_time=datetime.now().isoformat(),
                channels=channels
            )
            self.raw_samples.append(sample)

    def add_processed_sample(self,
                             timestamp: float,
                             band_powers: Dict[str, float],
                             brain_state: str,
                             signal_quality: float,
                             heart_rate: float,
                             hrv_rmssd: float,
                             # NEW artifact features
                             emg_intensity: float = 0.0,
                             forehead_emg: float = 0.0,
                             blink_intensity: float = 0.0,
                             movement_intensity: float = 0.0,
                             data_quality: float = 1.0,
                             # Legacy
                             has_artifact: bool = False,
                             artifact_type: str = "clean",
                             acc_data: Optional[List[float]] = None,
                             gyro_data: Optional[List[float]] = None,
                             is_talking: bool = False):
        """
        Add processed sample (called at 1 Hz)
        """
        if not self.is_recording:
            return

        sample = ProcessedSample(
            timestamp=timestamp,
            local_time=datetime.now().isoformat(),
            band_powers=band_powers,
            brain_state=brain_state,
            signal_quality=signal_quality,
            heart_rate=heart_rate,
            hrv_rmssd=hrv_rmssd,
            emg_intensity=emg_intensity,
            forehead_emg=forehead_emg,
            blink_intensity=blink_intensity,
            movement_intensity=movement_intensity,
            data_quality=data_quality,
            has_artifact=has_artifact,
            artifact_type=artifact_type,
            acc_data=acc_data,
            gyro_data=gyro_data,
            is_talking=is_talking
        )
        self.processed_samples.append(sample)

        # Track talking for analysis
        self.talking_buffer.append(is_talking)

    def add_event(self, event_type: str, description: str, data: Optional[Dict] = None):
        """
        Add event marker

        Args:
            event_type: 'artifact', 'state_change', 'marker', 'talking', etc.
            description: Human-readable description
            data: Optional additional data
        """
        if not self.is_recording and event_type not in ['session_start', 'session_stop']:
            return

        event = SessionEvent(
            timestamp=datetime.now().timestamp(),
            local_time=datetime.now().isoformat(),
            event_type=event_type,
            description=description,
            data=data
        )
        self.events.append(event)

    def add_marker(self, label: str, notes: str = ""):
        """
        Add a manual marker (e.g., "started talking", "eyes closed")
        """
        self.add_event("marker", label, {"notes": notes})
        logger.info(f"📌 Marker added: {label}")

    def _save_session(self) -> str:
        """
        Save session data to disk

        Returns:
            Path to session directory
        """
        if not self.current_session:
            return ""

        session_path = os.path.join(self.sessions_dir, self.current_session.session_id)

        # Save metadata
        metadata_path = os.path.join(session_path, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(asdict(self.current_session), f, indent=2)

        # Save processed samples (most important - small file)
        processed_path = os.path.join(session_path, "processed.json")
        with open(processed_path, 'w') as f:
            json.dump([asdict(s) for s in self.processed_samples], f, indent=2)

        # Save events
        events_path = os.path.join(session_path, "events.json")
        with open(events_path, 'w') as f:
            json.dump([asdict(e) for e in self.events], f, indent=2)

        # Save raw EEG as CSV (more efficient for large data)
        if self.save_raw and self.raw_samples:
            raw_path = os.path.join(session_path, "eeg_raw.csv")
            with open(raw_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'local_time', 'TP9', 'AF7', 'AF8', 'TP10'])
                for sample in self.raw_samples:
                    writer.writerow([
                        sample.timestamp,
                        sample.local_time,
                        *sample.channels
                    ])

        # Generate summary
        summary = self._generate_summary()
        summary_path = os.path.join(session_path, "summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        return session_path

    def _generate_summary(self) -> Dict:
        """Generate session summary statistics"""
        if not self.processed_samples:
            return {}

        # Calculate statistics
        brain_states = [s.brain_state for s in self.processed_samples]
        state_counts = {}
        for state in brain_states:
            state_counts[state] = state_counts.get(state, 0) + 1

        # Average band powers
        avg_band_powers = {}
        for band in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
            values = [s.band_powers.get(band, 0) for s in self.processed_samples]
            avg_band_powers[band] = sum(values) / len(values) if values else 0

        # Signal quality
        qualities = [s.signal_quality for s in self.processed_samples]

        # Artifact ratio
        artifact_count = sum(1 for s in self.processed_samples if s.has_artifact)

        # Talking ratio
        talking_count = sum(1 for s in self.processed_samples if s.is_talking)

        # Heart rate stats
        heart_rates = [s.heart_rate for s in self.processed_samples if s.heart_rate > 0]

        # NEW: Artifact feature averages
        emg_values = [s.emg_intensity for s in self.processed_samples]
        forehead_values = [s.forehead_emg for s in self.processed_samples]
        blink_values = [s.blink_intensity for s in self.processed_samples]
        movement_values = [s.movement_intensity for s in self.processed_samples]
        quality_values = [s.data_quality for s in self.processed_samples]

        return {
            'duration_seconds': self.current_session.duration_seconds if self.current_session else 0,
            'total_samples': len(self.processed_samples),
            'brain_state_distribution': state_counts,
            'dominant_state': max(state_counts, key=state_counts.get) if state_counts else 'unknown',
            'average_band_powers': avg_band_powers,
            'signal_quality': {
                'mean': sum(qualities) / len(qualities) if qualities else 0,
                'min': min(qualities) if qualities else 0,
                'max': max(qualities) if qualities else 0,
            },
            # NEW: Artifact feature summary (continuous 0-1)
            'artifact_features': {
                'emg_intensity': {'mean': sum(emg_values) / len(emg_values) if emg_values else 0, 'max': max(emg_values) if emg_values else 0},
                'forehead_emg': {'mean': sum(forehead_values) / len(forehead_values) if forehead_values else 0, 'max': max(forehead_values) if forehead_values else 0},
                'blink_intensity': {'mean': sum(blink_values) / len(blink_values) if blink_values else 0, 'max': max(blink_values) if blink_values else 0},
                'movement_intensity': {'mean': sum(movement_values) / len(movement_values) if movement_values else 0, 'max': max(movement_values) if movement_values else 0},
                'data_quality': {'mean': sum(quality_values) / len(quality_values) if quality_values else 1.0, 'min': min(quality_values) if quality_values else 1.0},
            },
            'artifact_ratio': artifact_count / len(self.processed_samples) if self.processed_samples else 0,
            'talking_ratio': talking_count / len(self.processed_samples) if self.processed_samples else 0,
            'heart_rate': {
                'mean': sum(heart_rates) / len(heart_rates) if heart_rates else 0,
                'min': min(heart_rates) if heart_rates else 0,
                'max': max(heart_rates) if heart_rates else 0,
            },
            'events_count': len(self.events),
        }

    def get_session_status(self) -> Dict:
        """Get current recording status"""
        return {
            'is_recording': self.is_recording,
            'session_id': self.current_session.session_id if self.current_session else None,
            'duration_seconds': (
                (datetime.now() - datetime.fromisoformat(self.current_session.start_time)).total_seconds()
                if self.current_session else 0
            ),
            'samples_recorded': len(self.processed_samples),
            'events_count': len(self.events),
        }

    def list_sessions(self) -> List[Dict]:
        """List all saved sessions"""
        sessions = []

        if not os.path.exists(self.sessions_dir):
            return sessions

        for session_id in sorted(os.listdir(self.sessions_dir), reverse=True):
            session_path = os.path.join(self.sessions_dir, session_id)
            if not os.path.isdir(session_path):
                continue

            metadata_path = os.path.join(session_path, "metadata.json")
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    sessions.append(metadata)
                except Exception as e:
                    logger.error(f"Error loading session {session_id}: {e}")

        return sessions

    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load a saved session"""
        session_path = os.path.join(self.sessions_dir, session_id)

        if not os.path.exists(session_path):
            logger.error(f"Session not found: {session_id}")
            return None

        result = {}

        # Load metadata
        metadata_path = os.path.join(session_path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                result['metadata'] = json.load(f)

        # Load processed samples
        processed_path = os.path.join(session_path, "processed.json")
        if os.path.exists(processed_path):
            with open(processed_path, 'r') as f:
                result['processed'] = json.load(f)

        # Load events
        events_path = os.path.join(session_path, "events.json")
        if os.path.exists(events_path):
            with open(events_path, 'r') as f:
                result['events'] = json.load(f)

        # Load summary
        summary_path = os.path.join(session_path, "summary.json")
        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                result['summary'] = json.load(f)

        return result

    def update_session_metadata(self, session_id: str, notes: Optional[str] = None, tags: Optional[List[str]] = None, name: Optional[str] = None) -> bool:
        """
        Update session metadata (notes, tags, or friendly name)

        Args:
            session_id: Session ID to update
            notes: New notes (or None to keep existing)
            tags: New tags (or None to keep existing)
            name: Friendly name for the session (or None to keep existing)

        Returns:
            True if updated successfully, False otherwise
        """
        session_path = os.path.join(self.sessions_dir, session_id)
        metadata_path = os.path.join(session_path, "metadata.json")

        if not os.path.exists(metadata_path):
            logger.error(f"Session metadata not found: {session_id}")
            return False

        try:
            # Load existing metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # Update fields if provided
            if notes is not None:
                metadata['notes'] = notes
            if tags is not None:
                metadata['tags'] = tags
            if name is not None:
                metadata['name'] = name  # Friendly name

            # Save updated metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Updated metadata for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating session metadata: {e}")
            return False

    def rename_session(self, session_id: str, new_name: str) -> bool:
        """
        Add a friendly name to a session (doesn't change session_id, just adds 'name' field)

        Args:
            session_id: Session ID (timestamp-based like 20251121_192907)
            new_name: Friendly name (e.g., "Good TP9 Contact Session")

        Returns:
            True if renamed successfully, False otherwise
        """
        return self.update_session_metadata(session_id, name=new_name)


# Global instance
session_recorder = SessionRecorder()
