"""
app/schemas/user.py
-------------------
Input schema for the end-user profile submitted to the API.

Strict validation (extra="forbid") ensures unknown fields surface as 422
errors at the HTTP boundary rather than silently propagating through the
agent pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    """Validated user profile passed as the seed input to the agent graph."""

    model_config = ConfigDict(extra="forbid")

    medical_history: List[str]
    short_term_goals: List[str]
    long_term_goals: List[str]
    # Each slot: {"date": "YYYY-MM-DD", "start_time": "HH:MM", "end_time": "HH:MM"}
    availability: List[Dict[str, Any]]
