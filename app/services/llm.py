"""
LLM Service
════════════
Centralised LLM instance used by all agents.

All agents import `llm` from here instead of creating their own.
This ensures a single place to change the model, key, or params.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GOOGLE_API_KEY, GOOGLE_MODEL

llm = ChatGoogleGenerativeAI(
    model=GOOGLE_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0,
    convert_system_message_to_human=True,
)
