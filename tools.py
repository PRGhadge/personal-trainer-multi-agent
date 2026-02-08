from __future__ import annotations

# This file contains external tool integrations.
# In production, replace the stub with real Google Calendar API calls.

from typing import Any, Dict


def create_calendar_event(session: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stub for Google Calendar API integration.
    Replace with real API calls and OAuth flow in production.
    """
    # Simulate event creation by echoing payload with a fake event id.
    duration = session.get("duration_minutes")
    if duration is None:
        raise KeyError("duration_minutes is required to create a calendar event")
    return {
        "event_id": f"evt_{session['date']}_{session['start_time']}",
        "title": session["session_name"],
        "date": session["date"],
        "start_time": session["start_time"],
        "duration_minutes": duration,
    }
