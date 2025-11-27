"""
Supabase client helper (REST interface).
"""

from __future__ import annotations

import os
from functools import lru_cache

import supabase


@lru_cache(maxsize=1)
def get_client() -> supabase.Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_*_KEY must be set")
    return supabase.create_client(url, key)

