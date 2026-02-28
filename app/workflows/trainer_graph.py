from __future__ import annotations

import logging
from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.agents.calendar_integration import calendar_integration_agent
from app.agents.evaluation import evaluation_agent
from app.agents.medical_safety import medical_safety_agent
from app.agents.scheduling import scheduling_agent
from app.agents.workout_planning import workout_planning_agent
from app.schemas.agents import AgentState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("medical_safety", medical_safety_agent)
    graph.add_node("workout_planning", workout_planning_agent)
    graph.add_node("scheduling", scheduling_agent)
    graph.add_node("evaluation", evaluation_agent)
    graph.add_node("calendar_integration", calendar_integration_agent)

    graph.add_edge("medical_safety", "workout_planning")
    graph.add_edge("workout_planning", "scheduling")
    graph.add_edge("scheduling", "evaluation")

    # Calendar integration is an opt-in side effect — never route there without consent.
    def _should_create_events(state: AgentState) -> str:
        return "calendar_integration" if state.get("user_confirmation") else END

    graph.add_conditional_edges("evaluation", _should_create_events)

    graph.set_entry_point("medical_safety")
    graph.set_finish_point("calendar_integration")

    return graph


@lru_cache(maxsize=1)
def get_compiled_graph():
    """Compile once and cache. Compilation is expensive; do not call per request."""
    logger.info("Compiling LangGraph graph")
    return build_graph().compile()
