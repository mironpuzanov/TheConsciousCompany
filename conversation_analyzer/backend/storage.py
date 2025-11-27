"""
Supabase-backed persistence utilities.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .supabase_client import get_client


def upsert_session(session_payload: Dict[str, Any]) -> str:
    client = get_client()
    response = client.table("conversation_sessions").upsert(session_payload, returning="representation").execute()
    session = response.data[0]
    return session["id"]


def insert_turns(turn_rows: List[Dict[str, Any]]) -> None:
    if not turn_rows:
        return
    try:
        client = get_client()
        client.table("conversation_turns").insert(turn_rows).execute()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to insert turns: {e}")


def insert_state_trace(state_rows: List[Dict[str, Any]]) -> None:
    if not state_rows:
        return
    try:
        client = get_client()
        client.table("conversation_state_trace").insert(state_rows).execute()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to insert state trace: {e}")


def insert_rules(rule_rows: List[Dict[str, Any]]) -> None:
    if not rule_rows:
        return
    try:
        client = get_client()
        client.table("conversation_rules_fired").insert(rule_rows).execute()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to insert rules: {e}")


def insert_embeddings(embedding_rows: List[Dict[str, Any]]) -> None:
    if not embedding_rows:
        return
    try:
        client = get_client()
        client.table("conversation_embeddings").insert(embedding_rows).execute()
    except Exception as e:
        # Log but don't fail the whole request if embeddings fail
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to insert embeddings (schema cache may need refresh): {e}")
        # Silently continue - embeddings are optional for MVP

