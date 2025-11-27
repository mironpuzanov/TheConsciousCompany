"""
Symbolic reasoning layer for converting signals into interpretable insights.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping

RULESET_PATH = Path(__file__).parent.parent / "config" / "ruleset_v1.json"


@dataclass
class Rule:
    id: str
    version: int
    description: str
    conditions: List[str]
    action: str
    telemetry_key: str


class RuleEngine:
    def __init__(self, rules: List[Rule]):
        self.rules = rules

    @classmethod
    def load(cls, path: Path = RULESET_PATH) -> "RuleEngine":
        data = json.loads(path.read_text())
        return cls([Rule(**item) for item in data])

    def evaluate(self, context: Mapping[str, float | str]) -> List[Dict[str, str]]:
        fired = []
        for rule in self.rules:
            if self._matches(rule, context):
                fired.append(
                    {
                        "id": rule.id,
                        "description": rule.description,
                        "action": rule.action,
                        "telemetry_key": rule.telemetry_key,
                    }
                )
        return fired

    def _matches(self, rule: Rule, context: Mapping[str, float | str]) -> bool:
        for condition in rule.conditions:
            if ":" in condition and condition.startswith("topic"):
                _, topic = condition.split(":", 1)
                if context.get("topic") != topic:
                    return False
            elif ">" in condition:
                field, threshold = condition.split(">")
                threshold_val = float(threshold)
                # Handle both "state.stress" and "stress" formats
                field_key = field.strip()
                if "." in field_key:
                    # For "state.stress", try both "state.stress" and "stress"
                    value = context.get(field_key, context.get(field_key.split(".")[-1], 0.0))
                else:
                    value = context.get(field_key, 0.0)
                if not isinstance(value, (int, float)) or value <= threshold_val:
                    return False
            elif ":" in condition:
                field, key = condition.split(":")
                if context.get(field.strip()) != key.strip():
                    return False
        return True


_engine: RuleEngine | None = None


def get_rule_engine() -> RuleEngine:
    global _engine
    if _engine is None:
        _engine = RuleEngine.load()
    return _engine

