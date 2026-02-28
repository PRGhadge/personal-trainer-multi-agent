# Multi-Agent Personal Trainer System

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-green?logo=fastapi)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-red)

A **production-oriented multi-agent AI backend** that takes a user's medical history, goals, and availability and returns a fully evaluated, personalised workout plan — served as a REST API with strict schema validation, retry logic, and an LLM-as-a-judge evaluation framework.

---

## What Makes This Worth Looking At

- **5 specialised agents** orchestrated with LangGraph — each with its own responsibility, schema, and prompt
- **LLM-as-a-judge** evaluation scoring the plan across 5 quality dimensions before it reaches the user
- **3-layer production architecture** separating HTTP, orchestration, and domain logic — each independently testable
- **Schema validation at every boundary** — HTTP (FastAPI/Pydantic), agent output (JsonOutputParser + retry), and service layer
- **Standalone re-evaluation endpoint** — re-score a plan without re-running the full pipeline
- **Explicit consent gate** — calendar events are never created without `user_confirmation: true`

---

## How It Works

A single `POST /generate-plan` request triggers this pipeline:

```
User Request (JSON)
      │
      ▼  [422 if invalid — no LLM call wasted]
  FastAPI + Pydantic validation
      │
      ▼
  AgentService
      │
      ▼
  LangGraph Graph
      │
      ├─► [1] Medical Safety Agent
      │         Reads: medical_history
      │         Returns: risk_level, contraindications, warnings
      │
      ├─► [2] Workout Planning Agent
      │         Reads: medical_safety output + goals
      │         Returns: plan_type, weekly_sessions, session_templates
      │
      ├─► [3] Scheduling Agent
      │         Reads: workout_plan + availability
      │         Returns: scheduled_sessions (date, time, duration)
      │
      ├─► [4] Evaluation Agent  ← LLM-as-a-judge
      │         Reads: all three outputs above
      │         Returns: scores (1–5) + issues + verdict (pass/review/fail)
      │
      └─► [5] Calendar Integration Agent  ← only if user_confirmation=true
                Reads: scheduled_sessions
                Returns: calendar event stubs
```

Every agent validates its output against a strict Pydantic schema. If the LLM returns malformed JSON, a self-correction message is sent and it retries — up to 3 total attempts.

---

## Evaluation Framework

The Evaluation Agent acts as an independent LLM judge that scores the full plan:

| Dimension | What it checks |
|---|---|
| **Safety** | Are medical contraindications respected? |
| **Goal Alignment** | Does the plan address the user's stated goals? |
| **Realism** | Is the intensity and progression achievable? |
| **Schedule Fit** | Does it fit within availability without overloading days? |
| **Clarity** | Are sessions clearly named and structured? |

Returns a `verdict`: **pass**, **review**, or **fail** — with a list of specific issues when the plan has problems.

The evaluation is also available as a **standalone endpoint** (`POST /evaluate-plan`) for re-scoring a plan after manual edits without re-running the full pipeline.

---

## Real Output Example

`POST /generate-plan` with a user who has lower back pain and wants to run a 5K:

```json
{
  "medical_safety": {
    "risk_level": "medium",
    "contraindicated_exercises": ["heavy lifting", "high-impact activities"],
    "recommended_focus_areas": ["core strengthening", "flexibility", "low-impact cardio"],
    "warnings": ["Consult a healthcare professional before starting."]
  },
  "workout_plan": {
    "plan_type": "hybrid",
    "weekly_sessions": 4,
    "session_templates": [
      { "name": "Core & Flexibility", "duration_minutes": 30, "intensity": "medium" },
      { "name": "Low-Impact Cardio",  "duration_minutes": 30, "intensity": "medium" }
    ]
  },
  "schedule": {
    "scheduled_sessions": [
      { "date": "2026-03-03", "start_time": "07:00", "duration_minutes": 30, "session_name": "Core & Flexibility" },
      { "date": "2026-03-05", "start_time": "07:00", "duration_minutes": 30, "session_name": "Low-Impact Cardio" }
    ]
  },
  "evaluation": {
    "scores": { "safety": 3, "goal_alignment": 4, "realism": 4, "schedule_fit": 3, "clarity": 4 },
    "issues": ["Plan lacks a strength training component given the contraindications."],
    "verdict": "review"
  },
  "calendar_events": []
}
```

---

## Architecture — Three-Layer Separation

| Layer | File | Responsibility |
|---|---|---|
| **HTTP** | `app/main.py` | Request parsing, routing, error → HTTP status mapping |
| **Orchestration** | `app/services/agent_service.py` | Graph invocation, state → response mapping |
| **Domain** | `app/agents/*.py` | LLM calls, prompts, schema validation, retries |

This means: routes are testable without LLM calls, agents are testable without HTTP, and the graph topology is changeable without touching either.

---

## Project Structure

```
app/
├── main.py                    # FastAPI app — routes, lifespan, error handling
├── config.py                  # Settings singleton from environment variables
├── prompts.py                 # All LLM system prompts (single source of truth)
│
├── agents/
│   ├── base.py                # LLM factory + retry-wrapped JSON validation helper
│   ├── medical_safety.py
│   ├── workout_planning.py
│   ├── scheduling.py
│   ├── evaluation.py          # LLM-as-a-judge
│   └── calendar_integration.py
│
├── workflows/
│   └── trainer_graph.py       # LangGraph graph + lru_cache compiled singleton
│
├── schemas/
│   ├── user.py                # UserProfile (API input)
│   ├── agents.py              # Agent I/O schemas + AgentState TypedDict
│   └── api.py                 # HTTP request/response models (separate from agent schemas)
│
├── services/
│   └── agent_service.py       # Orchestration service — thin bridge between routes and graph
│
└── tools/
    └── calendar.py            # Calendar tool stub (swap in Google Calendar API here)
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate-plan` | Full 5-agent pipeline — medical → plan → schedule → evaluate |
| `POST` | `/evaluate-plan` | Standalone LLM-as-judge re-evaluation of a pre-built plan |
| `GET` | `/health` | Liveness check |

Auto-generated interactive docs (try it in-browser): `http://localhost:8000/docs`

---

## Quickstart

```bash
# 1. Clone and activate
cd personal-trainer-multi-agent
source venv/bin/activate

# 2. Install
pip install -r requirements.txt

# 3. Set API key
export OPENAI_API_KEY=sk-...

# 4. Run
uvicorn app.main:app --reload

# 5. Open docs in browser
open http://localhost:8000/docs
```

---

## Key Engineering Decisions

**Why LangGraph?**
Explicit state management via a shared `AgentState` TypedDict. Each agent reads only the fields it needs and writes only what it owns. Conditional routing (`evaluation → calendar`) is a first-class graph concern, not buried in agent logic.

**Why compile the graph once?**
`get_compiled_graph()` uses `lru_cache(maxsize=1)` — compilation runs once at startup via the FastAPI lifespan hook and the result is reused for every request. Compilation is expensive; request handling should not pay that cost.

**Why separate API schemas from agent schemas?**
`app/schemas/api.py` and `app/schemas/agents.py` are intentionally split. The API contract is versioned and public; agent schemas are internal. Changing one doesn't force changes to the other.

**Why a standalone `/evaluate-plan` endpoint?**
The evaluation agent is a pure function. Exposing it directly lets callers re-score a manually-edited plan without re-running three upstream LLM calls — lower latency, lower cost.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Required |
| `MODEL_NAME` | `gpt-4o-mini` | LLM model |
| `TEMPERATURE` | `0` | Deterministic outputs |
| `MAX_RETRIES` | `2` | Extra retries per agent on schema failure |
| `LOG_LEVEL` | `info` | Logging verbosity |
