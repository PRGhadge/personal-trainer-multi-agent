from __future__ import annotations

# This file defines the end-to-end multi-agent pipeline:
# - LLM-backed agents (medical safety, workout planning, scheduling)
# - A tool-backed agent (calendar integration)
# - LangGraph orchestration with explicit transitions and conditional routing
# It is the main executable for running the graph with mock inputs.

import json
import time
from typing import Any, Dict, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, ValidationError

from prompts import (
    MEDICAL_SAFETY_SYSTEM_PROMPT,
    WORKOUT_PLANNING_SYSTEM_PROMPT,
    SCHEDULING_SYSTEM_PROMPT,
    CALENDAR_INTEGRATION_SYSTEM_PROMPT,
    EVALUATION_SYSTEM_PROMPT,
)
from schemas import (
    UserProfile,
    MedicalSafetyOutput,
    WorkoutPlanOutput,
    SchedulingOutput,
    EvaluationOutput,
    AgentState,
)
from tools import create_calendar_event


# -------------------------
# LLM configuration helpers
# -------------------------


def _llm() -> ChatOpenAI:
    # Centralized LLM configuration for deterministic outputs.
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def _call_agent_with_retries(
    system_prompt: str,
    user_payload: Dict[str, Any],
    output_model: BaseModel,
    max_retries: int = 2,
) -> tuple[Dict[str, Any], int]:
    # Enforce strict JSON with a parser + schema validation. Retries if invalid.
    parser = JsonOutputParser(pydantic_object=output_model)
    llm = _llm()

    # Note: output format instructions are injected to enforce strict JSON.
    format_instructions = parser.get_format_instructions()
    messages = [
        SystemMessage(content=f"{system_prompt}\n\n{format_instructions}"),
        HumanMessage(content=json.dumps(user_payload)),
    ]

    last_error: Optional[str] = None
    for attempt in range(max_retries + 1):
        response = llm.invoke(messages)
        try:
            parsed = parser.parse(response.content)
            return output_model.model_validate(parsed).model_dump(), attempt
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            # Add a short correction instruction and retry.
            messages.append(
                HumanMessage(
                    content=(
                        "Your last response failed schema validation. "
                        "Return ONLY valid JSON matching the schema."
                    )
                )
            )
            time.sleep(0.1)

    raise RuntimeError(f"Agent output validation failed: {last_error}")


# -------------------------
# Agent node implementations
# -------------------------

def medical_safety_agent(state: AgentState) -> AgentState:
    # Agent 1: Analyze medical history and return constraints.
    user_profile = UserProfile.model_validate(state["user_profile"]).model_dump()
    output, _retries = _call_agent_with_retries(
        MEDICAL_SAFETY_SYSTEM_PROMPT,
        {"medical_history": user_profile["medical_history"]},
        MedicalSafetyOutput,
    )
    state["medical_safety"] = output
    return state


def workout_planning_agent(state: AgentState) -> AgentState:
    # Agent 2: Build a realistic workout plan aligned with goals and constraints.
    user_profile = UserProfile.model_validate(state["user_profile"]).model_dump()
    payload = {
        "medical_safety": state["medical_safety"],
        "short_term_goals": user_profile["short_term_goals"],
        "long_term_goals": user_profile["long_term_goals"],
    }
    output, _retries = _call_agent_with_retries(
        WORKOUT_PLANNING_SYSTEM_PROMPT,
        payload,
        WorkoutPlanOutput,
    )
    state["workout_plan"] = output
    return state


def scheduling_agent(state: AgentState) -> AgentState:
    # Agent 3: Fit workout sessions into the user's availability.
    user_profile = UserProfile.model_validate(state["user_profile"]).model_dump()
    payload = {
        "workout_plan": state["workout_plan"],
        "availability": user_profile["availability"],
    }
    output, _retries = _call_agent_with_retries(
        SCHEDULING_SYSTEM_PROMPT,
        payload,
        SchedulingOutput,
    )
    state["schedule"] = output
    return state


def calendar_integration_agent(state: AgentState) -> AgentState:
    # Agent 4: Tool agent to create calendar events only with explicit consent.
    # Tool agent: create calendar events only with explicit user confirmation.
    if not state.get("user_confirmation"):
        state["calendar_events"] = []
        return state

    scheduled_sessions = state["schedule"]["scheduled_sessions"]
    created_events = []
    for session in scheduled_sessions:
        created_events.append(create_calendar_event(session))
    state["calendar_events"] = created_events
    return state


def evaluation_agent(state: AgentState) -> AgentState:
    # Evaluator agent: LLM-as-a-judge for plan and schedule quality.
    payload = {
        "medical_safety": state["medical_safety"],
        "workout_plan": state["workout_plan"],
        "schedule": state["schedule"],
    }
    output, _retries = _call_agent_with_retries(
        EVALUATION_SYSTEM_PROMPT,
        payload,
        EvaluationOutput,
    )

    state["evaluation"] = output
    return state


# -------------------------
# Graph construction
# -------------------------

def build_graph() -> StateGraph:
    # Orchestrate agents with explicit transitions and a conditional branch.
    graph = StateGraph(AgentState)

    graph.add_node("medical_safety", medical_safety_agent)
    graph.add_node("workout_planning", workout_planning_agent)
    graph.add_node("scheduling", scheduling_agent)
    graph.add_node("evaluation", evaluation_agent)
    graph.add_node("calendar_integration", calendar_integration_agent)

    # Transition: Medical Safety -> Workout Planning
    graph.add_edge("medical_safety", "workout_planning")
    # Transition: Workout Planning -> Scheduling
    graph.add_edge("workout_planning", "scheduling")
    # Transition: Scheduling -> Evaluation
    graph.add_edge("scheduling", "evaluation")

    # Transition: Evaluation -> Calendar Integration (conditional)
    def should_create_events(state: AgentState) -> str:
        return "calendar_integration" if state.get("user_confirmation") else END

    graph.add_conditional_edges("evaluation", should_create_events)

    graph.set_entry_point("medical_safety")
    graph.set_finish_point("calendar_integration")

    return graph


if __name__ == "__main__":
    # Example run with mock user input (no calendar creation).
    app = build_graph().compile()
    result = app.invoke(
        {
            "user_profile": {
                "medical_history": [
                    "Mild lower back pain",
                    "No recent surgeries",
                ],
                "short_term_goals": ["Improve mobility", "Lose 5 lbs"],
                "long_term_goals": ["Build core strength", "Run a 5K"],
                "availability": [
                    {
                        "date": "2026-02-10",
                        "start_time": "07:00",
                        "end_time": "08:00",
                    },
                    {
                        "date": "2026-02-12",
                        "start_time": "07:00",
                        "end_time": "08:00",
                    },
                    {
                        "date": "2026-02-14",
                        "start_time": "09:00",
                        "end_time": "10:00",
                    },
                ],
            },
            "user_confirmation": False,
        }
    )
    print(json.dumps(result, indent=2))
