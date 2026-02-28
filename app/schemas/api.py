"""
app/schemas/api.py
------------------
HTTP request and response models for the FastAPI layer.

Separating API contracts from agent contracts matters because:
- The API surface is versioned and public; agent schemas are internal.
- Response models can cherry-pick agent output fields without leaking
  intermediate state (e.g. raw retry counts) to callers.
- It keeps the HTTP boundary type-safe and self-documenting via OpenAPI.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserProfile
from app.schemas.agents import (
    MedicalSafetyOutput,
    WorkoutPlanOutput,
    SchedulingOutput,
    EvaluationOutput,
)


# ---------------------------------------------------------------------------
# POST /generate-plan
# ---------------------------------------------------------------------------

class GeneratePlanRequest(BaseModel):
    """
    Full pipeline request: user profile + optional calendar-creation consent.

    ``user_confirmation=False`` by default so callers must explicitly opt in
    to calendar event creation.
    """

    model_config = ConfigDict(extra="forbid")

    user_profile: UserProfile
    user_confirmation: bool = False


class GeneratePlanResponse(BaseModel):
    """
    Full pipeline response containing every agent's output.

    All fields are typed against their agent schemas so the OpenAPI spec
    documents the complete response contract.
    """

    medical_safety: MedicalSafetyOutput
    workout_plan: WorkoutPlanOutput
    schedule: SchedulingOutput
    evaluation: EvaluationOutput
    # Calendar events are dicts because the stub returns raw dict payloads;
    # swap for a CalendarEvent schema when a real API integration lands.
    calendar_events: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# POST /evaluate-plan
# ---------------------------------------------------------------------------

class EvaluatePlanRequest(BaseModel):
    """
    Standalone evaluation request for re-scoring a pre-built plan.

    Useful when a client has already obtained medical_safety / workout_plan /
    schedule outputs and wants to re-evaluate after manual edits.
    """

    model_config = ConfigDict(extra="forbid")

    medical_safety: MedicalSafetyOutput
    workout_plan: WorkoutPlanOutput
    schedule: SchedulingOutput


class EvaluatePlanResponse(BaseModel):
    """Evaluation-only response wrapping the LLM-as-a-judge output."""

    evaluation: EvaluationOutput
