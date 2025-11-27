"""
ML Text Analysis Module
Uses conversation_analyzer ExpertRunner for psychological pattern detection
Provides sentiment, emotion, topic extraction, and stress analysis
"""

import sys
from pathlib import Path
import logging
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)

# Add parent directory to path (contains conversation_analyzer)
CONV_ANALYZER_PATH = Path(__file__).parent.parent
sys.path.insert(0, str(CONV_ANALYZER_PATH))

try:
    from conversation_analyzer.backend.expert_runner import get_expert_runner
    from conversation_analyzer.core.preprocess import TranscriptTurn
    MODELS_AVAILABLE = True
    logger.info("✅ Conversation analyzer models imported successfully")
except ImportError as e:
    logger.warning(f"⚠️  Could not import conversation analyzer: {e}")
    logger.warning("ML analysis will use fallback methods")
    MODELS_AVAILABLE = False


class MLAnalyzer:
    """
    Psychological pattern analysis using conversation_analyzer ExpertRunner
    Analyzes text for emotions, stress, psychological labels, and NER triggers
    """

    def __init__(self):
        """Initialize ML models via ExpertRunner"""
        self.models_loaded = False

        if MODELS_AVAILABLE:
            try:
                logger.info("Loading ML models via ExpertRunner...")
                self.expert_runner = get_expert_runner()
                self.models_loaded = True
                logger.info("✅ All ML models loaded successfully via ExpertRunner")

            except Exception as e:
                logger.error(f"Failed to load models: {e}")
                logger.warning("Using fallback analysis methods")
                self.models_loaded = False
        else:
            logger.warning("Models not available, using fallback methods")

    def analyze(self, text: str) -> Dict:
        """
        Analyze text for psychological patterns

        Args:
            text: Input text to analyze

        Returns:
            {
                'sentiment': {'label': str, 'score': float},
                'emotion': {'label': str, 'score': float},
                'topics': List[str],
                'is_question': bool,
                'word_count': int,
                'analysis_time': float,
                'stress_indicators': Dict[str, float],
                'psychological_labels': Dict[str, float]
            }
        """
        start_time = time.time()

        if not text or len(text.strip()) == 0:
            return self._empty_analysis()

        if self.models_loaded:
            result = self._analyze_with_expert_runner(text)
        else:
            result = self._analyze_fallback(text)

        result['analysis_time'] = time.time() - start_time
        result['word_count'] = len(text.split())

        return result

    def _analyze_with_expert_runner(self, text: str) -> Dict:
        """Analyze using ExpertRunner from conversation_analyzer"""
        try:
            # Create transcript turn
            turn = TranscriptTurn(
                speaker="user",
                text=text,
                timestamp=None
            )

            # Run analysis
            analyses = self.expert_runner.run([turn])
            analysis = analyses[0]

            # Extract sentiment from stress scores
            sentiment = self._extract_sentiment(analysis.stress)

            # Extract top emotion
            emotion = self._extract_emotion(analysis.emotions)

            # Extract topics from zero-shot psychological labels
            topics = self._extract_topics(analysis.zero_shot, text)

            # Question detection (simple heuristic)
            is_question = self._is_question(text)

            return {
                'sentiment': sentiment,
                'emotion': emotion,
                'topics': topics,
                'is_question': is_question,
                'stress_indicators': analysis.stress,
                'psychological_labels': analysis.zero_shot,
                'ner_triggers': analysis.ner,
                'raw_analysis': {
                    'emotions': analysis.emotions,
                    'stress': analysis.stress,
                    'zero_shot': analysis.zero_shot,
                    'ner': analysis.ner
                }
            }

        except Exception as e:
            logger.error(f"ExpertRunner analysis error: {e}")
            return self._analyze_fallback(text)

    def _extract_sentiment(self, stress_scores: Dict[str, float]) -> Dict:
        """
        Extract sentiment from stress/emotion scores

        conversation_analyzer doesn't have dedicated sentiment model,
        so we infer from stress and emotion patterns
        """
        # Check if we have positive/negative indicators in stress scores
        positive_indicators = ['joy', 'contentment', 'satisfaction']
        negative_indicators = ['stress', 'anxiety', 'anger', 'sadness', 'fear']

        positive_score = 0.0
        negative_score = 0.0

        for key, score in stress_scores.items():
            key_lower = key.lower()
            if any(pos in key_lower for pos in positive_indicators):
                positive_score += score
            if any(neg in key_lower for neg in negative_indicators):
                negative_score += score

        # Determine sentiment
        if positive_score > negative_score + 0.2:
            return {'label': 'positive', 'score': positive_score}
        elif negative_score > positive_score + 0.2:
            return {'label': 'negative', 'score': negative_score}
        else:
            return {'label': 'neutral', 'score': 0.5}

    def _extract_emotion(self, emotions: Dict[str, float]) -> Dict:
        """Extract top emotion from emotion scores"""
        if not emotions:
            return {'label': 'neutral', 'score': 0.0}

        # Get top emotion
        top_emotion = max(emotions.items(), key=lambda x: x[1])

        # Map to standard emotion labels
        emotion_map = {
            'joy': 'joy',
            'sadness': 'sadness',
            'anger': 'anger',
            'fear': 'fear',
            'surprise': 'surprise',
            'disgust': 'disgust',
            'neutral': 'neutral',
            # Additional mappings from models
            'anxiety': 'anxiety',
            'love': 'joy',
            'optimism': 'joy',
            'pessimism': 'sadness'
        }

        label = emotion_map.get(top_emotion[0], top_emotion[0])
        return {'label': label, 'score': top_emotion[1]}

    def _extract_topics(self, zero_shot: Dict[str, float], text: str) -> List[str]:
        """
        Extract topics from zero-shot psychological labels and text

        Zero-shot labels from conversation_analyzer:
        - avoidance, self-criticism, reflection, decisiveness, support-seeking, stress
        """
        topics = []

        # From zero-shot psychological labels (threshold: 0.5)
        psych_topics = [label for label, score in zero_shot.items() if score > 0.5]
        topics.extend(psych_topics)

        # Add keyword-based topics
        keyword_topics = self._extract_keyword_topics(text)
        topics.extend(keyword_topics)

        # Remove duplicates and return
        return list(set(topics)) if topics else ['general']

    def _extract_keyword_topics(self, text: str) -> List[str]:
        """Simple keyword-based topic extraction (fallback/supplement)"""
        topic_keywords = {
            'work': ['work', 'job', 'project', 'deadline', 'meeting', 'boss', 'colleague'],
            'family': ['family', 'mom', 'dad', 'parent', 'sibling', 'child', 'kids'],
            'health': ['health', 'doctor', 'sick', 'pain', 'hospital', 'medication'],
            'relationships': ['relationship', 'partner', 'friend', 'dating', 'marriage'],
            'future': ['future', 'plan', 'goal', 'dream', 'hope', 'worry'],
            'past': ['past', 'memory', 'remember', 'regret', 'used to']
        }

        text_lower = text.lower()
        detected_topics = []

        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_topics.append(topic)

        return detected_topics

    def _is_question(self, text: str) -> bool:
        """Detect if text is a question"""
        text_lower = text.lower().strip()

        # Check for question mark
        if '?' in text:
            return True

        # Check for question words at start
        question_starters = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does']
        if any(text_lower.startswith(q) for q in question_starters):
            return True

        return False

    def _analyze_fallback(self, text: str) -> Dict:
        """Fallback analysis using rule-based methods"""
        text_lower = text.lower()

        # Simple sentiment (keyword-based)
        positive_words = ['good', 'great', 'happy', 'excellent', 'love', 'wonderful', 'amazing', 'fine', 'nice', 'better']
        negative_words = ['bad', 'terrible', 'sad', 'awful', 'hate', 'horrible', 'worried', 'anxious', 'stressed', 'upset', 'angry']

        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        if pos_count > neg_count:
            sentiment = {'label': 'positive', 'score': min(0.6 + (pos_count * 0.1), 0.95)}
        elif neg_count > pos_count:
            sentiment = {'label': 'negative', 'score': min(0.6 + (neg_count * 0.1), 0.95)}
        else:
            sentiment = {'label': 'neutral', 'score': 0.5}

        # Simple emotion (keyword matching)
        emotion_keywords = {
            'joy': ['happy', 'excited', 'great', 'wonderful', 'amazing'],
            'sadness': ['sad', 'depressed', 'down', 'unhappy', 'crying'],
            'anger': ['angry', 'frustrated', 'annoyed', 'mad', 'furious'],
            'fear': ['worried', 'scared', 'afraid', 'terrified'],
            'anxiety': ['anxious', 'nervous', 'worried', 'stressed', 'overwhelmed']
        }

        detected_emotion = 'neutral'
        max_score = 0.0

        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for word in keywords if word in text_lower)
            score = min(count * 0.3, 0.95)
            if score > max_score:
                max_score = score
                detected_emotion = emotion

        emotion = {'label': detected_emotion, 'score': max(max_score, 0.3) if detected_emotion != 'neutral' else 0.3}

        # Topic extraction
        topics = self._extract_keyword_topics(text)

        # Question detection
        is_question = self._is_question(text)

        return {
            'sentiment': sentiment,
            'emotion': emotion,
            'topics': topics if topics else ['general'],
            'is_question': is_question,
            'stress_indicators': {},
            'psychological_labels': {},
            'ner_triggers': {}
        }

    def _empty_analysis(self) -> Dict:
        """Return empty analysis for blank text"""
        return {
            'sentiment': {'label': 'neutral', 'score': 0.0},
            'emotion': {'label': 'neutral', 'score': 0.0},
            'topics': [],
            'is_question': False,
            'word_count': 0,
            'analysis_time': 0.0,
            'stress_indicators': {},
            'psychological_labels': {},
            'ner_triggers': {}
        }

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """
        Analyze multiple texts in batch

        Args:
            texts: List of text strings

        Returns:
            List of analysis results
        """
        if self.models_loaded:
            try:
                # Create turns
                turns = [
                    TranscriptTurn(
                        speaker="user",
                        text=text,
                        timestamp=None
                    )
                    for text in texts
                ]

                # Run batch analysis
                analyses = self.expert_runner.run(turns)

                # Convert to our format
                results = []
                for text, analysis in zip(texts, analyses):
                    results.append({
                        'sentiment': self._extract_sentiment(analysis.stress),
                        'emotion': self._extract_emotion(analysis.emotions),
                        'topics': self._extract_topics(analysis.zero_shot, text),
                        'is_question': self._is_question(text),
                        'word_count': len(text.split()),
                        'stress_indicators': analysis.stress,
                        'psychological_labels': analysis.zero_shot
                    })

                return results

            except Exception as e:
                logger.error(f"Batch analysis error: {e}")
                return [self.analyze(text) for text in texts]
        else:
            return [self.analyze(text) for text in texts]

    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        return {
            'models_loaded': self.models_loaded,
            'models_available': MODELS_AVAILABLE,
            'backend': 'ExpertRunner' if self.models_loaded else 'fallback',
            'emotion_models': 'emotion_distilroberta, emotion_distilbert, twitter_roberta_emotion' if self.models_loaded else 'keyword-based',
            'stress_models': 'beto_emotion, hatexplain' if self.models_loaded else 'keyword-based',
            'psychological_labels': 'zero_shot_psych (avoidance, self-criticism, stress, etc.)' if self.models_loaded else 'none',
            'ner_triggers': 'bert-base-NER' if self.models_loaded else 'none'
        }


# Test/debug functionality
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n=== ML Analyzer Test (with ExpertRunner) ===\n")

    analyzer = MLAnalyzer()

    print("Model info:", analyzer.get_model_info())

    # Test cases
    test_texts = [
        "I'm feeling great today! The weather is wonderful.",
        "I'm really worried about this deadline at work.",
        "I don't know what to do anymore. Everything feels overwhelming.",
        "How can I manage my stress better?",
        "My family is doing well, we had a nice dinner together."
    ]

    print("\n--- Analysis Results ---\n")

    for i, text in enumerate(test_texts, 1):
        print(f"Text {i}: \"{text}\"")
        result = analyzer.analyze(text)

        print(f"  Sentiment: {result['sentiment']['label']} ({result['sentiment']['score']:.2f})")
        print(f"  Emotion: {result['emotion']['label']} ({result['emotion']['score']:.2f})")
        print(f"  Topics: {', '.join(result['topics'])}")
        print(f"  Is Question: {result['is_question']}")

        if result.get('psychological_labels'):
            print(f"  Psychological Labels: {result['psychological_labels']}")

        print(f"  Analysis Time: {result['analysis_time']:.4f}s")
        print()

    print("\n=== Test Complete ===")
