"""
Lazy-loading registry for Hugging Face pipelines used by the conversation analyzer.

This module centralises model loading so we can:
    * Honour the definitions in `conversation_analyzer/model_registry.yaml`.
    * Reuse instantiated pipelines across requests (singleton-style).
    * Provide lightweight wrappers for emotion/stress/zero-shot/NER calls.
    * Throttle model loading to prevent resource exhaustion.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Dict, List

import yaml
from transformers import pipeline

MODEL_REGISTRY_PATH = Path(__file__).parent.parent / "model_registry.yaml"


@dataclass(frozen=True)
class ModelSpec:
    """Represents a model entry within the registry."""

    id: str
    model: str
    task: str
    revision: str | None = None


class PipelineRegistry:
    """
    Manages cached pipeline instances grouped by logical task.
    Throttles model loading to prevent resource exhaustion.
    """

    def __init__(self, registry: Dict[str, List[ModelSpec]]):
        self._registry = registry
        self._load_lock = Lock()
        self._last_load_time = 0.0
        self._load_delay = 2.0  # 2 seconds between model loads

    @classmethod
    def from_file(cls, path: Path = MODEL_REGISTRY_PATH) -> "PipelineRegistry":
        data = yaml.safe_load(path.read_text())
        grouped: Dict[str, List[ModelSpec]] = {}
        for section, specs in data.items():
            entries = [ModelSpec(**spec) for spec in specs]
            grouped[section] = entries
        return cls(grouped)

    def get_pipeline(self, model_id: str):
        # Check if already cached
        cache_key = f"_cached_{model_id}"
        if hasattr(self, cache_key):
            return getattr(self, cache_key)
        
        # Throttle loading to prevent overwhelming the system
        with self._load_lock:
            elapsed = time.time() - self._last_load_time
            if elapsed < self._load_delay:
                time.sleep(self._load_delay - elapsed)
            self._last_load_time = time.time()
            
            spec = self.get_spec(model_id)
            task = self._infer_pipeline_task(spec.task)
            pipeline_instance = pipeline(task, model=spec.model, revision=spec.revision)
            
            # Cache it
            setattr(self, cache_key, pipeline_instance)
            return pipeline_instance

    def get_spec(self, model_id: str) -> ModelSpec:
        spec = next(
            (s for specs in self._registry.values() for s in specs if s.id == model_id),
            None,
        )
        if spec is None:
            raise KeyError(f"Unknown model id: {model_id}")
        return spec

    @staticmethod
    def _infer_pipeline_task(task: str) -> str:
        mapping = {
            "emotion_classification": "text-classification",
            "sentiment_stress": "text-classification",
            "aggression_detection": "text-classification",
            "zero_shot_psychological_labels": "zero-shot-classification",
            "trigger_ner": "ner",
            "embeddings": "feature-extraction",
        }
        return mapping.get(task, "text-classification")


_registry_instance: PipelineRegistry | None = None


def get_registry() -> PipelineRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = PipelineRegistry.from_file()
    return _registry_instance

