from __future__ import annotations

import logging

from app.agents.base import _call_agent_with_retries
from app.prompts import SCHEDULING_SYSTEM_PROMPT
from app.schemas.agents import AgentState, SchedulingOutput
from app.schemas.user import UserProfile

logger = logging.getLogger(__name__)


def scheduling_agent(state: AgentState) -> AgentState:
    """Map the workout plan onto the user's availability windows."""
    logger.info("Running Scheduling Agent")

    user_profile = UserProfile.model_validate(state["user_profile"]).model_dump()
    payload = {
        "workout_plan": state["workout_plan"],
        "availability": user_profile["availability"],
    }

    output, retries = _call_agent_with_retries(
        SCHEDULING_SYSTEM_PROMPT,
        payload,
        SchedulingOutput,
    )

    logger.info(
        "Scheduling done (retries=%d, sessions=%d)",
        retries, len(output.get("scheduled_sessions", [])),
    )
    state["schedule"] = output
    return state
