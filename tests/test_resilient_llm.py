"""
Resilient LLM Fallback Test Suite
═════════════════════════════════
Verifies multi-tier Gemini fallback hierarchy across:
- Google Gemini Primary Key (gemini-2.5-flash from morning-digest)
- Google Gemini Backup Key
- Fallback Model (gemini-1.5-flash)
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Disable LangSmith tracing in tests
os.environ["LANGCHAIN_TRACING_V2"] = "false"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pydantic import BaseModel
from langchain_core.runnables import RunnableLambda
from app.services.llm import get_resilient_llm, llm
from app.schemas.models import ExtractedIntent, RiskAnalysis, FinalDecision


class TestResilientLLM(unittest.TestCase):

    def test_01_resilient_llm_has_fallbacks(self):
        """Verify the global LLM instance is configured with fallback tiers."""
        self.assertTrue(hasattr(llm, "fallbacks"))
        self.assertGreaterEqual(len(llm.fallbacks), 1)

    def test_02_structured_output_fallbacks_chain(self):
        """Verify with_structured_output produces a RunnableWithFallbacks for Pydantic models."""
        intent_chain = llm.with_structured_output(ExtractedIntent)
        self.assertTrue(hasattr(intent_chain, "fallbacks"))
        self.assertGreaterEqual(len(intent_chain.fallbacks), 1)

        risk_chain = llm.with_structured_output(RiskAnalysis)
        self.assertTrue(hasattr(risk_chain, "fallbacks"))

        decision_chain = llm.with_structured_output(FinalDecision)
        self.assertTrue(hasattr(decision_chain, "fallbacks"))

    def test_03_simulated_503_failover(self):
        """Simulate a 503 Service Unavailable / High Demand error and verify fallback activates."""
        def failing_primary(*args, **kwargs):
            raise RuntimeError("503 UNAVAILABLE: Model is currently experiencing high demand")

        def successful_fallback(*args, **kwargs):
            return ExtractedIntent(
                action_type="refund",
                refund_amount=75000.0,
                customer_id="CUST-8872",
                currency="INR",
                risk_category="financial"
            )

        mock_primary = RunnableLambda(failing_primary)
        mock_fallback = RunnableLambda(successful_fallback)

        resilient_runnable = mock_primary.with_fallbacks([mock_fallback])
        result = resilient_runnable.invoke({"request_text": "Refund 75000 INR"})

        self.assertIsInstance(result, ExtractedIntent)
        self.assertEqual(result.action_type, "refund")
        self.assertEqual(result.refund_amount, 75000.0)

    def test_04_fallback_model_tier(self):
        """Verify get_resilient_llm configures fallback models."""
        resilient = get_resilient_llm()
        self.assertEqual(resilient.runnable.model, "gemini-2.5-flash")
        # Ensure fallbacks contain secondary tiers
        self.assertGreaterEqual(len(resilient.fallbacks), 1)


if __name__ == "__main__":
    unittest.main()
