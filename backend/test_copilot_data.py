#!/usr/bin/env python3
"""Test what data copilot_session sends to frontend"""
import sys
sys.path.insert(0, '/Users/mironpuzanov/Consciousness OS/backend')

from ml_analyzer import MLAnalyzer
from fusion_engine import FusionEngine

# Initialize components
ml_analyzer = MLAnalyzer()
fusion = FusionEngine()

# Test message
user_text = "I'm feeling stressed about work"

# Run ML analysis
print("\n=== ML Analysis ===")
text_features = ml_analyzer.analyze(user_text)
print(f"Sentiment: {text_features['sentiment']}")
print(f"Emotion: {text_features['emotion']}")
print(f"Topics: {text_features['topics']}")
print(f"Is question: {text_features['is_question']}")
if text_features.get('stress_indicators'):
    print(f"Stress indicators: {text_features['stress_indicators']}")
if text_features.get('psychological_labels'):
    print(f"Psychological labels: {text_features['psychological_labels']}")

# Fake brain state (realistic values)
brain_state = {
    'stress': 0.7,
    'hr': 85,
    'cognitive_load': 0.6,
    'emotion_arousal': 0.8,
    'beta': 45.0,  # High beta (stressed/alert)
    'alpha': 25.0,  # Low alpha (not relaxed)
    'theta': 15.0,
    'gamma': 80.0,  # High gamma (high mental activity)
    'delta': 10.0,
    'brain_state': 'stressed',
    'signal_quality': 0.85,
    'emg_intensity': 0.9  # High muscle tension
}

print("\n=== Brain State (Input) ===")
for key, value in brain_state.items():
    print(f"{key}: {value}")

# Run fusion
print("\n=== Fusion ===")
fused_state = fusion.fuse(brain_state, text_features, user_text)

# Extract what would be sent to frontend
print("\n=== Data Sent to Frontend (state_update message) ===")
frontend_data = {
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
        'emg': fused_state.get('emg_intensity', 0.0)
    },
    'text_features': {
        'sentiment': fused_state['sentiment'],
        'sentiment_score': fused_state['sentiment_score'],
        'emotion': fused_state['emotion'],
        'emotion_score': fused_state['emotion_score'],
        'topics': fused_state['topics']
    },
    'incongruence': fused_state['incongruence']
}

print("\nBrain State:")
for key, value in frontend_data['brain_state'].items():
    if isinstance(value, float):
        print(f"  {key}: {value:.2f}")
    else:
        print(f"  {key}: {value}")

print("\nText Features:")
for key, value in frontend_data['text_features'].items():
    if key == 'topics':
        print(f"  {key}: {value}")
    elif isinstance(value, float):
        print(f"  {key}: {value:.2f}")
    else:
        print(f"  {key}: {value}")

print(f"\nIncongruence: {frontend_data['incongruence']}")

print("\n=== Expected Frontend Display ===")
print(f"Stress: {frontend_data['brain_state']['stress']:.2f} -> {frontend_data['brain_state']['stress']*100:.0f}%")
print(f"Cognitive Load: {frontend_data['brain_state']['cognitive_load']:.2f} -> {frontend_data['brain_state']['cognitive_load']*100:.0f}%")
print(f"Emotional Arousal: {frontend_data['brain_state']['emotion_arousal']:.2f} -> {frontend_data['brain_state']['emotion_arousal']*100:.0f}%")
print(f"Alpha: {frontend_data['brain_state']['alpha']:.0f} (shown as-is)")
print(f"Beta: {frontend_data['brain_state']['beta']:.0f} (shown as-is)")
print(f"Theta: {frontend_data['brain_state']['theta']:.0f} (shown as-is)")
print(f"Gamma: {frontend_data['brain_state']['gamma']:.0f} (shown as-is)")
print(f"Delta: {frontend_data['brain_state']['delta']:.0f} (shown as-is)")
print(f"EMG: {frontend_data['brain_state']['emg']:.2f} -> {frontend_data['brain_state']['emg']*100:.0f}%")
print(f"Sentiment: {frontend_data['text_features']['sentiment']} ({frontend_data['text_features']['sentiment_score']*100:.0f}%)")
print(f"Emotion: {frontend_data['text_features']['emotion']} ({frontend_data['text_features']['emotion_score']*100:.0f}%)")
