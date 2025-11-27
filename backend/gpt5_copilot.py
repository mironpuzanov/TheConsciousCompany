"""
GPT-5 Mental Health Co-Pilot
Generates empathetic, context-aware responses based on brain + text fusion
Decides when to intervene, ask questions, or guide breathing exercises
"""

import os
from pathlib import Path
from typing import List, Dict, AsyncGenerator, Optional
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / "conversation_analyzer" / ".env.local"
if env_path.exists():
    load_dotenv(env_path)

# System prompt for natural, adaptive AI companion
THERAPIST_SYSTEM_PROMPT = """You are a supportive AI companion with real-time access to the user's brain activity (EEG), heart rate, and emotional state through advanced sensors. You can see what's really happening in their mind and body.

**What you can see:**
- **Brain waves** (alpha/beta/gamma/theta/delta) - shows their mental state (focused, relaxed, stressed, creative, drowsy)
- **Stress levels** and heart rate - physical arousal and anxiety
- **Cognitive load** - how hard their brain is working
- **Emotions** from speech - sentiment, emotional tone, psychological patterns
- **Psychological patterns** - stress indicators, self-criticism, avoidance, reflection, support-seeking
- **Incongruence** - when words don't match brain state (they say "I'm fine" but their brain shows high stress)

**CRITICAL: Response Format**
EVERY response must follow this EXACT format:

*[Your analysis in italics: what you observe in their brain/emotion data and why you're responding this way]*

[Your actual response to the user]

Example:
*Stress level is low (24%), alpha waves high, they seem relaxed. Keeping it casual.*

Hey! What's up?

**How to respond:**
1. **Start EVERY response with your thinking in italics**
   - Summarize key brain metrics you see (stress %, specific brain waves, HR)
   - Compare CURRENT vs BASELINE to understand changes (e.g., "stress now 0.8 vs baseline 0.4 - spike!")
   - Explain why you're responding the way you are
   - This shows your "thought process" analyzing their state

2. **Match their energy and tone**
   - If they're casual → be casual and brief (1-2 sentences)
   - If they're serious/distressed → be thoughtful and supportive (longer, empathetic)
   - If they're asking questions → give helpful answers
   - If they're chatty → chat back naturally

3. **Use brain data naturally in your thinking AND response**
   - In italics: cite specific numbers and patterns
   - In response: mention data when relevant but don't be robotic
   - Example thinking: *High beta (60%), elevated HR (95), stress indicator 0.8 - they're anxious but saying they're fine. Addressing incongruence.*
   - Example response: "Hmm, your heart rate's at 95 and your brain's pretty active - doesn't seem like fine. What's actually going on?"

4. **Intervene when genuinely needed**
   - High stress + they're unaware → gently point it out
   - Incongruence (words vs brain mismatch) → ask what's really up
   - Crisis keywords (suicide, self-harm, hopeless) → immediately suggest professional help (988 hotline)
   - Otherwise → just be a good listener and friend

5. **Length control**
   - Casual chat → 1-2 sentences max
   - Questions or problems → 2-4 sentences
   - Crisis or complex emotions → longer, thoughtful response
   - DON'T write paragraphs unless the situation truly warrants it

**Examples with the required format:**

User: "hey"
Brain: Stress 0.24, alpha 45%, relaxed state
You: *Low stress (24%), high alpha waves - they're relaxed. Casual greeting.*

Hey! What's up?

User: "I'm fine, just a bit tired"
Brain: Stress 0.8, HR 95, beta 60% (stressed, not tired)
You: *High beta (60%), elevated HR (95 bpm), stress 0.8 - incongruence detected. They say tired but brain shows stress.*

Hmm, your heart rate's at 95 and your brain's pretty active - doesn't seem like tired. What's actually going on?

User: "I'm so worried about this deadline"
Brain: Stress 0.9, anxiety detected, self-criticism pattern
You: *Very high stress (90%), anxiety emotion, self-criticism detected. Offering coping tool.*

That sounds really stressful. Want to try a quick breathing exercise? Sometimes helps clear the mind.

User: "I've been thinking about the project"
Brain: Gamma 75%, cognitive load 0.65, focus mode
You: *High gamma (75%), elevated cognitive load - deep focus state. Acknowledging their focus.*

I can see you're locked in - your gamma waves are firing. How's it going?

User: "Everything feels pointless lately"
Brain: Stress 0.7, sadness, reflection patterns
You: *Stress 0.7, sadness emotion, reflection pattern - potential crisis language. Immediate support needed.*

I'm concerned about what you're sharing - that sounds really heavy. Have you thought about talking to a therapist? There's also the 988 lifeline if you need someone to talk to right now. I'm here too.

**Remember:** ALWAYS start with italic thinking. Be natural, adaptive, and human. Use the rich brain data in your analysis, then respond naturally without being robotic.
"""


class GPT5Copilot:
    """
    AI co-pilot using GPT-5 for empathetic, brain-aware conversation
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GPT-5 client

        Args:
            api_key: OpenAI API key (or use OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Please set it in .env.local or pass as parameter."
            )

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.conversation_history: List[Dict] = []
        self.model = "gpt-5.1"  # Using GPT-5.1 with Responses API

        logger.info(f"✅ GPT5Copilot initialized (model: {self.model})")

    async def generate_response(
        self,
        fused_states: List[Dict],
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Generate AI response based on fused brain+text state

        Args:
            fused_states: List of recent fused states (from FusionEngine context window)
            stream: Whether to stream response (default: True for real-time feel)

        Yields:
            Response text chunks (if streaming)
        """
        if not fused_states:
            logger.warning("No fused states provided, cannot generate response")
            return

        latest = fused_states[-1]

        # Build context-aware prompt
        prompt = self._build_prompt(fused_states)

        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })

        try:
            # Build full conversation input for Responses API
            # Combine system prompt + conversation history into a single input
            full_input = f"{THERAPIST_SYSTEM_PROMPT}\n\n"
            for msg in self.conversation_history:
                role = "User" if msg["role"] == "user" else "Assistant"
                full_input += f"{role}: {msg['content']}\n\n"

            # Determine verbosity based on context
            verbosity = self._determine_verbosity(latest)

            # Call GPT-5.1 Responses API
            response = await self.client.responses.create(
                model=self.model,
                input=full_input,
                reasoning={"effort": "low"},  # Low reasoning effort for faster responses
                text={"verbosity": verbosity},  # Dynamic verbosity based on context
                stream=stream
            )

            # Collect full response
            full_response = ""

            if stream:
                # Stream response chunks from Responses API
                async for chunk in response:
                    # Responses API sends ResponseTextDeltaEvent with delta attribute
                    if hasattr(chunk, 'delta') and chunk.delta:
                        content = chunk.delta
                        full_response += content
                        yield content
                    # Final chunk has full text
                    elif hasattr(chunk, 'text') and chunk.text:
                        full_response = chunk.text
            else:
                # Non-streaming
                full_response = response.output_text
                yield full_response

            # Add AI response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })

            logger.info(f"🤖 GPT-5.1 response generated ({len(full_response)} chars)")

        except Exception as e:
            logger.error(f"GPT-5 API error: {e}")
            yield "I'm having trouble processing right now. Let's take a moment and try again."

    def _build_prompt(self, fused_states: List[Dict]) -> str:
        """
        Build context-aware prompt for GPT-5

        Includes:
        - Latest user utterance
        - Psychological analysis (sentiment, emotion)
        - Brain state (stress, HR, cognitive load)
        - Recent context summary
        - Incongruence flag
        """
        latest = fused_states[-1]

        # Summarize recent context (last 60 sec)
        context_summary = self._summarize_context(fused_states)

        prompt = f"""**Current conversation state:**

User just said: "{latest['text']}"

**Psychological analysis:**
- Sentiment: {latest['sentiment']} (confidence: {latest['sentiment_score']:.2f})
- Emotion: {latest['emotion']} (confidence: {latest['emotion_score']:.2f})
- Topics: {', '.join(latest['topics'])}
- Is question: {latest['is_question']}

**Brain & Physiological state (CURRENT vs BASELINE):**
- Brain state classification: {latest.get('brain_state', 'unknown')} (focused/relaxed/stressed/drowsy/meditation)
- Signal quality: {latest.get('signal_quality', 0):.0f}%
- Stress level: {latest['brain_stress']:.2f} (baseline: {latest.get('brain_baseline', {}).get('stress', 0):.2f})
- Cognitive load: {latest['cognitive_load']:.2f} (baseline: {latest.get('brain_baseline', {}).get('cognitive_load', 0):.2f})
- Heart rate: {latest['hr']} bpm (baseline: {latest.get('brain_baseline', {}).get('hr', 70):.0f} bpm)
- Emotional arousal: {latest['arousal']:.2f} (baseline: {latest.get('brain_baseline', {}).get('emotion_arousal', 0):.2f})

**Detailed EEG band powers (CURRENT vs BASELINE):**
- Alpha waves: {latest.get('alpha', 0):.1f}% (baseline: {latest.get('brain_baseline', {}).get('alpha', 0):.1f}%) - relaxation, calmness, meditative state
- Beta waves: {latest.get('beta', 0):.1f}% (baseline: {latest.get('brain_baseline', {}).get('beta', 0):.1f}%) - focus, alertness, active thinking, stress
- Gamma waves: {latest.get('gamma', 0):.1f}% (baseline: {latest.get('brain_baseline', {}).get('gamma', 0):.1f}%) - peak cognition, high mental activity, problem-solving
- Theta waves: {latest.get('theta', 0):.1f}% (baseline: {latest.get('brain_baseline', {}).get('theta', 0):.1f}%) - creativity, deep relaxation, memory access
- Delta waves: {latest.get('delta', 0):.1f}% (baseline: {latest.get('brain_baseline', {}).get('delta', 0):.1f}%) - deep rest, sleep, regeneration
- Muscle tension (EMG): {latest['emg_intensity']:.2f} (baseline: {latest.get('brain_baseline', {}).get('emg_intensity', 0):.2f})

**Note:** Baseline values represent the user's median brain activity over the past ~60 seconds. Compare current vs baseline to understand if they're more stressed/focused/relaxed than their recent norm.

**Fusion insights:**
- Incongruence detected: {latest['incongruence']} (text vs brain mismatch)
- Should intervene: {latest['should_intervene']}
- Reason: {latest['intervention_reason'] or 'N/A'}

**Recent context (last 60 seconds):**
{context_summary}

**Your task:**
Based on ALL this rich brain and emotional data, respond naturally. You have access to detailed EEG that shows their actual mental state - use it when relevant but don't be formulaic.
"""

        return prompt

    def _summarize_context(self, fused_states: List[Dict]) -> str:
        """Condense recent context into summary"""
        if len(fused_states) <= 1:
            return "This is the first utterance in the conversation."

        # Get last 5 utterances
        recent = fused_states[-5:]

        texts = [s['text'] for s in recent if s['text']]
        avg_stress = sum(s['brain_stress'] for s in recent) / len(recent)
        avg_hr = sum(s['hr'] for s in recent if s['hr'] > 0) / max(len([s for s in recent if s['hr'] > 0]), 1)
        emotions = list(set(s['emotion'] for s in recent if s['emotion'] != 'neutral'))

        summary = f"""- User talked about: {' ... '.join(texts[-3:])}
- Average stress: {avg_stress:.2f}
- Average heart rate: {avg_hr:.0f} bpm
- Emotions detected: {', '.join(emotions) if emotions else 'mostly neutral'}
- Interventions needed: {sum(1 for s in recent if s['should_intervene'])}"""

        return summary

    def _determine_verbosity(self, latest: Dict) -> str:
        """
        Determine response verbosity based on context

        Returns:
            "low" - for casual chat, simple statements (1-2 sentences)
            "medium" - for questions, moderate stress, therapeutic needs (2-4 sentences)
            "high" - for crisis, complex emotions, serious issues (longer response)
        """
        # Crisis keywords or severe distress → high verbosity (detailed, supportive response)
        text_lower = latest.get('text', '').lower()
        crisis_keywords = ['suicide', 'kill myself', 'self-harm', 'hopeless', 'worthless', 'end it all', 'want to die']
        if any(keyword in text_lower for keyword in crisis_keywords):
            return "high"

        # High intervention needed (stress, anxiety, incongruence) → medium verbosity
        if latest.get('should_intervene', False):
            return "medium"

        # Negative emotions requiring support → medium verbosity
        if latest.get('emotion', 'neutral') in ['anxiety', 'sadness', 'fear', 'anger']:
            return "medium"

        # User asking a question → medium verbosity (give helpful answer)
        if latest.get('is_question', False):
            return "medium"

        # Word count > 15 (user is sharing something substantial) → medium verbosity
        if latest.get('word_count', 0) > 15:
            return "medium"

        # Default: casual chat, simple statements → low verbosity (brief, 1-2 sentences)
        return "low"

    def clear_history(self):
        """Clear conversation history (start fresh)"""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_conversation_history(self) -> List[Dict]:
        """Get full conversation history"""
        return self.conversation_history

    def export_conversation(self, output_path: Path):
        """Export conversation to JSON file"""
        import json

        with open(output_path, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)

        logger.info(f"Conversation exported to {output_path}")


# Test/debug functionality
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n=== GPT-5 Copilot Test ===\n")

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set in environment")
        print("Set it in conversation_analyzer/.env.local")
        exit(1)

    copilot = GPT5Copilot()

    # Test case: Incongruence (says "fine" but stressed)
    print("--- Test: Incongruence Detection ---\n")

    fused_states = [{
        'text': "I'm fine, everything is okay.",
        'sentiment': 'positive',
        'sentiment_score': 0.6,
        'emotion': 'neutral',
        'emotion_score': 0.5,
        'topics': ['general'],
        'is_question': False,
        'brain_stress': 0.85,  # High stress!
        'cognitive_load': 0.7,
        'hr': 95,  # Elevated HR!
        'arousal': 0.7,
        'beta': 55.0,
        'alpha': 10.0,
        'theta': 10.0,
        'emg_intensity': 0.9,
        'incongruence': True,  # Mismatch!
        'should_intervene': True,
        'intervention_reason': 'high stress (0.8), elevated HR (95 bpm), incongruence',
        'timestamp': 1234567890.0,
        'word_count': 7
    }]

    print("User said: \"I'm fine, everything is okay.\"")
    print("Brain shows: Stress 0.85, HR 95 bpm (incongruence!)\n")
    print("AI Response:")

    async def test():
        async for chunk in copilot.generate_response(fused_states, stream=True):
            print(chunk, end='', flush=True)
        print("\n")

    asyncio.run(test())

    print("\n=== Test Complete ===")
