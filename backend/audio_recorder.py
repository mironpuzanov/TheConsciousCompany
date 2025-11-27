"""
Audio Recording Module
Records from system microphone with real-time streaming support
Optimized for Whisper transcription (16kHz)
"""

import pyaudio
import wave
import asyncio
import numpy as np
from pathlib import Path
from typing import Optional, Callable
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AudioRecorder:
    """
    Records audio from system microphone
    Supports both file recording and real-time streaming
    """

    def __init__(
        self,
        sample_rate: int = 16000,  # Whisper optimized
        chunk_size: int = 1024,
        channels: int = 1,
        format: int = pyaudio.paInt16
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format = format

        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording = False
        self.frames = []

        logger.info(f"AudioRecorder initialized: {sample_rate}Hz, {channels} channel(s)")

    def list_devices(self):
        """List available audio input devices"""
        logger.info("Available audio input devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                logger.info(f"  [{i}] {info['name']} - {info['maxInputChannels']} channels")

    def start_recording(self, output_path: Optional[Path] = None) -> Path:
        """
        Start recording audio to file

        Args:
            output_path: Path to save WAV file (auto-generated if None)

        Returns:
            Path to output file
        """
        if self.is_recording:
            raise RuntimeError("Already recording")

        # Generate output path if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"recordings/audio_{timestamp}.wav")
            output_path.parent.mkdir(parents=True, exist_ok=True)

        self.output_path = output_path
        self.frames = []

        # Open audio stream
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._recording_callback
        )

        self.is_recording = True
        self.stream.start_stream()

        logger.info(f"✅ Recording started: {output_path}")
        return output_path

    def _recording_callback(self, in_data, frame_count, time_info, status):
        """Callback for file recording"""
        if self.is_recording:
            self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    def stop_recording(self) -> Path:
        """
        Stop recording and save to file

        Returns:
            Path to saved WAV file
        """
        if not self.is_recording:
            raise RuntimeError("Not recording")

        self.is_recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        # Save to WAV file
        with wave.open(str(self.output_path), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))

        logger.info(f"✅ Recording saved: {self.output_path}")
        return self.output_path

    async def stream_audio(self, chunk_duration: float = 2.0) -> bytes:
        """
        Stream audio in real-time chunks (for Whisper)

        Args:
            chunk_duration: Duration of each chunk in seconds (default: 2s)

        Yields:
            Audio chunks as bytes (16kHz, mono, int16)
        """
        if self.is_recording:
            raise RuntimeError("Already recording to file, cannot stream simultaneously")

        chunk_frames = int(self.sample_rate * chunk_duration / self.chunk_size)

        logger.info(f"🎤 Starting audio stream (chunks: {chunk_duration}s)")

        try:
            # Open stream
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            buffer = []

            while True:
                # Read audio data (use run_in_executor to avoid blocking event loop)
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None,
                    lambda: stream.read(self.chunk_size, exception_on_overflow=False)
                )
                buffer.append(data)

                # Yield chunk when buffer is full
                if len(buffer) >= chunk_frames:
                    chunk = b''.join(buffer)
                    buffer = []

                    # Convert to numpy for processing
                    audio_np = np.frombuffer(chunk, dtype=np.int16)

                    # Normalize to float32 [-1, 1] (Whisper expects this)
                    audio_float = audio_np.astype(np.float32) / 32768.0

                    yield audio_float

        except Exception as e:
            logger.error(f"Error in audio stream: {e}")
            raise
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            logger.info("🎤 Audio stream stopped")

    def get_audio_level(self) -> float:
        """
        Get current audio input level (0-1)
        Useful for visualizing microphone activity

        Returns:
            Audio level (RMS amplitude)
        """
        if not self.stream or not self.is_recording:
            return 0.0

        try:
            data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            audio_np = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_np.astype(np.float32) ** 2))
            # Normalize to 0-1 range
            return min(rms / 3000.0, 1.0)
        except:
            return 0.0

    def close(self):
        """Clean up audio resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()
        logger.info("AudioRecorder closed")


# Test/debug functionality
if __name__ == "__main__":
    import time

    logging.basicConfig(level=logging.INFO)

    recorder = AudioRecorder()

    print("\n=== Audio Recorder Test ===\n")
    recorder.list_devices()

    print("\n--- Test 1: File Recording (5 seconds) ---")
    output = recorder.start_recording()
    print("Recording... (5 seconds)")
    time.sleep(5)
    recorder.stop_recording()
    print(f"Saved to: {output}")

    print("\n--- Test 2: Streaming (10 seconds) ---")
    async def test_stream():
        chunk_count = 0
        async for chunk in recorder.stream_audio(chunk_duration=2.0):
            chunk_count += 1
            print(f"Chunk {chunk_count}: {len(chunk)} samples, RMS: {np.sqrt(np.mean(chunk**2)):.4f}")
            if chunk_count >= 5:  # 10 seconds (5 chunks × 2 sec)
                break

    asyncio.run(test_stream())

    recorder.close()
    print("\n=== Tests Complete ===")
