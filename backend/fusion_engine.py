"""
Brain-Text Fusion Engine
Combines EEG brain data with text analysis features
Detects incongruence, stress triggers, and intervention opportunities
"""

import time
from collections import deque
from typing import Dict, List, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class FusionEngine:
    """
    Fuses brain activity (EEG) with text analysis (sentiment/emotion)
    Maintains context window and detects intervention triggers
    """

    def __init__(self, window_size: int = 60):
        """
        Initialize fusion engine

        Args:
            window_size: Context window size in seconds (default: 60)
        """
        self.window_size = window_size
        self.context_window: deque = deque(maxlen=window_size)

        # Intervention thresholds
        self.stress_threshold = 0.7
        self.hr_spike_threshold = 90  # bpm
        self.incongruence_sensitivity = 0.5

        logger.info(f"FusionEngine initialized (window: {window_size}s)")

    def fuse(
        self,
        brain_state: Dict,
        text_features: Dict,
        raw_text: str
    ) -> Dict:
        """
        Fuse brain data with text analysis

        Args:
            brain_state: {
                'stress': float (0-1),
                'cognitive_load': float (0-1),
                'hr': int (bpm),
                'emotion_arousal': float (0-1),
                'beta': float (band power %),
                'alpha': float,
                'theta': float,
                'emg_intensity': float (0-1)
            }
            text_features: {
                'sentiment': {'label': str, 'score': float},
                'emotion': {'label': str, 'score': float},
                'topics': List[str],
                'is_question': bool
            }
            raw_text: Original transcribed text

        Returns:
            Unified fused state dictionary
        """
        # Input validation
        if not brain_state:
            logger.warning("Empty brain_state provided, using defaults")
            brain_state = self._get_default_brain_state()

        if not text_features:
            logger.warning("Empty text_features provided, using defaults")
            text_features = self._get_default_text_features()

        if not raw_text:
            logger.warning("Empty raw_text provided")
            raw_text = ""

        timestamp = time.time()

        # Extract values safely
        sentiment_label = text_features.get('sentiment', {}).get('label', 'neutral')
        sentiment_score = text_features.get('sentiment', {}).get('score', 0.5)
        emotion_label = text_features.get('emotion', {}).get('label', 'neutral')
        emotion_score = text_features.get('emotion', {}).get('score', 0.5)

        brain_stress = brain_state.get('stress', 0.0)
        cognitive_load = brain_state.get('cognitive_load', 0.0)
        hr = brain_state.get('hr', 70)

        # Detect incongruence
        incongruence = self._detect_incongruence(
            sentiment_label,
            sentiment_score,
            brain_stress,
            emotion_label
        )

        # Determine if intervention needed
        should_intervene = self._should_intervene(
            brain_stress,
            hr,
            emotion_label,
            incongruence
        )

        # Create fused state
        fused_state = {
            # Text data
            'text': raw_text,
            'sentiment': sentiment_label,
            'sentiment_score': sentiment_score,
            'emotion': emotion_label,
            'emotion_score': emotion_score,
            'topics': text_features.get('topics', []),
            'is_question': text_features.get('is_question', False),

            # Brain data
            'brain_stress': brain_stress,
            'cognitive_load': cognitive_load,
            'hr': hr,
            'arousal': brain_state.get('emotion_arousal', 0.0),
            'beta': brain_state.get('beta', 0.0),
            'alpha': brain_state.get('alpha', 0.0),
            'theta': brain_state.get('theta', 0.0),
            'gamma': brain_state.get('gamma', 0.0),
            'delta': brain_state.get('delta', 0.0),
            'brain_state': brain_state.get('brain_state', 'unknown'),
            'signal_quality': brain_state.get('signal_quality', 0.0),
            'emg_intensity': brain_state.get('emg_intensity', 0.0),

            # Fusion insights
            'incongruence': incongruence,
            'should_intervene': should_intervene,
            'intervention_reason': self._get_intervention_reason(
                brain_stress, hr, emotion_label, incongruence
            ),

            # Metadata
            'timestamp': timestamp,
            'word_count': len(raw_text.split()) if raw_text else 0
        }

        # Add to context window
        self.context_window.append(fused_state)

        return fused_state

    def _detect_incongruence(
        self,
        sentiment: str,
        sentiment_score: float,
        brain_stress: float,
        emotion: str
    ) -> bool:
        """
        Detect mismatch between what user says and brain shows

        Examples:
        - Says "I'm fine" (positive) but brain shows high stress
        - Says "I'm happy" but detected emotion is sadness
        """
        # Text says positive/neutral but brain shows stress
        text_positive = sentiment in ['positive', 'neutral'] and sentiment_score > 0.5
        brain_stressed = brain_stress > self.incongruence_sensitivity

        if text_positive and brain_stressed:
            logger.info(f"⚠️  Incongruence detected: Text '{sentiment}' but stress {brain_stress:.2f}")
            return True

        # Text emotion doesn't match detected negative emotions
        negative_emotions = ['sadness', 'fear', 'anxiety', 'anger']
        text_negative = emotion in negative_emotions

        if not text_negative and brain_stressed:
            return True

        return False

    def _should_intervene(
        self,
        brain_stress: float,
        hr: int,
        emotion: str,
        incongruence: bool
    ) -> bool:
        """
        Determine if AI should intervene now

        Intervention triggers:
        1. High stress (>0.7)
        2. HR spike (>90 bpm)
        3. Negative emotions (fear, anxiety, anger)
        4. Incongruence detected
        """
        # High stress
        if brain_stress > self.stress_threshold:
            return True

        # HR spike
        if hr > self.hr_spike_threshold:
            return True

        # Negative emotions
        if emotion in ['fear', 'anxiety', 'anger', 'sadness']:
            return True

        # Incongruence
        if incongruence:
            return True

        return False

    def _get_intervention_reason(
        self,
        brain_stress: float,
        hr: int,
        emotion: str,
        incongruence: bool
    ) -> Optional[str]:
        """Get human-readable reason for intervention"""
        reasons = []

        if brain_stress > self.stress_threshold:
            reasons.append(f"high stress ({brain_stress:.1f})")

        if hr > self.hr_spike_threshold:
            reasons.append(f"elevated HR ({hr} bpm)")

        if emotion in ['fear', 'anxiety']:
            reasons.append(f"{emotion} detected")

        if incongruence:
            reasons.append("incongruence (text vs brain mismatch)")

        return ', '.join(reasons) if reasons else None

    def get_context_summary(self, last_n: int = 10) -> Dict:
        """
        Get summary of recent context window

        Args:
            last_n: Number of recent states to summarize

        Returns:
            Summary statistics
        """
        if not self.context_window:
            return {
                'count': 0,
                'avg_stress': 0.0,
                'avg_hr': 0,
                'emotions': [],
                'topics': [],
                'texts': []
            }

        recent = list(self.context_window)[-last_n:]

        return {
            'count': len(recent),
            'avg_stress': np.mean([s['brain_stress'] for s in recent]),
            'avg_hr': np.mean([s['hr'] for s in recent if s['hr'] > 0]),
            'emotions': [s['emotion'] for s in recent if s['emotion'] != 'neutral'],
            'topics': list(set(topic for s in recent for topic in s['topics'])),
            'texts': [s['text'] for s in recent if s['text']],
            'interventions_triggered': sum(1 for s in recent if s['should_intervene']),
            'incongruence_detected': sum(1 for s in recent if s['incongruence'])
        }

    def get_stress_trend(self, window: int = 10) -> str:
        """
        Analyze stress trend (increasing, decreasing, stable)

        Args:
            window: Number of recent samples to analyze

        Returns:
            'increasing', 'decreasing', or 'stable'
        """
        if len(self.context_window) < window:
            return 'stable'

        recent = list(self.context_window)[-window:]
        stress_values = [s['brain_stress'] for s in recent]

        # Linear regression to detect trend
        x = np.arange(len(stress_values))
        slope = np.polyfit(x, stress_values, 1)[0]

        if slope > 0.05:
            return 'increasing'
        elif slope < -0.05:
            return 'decreasing'
        else:
            return 'stable'

    def clear_context(self):
        """Clear context window"""
        self.context_window.clear()
        logger.info("Context window cleared")

    def set_thresholds(
        self,
        stress: Optional[float] = None,
        hr: Optional[int] = None,
        incongruence_sensitivity: Optional[float] = None
    ):
        """
        Adjust intervention thresholds

        Args:
            stress: Stress threshold (0-1)
            hr: HR threshold (bpm)
            incongruence_sensitivity: Sensitivity (0-1)
        """
        if stress is not None:
            self.stress_threshold = stress
            logger.info(f"Stress threshold set to {stress}")

        if hr is not None:
            self.hr_spike_threshold = hr
            logger.info(f"HR threshold set to {hr} bpm")

        if incongruence_sensitivity is not None:
            self.incongruence_sensitivity = incongruence_sensitivity
            logger.info(f"Incongruence sensitivity set to {incongruence_sensitivity}")

    def _get_default_brain_state(self) -> Dict:
        """Return default brain state when none provided"""
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

    def _get_default_text_features(self) -> Dict:
        """Return default text features when none provided"""
        return {
            'sentiment': {'label': 'neutral', 'score': 0.5},
            'emotion': {'label': 'neutral', 'score': 0.5},
            'topics': ['general'],
            'is_question': False
        }


# Test/debug functionality
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n=== Fusion Engine Test ===\n")

    engine = FusionEngine(window_size=60)

    # Test case 1: Normal conversation
    print("--- Test 1: Normal Conversation ---")
    brain_state_1 = {
        'stress': 0.3,
        'cognitive_load': 0.4,
        'hr': 70,
        'emotion_arousal': 0.2,
        'beta': 25.0,
        'alpha': 40.0,
        'theta': 15.0,
        'emg_intensity': 0.2
    }

    text_features_1 = {
        'sentiment': {'label': 'positive', 'score': 0.8},
        'emotion': {'label': 'joy', 'score': 0.7},
        'topics': ['family', 'general'],
        'is_question': False
    }

    fused_1 = engine.fuse(brain_state_1, text_features_1, "I'm feeling good today, my family is doing well.")
    print(f"Text: \"{fused_1['text']}\"")
    print(f"Sentiment: {fused_1['sentiment']} ({fused_1['sentiment_score']:.2f})")
    print(f"Emotion: {fused_1['emotion']}")
    print(f"Stress: {fused_1['brain_stress']:.2f}")
    print(f"HR: {fused_1['hr']} bpm")
    print(f"Incongruence: {fused_1['incongruence']}")
    print(f"Should Intervene: {fused_1['should_intervene']}")
    print()

    # Test case 2: Incongruence (says "fine" but stressed)
    print("--- Test 2: Incongruence Detection ---")
    brain_state_2 = {
        'stress': 0.8,
        'cognitive_load': 0.7,
        'hr': 95,
        'emotion_arousal': 0.7,
        'beta': 55.0,
        'alpha': 10.0,
        'theta': 10.0,
        'emg_intensity': 0.9
    }

    text_features_2 = {
        'sentiment': {'label': 'positive', 'score': 0.6},
        'emotion': {'label': 'neutral', 'score': 0.5},
        'topics': ['general'],
        'is_question': False
    }

    fused_2 = engine.fuse(brain_state_2, text_features_2, "I'm fine, everything is okay.")
    print(f"Text: \"{fused_2['text']}\"")
    print(f"Sentiment: {fused_2['sentiment']} ({fused_2['sentiment_score']:.2f})")
    print(f"Stress: {fused_2['brain_stress']:.2f} ⚠️")
    print(f"HR: {fused_2['hr']} bpm ⚠️")
    print(f"Incongruence: {fused_2['incongruence']} ⚠️")
    print(f"Should Intervene: {fused_2['should_intervene']} ✅")
    print(f"Reason: {fused_2['intervention_reason']}")
    print()

    # Test case 3: High anxiety
    print("--- Test 3: High Anxiety ---")
    brain_state_3 = {
        'stress': 0.9,
        'cognitive_load': 0.6,
        'hr': 92,
        'emotion_arousal': 0.8,
        'beta': 60.0,
        'alpha': 5.0,
        'theta': 8.0,
        'emg_intensity': 0.85
    }

    text_features_3 = {
        'sentiment': {'label': 'negative', 'score': 0.9},
        'emotion': {'label': 'anxiety', 'score': 0.95},
        'topics': ['work', 'stress'],
        'is_question': False
    }

    fused_3 = engine.fuse(brain_state_3, text_features_3, "I'm so worried about this deadline, I don't know if I can finish.")
    print(f"Text: \"{fused_3['text']}\"")
    print(f"Emotion: {fused_3['emotion']} ({fused_3['emotion_score']:.2f})")
    print(f"Stress: {fused_3['brain_stress']:.2f} ⚠️")
    print(f"HR: {fused_3['hr']} bpm")
    print(f"Should Intervene: {fused_3['should_intervene']} ✅")
    print(f"Reason: {fused_3['intervention_reason']}")
    print()

    # Context summary
    print("--- Context Summary ---")
    summary = engine.get_context_summary(last_n=3)
    print(f"States in window: {summary['count']}")
    print(f"Avg stress: {summary['avg_stress']:.2f}")
    print(f"Avg HR: {summary['avg_hr']:.0f} bpm")
    print(f"Emotions: {summary['emotions']}")
    print(f"Topics: {summary['topics']}")
    print(f"Interventions triggered: {summary['interventions_triggered']}")
    print(f"Incongruence detected: {summary['incongruence_detected']}")
    print()

    # Stress trend
    trend = engine.get_stress_trend(window=3)
    print(f"Stress trend: {trend}")

    print("\n=== Test Complete ===")
