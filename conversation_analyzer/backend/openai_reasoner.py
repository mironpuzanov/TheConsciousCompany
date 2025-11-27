"""
Utility wrapper around the OpenAI API for generating narrative insights.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI

# Load .env.local from conversation_analyzer directory
_env_path = Path(__file__).parent.parent / ".env.local"
if _env_path.exists():
    load_dotenv(_env_path)

SUMMARY_PROMPT = """You are a psychological analyst examining conversation patterns.
Analyze the conversation data and provide:
1. A concise psychological summary (3-4 sentences) focusing on:
   - Key psychological patterns observed (avoidance, stress, self-criticism, etc.)
   - Notable patterns or mistakes from a psychological perspective
   - Overall emotional and cognitive dynamics
2. Quality scores (1-5 each): actionable, accurate, novel

Return JSON with keys: narrative, scores{{actionable, accurate, novel}}.
Do NOT include advice or takeaways - only analytical observations."""

CACHE_DIR = Path(__file__).parent.parent / "cache" / "openai"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        import logging
        logger = logging.getLogger(__name__)
        logger.error("OPENAI_API_KEY not found in environment. Check .env.local file.")
        raise RuntimeError("OPENAI_API_KEY is not set. Make sure .env.local exists in conversation_analyzer/ directory.")
    return OpenAI(api_key=api_key)


def generate_insight(payload: Dict[str, Any], model: str = "gpt-5", use_cache: bool = True) -> Dict[str, Any]:
    cache_path: Path | None = None
    if use_cache:
        cache_key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        cache_path = CACHE_DIR / f"{cache_key}.json"
        if cache_path.exists():
            try:
                return json.loads(cache_path.read_text())
            except json.JSONDecodeError:
                pass

    client = get_client()
    try:
        # Try gpt-5 first, fallback to gpt-4o if not available
        models_to_try = [model, "gpt-4o", "gpt-4-turbo"]
        summary = None
        last_error = None
        
        for model_name in models_to_try:
            try:
                # GPT-5 doesn't support temperature, only gpt-4o does
                params = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": SUMMARY_PROMPT},
                        {"role": "user", "content": json.dumps(payload, indent=2)},
                    ],
                    "response_format": {"type": "json_object"},
                }
                # Only add temperature for non-GPT-5 models
                if not model_name.startswith("gpt-5"):
                    params["temperature"] = 0.7
                
                response = client.chat.completions.create(**params)
                message = response.choices[0].message.content
                if isinstance(message, dict):
                    summary = message
                else:
                    summary = json.loads(message) if message else {}
                if summary:
                    break
            except Exception as e:
                last_error = e
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Model {model_name} failed: {type(e).__name__}: {e}, trying next model...")
                continue
        
        if not summary:
            raise last_error or Exception("All models failed")
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        error_msg = str(e)
        logger.error(f"OpenAI API call failed: {type(e).__name__}: {error_msg}", exc_info=True)
        # Provide more helpful error message
        if "API key" in error_msg or "authentication" in error_msg.lower():
            error_display = "API key issue - check .env.local"
        elif "model" in error_msg.lower() and "not found" in error_msg.lower():
            error_display = f"Model not available: {error_msg[:50]}"
        else:
            error_display = error_msg[:100]
        summary = {
            "narrative": f"LLM summary unavailable ({error_display}); showing raw analysis only.",
            "scores": {"actionable": 0, "accurate": 0, "novel": 0},
        }

    if cache_path is not None:
        cache_path.write_text(json.dumps(summary))

    return summary

