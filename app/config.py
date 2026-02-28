from __future__ import annotations

import os
from functools import lru_cache
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gpt-4o-mini"))
    temperature: float = field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0")))
    # Extra attempts after the first; 2 means 3 total.
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "2")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "info"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
