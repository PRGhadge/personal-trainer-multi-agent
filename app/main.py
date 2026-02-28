from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.schemas.api import (
    EvaluatePlanRequest,
    EvaluatePlanResponse,
    GeneratePlanRequest,
    GeneratePlanResponse,
)
from app.services.agent_service import AgentService
from app.workflows.trainer_graph import get_compiled_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting up — compiling LangGraph graph")
    get_compiled_graph()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Personal Trainer Multi-Agent API",
    description="LangGraph multi-agent system for personalised workout plan generation and evaluation.",
    version="1.0.0",
    lifespan=lifespan,
)

_service = AgentService()
logger = logging.getLogger(__name__)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError) -> JSONResponse:
    logger.error("Agent pipeline error: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Agent pipeline error", "message": str(exc)},
    )


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok"}


@app.post(
    "/generate-plan",
    response_model=GeneratePlanResponse,
    summary="Run the full agent pipeline",
    description="Runs Medical Safety → Workout Planning → Scheduling → Evaluation, "
    "with optional Calendar Integration when user_confirmation=true.",
)
async def generate_plan(request: GeneratePlanRequest) -> GeneratePlanResponse:
    try:
        response = _service.run_full_pipeline(request)
    except RuntimeError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in /generate-plan")
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    logger.info("POST /generate-plan → verdict=%s", response.evaluation.verdict)
    return response


@app.post(
    "/evaluate-plan",
    response_model=EvaluatePlanResponse,
    summary="Re-evaluate a pre-built plan",
    description="Runs only the LLM-as-a-judge evaluation on provided medical_safety, "
    "workout_plan, and schedule — without re-running the full pipeline.",
)
async def evaluate_plan(request: EvaluatePlanRequest) -> EvaluatePlanResponse:
    try:
        response = _service.run_evaluation(request)
    except RuntimeError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in /evaluate-plan")
        raise HTTPException(status_code=500, detail="Internal server error") from exc

    logger.info("POST /evaluate-plan → verdict=%s", response.evaluation.verdict)
    return response
