from __future__ import annotations

import logging

from app.agents.base import _call_agent_with_retries
from app.prompts import MEDICAL_SAFETY_SYSTEM_PROMPT
from app.schemas.agents import AgentState, MedicalSafetyOutput
from app.schemas.user import UserProfile

logger = logging.getLogger(__name__)


def medical_safety_agent(state: AgentState) -> AgentState:
    """Analyse medical history; only medical_history is sent to the LLM."""
    logger.info("Running Medical Safety Agent")

    user_profile = UserProfile.model_validate(state["user_profile"]).model_dump()
    output, retries = _call_agent_with_retries(
        MEDICAL_SAFETY_SYSTEM_PROMPT,
        {"medical_history": user_profile["medical_history"]},
        MedicalSafetyOutput,
    )

    logger.info("Medical Safety done (retries=%d, risk=%s)", retries, output.get("risk_level"))
    state["medical_safety"] = output
    return state
