"""
AI Co-Pilot Session Coordinator
Orchestrates all components: audio, transcription, ML analysis, fusion, GPT-5
Manages real-time conversation flow and WebSocket communication
"""

import asyncio
import logging
from typing import Optional, Callable
from pathlib import Path
from collections import deque
import json
import time
import statistics

from audio_recorder import AudioRecorder
from whisper_transcriber import WhisperTranscriber
from ml_analyzer import MLAnalyzer
from fusion_engine import FusionEngine
from gpt5_copilot import GPT5Copilot

logger = logging.getLogger(__name__)


class CopilotSession:
    """
    Real-time AI co-pilot session
    Coordinates: Audio → Whisper → ML → Fusion → GPT-5 → Response
    """

    def __init__(self):
        """Initialize all components"""
        logger.info("Initializing CopilotSession...")

        # Initialize components
        self.audio_recorder = AudioRecorder()
        self.transcriber = WhisperTranscriber(model_size="base")
        self.ml_analyzer = MLAnalyzer()
        self.fusion_engine = FusionEngine(window_size=60)
        self.gpt5_copilot = GPT5Copilot()

        # Session state
        self.is_active = False
        self.brain_state: Optional[dict] = None
        self.session_start_time = 0
        self.gpt_decision_interval = 10.0  # Seconds between GPT decisions
        self.last_gpt_decision = 0
        self.websocket_callback: Optional[Callable] = None  # Store for brain state updates

        # Brain state history for median/average calculation (store last 60 samples = ~60 seconds)
        self.brain_state_history = deque(maxlen=60)

        logger.info("✅ CopilotSession initialized successfully")

    async def start_session(self, websocket_callback: Callable):
        """
        Start real-time co-pilot session

        Args:
            websocket_callback: Async function to send messages to frontend
                               await websocket_callback({'type': ..., 'data': ...})
        """
        if self.is_active:
            logger.warning("Session already active, stopping previous session first")
            self.stop_session()
            await asyncio.sleep(0.5)  # Give previous session time to clean up

        self.is_active = True
        self.session_start_time = time.time()
        self.websocket_callback = websocket_callback  # Store for brain state updates

        logger.info("🚀 Starting AI co-pilot session")

        # Send initial AI greeting
        await websocket_callback({
            'type': 'ai_message',
            'text': "Hi! I'm here to check in with you. How are you feeling today?",
            'timestamp': time.time()
        })

        # TEXT-ONLY MODE: Disable audio to avoid microphone permission crashes
        logger.info("⚠️ Running in TEXT-ONLY mode (microphone disabled)")
        logger.info("Type messages in the chat interface to interact with the AI")

        # Keep session alive for text message processing
        # The receive_messages task in main.py handles incoming text
        try:
            while self.is_active:
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            logger.info("Session cancelled")
        except Exception as e:
            logger.error(f"Session error: {e}", exc_info=True)
            await websocket_callback({
                'type': 'error',
                'message': f"Session error: {str(e)}",
                'timestamp': time.time()
            })

        self.is_active = False
        logger.info("AI co-pilot session ended")

    async def _process_utterance(
        self,
        transcript_result: dict,
        websocket_callback: Callable
    ):
        """
        Process transcribed utterance through ML → Fusion → GPT-5

        Args:
            transcript_result: Whisper transcription result
            websocket_callback: Function to send updates to frontend
        """
        text = transcript_result['text']
        timestamp = transcript_result['timestamp']

        logger.info(f"Processing: \"{text}\"")

        # Send transcript to frontend ONLY for voice (not text messages)
        # Text messages are already shown in frontend optimistically
        if transcript_result.get('confidence', 1.0) < 1.0:
            # Voice transcript (confidence < 1.0) - send to frontend
            await websocket_callback({
                'type': 'transcript',
                'text': text,
                'confidence': transcript_result['confidence'],
                'timestamp': timestamp
            })

        # Analyze text with ML models
        text_features = self.ml_analyzer.analyze(text)

        # Fuse with brain state
        if self.brain_state is None:
            # If no brain data yet, use defaults
            self.brain_state = self._get_default_brain_state()

        fused_state = self.fusion_engine.fuse(
            brain_state=self.brain_state,
            text_features=text_features,
            raw_text=text
        )

        # Add baseline brain state for context (median over session)
        baseline = self.get_brain_state_baseline()
        fused_state['brain_baseline'] = baseline

        # Send fused state to frontend (for UI updates)
        await websocket_callback({
            'type': 'state_update',
            'brain_state': {
                'stress': fused_state['brain_stress'],
                'hr': fused_state['hr'],
                'emotion': fused_state['emotion'],
                'emotion_arousal': fused_state.get('arousal', 0.0),
                'cognitive_load': fused_state['cognitive_load'],
                'alpha': fused_state.get('alpha', 0.0),
                'beta': fused_state.get('beta', 0.0),
                'gamma': fused_state.get('gamma', 0.0),
                'theta': fused_state.get('theta', 0.0),
                'delta': fused_state.get('delta', 0.0),
                'emg_intensity': fused_state.get('emg_intensity', 0.0)  # Changed from 'emg' to 'emg_intensity'
            },
            'text_features': {
                'sentiment': {
                    'label': fused_state['sentiment'],
                    'score': fused_state['sentiment_score']
                },
                'emotion': {
                    'label': fused_state['emotion'],
                    'score': fused_state['emotion_score']
                },
                'topics': fused_state['topics'],
                'psychological_labels': text_features.get('psychological_labels', {}),
                'stress_indicators': text_features.get('stress_indicators', {})
            },
            'incongruence': fused_state['incongruence'],
            'timestamp': timestamp
        })

        # Check if AI should respond
        should_respond = self._should_gpt_respond(fused_state)

        if should_respond:
            logger.info("🤖 GPT-5 generating response...")

            try:
                # Send typing indicator
                await websocket_callback({
                    'type': 'ai_typing',
                    'timestamp': time.time()
                })

                # Generate GPT-5 response
                full_response = ""
                async for chunk in self.gpt5_copilot.generate_response(
                    list(self.fusion_engine.context_window),
                    stream=True
                ):
                    full_response += chunk

                    # Stream to frontend
                    await websocket_callback({
                        'type': 'ai_message_chunk',
                        'text': chunk,
                        'timestamp': time.time()
                    })

                # Send complete message
                await websocket_callback({
                    'type': 'ai_message_complete',
                    'text': full_response,
                    'timestamp': time.time()
                })

                self.last_gpt_decision = time.time()

            except Exception as e:
                logger.error(f"GPT-5 response generation failed: {e}")
                # Send fallback message
                await websocket_callback({
                    'type': 'ai_message_complete',
                    'text': "I'm having trouble generating a response right now. Let's take a breath and continue.",
                    'timestamp': time.time()
                })

    async def process_text_message(self, text: str, websocket_callback: Callable):
        """
        Process a typed text message from the user

        Args:
            text: User's typed message
            websocket_callback: Function to send updates to frontend
        """
        logger.info(f"Processing text message: \"{text}\"")

        # Create transcript result similar to audio transcription
        transcript_result = {
            'text': text,
            'timestamp': time.time(),
            'confidence': 1.0  # Text input has 100% confidence
        }

        # Process through the same pipeline as voice
        await self._process_utterance(transcript_result, websocket_callback)

    def _should_gpt_respond(self, fused_state: dict) -> bool:
        """
        Determine if GPT should respond now

        Criteria:
        1. Intervention needed (stress spike, incongruence)
        2. User asked a question
        3. Time interval elapsed (every 10-15 seconds)
        """
        # Immediate intervention needed
        if fused_state['should_intervene']:
            logger.info(f"Intervention triggered: {fused_state['intervention_reason']}")
            return True

        # User asked a question
        if fused_state['is_question']:
            logger.info("User asked a question")
            return True

        # Time-based (don't respond too frequently)
        time_since_last = time.time() - self.last_gpt_decision
        if time_since_last > self.gpt_decision_interval:
            logger.info(f"Time interval elapsed ({time_since_last:.1f}s)")
            return True

        return False

    def update_brain_state(self, brain_state: dict):
        """
        Update brain state from main.py EEG processing

        Called every second with latest brain data

        Args:
            brain_state: {
                'stress': float,
                'cognitive_load': float,
                'hr': int,
                'emotion_arousal': float,
                'beta': float,
                'alpha': float,
                'theta': float,
                'emg_intensity': float
            }
        """
        self.brain_state = brain_state

        # Add to history for baseline calculation
        self.brain_state_history.append({
            'stress': brain_state.get('stress', 0.0),
            'cognitive_load': brain_state.get('cognitive_load', 0.0),
            'hr': brain_state.get('hr', 70),
            'emotion_arousal': brain_state.get('emotion_arousal', 0.0),
            'alpha': brain_state.get('alpha', 0.0),
            'beta': brain_state.get('beta', 0.0),
            'gamma': brain_state.get('gamma', 0.0),
            'theta': brain_state.get('theta', 0.0),
            'delta': brain_state.get('delta', 0.0),
            'emg_intensity': brain_state.get('emg_intensity', 0.0),
            'timestamp': time.time()
        })

        # Send brain state update to frontend via WebSocket
        if self.websocket_callback and self.is_active:
            import asyncio
            try:
                # Create task to send update (async callback)
                asyncio.create_task(self.websocket_callback({
                    'type': 'state_update',
                    'brain_state': {
                        'stress': brain_state.get('stress', 0.0),
                        'hr': brain_state.get('hr', 70),
                        'emotion': 'unknown',  # Emotion comes from text analysis
                        'emotion_arousal': brain_state.get('emotion_arousal', 0.0),
                        'cognitive_load': brain_state.get('cognitive_load', 0.0),
                        'alpha': brain_state.get('alpha', 0.0),
                        'beta': brain_state.get('beta', 0.0),
                        'gamma': brain_state.get('gamma', 0.0),
                        'theta': brain_state.get('theta', 0.0),
                        'delta': brain_state.get('delta', 0.0),
                        'emg_intensity': brain_state.get('emg_intensity', 0.0)
                    },
                    'timestamp': time.time()
                }))
            except Exception as e:
                logger.warning(f"Failed to send brain state to frontend: {e}")

    def get_brain_state_baseline(self) -> dict:
        """
        Calculate median/average baseline from brain state history

        Returns:
            dict with median values for each metric
        """
        if len(self.brain_state_history) < 5:
            # Not enough data yet, return current state or defaults
            return self.brain_state if self.brain_state else self._get_default_brain_state()

        # Calculate median for each metric
        baseline = {}
        metrics = ['stress', 'cognitive_load', 'hr', 'emotion_arousal',
                  'alpha', 'beta', 'gamma', 'theta', 'delta', 'emg_intensity']

        for metric in metrics:
            values = [state[metric] for state in self.brain_state_history]
            baseline[metric] = statistics.median(values)

        return baseline

    def _get_default_brain_state(self) -> dict:
        """Return default brain state when no EEG data available"""
        return {
            'stress': 0.3,
            'cognitive_load': 0.3,
            'hr': 70,
            'emotion_arousal': 0.2,
            'beta': 25.0,
            'alpha': 40.0,
            'theta': 15.0,
            'emg_intensity': 0.2
        }

    def stop_session(self):
        """Stop active session"""
        self.is_active = False
        logger.info("Stopping session...")

    def export_session(self, output_dir: Path):
        """
        Export session data for later analysis

        Saves:
        - Conversation transcript
        - Brain state history
        - Fused states
        - GPT responses
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Export conversation
        conversation_path = output_dir / "conversation.json"
        self.gpt5_copilot.export_conversation(conversation_path)

        # Export fusion context
        context_path = output_dir / "fusion_context.json"
        with open(context_path, 'w') as f:
            json.dump(list(self.fusion_engine.context_window), f, indent=2)

        logger.info(f"Session exported to {output_dir}")


# Global instance
copilot_session = CopilotSession()


# Test/debug
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n=== Copilot Session Test ===\n")

    # Mock websocket callback
    async def mock_websocket(message: dict):
        msg_type = message['type']
        if msg_type == 'transcript':
            print(f"\n[USER]: {message['text']}")
        elif msg_type == 'ai_message_chunk':
            print(message['text'], end='', flush=True)
        elif msg_type == 'ai_message_complete':
            print(f"\n")
        elif msg_type == 'state_update':
            brain = message['brain_state']
            print(f"  [Brain: Stress {brain['stress']:.2f}, HR {brain['hr']} bpm]")

    # Mock brain state updates
    async def update_brain_periodically():
        """Simulate brain state updates"""
        while copilot_session.is_active:
            # Simulate varying brain state
            copilot_session.update_brain_state({
                'stress': 0.5 + (time.time() % 10) / 20,  # Varies 0.5-1.0
                'cognitive_load': 0.4,
                'hr': 75,
                'emotion_arousal': 0.3,
                'beta': 30.0,
                'alpha': 35.0,
                'theta': 15.0,
                'emg_intensity': 0.3
            })
            await asyncio.sleep(1.0)

    # Run test
    async def test():
        print("Starting test session...")
        print("Speak into your microphone when the AI asks you a question.\n")

        # Start brain state updates
        brain_task = asyncio.create_task(update_brain_periodically())

        # Start session (will run until interrupted)
        try:
            await copilot_session.start_session(mock_websocket)
        except KeyboardInterrupt:
            print("\n\nTest interrupted")
        finally:
            copilot_session.stop_session()
            brain_task.cancel()

    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\n\nExiting...")

    print("\n=== Test Complete ===")
