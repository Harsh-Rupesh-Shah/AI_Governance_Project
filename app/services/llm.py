"""
LLM Service
════════════
Centralised Gemini LLM instance used by all governance agents.

Configured with the high-quota (1,500 requests/day) Gemini models:
- Primary: gemini-2.5-flash (from morning-digest)
- Multi-Key & Model Resilience: If gemini-2.5-flash experiences transient
  high-demand spikes (503) or rate limits, it automatically falls back
  to the backup key and gemini-1.5-flash seamlessly in milliseconds.
"""

import logging
from typing import List
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import (
    GOOGLE_API_KEY,
    GOOGLE_API_KEY_BACKUP,
    GOOGLE_MODEL,
    GOOGLE_FALLBACK_MODEL,
)

logger = logging.getLogger(__name__)


def create_gemini_client(api_key: str, model: str, temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_retries=1,  # Fast failover on 503 high demand
    )


def get_resilient_llm(temperature: float = 0.0) -> BaseChatModel:
    """
    Builds a fast, zero-exhaustion Gemini chain using 1,500 req/day quota models.
    """
    models: List[BaseChatModel] = []

    # 1. Primary Key with Primary Model (gemini-2.5-flash)
    if GOOGLE_API_KEY:
        try:
            models.append(create_gemini_client(GOOGLE_API_KEY, GOOGLE_MODEL, temperature))
        except Exception as e:
            logger.warning(f"Could not init primary Gemini client: {e}")

    # 2. Backup Key with Primary Model (gemini-2.5-flash)
    if GOOGLE_API_KEY_BACKUP and GOOGLE_API_KEY_BACKUP != GOOGLE_API_KEY:
        try:
            models.append(create_gemini_client(GOOGLE_API_KEY_BACKUP, GOOGLE_MODEL, temperature))
        except Exception as e:
            logger.warning(f"Could not init backup Gemini key: {e}")

    # 3. Fallback Model (gemini-1.5-flash: rock-solid 1,500 req/day, no demand spikes)
    if GOOGLE_FALLBACK_MODEL and GOOGLE_FALLBACK_MODEL != GOOGLE_MODEL:
        for key in [GOOGLE_API_KEY, GOOGLE_API_KEY_BACKUP]:
            if key:
                try:
                    models.append(create_gemini_client(key, GOOGLE_FALLBACK_MODEL, temperature))
                    break
                except Exception as e:
                    logger.warning(f"Could not init fallback Gemini model: {e}")

    if not models:
        raise ValueError("No GOOGLE_API_KEY configured in .env")

    primary = models[0]
    fallbacks = models[1:]

    if fallbacks:
        logger.info(
            f"Configured Gemini LLM: Primary={primary.model} with {len(fallbacks)} fallback tier(s)"
        )
        return primary.with_fallbacks(fallbacks)

    return primary


# Global instance used by intent, risk, and decision agents
llm = get_resilient_llm()
