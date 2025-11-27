"""
Backend package for the Conversation Analyzer service.

Modules:
    pipelines         - Hugging Face pipeline management.
    arbiter           - Reliability weighting logic.
    state_engine      - Latent psychological state updates.
    rules             - Symbolic reasoning / rule execution.
    insight_builder   - Aggregation helpers for API responses.
    openai_reasoner   - LLM-based narrative synthesis.
    storage           - Session persistence utilities.
    routes            - FastAPI router exposing the analysis entrypoints.
"""

from . import (
    analyzer,
    arbiter,
    insight_builder,
    openai_reasoner,
    pipelines,
    routes,
    rules,
    state_engine,
    storage,
)

__all__ = [
    "analyzer",
    "pipelines",
    "arbiter",
    "state_engine",
    "rules",
    "insight_builder",
    "openai_reasoner",
    "storage",
    "routes",
]

