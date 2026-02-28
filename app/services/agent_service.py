from __future__ import annotations

import logging
from typing import Any, Dict

from app.agents.evaluation import evaluation_agent
from app.schemas.agents import AgentState, EvaluationOutput, MedicalSafetyOutput, WorkoutPlanOutput, SchedulingOutput
from app.schemas.api import (
    EvaluatePlanRequest,
    EvaluatePlanResponse,
    GeneratePlanRequest,
    GeneratePlanResponse,
)
from app.workflows.trainer_graph import get_compiled_graph

logger = logging.getLogger(__name__)


class AgentService:
    """Bridge between FastAPI routes and the LangGraph pipeline."""

    def run_full_pipeline(self, request: GeneratePlanRequest) -> GeneratePlanResponse:
        logger.info("Starting full pipeline (user_confirmation=%s)", request.user_confirmation)

        initial_state: AgentState = {
            "user_profile": request.user_profile.model_dump(),
            "user_confirmation": request.user_confirmation,
        }

        final_state: Dict[str, Any] = get_compiled_graph().invoke(initial_state)

        logger.info("Pipeline complete (verdict=%s)", final_state.get("evaluation", {}).get("verdict"))

        return GeneratePlanResponse(
            medical_safety=MedicalSafetyOutput.model_validate(final_state["medical_safety"]),
            workout_plan=WorkoutPlanOutput.model_validate(final_state["workout_plan"]),
            schedule=SchedulingOutput.model_validate(final_state["schedule"]),
            evaluation=EvaluationOutput.model_validate(final_state["evaluation"]),
            calendar_events=final_state.get("calendar_events", []),
        )

    def run_evaluation(self, request: EvaluatePlanRequest) -> EvaluatePlanResponse:
        """Run only the evaluation agent on a pre-built plan. Skips upstream LLM calls."""
        logger.info("Starting standalone evaluation")

        state: AgentState = {
            "medical_safety": request.medical_safety.model_dump(),
            "workout_plan": request.workout_plan.model_dump(),
            "schedule": request.schedule.model_dump(),
            "user_confirmation": False,
        }

        updated_state = evaluation_agent(state)
        logger.info("Evaluation complete (verdict=%s)", updated_state.get("evaluation", {}).get("verdict"))

        return EvaluatePlanResponse(
            evaluation=EvaluationOutput.model_validate(updated_state["evaluation"])
        )
