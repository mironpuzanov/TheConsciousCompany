# Conversation Analyzer Product Plan

## Purpose

Build a temporal, causal, user-adaptive conversation intelligence stack that understands the human behind the signals. The system orchestrates language, audio, EEG, and contextual metadata through hierarchical causal reasoning instead of naïve multimodal fusion. Initial scope still ships a text-first analyzer, but the architecture is designed from day one for personalized psychological modeling, state machines, symbolic overlays, and reliability-aware experts.

## UX Outcomes

- Emotional radar: detect valence, arousal, discrete emotions, and micro-shifts over a conversation timeline.
- Cognitive-semantic layer: estimate cognitive load, ambiguity tolerance, decisiveness, clarity, goal orientation.
- Risk radar: flag burnout signals, avoidance loops, withdrawal, rumination, and escalating conflict patterns.
- Insight layer: surface “why” narratives (triggers, unmet needs, context dependencies) and provide actionable regulation prompts.
- Longitudinal dashboard: highlight drift from baseline, new recurring stressors, recovery speed, and positive habit formation.

## Data Sources & Contracts

| Source | Format | Key Fields | Notes |
| --- | --- | --- | --- |
| Transcripts | JSONL / turn-by-turn segments | `timestamp`, `speaker`, `text`, `confidence` | Import from meeting recordings or live ASR (OpenAI Realtime / Whisper). |
| Conversational metadata | JSON sidecar | `context`, `participants`, `meeting_type`, `goals` | Provides grounding for trigger analysis and cohort modeling. |
| EEG streams (future) | Binary + JSON metadata | `band_powers`, `markers`, `sampling_rate` | Align via timestamps for multimodal fusion. |
| Wearable vitals (future) | JSON over WebSocket | `hr`, `hrv`, `gsr`, `posture` | Use for physiological corroboration of linguistic cues. |

## Architecture Principles

1. **Hierarchical causal modeling**
   - EEG, HRV, posture propose physiological hypotheses.
   - Language/audio resolve ambiguity, apply situational context.
   - Arbiter decides when physiology outranks semantics (and vice versa) using Bayesian belief updates.
2. **Latent psychological state machine**
   - Maintain a central evolving state vector per user capturing arousal, affect, regulation, motivation, cognitive load, and coping strategy.
   - Each modality issues *state delta* proposals; temporal coherence and priors keep the trajectory realistic.
3. **Mixture of experts + reliability arbiter**
   - Dedicated experts per modality/task (e.g., `EEGStressExpert`, `VoiceProsodyExpert`, `TextIntentExpert`, `ContextualMemoryExpert`).
   - Arbiter weights experts using recency, sensor confidence, artifact detectors, and user-specific trust metrics.
4. **Common task learning**
   - Cross-modal objectives (EEG predicting speech valence, text predicting physiological drift) encourage cooperation without blending embeddings.
   - Shared tasks become self-supervised signals for continual learning.
5. **Symbolic psychological layer**
   - Rule engine (Datalog-ish or jsonlogic) interprets expert outputs and latent states into explainable insights.
   - Rules are customizable per user/coach, enabling transparent narratives (“semantic contradiction + sustained beta → anticipatory anxiety”).
6. **User-adaptive personal brain models**
   - Each user maintains calibration curves mapping their unique physiology/linguistics to psychological states.
   - Continual learning loop updates priors, rule thresholds, arbiter weights, and state-machine parameters.

## System Breakdown (text-first milestone with future hooks)

1. **Acquisition & Normalization**
   - Transcript ingestion via REST/WebSocket; audio embeddings optional.
   - Sensor adapters register modalities with metadata about sampling rate, latency, and trust score.
2. **Preprocessing**
   - Turn segmentation, speaker diarization, context linking.
   - Artifact detection per modality (EEG dropouts, ASR low confidence, emotionless TTS transcripts).
3. **Expert Layer**
   - **Sentiment & emotion (per utterance)**: `j-hartmann/emotion-english-distilroberta-base`, `bhadresh-savani/distilbert-base-uncased-emotion`, `cardiffnlp/twitter-roberta-base-emotion`.
   - **Sentiment/stress/aggression**: `finiteautomata/beto-emotion-analysis`, `Hate-speech-CNERG/bert-base-uncased-hatexplain`, `MoritzLaurer/deberta-v3-large-zeroshot-v2` for burnout/rumination label sets.
   - **Psych traits / behavioral categories**: `dslim/bert-base-NER` for triggers/entities, `valhalla/distilbart-mnli-12-1` for zero-shot psychological labels (avoidance, self-criticism, resilience), `InstructorXL`, `all-MiniLM-L6-v2`, `all-mpnet-base-v2` for embedding-based clustering of language style and tone habits.
   - **Cognitive/intent markers**: `allenai/scibert_scivocab_uncased` (fine-tune for cognitive load heuristics), OpenAI GPT-4.1-mini prompts for reasoning about mental effort (swap to self-hosted Llama later).
   - **Conversation/topic structure**: BERTopic + embeddings (MiniLM/MPNet) and optionally `digitalepidemiologylab/covid-twitter-bert` or other domain BERTs for topic extraction.
   - **Summarization/key insights**: `facebook/bart-large-cnn`, `t5-base` to condense sessions into action-oriented briefs.
   - **Audio experts** (future): `speechbrain/emotion-recognition-wav2vec2-IEMOCAP`, `audeering/wav2vec2-large-robust-12-ft-emotion-msp-dbw`.
   - **Physiology experts** (future): existing EEG band interpreters, HRV stress estimator.
4. **Reliability Arbiter**
   - Computes per-expert weights using sensor QA, historical accuracy, situational priors (e.g., “user tends to under-report stress verbally”).
   - Implements arbitration strategies (Bayesian model averaging, winner-take-most when big discrepancies).
5. **Latent State Engine**
   - Kalman/particle filter that updates user’s psychological state using expert outputs + arbiter weights.
   - Supports hypothesis branching when signals conflict (“parallel universes” pruned as evidence arrives).
6. **Symbolic Reasoner**
   - Rule graph translates state trajectory into narratives, detections, and prompts.
   - Supports counterfactual queries (“what if we trusted voice more than text here?”).
7. **Insight Surfaces**
   - Timeline, trigger graph, longitudinal baseline shift, regulation pattern suggestions, coach-facing debug view (showing expert weights + rules fired).
   - MVP insight bundle: per-sentence emotional map, recurring themes, avoidance/self-criticism markers, summary of triggers and coping responses, plus longitudinal comparison if prior sessions exist.
   - **Conversation Insights UI**: shipped inside `consciousness-app` (Vite React). Users toggle from the EEG dashboard to a dedicated panel. Features include:
     1. Transcript upload form (text or JSON) calling `/conversation/analyze`.
     2. Narrative summary card with Actionable/Accurate/Novel scores and takeaways.
     3. Turn-by-turn chips showing speakers, timestamps, top emotions/psych labels.
     4. Rules-fired list and quick emotion heat map chips.
     5. (Next) Session history + Supabase-backed search for prior insights.

## MVP Flow (“Upload transcript → insight”)

1. User uploads meeting transcript (JSON/Markdown/plain text). We split into sentences/turns.
2. Emotion/sentiment experts run per turn → produce temporal map + confidence.
3. Psychological zero-shot classifier labels each turn for avoidance, self-criticism, reflection, decisiveness, etc.
4. Embedding store (MiniLM/MPNet) updated; BERTopic + clustering detect recurring themes, triggers, language style shifts.
5. Summarizer (BART/T5) distills key behavioral insights; symbolic layer cross-references rules (e.g., “avoidance spikes when discussing hiring”).
6. Latent state engine updates long-term profile; insights persisted with metadata for longitudinal tracking and semantic search.

## Data Storage & Supabase Integration

- Primary datastore: Supabase Postgres (project `dorgfthzvdldazfstplm`) with `pgvector`.
- Tables:
  - `conversation_sessions` stores metadata + OpenAI summary/score payloads (one row per upload).
  - `conversation_turns` stores per-turn speaker text, timestamps, emotions, zero-shot labels, and artifact flags.
  - `conversation_state_trace` keeps the full latent state trajectory for charting.
  - `conversation_rules_fired` provides explainability/audit logs.
  - `conversation_embeddings` keeps MiniLM/MPNet/Instructor embeddings (vector(1536)) for semantic recall and future coaching search flows.
- RLS/RBAC: reuse journaling app policies; every row links to `user_id`.
- DuckDB remains as a local scratchpad for offline notebooks, but production flows read/write Supabase.

## Local HF Stack & Dev Environment (MacBook Pro M3)

- **Hardware**: M3/M3 Pro handles DistilRoBERTa/MPNet-sized models on CPU or Apple MPS; expect ~1–2 seconds per 200-token segment.
- **Virtual env**: `python3 -m venv venv && source venv/bin/activate`.
- **Dependencies**:
  - `pip install torch==2.2.2 --extra-index-url https://download.pytorch.org/whl/cpu`
  - `pip install "transformers>=4.38" accelerate sentencepiece datasets sentence-transformers spacy umap-learn hdbscan bertopic duckdb fastapi uvicorn openai`.
- **Runtime tips**:
  - Set `PYTORCH_ENABLE_MPS_FALLBACK=1` for mixed CPU/MPS execution.
  - Instantiate HF pipelines once at startup; `.to("mps")` when supported, otherwise stay on CPU.
  - Cache models in `~/.cache/huggingface`; pin exact versions in `conversation_analyzer/model_registry.yaml`.
  - Process transcripts sequentially first; add batching later. Use Redis/SQLite cache for re-analyses of the same text.

## Risks & Mitigations

- **Artifact handling**: encode artifact confidence per modality; symbolic layer rules consume `signal_quality` so EEG/EMG noise never drives insights. Plan calibration dataset with labeled artifacts.
- **Inference cost**: default to distilled/efficient models (DistilRoBERTa, MiniLM). Reserve Llama-3-8B only for summary/meta reasoning with batching + caching.
- **Evaluation clarity**: beyond unit F1/kappa, define “insight correctness” rubric with psychologists + beta users (actionability/accuracy/novelty scores).
- **Privacy & compliance**: enforce transcript anonymization (NER + custom scrub list), encrypt storage (at rest + in transit), explicit consent + data retention controls for GDPR.
- **Rule explosion**: start with minimal rule pack (≈15 high-signal rules). Implement rule versioning + telemetry to decide when to add/retire rules.
- **Dataset scarcity**: bootstrap with synthetic transcripts + internal sessions, then schedule human annotation sprints to fine-tune personal brain priors.
- **Personalization edge cases**: light calibration (2–3 sessions) may miss atypical language/emotion patterns; add fallback heuristics + outlier detection to request more data before overfitting.
- **Latency for long transcripts**: chunk >10k-token meetings, run HF models piecewise, optionally pre-summarize to keep total runtime under 60s.
- **Sensitive data review**: surface all detected PII/entities to the user before analysis so they can redact if necessary.

## MVP Guardrails

1. Pipeline focus: per-turn emotion/sentiment + zero-shot psych labels + embeddings → latent state → insight summary. Topic modeling and symbolic variants behind feature flags until validated.
2. Personalization: begin with light calibration (first 2–3 sessions) to set priors; embeddings clustering surfaces recurring motifs before rule tuning.
3. Insight UX: highlight triggers, cognitive load spikes, avoidance loops with concise “why it matters” text + optional guidance prompt.
4. EEG/audio: treated as additive state updates later; require artifact-informed weighting before influencing arbiter.
5. Artifact logging feeds arbiter weights; never discard data silently—store `%artifact` per modality for longitudinal QA.
6. Longitudinal normalization ensures early sessions don’t skew baselines; apply rolling z-scores with wide confidence intervals until ≥5 sessions.
7. UI constraint: surface only the top 1–2 actionable takeaways plus an optional deep dive; symbolic outputs stay in an “advanced” panel.
8. Micro-calibration: after each session, capture quick user feedback (e.g., “insight accuracy 1–5”) to refine personalization weights and rule confidences.

## Reasoning Engine Strategy (OpenAI now, Llama later)

- **Current reality (MVP)**: we call OpenAI GPT-4.1-mini / GPT-4o-mini for insight summaries and meta reasoning. No GPU rental required; fast iteration while we validate flow.
- **Why OpenAI first**:
  - zero setup on your MacBook; just configure API key.
  - predictable latency and strong reasoning quality for narrative synthesis.
  - lets us ship upload-to-insight quickly without infra work.
- **How it fits**:
  1. Experts run locally (Hugging Face pipelines on CPU or HF Inference API).
  2. Backend sends structured prompt (latent state, rule hits, key turns) to OpenAI to generate causal narrative + actionable suggestions.
  3. Responses cached per transcript hash so re-analyses cost nothing.
- **Future upgrade**: once we need strict privacy/on-prem, spin up Llama-3-8B (or similar) on rented GPU via `vLLM`/`text-generation-inference`. Keep architecture modular so swapping OpenAI → Llama is just changing the reasoning adapter.

## MVP Success Criteria

- Deliver per-session emotional map, recurring themes, and coping/regulation suggestions from the upload workflow.
- Accuracy: emotion/sentiment F1 ≥ 0.7 on internal benchmark; zero-shot psych labels reviewed by humans hit ≥70% agreement.
- Usability: ≥80% of beta testers report insights feel psychologically accurate/helpful (survey + interviews).
- Efficiency: default inference stack runs <30s for a 5k-token transcript on single GPU; Llama-3 summaries cached per session to avoid per-turn costs.
- Insight rubric: each session rated 1–5 on Actionable, Accurate, Novel; average ≥3.5 indicates acceptable quality.

## Integration With Existing Stack

- Introduce `conversation_analyzer` backend service with three subsystems: `expert_registry`, `state_engine`, `insight_api`.
- Extend session schema with `psych_state_trace`, `expert_weights`, and `rules_fired` arrays for transparency.
- Model hosting remains HF endpoints/on-device, but each expert advertises `capabilities`, `confidence_metrics`, and `cost`.
- DuckDB/Parquet store now keeps both per-turn raw outputs and latent-state trajectories; plan upgrade to time-series DB (Influx/Timescale) when multimodal sampling increases.

## Evaluation Plan

- **Unit signals**: standard benchmarks (GoEmotions, MELD, EmoWOZ, SEW) for accuracy/F1; maintain evaluation notebook.
- **Conversation-level metrics**: agreement vs. expert psychologists on 20 labeled meetings (Cohen’s kappa, narrative quality rubric).
- **User-perceived value**: run beta with 5 teams, gather SUS + qualitative feedback on actionable insights.
- **Fairness**: monitor emotion/stress predictions across gender/culture-coded datasets; add bias mitigation prompts if drift detected.
- **Insight rubric logging**: store Actionable/Accurate/Novel scores per session to drive supervised fine-tuning.
- **Rule lifecycle**: track precision/recall per rule, auto-flag low-performing rules for pruning or retraining.

## Milestone Roadmap

1. **Week 0-1 (now)**: finalize hierarchical causal spec, define expert/arbiter/state schemas, lock the MVP “upload transcript → insight” service contract, and pick the HF models listed above.
2. **Week 2**: build expert registry + text expert adapters + arbiter MVP (weights derived from ASR confidence + heuristics). CLI pipeline to process transcripts into latent state traces.
3. **Week 3**: implement state engine (Kalman-ish), symbolic layer, narrative generator LLM. Export Markdown/PDF report showing trajectories + rules.
4. **Week 4**: personalization loop (user calibration data ingestion, weight learning, rule customization). Add reliability dashboards.
5. **Week 5+**: onboard audio/EEG experts, enable common-task training jobs, experiment with personal brain models + counterfactual evaluation.

## Open Questions / Next Decisions

- Which transcripts to use for initial fine-tuning? (Internal meeting corpus vs. public corpora like AMI, IEMOCAP).
- Do we embed anonymization/pseudonymization before sending to external APIs?
- How to prioritize on-device inference vs. cloud endpoints for privacy-sensitive orgs?
- What cadence for refreshing user baselines as life context shifts?
- How to collect lightweight post-session calibration signals without fatigue?

## Immediate Next Steps

1. Draft spec for `expert_registry.yaml`, `arbiter_config.json`, and `state_schema.json`.
2. Define rule language + starter rules capturing contradictions (EEG stress + “I’m fine”, semantic dissonance, cognitive overload).
3. Collect calibration transcripts per persona (calm stand-up, conflict escalation, burnout check-in) to seed personal brain modeling.
4. Decide on continual learning orchestrator (Prefect vs. Temporal vs. lightweight custom) for refreshing expert weights and user baselines.
5. Prototype the “upload meeting transcript” workflow (CLI or minimal web form) that runs text experts, updates latent state, and emits an insight draft so we can validate usefulness quickly.
6. Finalize local dev instructions (venv, HF downloads, OpenAI key management) and commit a bootstrap script for Mac setups.


