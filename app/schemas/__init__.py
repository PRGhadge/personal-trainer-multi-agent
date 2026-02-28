"""
app/schemas/__init__.py
-----------------------
Re-exports every schema so callers can do:
    from app.schemas import UserProfile, GeneratePlanRequest, ...

Splitting into user / agents / api submodules keeps each file focused;
this __init__ collapses them into a flat, convenient namespace.
"""

from app.schemas.user import UserProfile
from app.schemas.agents import (
    MedicalSafetyOutput,
    SessionTemplate,
    WorkoutPlanOutput,
    ScheduledSession,
    SchedulingOutput,
    EvaluationScores,
    EvaluationOutput,
    AgentState,
)
from app.schemas.api import (
    GeneratePlanRequest,
    GeneratePlanResponse,
    EvaluatePlanRequest,
    EvaluatePlanResponse,
)

__all__ = [
    "UserProfile",
    "MedicalSafetyOutput",
    "SessionTemplate",
    "WorkoutPlanOutput",
    "ScheduledSession",
    "SchedulingOutput",
    "EvaluationScores",
    "EvaluationOutput",
    "AgentState",
    "GeneratePlanRequest",
    "GeneratePlanResponse",
    "EvaluatePlanRequest",
    "EvaluatePlanResponse",
]
