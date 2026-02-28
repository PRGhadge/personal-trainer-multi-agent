from __future__ import annotations

import logging

from app.agents.base import _call_agent_with_retries
from app.prompts import EVALUATION_SYSTEM_PROMPT
from app.schemas.agents import AgentState, EvaluationOutput

logger = logging.getLogger(__name__)


def evaluation_agent(state: AgentState) -> AgentState:
    """LLM-as-a-judge: score the combined plan across 5 quality dimensions."""
    logger.info("Running Evaluation Agent")

    payload = {
        "medical_safety": state["medical_safety"],
        "workout_plan": state["workout_plan"],
        "schedule": state["schedule"],
    }

    output, retries = _call_agent_with_retries(
        EVALUATION_SYSTEM_PROMPT,
        payload,
        EvaluationOutput,
    )

    logger.info("Evaluation done (retries=%d, verdict=%s)", retries, output.get("verdict"))
    state["evaluation"] = output
    return state
