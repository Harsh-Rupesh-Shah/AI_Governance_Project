"""
Intent Extraction Agent
═══════════════════════
First node in the LangGraph governance workflow.

Takes raw natural language request → extracts structured intent
using Google Gemini with enforced Pydantic output schema.

Input from state:  request_text
Writes to state:   action_type, refund_amount, customer_id, currency, risk_category
"""

from langchain_core.prompts import ChatPromptTemplate

from app.services.llm import llm
from app.schemas.models import GovernanceState, ExtractedIntent


# ── System Prompt ────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an intent extraction agent inside an AI governance system.

Your job: take a natural language request and extract its structured intent.

Rules:
- Identify the action type (refund, access_request, deployment, data_deletion, etc.)
- Extract monetary amounts and currency if present
- Extract customer/user identifiers if mentioned
- Classify the risk category: financial, security, operational, or compliance
- Do NOT infer information that is not present in the request
- If a field is not applicable, leave it as null
"""


# ── LLM Chain ───────────────────────────────────────────────────

structured_llm = llm.with_structured_output(ExtractedIntent)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{request_text}"),
])

chain = prompt | structured_llm


# ── Agent Node Function ─────────────────────────────────────────

def intent_agent(state: GovernanceState) -> dict:
    """
    LangGraph node: extract structured intent from request_text.
    Returns a partial state update dict.
    """
    result: ExtractedIntent = chain.invoke({
        "request_text": state["request_text"]
    })

    return {
        "action_type": result.action_type,
        "refund_amount": result.refund_amount,
        "customer_id": result.customer_id,
        "currency": result.currency,
        "risk_category": result.risk_category,
    }
