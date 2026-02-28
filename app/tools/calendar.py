"""
app/tools/calendar.py
---------------------
Calendar integration tool invoked by the Calendar Integration Agent.

Currently a stub that simulates event creation by echoing the session payload
with a synthetic event ID.  To go live, replace the function body with real
Google Calendar API calls (OAuth 2.0 + ``google-api-python-client``).

Keeping tool implementations in ``app/tools/`` decouples them from agent
logic; swapping the implementation never touches the agent or the graph.
"""

from __future__ import annotations

from typing import Any, Dict


def create_calendar_event(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stub for Google Calendar API integration.

    Args:
        session: A scheduled session dict with at minimum:
                 date, start_time, duration_minutes, session_name.

    Returns:
        A dict representing the created (or simulated) calendar event.

    Raises:
        KeyError: If ``duration_minutes`` is missing from the session payload.
    """
    # Validate required field before constructing the response.
    duration = session.get("duration_minutes")
    if duration is None:
        raise KeyError("duration_minutes is required to create a calendar event")

    # Deterministic synthetic ID: easy to trace in logs and tests.
    return {
        "event_id": f"evt_{session['date']}_{session['start_time']}",
        "title": session["session_name"],
        "date": session["date"],
        "start_time": session["start_time"],
        "duration_minutes": duration,
    }
