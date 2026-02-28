from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional, Tuple, Type

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError

from app.config import get_settings

logger = logging.getLogger(__name__)


def _llm() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(model=settings.model_name, temperature=settings.temperature)


def _call_agent_with_retries(
    system_prompt: str,
    user_payload: Dict[str, Any],
    output_model: Type[BaseModel],
    max_retries: Optional[int] = None,
) -> Tuple[Dict[str, Any], int]:
    """
    Call an LLM agent and validate the response against a Pydantic schema.
    On validation failure, appends a correction message and retries.
    Raises RuntimeError if all attempts are exhausted.
    """
    settings = get_settings()
    if max_retries is None:
        max_retries = settings.max_retries

    parser = JsonOutputParser(pydantic_object=output_model)
    llm = _llm()

    messages = [
        SystemMessage(content=f"{system_prompt}\n\n{parser.get_format_instructions()}"),
        HumanMessage(content=json.dumps(user_payload)),
    ]

    last_error: Optional[str] = None
    for attempt in range(max_retries + 1):
        if attempt > 0:
            logger.warning("Retry %d/%d for %s", attempt, max_retries, output_model.__name__)

        response = llm.invoke(messages)
        try:
            parsed = parser.parse(response.content)
            return output_model.model_validate(parsed).model_dump(), attempt
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            logger.warning("Validation failed (attempt %d): %s", attempt, last_error)
            messages.append(
                HumanMessage(
                    content="Your last response failed schema validation. "
                    "Return ONLY valid JSON matching the schema."
                )
            )
            time.sleep(0.1)

    raise RuntimeError(
        f"{output_model.__name__} failed after {max_retries + 1} attempts. "
        f"Last error: {last_error}"
    )
