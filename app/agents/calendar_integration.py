from __future__ import annotations

import logging

from app.schemas.agents import AgentState
from app.tools.calendar import create_calendar_event

logger = logging.getLogger(__name__)


def calendar_integration_agent(state: AgentState) -> AgentState:
    """
    Create calendar events for each scheduled session.
    No-op if user_confirmation is False — never create external side effects without consent.
    """
    if not state.get("user_confirmation"):
        logger.info("Calendar integration skipped: user_confirmation=False")
        state["calendar_events"] = []
        return state

    sessions = state["schedule"]["scheduled_sessions"]
    logger.info("Creating %d calendar event(s)", len(sessions))

    events = [create_calendar_event(s) for s in sessions]
    state["calendar_events"] = events
    logger.info("%d event(s) created", len(events))
    return state
