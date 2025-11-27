"""
Whisper Transcription Module
Real-time speech-to-text using faster-whisper
Optimized for streaming audio with minimal latency
"""

import numpy as np
from faster_whisper import WhisperModel
from typing import Dict, Optional, List
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """
    Real-time speech transcription using Whisper
    Uses faster-whisper for optimized inference
    """

    def __init__(
        self,
        model_size: str = "base",  # tiny, base, small, medium, large
        device: str = "cpu",  # cpu or cuda
        compute_type: str = "int8"  # int8, int16, float16, float32
    ):
        """
        Initialize Whisper model

        Args:
            model_size: Model size (base recommended for speed/accuracy balance)
            device: cpu or cuda
            compute_type: Quantization type (int8 recommended for CPU)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

        logger.info(f"Loading Whisper model: {model_size} on {device} ({compute_type})")

        try:
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=str(Path.home() / ".cache" / "whisper")
            )
            logger.info(f"✅ Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

        # Transcription settings
        self.language = "en"  # Auto-detect or specify
        self.min_silence_duration = 0.5  # Seconds of silence to end segment
        self.last_transcription_time = 0

    async def transcribe_stream(
        self,
        audio_chunk: np.ndarray,
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio chunk in real-time

        Args:
            audio_chunk: Audio data as float32 numpy array [-1, 1]
            language: Language code (None for auto-detect)

        Returns:
            {
                'text': str,           # Transcribed text
                'language': str,       # Detected language
                'confidence': float,   # Average confidence (0-1)
                'timestamp': float,    # Unix timestamp
                'duration': float,     # Audio chunk duration
                'segments': list       # Detailed segments (optional)
            }
        """
        start_time = time.time()

        # Check if audio is too short or silent
        if len(audio_chunk) < 1600:  # <0.1 seconds at 16kHz
            return {
                'text': '',
                'language': self.language,
                'confidence': 0.0,
                'timestamp': start_time,
                'duration': len(audio_chunk) / 16000.0,
                'segments': []
            }

        # Check if audio is silent (RMS < threshold)
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        if rms < 0.01:  # Very quiet
            return {
                'text': '',
                'language': self.language,
                'confidence': 0.0,
                'timestamp': start_time,
                'duration': len(audio_chunk) / 16000.0,
                'segments': []
            }

        try:
            # Transcribe
            segments, info = self.model.transcribe(
                audio_chunk,
                language=language or self.language,
                beam_size=1,  # Faster inference (trade-off accuracy)
                best_of=1,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(
                    min_silence_duration_ms=int(self.min_silence_duration * 1000)
                )
            )

            # Extract text and confidence
            text_parts = []
            confidences = []
            segment_list = []

            for segment in segments:
                text_parts.append(segment.text.strip())
                confidences.append(segment.avg_logprob)  # Log probability
                segment_list.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text.strip(),
                    'confidence': segment.avg_logprob
                })

            full_text = ' '.join(text_parts).strip()
            avg_confidence = np.mean(confidences) if confidences else 0.0

            # Convert log prob to probability (rough approximation)
            confidence_score = min(max((avg_confidence + 2) / 2, 0.0), 1.0)

            inference_time = time.time() - start_time
            self.last_transcription_time = inference_time

            # Log if text found
            if full_text:
                logger.info(f"🎤 Transcribed ({inference_time:.2f}s): \"{full_text}\" (confidence: {confidence_score:.2f})")

            return {
                'text': full_text,
                'language': info.language,
                'confidence': confidence_score,
                'timestamp': start_time,
                'duration': len(audio_chunk) / 16000.0,
                'segments': segment_list,
                'inference_time': inference_time
            }

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {
                'text': '',
                'language': self.language,
                'confidence': 0.0,
                'timestamp': start_time,
                'duration': len(audio_chunk) / 16000.0,
                'segments': [],
                'error': str(e)
            }

    def transcribe_file(self, audio_path: Path) -> str:
        """
        Transcribe entire audio file

        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)

        Returns:
            Full transcription text
        """
        logger.info(f"Transcribing file: {audio_path}")

        try:
            segments, info = self.model.transcribe(
                str(audio_path),
                language=self.language,
                beam_size=5,  # Higher accuracy for offline processing
                vad_filter=True
            )

            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())

            full_text = ' '.join(text_parts).strip()

            logger.info(f"✅ Transcription complete: {len(full_text)} characters")
            return full_text

        except Exception as e:
            logger.error(f"File transcription error: {e}")
            return ""

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return [
            'en', 'zh', 'es', 'fr', 'de', 'ja', 'ko', 'ru', 'pt', 'it',
            'nl', 'ar', 'tr', 'pl', 'uk', 'vi', 'hi', 'th', 'id', 'he'
        ]

    def set_language(self, language: str):
        """Set default transcription language"""
        if language in self.get_supported_languages():
            self.language = language
            logger.info(f"Language set to: {language}")
        else:
            logger.warning(f"Unsupported language: {language}, using auto-detect")

    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            'model_size': self.model_size,
            'device': self.device,
            'compute_type': self.compute_type,
            'language': self.language,
            'last_inference_time': self.last_transcription_time
        }


# Test/debug functionality
if __name__ == "__main__":
    import asyncio
    from audio_recorder import AudioRecorder

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n=== Whisper Transcriber Test ===\n")

    # Initialize
    transcriber = WhisperTranscriber(model_size="base", device="cpu")
    recorder = AudioRecorder()

    print("Model info:", transcriber.get_model_info())
    print("\nSupported languages:", transcriber.get_supported_languages()[:10], "...")

    print("\n--- Real-Time Transcription Test (20 seconds) ---")
    print("Speak into your microphone...\n")

    async def test_realtime():
        chunk_count = 0
        full_transcript = []

        async for audio_chunk in recorder.stream_audio(chunk_duration=3.0):
            chunk_count += 1
            print(f"\nChunk {chunk_count}:")

            # Transcribe
            result = await transcriber.transcribe_stream(audio_chunk)

            if result['text']:
                full_transcript.append(result['text'])
                print(f"  Text: \"{result['text']}\"")
                print(f"  Confidence: {result['confidence']:.2f}")
                print(f"  Inference time: {result['inference_time']:.2f}s")

            if chunk_count >= 6:  # 18 seconds (6 chunks × 3 sec)
                break

        print("\n--- Full Transcript ---")
        print(' '.join(full_transcript))

    try:
        asyncio.run(test_realtime())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    finally:
        recorder.close()

    print("\n=== Test Complete ===")
