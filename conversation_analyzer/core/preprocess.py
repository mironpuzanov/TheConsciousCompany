"""
Transcript preprocessing utilities.

Converts raw transcript payloads (text blocks or structured turns) into
normalized `TranscriptTurn` objects and performs basic artifact checks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, Iterable, List, Sequence

import spacy


@dataclass
class TranscriptTurn:
    speaker: str
    text: str
    timestamp: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def _ensure_turn_dict(turn: Dict[str, Any]) -> TranscriptTurn:
    return TranscriptTurn(
        speaker=turn.get("speaker", "unknown"),
        text=turn.get("text", "").strip(),
        timestamp=turn.get("timestamp"),
        metadata={k: v for k, v in turn.items() if k not in {"speaker", "text", "timestamp"}},
    )


def parse_transcript(payload: Dict[str, Any]) -> List[TranscriptTurn]:
    """
    Accepts either:
      - list of turn dictionaries
      - raw text string (split into sentences)
      - JSON string representing either of the above
    """

    transcript = payload.get("transcript")
    if transcript is None:
        raise ValueError("payload missing 'transcript'")

    if isinstance(transcript, str):
        try:
            data = json.loads(transcript)
        except json.JSONDecodeError:
            sentences = _segment_text(transcript)
            return [
                TranscriptTurn(speaker=payload.get("default_speaker", "user"), text=sent, timestamp=None)
                for sent in sentences
                if sent.strip()
            ]
        else:
            transcript = data

    if isinstance(transcript, Sequence):
        return [_ensure_turn_dict(turn) for turn in transcript if isinstance(turn, dict)]

    raise TypeError("Unsupported transcript format")


@lru_cache(maxsize=1)
def _get_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        return spacy.blank("en")


def _segment_text(text: str) -> Iterable[str]:
    nlp = _get_spacy_model()
    doc = nlp(text)
    if doc.has_annotation("SENT_START"):
        return [sent.text.strip() for sent in doc.sents]
    # Fallback: split on newlines
    return [segment.strip() for segment in text.splitlines() if segment.strip()]

