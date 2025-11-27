"""
Helpers to consolidate raw model outputs, rule hits, and state traces into API payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class TurnInsight:
    timestamp: float
    speaker: str
    text: str
    emotions: Dict[str, float]
    psych_labels: List[str]
    stress: Dict[str, float] = None
    ner_entities: List[str] = None


def build_response(
    turns: List[TurnInsight],
    state_trace: List[Dict[str, float]],
    rules_fired: List[Dict[str, str]],
    llm_summary: Dict[str, Any] | None = None,
    additional_insights: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "turns": [turn.__dict__ for turn in turns],
        "state_trace": state_trace,
        "rules_fired": rules_fired,
        "llm_summary": llm_summary or {},
        "additional_insights": additional_insights or {},
    }

