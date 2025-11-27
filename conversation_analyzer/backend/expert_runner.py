"""
Executes Hugging Face experts over preprocessed transcript turns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Sequence

import yaml
from sentence_transformers import SentenceTransformer

from conversation_analyzer.core.preprocess import TranscriptTurn

from .pipelines import PipelineRegistry, get_registry

EXPERT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "expert_registry.yaml"
ZERO_SHOT_LABELS = [
    "avoidance",
    "self-criticism",
    "reflection",
    "decisiveness",
    "support-seeking",
    "stress",
]


@dataclass
class TurnAnalysis:
    turn: TranscriptTurn
    emotions: Dict[str, float] = field(default_factory=dict)
    stress: Dict[str, float] = field(default_factory=dict)
    zero_shot: Dict[str, float] = field(default_factory=dict)
    ner: List[str] = field(default_factory=list)
    embeddings: Dict[str, List[float]] = field(default_factory=dict)
    artifact: str = "none"


class ExpertRunner:
    def __init__(self, registry: PipelineRegistry | None = None):
        self.registry = registry or get_registry()
        self.config = yaml.safe_load(EXPERT_CONFIG_PATH.read_text())
        self._embedding_models: Dict[str, SentenceTransformer] = {}

    def run(self, turns: Sequence[TranscriptTurn]) -> List[TurnAnalysis]:
        analyses: List[TurnAnalysis] = []
        for turn in turns:
            analysis = TurnAnalysis(turn=turn)
            if turn.text:
                analysis.emotions = self._run_emotion_models(turn.text)
                analysis.stress = self._run_stress_models(turn.text)
                analysis.zero_shot = self._run_zero_shot(turn.text)
                analysis.ner = self._run_ner(turn.text)
                analysis.embeddings = self._generate_embeddings(turn.text)
            analysis.artifact = self._infer_artifact(turn.text)
            analyses.append(analysis)
        return analyses

    def _run_emotion_models(self, text: str) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        # Use only the first (most reliable) emotion model to reduce resource usage
        models = self.config["text_experts"]["emotion"]["models"][:1]  # Only first model
        for spec in models:
            model_id = spec["ref"]
            clf = self.registry.get_pipeline(model_id)
            result = clf(text)
            for entry in result:
                label = entry["label"]
                scores[label] = max(scores.get(label, 0.0), entry["score"])
        return scores

    def _run_stress_models(self, text: str) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        # Use only the first stress model to reduce resource usage
        models = self.config["text_experts"]["stress"]["models"][:1]  # Only first model
        for spec in models:
            model_id = spec["ref"]
            clf = self.registry.get_pipeline(model_id)
            result = clf(text)
            for entry in result:
                label = entry["label"]
                scores[f"{model_id}:{label}"] = entry["score"]
        return scores

    def _run_zero_shot(self, text: str) -> Dict[str, float]:
        model_id = self.config["text_experts"]["psychological_labels"]["models"][0]["ref"]
        classifier = self.registry.get_pipeline(model_id)
        result = classifier(text, candidate_labels=ZERO_SHOT_LABELS, multi_label=True)
        return {label: score for label, score in zip(result["labels"], result["scores"])}

    def _run_ner(self, text: str) -> List[str]:
        model_id = self.config["text_experts"]["triggers"]["models"][0]["ref"]
        ner_pipeline = self.registry.get_pipeline(model_id)
        entities = ner_pipeline(text)
        return list({ent["word"] for ent in entities})

    def _generate_embeddings(self, text: str) -> Dict[str, List[float]]:
        embeddings: Dict[str, List[float]] = {}
        # Use only the primary embedding model to reduce resource usage
        primary_key = "primary"
        if primary_key in self.config["embeddings"]:
            cfg = self.config["embeddings"][primary_key]
            model_id = cfg["ref"]
            spec = self.registry.get_spec(model_id)
            model = self._get_embedding_model(spec.model)
            vector = model.encode(text).tolist()
            embeddings[primary_key] = vector
        return embeddings

    def _get_embedding_model(self, model_name: str) -> SentenceTransformer:
        if model_name not in self._embedding_models:
            # Throttle embedding model loading
            import time
            time.sleep(1.0)  # 1 second delay before loading embedding model
            self._embedding_models[model_name] = SentenceTransformer(model_name)
        return self._embedding_models[model_name]

    @staticmethod
    def _infer_artifact(text: str) -> str:
        word_count = len(text.split())
        if word_count == 0:
            return "severe"
        if word_count < 3:
            return "moderate"
        return "mild"


_runner: ExpertRunner | None = None


def get_expert_runner() -> ExpertRunner:
    global _runner
    if _runner is None:
        _runner = ExpertRunner()
    return _runner

