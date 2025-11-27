"""
FastAPI router exposing conversation analysis endpoints.

Concrete processing will be wired once the preprocessing + expert pipeline is implemented.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from . import analyzer, storage

router = APIRouter(prefix="/conversation", tags=["conversation"])


@router.post("/analyze")
async def analyze_conversation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze conversation transcript and return psychological insights.
    """

    if "transcript" not in payload:
        raise HTTPException(status_code=400, detail="transcript is required")

    try:
        analysis = analyzer.analyze(payload)
        # analyzer.analyze() already saves everything to Supabase and returns the analysis dict
        # The analysis dict should contain all the results
        session_id = payload.get("session_id") or datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        return {"session_id": session_id, "analysis": analysis}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

