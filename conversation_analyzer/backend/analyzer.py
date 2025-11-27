"""
Orchestrates the end-to-end conversation analysis pipeline.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

# Load .env.local from conversation_analyzer directory
_env_path = Path(__file__).parent.parent / ".env.local"
if _env_path.exists():
    load_dotenv(_env_path)

from conversation_analyzer.core import preprocess

from .arbiter import get_arbiter
from .expert_runner import TurnAnalysis, get_expert_runner
from .insight_builder import TurnInsight, build_response
from .openai_reasoner import generate_insight
from .rules import get_rule_engine
from .state_engine import get_state_engine
from .storage import insert_embeddings, insert_rules, insert_state_trace, insert_turns, upsert_session

POSITIVE_LABELS = {"joy", "love", "gratitude", "admiration", "optimism"}
NEGATIVE_LABELS = {"anger", "disgust", "sadness", "fear", "annoyance", "pessimism"}


def analyze(payload: Dict[str, Any]) -> Dict[str, Any]:
    turns = preprocess.parse_transcript(payload)
    if not turns:
        return build_response([], [], [], llm_summary={"narrative": "No transcript turns supplied."})

    runner = get_expert_runner()
    analyses = runner.run(turns)

    arbiter = get_arbiter()
    state_engine = get_state_engine()
    rule_engine = get_rule_engine()

    state = state_engine.new_state()
    state_trace: List[Dict[str, float]] = []
    rule_hits: List[Dict[str, str]] = []
    turn_insights: List[TurnInsight] = []

    turn_rows: List[Dict[str, Any]] = []
    embedding_rows: List[Dict[str, Any]] = []

    for idx, analysis in enumerate(analyses):
        deltas = _derive_state_deltas(analysis, arbiter)
        state = state_engine.apply(state, deltas)
        state_snapshot = {"timestamp": analysis.turn.timestamp or 0.0, **state.values}
        state_trace.append(state_snapshot)

        # Build context for rule evaluation with all available signals
        # Include both "state.X" and "X" formats for rule matching
        stress_val = state.values.get("stress", 0.0)
        avoidance_val = state.values.get("avoidance", 0.0)
        self_criticism_val = state.values.get("self_criticism", 0.0)
        
        context = {
            "topic": analysis.turn.metadata.get("topic"),
            "state.stress": stress_val,
            "stress": stress_val,  # Also include without prefix
            "state.avoidance": avoidance_val,
            "avoidance": avoidance_val,
            "state.self_criticism": self_criticism_val,
            "self_criticism": self_criticism_val,
            # Add emotion scores for rule matching (both formats)
            **{f"emotion.{k}": v for k, v in analysis.emotions.items()},
            **{k: v for k, v in analysis.emotions.items()},  # Also direct access
        }
        rule_hits.extend(rule_engine.evaluate(context))

        # Only include psych labels with confidence > 0.4 to reduce false positives
        significant_labels = [
            label for label, score in sorted(analysis.zero_shot.items(), key=lambda x: x[1], reverse=True)
            if score > 0.4
        ][:3]
        
        turn_insights.append(
            TurnInsight(
                timestamp=analysis.turn.timestamp or 0.0,
                speaker=analysis.turn.speaker,
                text=analysis.turn.text,
                emotions=analysis.emotions,
                psych_labels=significant_labels,  # Only high-confidence labels
                stress=analysis.stress,
                ner_entities=analysis.ner,
            )
        )
        turn_rows.append(
            {
                "turn_index": idx,
                "speaker": analysis.turn.speaker,
                "text": analysis.turn.text,
                "timestamp": analysis.turn.timestamp,
                "emotions": analysis.emotions,
                "psych_labels": analysis.zero_shot,
                "stress": analysis.stress,
                "artifact": analysis.artifact,
            }
        )
        for name, vector in analysis.embeddings.items():
            embedding_rows.append({"turn_index": idx, "embedding_name": name, "embedding": vector})

    # Build additional insights from all model outputs
    all_ner_entities = []
    stress_scores = []
    emotion_trends = {}
    for analysis in analyses:  # analyses is the list from runner.run(turns)
        all_ner_entities.extend(analysis.ner)
        if analysis.stress:
            stress_scores.extend(analysis.stress.values())
        for emotion, score in analysis.emotions.items():
            if emotion not in emotion_trends:
                emotion_trends[emotion] = []
            emotion_trends[emotion].append(score)
    
    # Calculate trends
    emotion_avg = {k: sum(v) / len(v) if v else 0 for k, v in emotion_trends.items()}
    avg_stress = sum(stress_scores) / len(stress_scores) if stress_scores else 0.0
    max_stress = max(stress_scores) if stress_scores else 0.0
    
    # Only count significant stress ( > 0.5) instead of any stress
    significant_stress_scores = [s for s in stress_scores if s > 0.5]
    significant_stress_count = len(significant_stress_scores)
    avg_significant_stress = sum(significant_stress_scores) / len(significant_stress_scores) if significant_stress_scores else 0.0
    
    additional_insights = {
        "ner_entities": list(set(all_ner_entities))[:20],  # Unique entities, top 20
        "stress_summary": {
            "average": avg_stress,
            "peak": max_stress,
            "detections": significant_stress_count,  # Only significant stress
            "total_turns_analyzed": len(stress_scores),
            "significant_stress_average": avg_significant_stress,
        },
        "emotion_summary": dict(sorted(emotion_avg.items(), key=lambda x: x[1], reverse=True)[:5]),
        "total_turns": len(turns),
        "psychological_patterns": {
            label: sum(1 for a in analyses if a.zero_shot.get(label, 0) > 0.4)  # Higher threshold to reduce noise
            for label in ["avoidance", "self-criticism", "stress", "reflection", "decisiveness", "support-seeking"]
        },
    }
    
    summary_payload = {
        "turns": [ti.__dict__ for ti in turn_insights[:5]],
        "recent_state": state_trace[-5:],
        "rules": rule_hits[-5:],
        "additional_insights": additional_insights,
    }
    llm_summary = generate_insight(summary_payload)

    session_payload = {
        "external_id": payload.get("session_id"),
        "title": payload.get("title"),
        "summary": llm_summary,
    }
    session_id = upsert_session(session_payload)

    for row in turn_rows:
        row["session_id"] = session_id
    for row in embedding_rows:
        row["session_id"] = session_id
    for idx, state_row in enumerate(state_trace):
        values = {k: v for k, v in state_row.items() if k != "timestamp"}
        state_row.clear()
        state_row.update(
            {
                "session_id": session_id,
                "point_index": idx,
                "timestamp": values.pop("timestamp", 0.0),
                "values": values,
            }
        )
    for rule_row in rule_hits:
        rule_row["session_id"] = session_id

    insert_turns(turn_rows)
    insert_embeddings(embedding_rows)
    insert_state_trace(state_trace)
    insert_rules(rule_hits)

    return build_response(turn_insights, state_trace, rule_hits, llm_summary=llm_summary, additional_insights=additional_insights)


def _derive_state_deltas(analysis: TurnAnalysis, arbiter) -> Dict[str, float]:
    emotions = analysis.emotions

    def sum_labels(label_set: set[str]) -> float:
        return sum(score for label, score in emotions.items() if label.lower() in label_set)

    pos = sum_labels(POSITIVE_LABELS)
    neg = sum_labels(NEGATIVE_LABELS)
    valence = max(min(pos - neg, 1.0), -1.0)

    stress_score = max(analysis.stress.values(), default=0.0)
    avoidance = analysis.zero_shot.get("avoidance", 0.0)
    self_criticism = analysis.zero_shot.get("self-criticism", 0.0)

    emotion_weight = arbiter.score("emotion", max(emotions.values(), default=0.5), analysis.artifact)
    stress_weight = arbiter.score("stress", stress_score, analysis.artifact)
    psych_weight = arbiter.score("psychological_labels", max(analysis.zero_shot.values(), default=0.5), analysis.artifact)

    return {
        "valence": valence * emotion_weight,
        "stress": stress_score * stress_weight,
        "avoidance": avoidance * psych_weight,
        "self_criticism": self_criticism * psych_weight,
    }

