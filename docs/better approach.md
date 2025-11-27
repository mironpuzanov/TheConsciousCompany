⸻

EEG + EMG + Semantics Unified Modeling Framework

Technical Specification — v1.1

⸻

1. Purpose

This document defines the correct, scientifically grounded method for using consumer-grade EEG (e.g., Muse 2 / Muse S) to model human emotional, cognitive, and conversational states in natural settings (talking, moving, thinking, expressing emotion).

Unlike meditation apps or medical EEG pipelines, this system:
	•	does not aim for perfect neural purity
	•	does not remove all artifacts
	•	uses physiological artifacts (EMG, movement) as meaningful emotional-cognitive signals
	•	integrates EEG trends with semantic understanding of speech and text
	•	outputs psychological state patterns, not medical diagnoses

This is the foundation of the Consciousness Operating System.

⸻

2. Core Philosophy

You are NOT building a medical EEG.

You are building a cognitive–emotional sensing system that works in real life, during:
	•	conversation
	•	journaling
	•	thinking
	•	stress
	•	coaching sessions
	•	emotional reflection

In this environment:

Artifacts are part of the psychology, not noise.

Jaw tension = stress
Forehead EMG = cognitive effort
Blink bursts = overwhelm
Speech-induced EMG = engagement
Movement = emotional activation

Therefore:
	•	We keep artifacts
	•	We label them
	•	We model them
	•	We correlate them with semantics and context

This is the breakthrough.

⸻

3. Physiological Foundations

3.1 EEG Bands (Normal Awake)

Band	Frequency	Mental Meaning	Typical Awake %
Delta	0.5–4 Hz	drowsiness, high fatigue	10–25%
Theta	4–8 Hz	internal focus, early emotion	10–20%
Alpha	8–13 Hz	calmness, disengagement	15–35%
Beta	13–30 Hz	tension, problem-solving	12–30%
Gamma	30–45 Hz	attention OR muscle EMG	1–5% neural; can hit 60% EMG

Key fact:
If the user is speaking, gamma becomes mostly EMG.
This is expected and useful.

⸻

4. The Correct Artifact Approach

4.1 Do NOT remove artifacts

Classical EEG processing removes:
	•	jaw tension
	•	talking
	•	forehead muscle activity
	•	micro-expressions
	•	movement
	•	emotional facial contractions

In your use case, this would remove all meaningful signals.

Rule:
Artifacts are secondary emotional features, not errors.

⸻

4.2 Instead of removal → Hybrid Cleaning

A. Remove only true garbage

These must be eliminated:
	•	signal clipping
	•	DC drift
	•	electrode detachment
	•	large mechanical spikes
	•	electrical interference (50/60 Hz)

This ensures baseline quality without destroying psycho-physiological information.

B. Keep physiological artifacts

These are intentional data channels:
	•	EMG (jaw, forehead)
	•	eye blinks
	•	head movement
	•	speech-induced EMG
	•	emotional micro-expressions

These encode:
	•	anxiety
	•	engagement
	•	discomfort
	•	thinking load
	•	emotional activation

⸻

4.3 Artifact intensity → a feature, not a flag

We don’t use:
❌ “artifact → discard this window”

We use:
✔ “artifact_intensity = 0.34”
✔ “artifact_type = ‘jaw EMG’”
✔ “jaw_activity_trend = rising”
✔ “data_quality_score = 0.82”

This becomes part of multimodal modeling.

⸻

5. Signal Pipeline

Step 1 — Band Power Extraction

Per 500–1000 ms window:
	•	band-pass 0.5–45 Hz
	•	PSD (Welch)
	•	compute delta/theta/alpha/beta/gamma ratios

Stored as normalized values.

⸻

Step 2 — Artifact Feature Extraction

EMG indicators
	•	gamma > 15% of total power
	•	sudden increases in 30–80 Hz region
	•	AF7/AF8 spikes (forehead)
	•	jaw spectral bursts (25–40 Hz)
	•	speech-related harmonics

Movement indicators
	•	IMU variance
	•	accelerometer RMS
	•	micro-movement bursts

Blink & eye movement
	•	high-beta spike + vertical motion
	•	delta transient + front sensor asymmetry

All of these remain in the dataset.

⸻

Step 3 — Temporal Smoothing

Psychological states are not instant.

We apply:
	•	median filter (5–10 sec)
	•	exponential moving average (α = 0.2–0.4)
	•	trend extraction (1–3 min windows)

This creates stable, human-like emotion curves.

⸻

Step 4 — Latent Psychological State Modeling

Define latent state:

S = {
  stress: 0–1,
  activation: 0–1,
  cognitive_load: 0–1,
  calmness: 0–1,
  focus: 0–1
}

Update each second:

S(t) = 0.8 * S(t-1) + 0.2 * f(EEG, EMG, artifacts, speech, text)

This avoids oscillation and reflects continuous psychological transitions.

⸻

6. Integrating EEG + EMG + Semantics

This is the true power of your system.

EEG → brain-state trends
EMG → emotional activation
Speech prosody → voice emotion
Semantics → meaning, topics, avoidance patterns
Context → interpretation

You detect psychologically meaningful coincidences like:
	•	Topic → EMG spike → alpha drop → emotional activation
	•	Self-critical statement → jaw tension → beta rise
	•	Calm pause → alpha rise → reduced EMG
	•	Fast speech + gamma EMG → cognitive overload

These correlations form the Consciousness Model.

⸻

7. Meeting-Level Analysis (Not Second-by-Second)

Your insights come from 5–10 minute windows, not instant data.

You compute:
	•	stress slope
	•	cognitive load cycles
	•	topic-triggered activation
	•	emotional wave patterns
	•	moments of regulation
	•	stable vs unstable states
	•	semantic–physiological correlations

These are psychologically valid and incredibly actionable.

⸻

8. What the System Outputs

Not:
	•	raw EEG numbers
	•	medical indicators
	•	clinical diagnoses

But:
	•	patterns
	•	trends
	•	emotional triggers
	•	mind-state transitions
	•	topic-based activation maps
	•	baseline vs deviation changes
	•	weekly personal psychological signatures

Example insights:
	•	“Your stress increased by 37% when discussing relationships.”
	•	“Your attention was highest during reflection but lowest in tasks.”
	•	“Jaw tension consistently rises before you mention finances.”
	•	“You regained calm quickly after expressing frustration.”

This is coaching-level consciousness mapping.

⸻

9. Data Stored per Second

timestamp
delta
theta
alpha
beta
gamma

emg_intensity
jaw_activity
forehead_emg
blink_flag
movement

speech_activity
voice_prosody_emotion
semantic_sentiment
semantic_emotion
topic_shift

latent_stress
latent_activation
latent_calm
latent_cognitive_load

This creates one of the most powerful non-medical human-state datasets in the world.

⸻

10. Summary (One Paragraph)

Your system treats EEG and artifacts not as separate elements but as complementary signals representing mind, emotion, and behavior. Instead of removing artifacts, it uses them as features that reveal tension, emotional spikes, and cognitive effort. EEG trends are smoothed, converted into latent psychological states, and combined with semantic understanding of speech and text. The output is not medical diagnosis but deep insight: patterns, triggers, emotional activation curves, and long-term consciousness modeling. This is the scientific foundation of the Consciousness OS.

⸻

---

## 11. Technical Implementation Plan (Updated)

Based on this document, here's how we need to change our current implementation:

### 11.1 Artifact System Overhaul

**Current Problem:** Artifact detector flags everything as artifact and discards it (100% artifact_detected in session data).

**New Approach:**
- Remove binary `has_artifact` flag → Replace with continuous `artifact_intensity: 0.0-1.0`
- Add specific artifact feature channels:
  - `emg_intensity` (jaw/face muscle activity)
  - `forehead_emg` (cognitive effort indicator)
  - `blink_count` (overwhelm indicator)
  - `movement_rms` (emotional activation)
- Only discard true garbage: signal clipping, DC drift, electrode detachment, 50/60Hz interference

### 11.2 New Signal Processing Pipeline

```
1. Garbage Filter (remove only):
   - Signal clipping (>500µV)
   - DC drift
   - Power line interference (notch 50/60Hz)
   - Electrode disconnection

2. Feature Extraction (keep everything):
   - Band powers (delta/theta/alpha/beta/gamma)
   - EMG intensity from gamma (30-45Hz when >15% of total)
   - Jaw activity from AF7/AF8 spectral bursts
   - Movement from accelerometer RMS
   - Blink detection from delta transients

3. Temporal Smoothing:
   - Exponential moving average (α=0.3)
   - 5-10 second median filter for trends
   - 1-3 minute windows for state analysis

4. Latent State Modeling:
   → MOVED TO conversation_analyzer/ (combines EEG + semantic analysis)
```

### 11.3 Data Schema Changes

**Per-second record (backend/ outputs raw features only):**
```python
{
    "timestamp": float,
    # Band powers (normalized)
    "delta": float, "theta": float, "alpha": float, "beta": float, "gamma": float,
    # Artifact features (NOT flags) - NEW
    "emg_intensity": float,      # 0-1, jaw/face muscle activity
    "forehead_emg": float,       # 0-1, cognitive effort indicator
    "blink_intensity": float,    # 0-1, overwhelm indicator
    "movement_intensity": float, # 0-1, from accelerometer
    "data_quality": float,       # 0-1, signal quality (only discard if <0.5)
    # Heart rate
    "heart_rate": float,
    "hrv_rmssd": float,
    # Speech detection
    "is_talking": bool,
    # Legacy (backward compat)
    "artifact_type": str,        # informational only, not for discarding
}
```

**NOTE:** Latent psychological states (stress, activation, calm, etc.) will be computed
in `conversation_analyzer/` by combining this EEG data with semantic analysis.

### 11.4 Heart Rate Fix

Current issue: PPG data not being processed correctly. Yesterday it worked.
- Debug: Check if PPG stream is actually receiving data
- Verify `muselsl stream --ppg` is active
- Check ppg_processor.py for timing/buffer issues

### 11.5 Analysis Output Changes

**Session Summary → Psychological Insights:**
- Stress slope over session
- Cognitive load cycles
- Topic-triggered activation moments
- Emotional wave patterns (not "artifact_detected")
- Regulation moments (alpha rises, EMG drops)

### 11.6 Files to Modify

1. `backend/eeg_processor.py` - Remove aggressive artifact rejection, add artifact feature extraction
2. `backend/artifact_detector.py` - Convert to artifact feature extractor (intensity, type, not discard)
3. `backend/main.py` - Update data schema, add latent state computation
4. `backend/session_recorder.py` - New data fields
5. `backend/analysis/` - New module for psychological state modeling

### 11.7 Priority Order

1. **Fix heart rate** - Debug PPG stream
2. **Convert artifact detector** - From binary to continuous features
3. **Add latent state model** - Simple exponential smoothing first
4. **Update session recording** - New schema with all features
5. **Build analysis layer** - 5-10 minute window insights

