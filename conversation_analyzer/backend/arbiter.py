"""
Reliability-based weighting logic for combining expert outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping

import json

ARBITER_CONFIG_PATH = Path(__file__).parent.parent / "config" / "arbiter_config.json"


@dataclass(frozen=True)
class ArbiterConfig:
    base_weights: Mapping[str, float]
    artifact_penalty: Mapping[str, float]
    personalization: Mapping[str, float]
    confidence_thresholds: Mapping[str, float]

    @classmethod
    def load(cls, path: Path = ARBITER_CONFIG_PATH) -> "ArbiterConfig":
        data = json.loads(path.read_text())
        return cls(**data)


class ReliabilityArbiter:
    def __init__(self, config: ArbiterConfig):
        self.config = config

    def score(
        self,
        expert_name: str,
        confidence: float,
        artifact_level: str | None = None,
        personalization_weight: float | None = None,
    ) -> float:
        base = self.config.base_weights.get(expert_name, 0.0)
        artifact_factor = self.config.artifact_penalty.get(artifact_level or "mild", 1.0)
        personal = personalization_weight if personalization_weight is not None else 1.0
        confidence_factor = confidence
        return base * artifact_factor * personal * confidence_factor


_arbiter: ReliabilityArbiter | None = None


def get_arbiter() -> ReliabilityArbiter:
    global _arbiter
    if _arbiter is None:
        _arbiter = ReliabilityArbiter(ArbiterConfig.load())
    return _arbiter

