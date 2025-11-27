#!/usr/bin/env python3
"""Test the EXACT flow that copilot uses"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, '/Users/mironpuzanov/Consciousness OS/backend')

load_dotenv('.env')

from gpt5_copilot import GPT5Copilot
from ml_analyzer import MLAnalyzer
from fusion_engine import FusionEngine

async def test_full_copilot_flow():
    print("=== Testing Full Copilot Flow ===\n")

    # Initialize components
    print("1. Initializing GPT5Copilot...")
    gpt5 = GPT5Copilot()

    print("2. Initializing ML Analyzer...")
    ml_analyzer = MLAnalyzer()

    print("3. Initializing Fusion Engine...")
    fusion = FusionEngine()

    # Simulate user message
    user_text = "I'm feeling very angry"
    print(f"\n4. User message: '{user_text}'")

    # ML Analysis
    print("\n5. Running ML analysis...")
    text_features = ml_analyzer.analyze(user_text)
    print(f"   Text features: {text_features}")

    # Brain state (fake)
    brain_state = {
        'stress': 0.7,
        'hr': 85,
        'cognitive_load': 0.6,
        'emotion_arousal': 0.8
    }
    print(f"\n6. Brain state: {brain_state}")

    # Fusion
    print("\n7. Running fusion...")
    fused_state = fusion.fuse(brain_state, text_features, user_text)
    print(f"   Fused state: {fused_state}")

    # GPT-5 generation
    print("\n8. Generating GPT-5 response...")
    try:
        full_response = ""
        async for chunk in gpt5.generate_response([fused_state], stream=True):
            print(chunk, end='', flush=True)
            full_response += chunk

        print(f"\n\n9. Total response length: {len(full_response)} chars")
        if len(full_response) > 0:
            print("✅ SUCCESS: Got response from GPT-5!")
        else:
            print("❌ FAIL: Empty response from GPT-5")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_copilot_flow())
