# Conversation Analyzer Implementation Plan

## ✅ Done

- Repo prep, venv creation, pip upgrade.
- Installed core dependencies (PyTorch 2.6.0 CPU/MPS build, Transformers 4.57+, HF tooling, FastAPI stack, BERTopic, etc.).
- Environment variables set (`PYTORCH_ENABLE_MPS_FALLBACK=1`, OpenAI key placeholder); `.env` template + bootstrap script committed (`env.example`, `scripts/setup_conversation_analyzer.sh`).
- `conversation_analyzer/scripts/warmup_models.py` implemented with safe-run logging.
- Hugging Face cache warmed for: `j-hartmann/emotion-english-distilroberta-base`, `bhadresh-savani/distilbert-base-uncased-emotion`, `cardiffnlp/twitter-roberta-base-emotion`, `finiteautomata/beto-emotion-analysis`, `Hate-speech-CNERG/bert-base-uncased-hatexplain`, `valhalla/distilbart-mnli-12-1`, `dslim/bert-base-NER`, MiniLM/MPNet/Instructor embeddings, BART/T5 summarizers. (BERTopic warm-up warning expected with single sample.)
- Model registry + expert registry committed; EmoRoBERTa removed due to TF-only limitation.
- `arbiter_config.json`, `state_schema.json`, `ruleset_v1.json` created.
- Backend scaffolded: `pipelines.py`, `arbiter.py`, `state_engine.py`, `rules.py`, `insight_builder.py`, `openai_reasoner.py`, `storage.py`, `routes.py`.
- Preprocessing + expert execution integrated (`core/preprocess.py`, `backend/expert_runner.py`, `backend/analyzer.py`); `/conversation/analyze` now runs ingestion → experts → arbiter/state → rules.
- OpenAI reasoning + caching wired (summaries + Actionable/Accurate/Novel scores embedded in responses).

## Up Next

1. **Evaluation & Calibration (Plan §12)**: benchmark harness + micro-calibration prompts; log Actionable/Accurate/Novel scores.
2. **Ops polish (Plan §13)**: anonymization workflow, doc updates, future GPU/Llama roadmap.

## 4. Backend Skeleton

✅ Completed (modules + stub routes in place).

## 5. Preprocessing & Segmentation

✅ `core/preprocess.py` handles raw text/turns, spaCy sentence segmentation, normalization, and feeds artifact metadata to the pipeline.

## 6. Expert Layer Execution

✅ `backend/expert_runner.py` covers emotion/stress/zero-shot/NER/embeddings with artifact heuristics.

## 7. Reliability Arbiter & Latent State

✅ `backend/arbiter.py` + `state_engine.py` applied inside `backend/analyzer.py`, producing `psych_state_trace`.

## 8. Symbolic Reasoner

✅ `backend/rules.py` loaded in analyzer; rules fired per turn and recorded in response.

## 9. Reasoning & Summary (OpenAI)

✅ Summaries generated via `openai_reasoner.generate_insight` with SHA256-based disk cache; analyzer injects top turns/state/rules into prompts and embeds scores in responses.

## 10. Storage & Longitudinal DB

1. Primary store: Supabase Postgres with `pgvector` (tables for sessions, turns, embeddings, rule hits). Enforce RLS + row ownership.
2. Keep DuckDB/Parquet locally for offline analytics and debugging snapshots.
3. Implement Supabase persistence module + vector search helpers (pgvector index). Optional FAISS fallback for on-device experimentation.

## 11. API & Frontend Integration

1. Expose FastAPI endpoints:
   - `POST /conversation/analyze`
   - `GET /conversation/sessions/{id}`
2. Frontend (Vite) tasks:
   - File upload form, metadata inputs.
   - Emotional timeline chart.
   - Recurring themes list (BERTopic output).
   - Actionable insights card (top 2 takeaways + rubric scores).
3. Optional CLI/Markdown report generator.

## 12. Evaluation & Calibration

1. Build notebook/test harness benchmarking emotion/stress models on sample transcripts (GoEmotions subset).
2. Implement micro-calibration prompt after each session (UI) feeding scores back into personalization store.
3. Record Actionable/Accurate/Novel ratings per session.
4. Track rule telemetry for automatic pruning.

## 13. Ops & Future Work

1. Add anonymization workflow (NER-based scrub preview) before sending data to OpenAI.
2. Document bootstrap script `scripts/setup_conversation_analyzer.sh`.
3. Plan GPU/Llama deployment path (vLLM) but defer implementation.
4. Prepare backlog items: audio expert adapters, EEG alignment, common-task training jobs.


