"""
Muse EEG Streaming Module
Uses muselsl to connect to Muse device and stream EEG data
"""

import asyncio
import numpy as np
from typing import Optional, Callable, Dict
from pylsl import StreamInlet, resolve_byprop
import logging

logger = logging.getLogger(__name__)


class MuseStreamer:
    """
    Handles connection to Muse device via LSL (Lab Streaming Layer)
    Supports multiple sensor streams: EEG, PPG, ACC, GYRO
    """

    def __init__(self):
        self.eeg_inlet: Optional[StreamInlet] = None
        self.ppg_inlet: Optional[StreamInlet] = None
        self.acc_inlet: Optional[StreamInlet] = None
        self.gyro_inlet: Optional[StreamInlet] = None
        self.is_streaming = False
        self.eeg_sample_rate = 256  # Muse 2 sampling rate
        self.n_channels = 4  # TP9, AF7, AF8, TP10

    def connect(self, timeout: float = 10.0) -> bool:
        """
        Connect to all available Muse streams via LSL (EEG, PPG, ACC, GYRO)

        Args:
            timeout: Maximum time to wait for streams (seconds)

        Returns:
            True if at least EEG stream connected successfully, False otherwise
        """
        try:
            logger.info("Searching for Muse streams...")

            # Connect to EEG stream (required)
            eeg_streams = resolve_byprop('type', 'EEG', timeout=timeout)
            if not eeg_streams:
                logger.error("No EEG stream found. Make sure muselsl is running.")
                logger.error("Run: muselsl stream --ppg --acc --gyro")
                return False

            self.eeg_inlet = StreamInlet(eeg_streams[0], max_chunklen=12)
            eeg_info = self.eeg_inlet.info()
            logger.info(f"✅ Connected to EEG stream: {eeg_info.name()}")
            logger.info(f"   Channels: {eeg_info.channel_count()}, Rate: {eeg_info.nominal_srate()} Hz")

            # Try to connect to PPG stream (optional)
            try:
                ppg_streams = resolve_byprop('type', 'PPG', timeout=2.0)
                if ppg_streams:
                    self.ppg_inlet = StreamInlet(ppg_streams[0], max_chunklen=6)
                    ppg_info = self.ppg_inlet.info()
                    logger.info(f"✅ Connected to PPG stream: {ppg_info.name()}")
            except Exception as e:
                logger.warning(f"PPG stream not available: {e}")

            # Try to connect to ACC stream (optional)
            try:
                acc_streams = resolve_byprop('type', 'ACC', timeout=2.0)
                if acc_streams:
                    self.acc_inlet = StreamInlet(acc_streams[0], max_chunklen=1)
                    acc_info = self.acc_inlet.info()
                    logger.info(f"✅ Connected to ACC stream: {acc_info.name()}")
            except Exception as e:
                logger.warning(f"ACC stream not available: {e}")

            # Try to connect to GYRO stream (optional)
            try:
                gyro_streams = resolve_byprop('type', 'GYRO', timeout=2.0)
                if gyro_streams:
                    self.gyro_inlet = StreamInlet(gyro_streams[0], max_chunklen=1)
                    gyro_info = self.gyro_inlet.info()
                    logger.info(f"✅ Connected to GYRO stream: {gyro_info.name()}")
            except Exception as e:
                logger.warning(f"GYRO stream not available: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to Muse: {e}")
            return False

    def disconnect(self):
        """
        Disconnect from all Muse streams
        """
        self.is_streaming = False
        if self.eeg_inlet:
            self.eeg_inlet.close_stream()
            self.eeg_inlet = None
        if self.ppg_inlet:
            self.ppg_inlet.close_stream()
            self.ppg_inlet = None
        if self.acc_inlet:
            self.acc_inlet.close_stream()
            self.acc_inlet = None
        if self.gyro_inlet:
            self.gyro_inlet.close_stream()
            self.gyro_inlet = None
        logger.info("Disconnected from all Muse streams")

    async def stream_data(self, callback: Callable, auto_reconnect: bool = True, max_reconnect_attempts: int = 5):
        """
        Stream data from all available sensors asynchronously with auto-reconnect

        Args:
            callback: Function to call with sensor data
                     Receives (eeg_samples, eeg_timestamp, ppg_data, acc_data, gyro_data)
            auto_reconnect: If True, automatically reconnect when stream is lost (default: True)
            max_reconnect_attempts: Maximum number of reconnection attempts (default: 5)
        """
        if not self.eeg_inlet:
            raise RuntimeError("Not connected to Muse. Call connect() first.")

        self.is_streaming = True
        logger.info("Starting multi-sensor stream with auto-reconnect...")

        reconnect_attempts = 0

        while self.is_streaming and reconnect_attempts <= max_reconnect_attempts:
            consecutive_errors = 0
            no_data_count = 0  # Track consecutive iterations with no data
            max_consecutive_errors = 100  # Stop only after 100 consecutive errors
            max_no_data_iterations = 50  # Detect stream loss after 50 iterations (~0.5s) with no data
            chunks_processed = 0
            last_data_time = asyncio.get_event_loop().time()

            try:
                while self.is_streaming:
                    try:
                        # Pull EEG data (primary stream)
                        eeg_chunk, eeg_timestamps = self.eeg_inlet.pull_chunk(timeout=0.0, max_samples=12)
                        eeg_samples = None
                        eeg_timestamp = 0.0

                        if eeg_chunk:
                            eeg_samples = np.array(eeg_chunk)
                            eeg_timestamp = eeg_timestamps[0] if eeg_timestamps else 0.0
                            chunks_processed += 1
                            no_data_count = 0  # Reset no-data counter
                            last_data_time = asyncio.get_event_loop().time()

                            if chunks_processed % 100 == 0:  # Log every 100 chunks (~4 seconds)
                                logger.info(f"✅ EEG Stream active: processed {chunks_processed} chunks, shape: {eeg_samples.shape}")

                        # Pull PPG data (if available)
                        ppg_data = None
                        if self.ppg_inlet:
                            try:
                                ppg_chunk, ppg_timestamps = self.ppg_inlet.pull_chunk(timeout=0.0, max_samples=6)
                                if ppg_chunk and len(ppg_chunk) > 0:
                                    ppg_data = np.array(ppg_chunk[-1])  # Last sample [ambient, infrared, red]
                                    if chunks_processed % 100 == 0:
                                        logger.info(f"PPG data received: {ppg_data}")
                            except Exception as e:
                                logger.debug(f"Error pulling PPG: {e}")
                        elif chunks_processed % 5000 == 0:  # Only log every 5000 chunks (~20s) instead of every 500
                            logger.debug("PPG inlet not connected")

                        # Pull ACC data (if available)
                        acc_data = None
                        if self.acc_inlet:
                            try:
                                acc_chunk, _ = self.acc_inlet.pull_chunk(timeout=0.0, max_samples=1)
                                if acc_chunk and len(acc_chunk) > 0:
                                    acc_data = np.array(acc_chunk[-1])  # [x, y, z]
                            except Exception as e:
                                logger.debug(f"Error pulling ACC: {e}")

                        # Pull GYRO data (if available)
                        gyro_data = None
                        if self.gyro_inlet:
                            try:
                                gyro_chunk, _ = self.gyro_inlet.pull_chunk(timeout=0.0, max_samples=1)
                                if gyro_chunk and len(gyro_chunk) > 0:
                                    gyro_data = np.array(gyro_chunk[-1])  # [x, y, z]
                            except Exception as e:
                                logger.debug(f"Error pulling GYRO: {e}")

                        # Call callback with all sensor data
                        if eeg_samples is not None:
                            try:
                                await callback(eeg_samples, eeg_timestamp, ppg_data, acc_data, gyro_data)
                                consecutive_errors = 0  # Reset error counter on success
                            except Exception as e:
                                consecutive_errors += 1
                                logger.error(f"Error in callback (error #{consecutive_errors}): {e}", exc_info=True)
                                # Continue streaming even if callback fails
                                if consecutive_errors >= 10:
                                    logger.error(f"Too many callback errors ({consecutive_errors}), but continuing stream...")
                                pass
                        else:
                            # No EEG data - increment counter
                            no_data_count += 1

                            # Check if stream might be lost
                            if no_data_count >= max_no_data_iterations:
                                time_since_data = asyncio.get_event_loop().time() - last_data_time
                                if time_since_data > 5.0:  # No data for 5 seconds = stream lost
                                    logger.warning(f"⚠️  No data received for {time_since_data:.1f}s - LSL stream may have disconnected")
                                    if auto_reconnect:
                                        logger.info("🔄 Attempting auto-reconnect...")
                                        break  # Exit inner loop to trigger reconnect
                                    else:
                                        logger.error("Auto-reconnect disabled, stopping stream")
                                        self.is_streaming = False
                                        break

                            await asyncio.sleep(0.01)
                            continue

                        # Small sleep to prevent busy loop
                        await asyncio.sleep(0.01)

                    except Exception as e:
                        consecutive_errors += 1
                        if consecutive_errors <= 5:  # Only log first few errors
                            logger.error(f"Error processing chunk in stream_data: {e}", exc_info=True)
                        elif consecutive_errors == 6:
                            logger.warning(f"Multiple consecutive errors ({consecutive_errors}), suppressing logs...")

                        # Stop only if too many consecutive errors
                        if consecutive_errors >= max_consecutive_errors:
                            logger.error(f"Too many consecutive errors ({consecutive_errors})")
                            if auto_reconnect and reconnect_attempts < max_reconnect_attempts:
                                logger.info("🔄 Attempting auto-reconnect due to errors...")
                                break  # Exit inner loop to trigger reconnect
                            else:
                                logger.error("Stopping stream")
                                self.is_streaming = False
                                break

                        # Continue streaming even if one chunk fails
                        await asyncio.sleep(0.1)

                # If we broke out of inner loop and still streaming, attempt reconnect
                if self.is_streaming and auto_reconnect and reconnect_attempts < max_reconnect_attempts:
                    reconnect_attempts += 1
                    logger.info(f"🔄 Reconnection attempt {reconnect_attempts}/{max_reconnect_attempts}...")

                    # Close existing connections
                    self.disconnect()
                    await asyncio.sleep(2.0)  # Wait before reconnecting

                    # Try to reconnect
                    if self.connect(timeout=10.0):
                        logger.info(f"✅ Reconnected successfully! Resuming stream...")
                        reconnect_attempts = 0  # Reset counter on successful reconnect
                        chunks_processed = 0  # Reset chunk counter for new connection
                    else:
                        logger.error(f"❌ Reconnection attempt {reconnect_attempts} failed")
                        if reconnect_attempts >= max_reconnect_attempts:
                            logger.error("Max reconnection attempts reached, stopping stream")
                            self.is_streaming = False
                        else:
                            logger.info(f"Retrying in 5 seconds...")
                            await asyncio.sleep(5.0)
                else:
                    # Normal exit or max reconnects reached
                    break

            except Exception as e:
                logger.error(f"Fatal error in stream_data: {e}", exc_info=True)
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")

                if auto_reconnect and reconnect_attempts < max_reconnect_attempts:
                    reconnect_attempts += 1
                    logger.warning(f"Attempting recovery (attempt {reconnect_attempts}/{max_reconnect_attempts})...")
                    await asyncio.sleep(1.0)
                    continue
                else:
                    logger.error("Cannot recover, stopping stream")
                    self.is_streaming = False
                    break

        if reconnect_attempts > max_reconnect_attempts:
            logger.error(f"❌ Failed to maintain stream after {reconnect_attempts} reconnection attempts")
        else:
            logger.info(f"✅ Multi-sensor stream stopped gracefully")

    def get_device_info(self) -> Dict:
        """
        Get information about the connected Muse device and available streams

        Returns:
            Dictionary with device information
        """
        if not self.eeg_inlet:
            return {'connected': False}

        eeg_info = self.eeg_inlet.info()

        info = {
            'connected': True,
            'name': eeg_info.name(),
            'type': eeg_info.type(),
            'channel_count': eeg_info.channel_count(),
            'sample_rate': eeg_info.nominal_srate(),
            'channels': ['TP9', 'AF7', 'AF8', 'TP10'],  # Muse 2 electrode positions
            'sensors': {
                'eeg': True,
                'ppg': self.ppg_inlet is not None,
                'acc': self.acc_inlet is not None,
                'gyro': self.gyro_inlet is not None,
            }
        }

        return info


async def start_muselsl_stream():
    """
    Helper function to start muselsl stream in background
    This should be called before connecting to the stream

    Note: In production, you should run `muselsl stream` manually
    or use subprocess to start it automatically
    """
    import subprocess

    try:
        # Start muselsl stream as background process
        process = subprocess.Popen(
            ['muselsl', 'stream'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait a bit for stream to start
        await asyncio.sleep(3)

        logger.info("muselsl stream started")
        return process

    except Exception as e:
        logger.error(f"Failed to start muselsl stream: {e}")
        logger.info("Please run 'muselsl stream' manually in another terminal")
        return None
