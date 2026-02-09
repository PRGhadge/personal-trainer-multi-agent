from __future__ import annotations

# This file defines the shared schema contracts used across agents:
# - User profile input
# - Each agent's JSON output schema
# - The shared LangGraph state container

from typing import Any, Dict, List, TypedDict

from pydantic import BaseModel, Field, ConfigDict


class UserProfile(BaseModel):
    # Input schema for the end user profile.
    model_config = ConfigDict(extra="forbid")

    medical_history: List[str]
    short_term_goals: List[str]
    long_term_goals: List[str]
    availability: List[Dict[str, Any]]


class MedicalSafetyOutput(BaseModel):
    # Output schema for the Medical Safety Agent.
    model_config = ConfigDict(extra="forbid")

    risk_level: str = Field(pattern="^(low|medium|high)$")
    contraindicated_exercises: List[str]
    recommended_focus_areas: List[str]
    warnings: List[str]


class SessionTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    duration_minutes: int
    exercise_categories: List[str]
    intensity: str = Field(pattern="^(low|medium|high)$")


class WorkoutPlanOutput(BaseModel):
    # Output schema for the Workout Planning Agent.
    model_config = ConfigDict(extra="forbid")

    plan_type: str = Field(pattern="^(strength|cardio|hybrid|rehab)$")
    weekly_sessions: int
    session_templates: List[SessionTemplate]


class ScheduledSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: str
    start_time: str
    duration_minutes: int
    session_name: str


class SchedulingOutput(BaseModel):
    # Output schema for the Scheduling Agent.
    model_config = ConfigDict(extra="forbid")

    scheduled_sessions: List[ScheduledSession]


class EvaluationScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    safety: int
    goal_alignment: int
    realism: int
    schedule_fit: int
    clarity: int


class EvaluationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scores: EvaluationScores
    issues: List[str]
    verdict: str = Field(pattern="^(pass|review|fail)$")


class AgentState(TypedDict, total=False):
    # Shared LangGraph state passed between nodes.
    user_profile: Dict[str, Any]
    medical_safety: Dict[str, Any]
    workout_plan: Dict[str, Any]
    schedule: Dict[str, Any]
    user_confirmation: bool
    calendar_events: List[Dict[str, Any]]
    evaluation: Dict[str, Any]
