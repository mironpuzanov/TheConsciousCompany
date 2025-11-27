"""
Latent psychological state tracking helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping

import json

STATE_SCHEMA_PATH = Path(__file__).parent.parent / "config" / "state_schema.json"


@dataclass
class PsychState:
    values: Dict[str, float]

    def update(self, deltas: Mapping[str, float], decay: float) -> "PsychState":
        for key, delta in deltas.items():
            current = self.values.get(key, 0.0)
            self.values[key] = (decay * current) + ((1 - decay) * delta)
        return self


class StateEngine:
    def __init__(self, schema: dict):
        self.schema = schema
        self.decay = schema["metadata"]["decay"]

    @classmethod
    def from_schema(cls, path: Path = STATE_SCHEMA_PATH) -> "StateEngine":
        schema = json.loads(path.read_text())
        return cls(schema)

    def new_state(self) -> PsychState:
        return PsychState(values={field["name"]: 0.0 for field in self.schema["fields"]})

    def apply(self, current: PsychState, deltas: Mapping[str, float]) -> PsychState:
        return current.update(deltas, decay=self.decay)


_engine_instance: StateEngine | None = None


def get_state_engine() -> StateEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = StateEngine.from_schema()
    return _engine_instance

