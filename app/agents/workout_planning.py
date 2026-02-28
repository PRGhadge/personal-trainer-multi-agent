from __future__ import annotations

import logging

from app.agents.base import _call_agent_with_retries
from app.prompts import WORKOUT_PLANNING_SYSTEM_PROMPT
from app.schemas.agents import AgentState, WorkoutPlanOutput
from app.schemas.user import UserProfile

logger = logging.getLogger(__name__)


def workout_planning_agent(state: AgentState) -> AgentState:
    """Build a workout plan from medical constraints and user goals."""
    logger.info("Running Workout Planning Agent")

    user_profile = UserProfile.model_validate(state["user_profile"]).model_dump()
    payload = {
        "medical_safety": state["medical_safety"],
        "short_term_goals": user_profile["short_term_goals"],
        "long_term_goals": user_profile["long_term_goals"],
    }

    output, retries = _call_agent_with_retries(
        WORKOUT_PLANNING_SYSTEM_PROMPT,
        payload,
        WorkoutPlanOutput,
    )

    logger.info(
        "Workout Planning done (retries=%d, type=%s, sessions=%s)",
        retries, output.get("plan_type"), output.get("weekly_sessions"),
    )
    state["workout_plan"] = output
    return state
