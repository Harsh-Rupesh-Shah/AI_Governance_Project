import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from pathlib import Path

# Disable LangSmith tracing during tests to avoid network connection attempts
os.environ["LANGCHAIN_TRACING_V2"] = "false"

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Mock MongoClient early so modules that import persistence don't fail DNS resolution in offline/sandbox environments
import pymongo
pymongo.MongoClient = MagicMock()

from langchain_core.documents import Document
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.graph import StateGraph, START, END

from app.schemas.models import GovernanceState, ExtractedIntent, RiskAnalysis, FinalDecision
from app.schemas.api_models import GovernanceRequest, GovernanceResponse, AuditLogResponse
from app.services.llm import llm
from app.agents.intent_agent import intent_agent
from app.agents.memory_agent import memory_agent
from app.agents.risk_agent import risk_agent, ModelRefusalError
from app.agents.decision_agent import decision_agent
from app.agents.audit_agent import audit_agent


class TestGovernanceUpgrades(unittest.TestCase):

    def test_01_llm_service_configuration(self):
        """Verify modern parameters on ChatGoogleGenerativeAI (no convert_system_message_to_human)."""
        self.assertFalse(hasattr(llm, "convert_system_message_to_human") and getattr(llm, "convert_system_message_to_human") is True)
        self.assertEqual(llm.temperature, 0.0)
        self.assertTrue(bool(llm.model))

    def test_02_policy_loading_without_community(self):
        """Verify policy files are read correctly using pathlib and langchain_core.documents.Document."""
        policy_dir = PROJECT_ROOT / "app" / "policies"
        self.assertTrue(policy_dir.exists())

        documents = []
        for file_path in policy_dir.glob("*"):
            if file_path.suffix in [".md", ".txt"]:
                content = file_path.read_text(encoding="utf-8")
                if content.strip():
                    documents.append(
                        Document(
                            page_content=content,
                            metadata={"source": file_path.name}
                        )
                    )

        self.assertGreater(len(documents), 0)
        # Check that refund_policy.md was loaded
        sources = [d.metadata["source"] for d in documents]
        self.assertIn("refund_policy.md", sources)

    def test_03_intent_agent_mock_run(self):
        """Verify intent_agent node maps structured output to state."""
        mock_intent = ExtractedIntent(
            action_type="refund",
            refund_amount=75000.0,
            customer_id="CUST-100",
            currency="INR",
            risk_category="financial"
        )

        with patch("app.agents.intent_agent.chain") as mock_chain:
            mock_chain.invoke.return_value = mock_intent
            state: GovernanceState = {
                "request_id": "req-1",
                "user_id": "user-1",
                "request_text": "Please refund 75000 INR to customer CUST-100",
                "created_at": "2026-11-11T00:00:00Z",
                "action_type": None,
                "refund_amount": None,
                "customer_id": None,
                "currency": None,
                "risk_category": None,
                "retrieved_policies": [],
                "matched_policy_ids": [],
                "previous_refunds": [],
                "suspicious_activity_flags": [],
                "historical_risk_score": None,
                "risk_score": None,
                "risk_reason": None,
                "escalation_required": None,
                "decision": None,
                "decision_reason": None,
                "audit_id": None,
                "trace_id": None,
                "assigned_reviewer": None,
                "escalation_status": None,
            }
            update = intent_agent(state)
            self.assertEqual(update["action_type"], "refund")
            self.assertEqual(update["refund_amount"], 75000.0)
            self.assertEqual(update["customer_id"], "CUST-100")
            self.assertEqual(update["currency"], "INR")

    def test_04_risk_agent_deterministic_and_mock_llm(self):
        """Verify hybrid risk engine: deterministic base risk calculation and structured chain call."""
        mock_risk = RiskAnalysis(
            risk_score=0.6,
            risk_reason="High amount and previous refund history",
            escalation_required=True
        )

        with patch("app.agents.risk_agent.risk_chain") as mock_chain:
            mock_chain.invoke.return_value = mock_risk
            state: GovernanceState = {
                "request_id": "req-2",
                "user_id": "user-1",
                "request_text": "Refund 60000 INR",
                "created_at": "2026-11-11T00:00:00Z",
                "action_type": "refund",
                "refund_amount": 60000.0,
                "customer_id": "CUST-200",
                "currency": "INR",
                "risk_category": "financial",
                "retrieved_policies": ["Policy section 5: amounts over 50k"],
                "matched_policy_ids": ["refund_policy.md"],
                "previous_refunds": ["₹20000 on 2026-01-01"],
                "suspicious_activity_flags": [],
                "historical_risk_score": 0.3,
                "risk_score": None,
                "risk_reason": None,
                "escalation_required": None,
                "decision": None,
                "decision_reason": None,
                "audit_id": None,
                "trace_id": None,
                "assigned_reviewer": None,
                "escalation_status": None,
            }
            update = risk_agent(state)
            self.assertEqual(update["risk_score"], 0.6)
            self.assertTrue(update["escalation_required"])
            # Verify context passed to chain factored in deterministic rules (>50k gives +0.2, 1 previous refund gives +0.1)
            call_args = mock_chain.invoke.call_args[0][0]
            self.assertAlmostEqual(call_args["calculated_base_risk"], 0.3, places=2)

    def test_05_risk_agent_model_refusal_fallback(self):
        """Verify risk_agent gracefully handles ModelRefusalError by forcing escalation."""
        with patch("app.agents.risk_agent.risk_chain") as mock_chain:
            mock_chain.invoke.side_effect = ModelRefusalError("Refused safety")
            state: GovernanceState = {
                "request_id": "req-3",
                "user_id": "user-1",
                "request_text": "Suspicious request",
                "created_at": "2026-11-11T00:00:00Z",
                "action_type": "refund",
                "refund_amount": 1000.0,
                "customer_id": "CUST-300",
                "currency": "INR",
                "risk_category": "financial",
                "retrieved_policies": [],
                "matched_policy_ids": [],
                "previous_refunds": [],
                "suspicious_activity_flags": [],
                "historical_risk_score": None,
                "risk_score": None,
                "risk_reason": None,
                "escalation_required": None,
                "decision": None,
                "decision_reason": None,
                "audit_id": None,
                "trace_id": None,
                "assigned_reviewer": None,
                "escalation_status": None,
            }
            update = risk_agent(state)
            self.assertEqual(update["risk_score"], 1.0)
            self.assertTrue(update["escalation_required"])
            self.assertIn("REFUSAL", update["risk_reason"])

    def test_06_decision_agent_guardrails(self):
        """Verify decision_agent enforces hard guardrails on amounts, risk scores, and escalation flags."""
        # Test Guardrail B: Hard limit override when AI attempts to approve >= 50,000
        mock_verdict = FinalDecision(
            decision="APPROVE",
            decision_reason="Looks fine to me",
            assigned_reviewer=None,
            escalation_status="not_required"
        )

        with patch("app.agents.decision_agent.decision_chain") as mock_chain:
            mock_chain.invoke.return_value = mock_verdict
            state: GovernanceState = {
                "request_id": "req-4",
                "user_id": "user-1",
                "request_text": "Refund 85000 INR",
                "created_at": "2026-11-11T00:00:00Z",
                "action_type": "refund",
                "refund_amount": 85000.0,
                "customer_id": "CUST-400",
                "currency": "INR",
                "risk_category": "financial",
                "retrieved_policies": [],
                "matched_policy_ids": [],
                "previous_refunds": [],
                "suspicious_activity_flags": [],
                "historical_risk_score": None,
                "risk_score": 0.2,
                "risk_reason": "Low risk text",
                "escalation_required": False,
                "decision": None,
                "decision_reason": None,
                "audit_id": None,
                "trace_id": None,
                "assigned_reviewer": None,
                "escalation_status": None,
            }
            update = decision_agent(state)
            self.assertEqual(update["decision"], "ESCALATE")
            self.assertIn("[GUARDRAIL OVERRIDE]", update["decision_reason"])
            self.assertEqual(update["assigned_reviewer"], "Finance Ops")

    def test_07_memory_agent_and_store(self):
        """Verify memory_agent queries the long-term store and computes average risk score."""
        mock_store = InMemoryStore()
        # Seed past decisions for customer CUST-500
        mock_store.put(
            ("CUST-500", "decisions"),
            "past-1",
            {
                "action_type": "refund",
                "refund_amount": 10000,
                "created_at": "2026-01-01",
                "risk_score": 0.2,
                "decision": "APPROVE"
            }
        )
        mock_store.put(
            ("CUST-500", "decisions"),
            "past-2",
            {
                "action_type": "refund",
                "refund_amount": 25000,
                "created_at": "2026-02-01",
                "risk_score": 0.6,
                "decision": "DENY",
                "decision_reason": "Invalid invoice"
            }
        )

        state: GovernanceState = {
            "request_id": "req-5",
            "user_id": "user-1",
            "request_text": "Refund request",
            "created_at": "2026-11-11T00:00:00Z",
            "action_type": "refund",
            "refund_amount": 5000.0,
            "customer_id": "CUST-500",
            "currency": "INR",
            "risk_category": "financial",
            "retrieved_policies": [],
            "matched_policy_ids": [],
            "previous_refunds": [],
            "suspicious_activity_flags": [],
            "historical_risk_score": None,
            "risk_score": None,
            "risk_reason": None,
            "escalation_required": None,
            "decision": None,
            "decision_reason": None,
            "audit_id": None,
            "trace_id": None,
            "assigned_reviewer": None,
            "escalation_status": None,
        }

        update = memory_agent(state, store=mock_store)
        self.assertEqual(len(update["previous_refunds"]), 2)
        self.assertEqual(len(update["suspicious_activity_flags"]), 1)
        self.assertAlmostEqual(update["historical_risk_score"], 0.4, places=2)

    def test_08_audit_agent_stores_record(self):
        """Verify audit_agent generates IDs and saves to both audit and customer namespaces."""
        mock_store = InMemoryStore()
        state: GovernanceState = {
            "request_id": "req-6",
            "user_id": "user-1",
            "request_text": "Refund request",
            "created_at": "2026-11-11T00:00:00Z",
            "action_type": "refund",
            "refund_amount": 5000.0,
            "customer_id": "CUST-600",
            "currency": "INR",
            "risk_category": "financial",
            "retrieved_policies": ["policy 1"],
            "matched_policy_ids": ["refund_policy.md"],
            "previous_refunds": [],
            "suspicious_activity_flags": [],
            "historical_risk_score": None,
            "risk_score": 0.1,
            "risk_reason": "Safe",
            "escalation_required": False,
            "decision": "APPROVE",
            "decision_reason": "Fully compliant",
            "audit_id": None,
            "trace_id": None,
            "assigned_reviewer": None,
            "escalation_status": "not_required",
        }

        update = audit_agent(state, store=mock_store)
        self.assertTrue(bool(update["audit_id"]))
        self.assertTrue(bool(update["trace_id"]))

        # Verify record exists in ("audit", "trails")
        audit_items = mock_store.search(("audit", "trails"))
        self.assertEqual(len(audit_items), 1)
        self.assertEqual(audit_items[0].value["decision"], "APPROVE")

        # Verify record exists in ("CUST-600", "decisions")
        customer_items = mock_store.search(("CUST-600", "decisions"))
        self.assertEqual(len(customer_items), 1)
        self.assertEqual(customer_items[0].value["customer_id"], "CUST-600")

    def test_09_end_to_end_compiled_workflow(self):
        """Verify full StateGraph compilation and execution using mock LLM responses."""
        # Build fresh StateGraph matching workflow.py structure
        test_graph = StateGraph(GovernanceState)
        test_graph.add_node("intent_agent", intent_agent)
        test_graph.add_node("policy_agent", lambda s: {"retrieved_policies": ["Standard policy chunk"], "matched_policy_ids": ["refund_policy.md"]})
        test_graph.add_node("memory_agent", memory_agent)
        test_graph.add_node("risk_agent", risk_agent)
        test_graph.add_node("decision_agent", decision_agent)
        test_graph.add_node("audit_agent", audit_agent)

        test_graph.add_edge(START, "intent_agent")
        test_graph.add_edge("intent_agent", "policy_agent")
        test_graph.add_edge("policy_agent", "memory_agent")
        test_graph.add_edge("memory_agent", "risk_agent")
        test_graph.add_edge("risk_agent", "decision_agent")
        test_graph.add_edge("decision_agent", "audit_agent")
        test_graph.add_edge("audit_agent", END)

        # Compile with in-memory persistence for testing
        test_checkpointer = MemorySaver()
        test_store = InMemoryStore()
        test_app = test_graph.compile(checkpointer=test_checkpointer, store=test_store)

        mock_intent = ExtractedIntent(
            action_type="refund",
            refund_amount=3000.0,
            customer_id="CUST-700",
            currency="INR",
            risk_category="financial"
        )
        mock_risk = RiskAnalysis(
            risk_score=0.1,
            risk_reason="Low value within auto-approval threshold",
            escalation_required=False
        )
        mock_verdict = FinalDecision(
            decision="APPROVE",
            decision_reason="Valid low-risk request",
            assigned_reviewer=None,
            escalation_status="not_required"
        )

        with patch("app.agents.intent_agent.chain") as mock_intent_chain, \
             patch("app.agents.risk_agent.risk_chain") as mock_risk_chain, \
             patch("app.agents.decision_agent.decision_chain") as mock_decision_chain:

            mock_intent_chain.invoke.return_value = mock_intent
            mock_risk_chain.invoke.return_value = mock_risk
            mock_decision_chain.invoke.return_value = mock_verdict

            thread_id = "test-thread-700"
            config = {"configurable": {"thread_id": thread_id}}
            initial_state = {
                "request_id": thread_id,
                "user_id": "test-user",
                "request_text": "Please refund 3000 INR to customer CUST-700",
                "created_at": "2026-11-11T00:00:00Z",
            }

            for _ in test_app.stream(initial_state, config=config):
                pass

            final_state = test_app.get_state(config).values
            self.assertEqual(final_state["action_type"], "refund")
            self.assertEqual(final_state["refund_amount"], 3000.0)
            self.assertEqual(final_state["decision"], "APPROVE")
            self.assertTrue(bool(final_state["audit_id"]))

            # Verify audit trail was saved to test_store
            trails = test_store.search(("audit", "trails"))
            self.assertEqual(len(trails), 1)
            self.assertEqual(trails[0].value["decision"], "APPROVE")

    def test_10_api_models_validation(self):
        """Verify API Pydantic schemas validate request and response formats properly."""
        req = GovernanceRequest(request_text="Refund request for order 123")
        self.assertEqual(req.request_text, "Refund request for order 123")

        resp = GovernanceResponse(
            decision="APPROVE",
            decision_reason="Policy compliant",
            risk_score=0.15,
            audit_id="audit-123",
            thread_id="thread-123"
        )
        self.assertEqual(resp.decision, "APPROVE")
        self.assertEqual(resp.risk_score, 0.15)

        audit_log = AuditLogResponse(
            audit_id="audit-999",
            created_at="2026-11-11T12:00:00Z",
            request_text="Refund 500 INR",
            action_type="refund",
            refund_amount=500.0,
            customer_id="CUST-999",
            risk_score=0.1,
            decision="APPROVE",
            decision_reason="Approved per policy",
            assigned_reviewer=None
        )
        self.assertEqual(audit_log.audit_id, "audit-999")
        self.assertEqual(audit_log.refund_amount, 500.0)

    def test_11_fastapi_app_and_routes(self):
        """Verify FastAPI app mounts routes and responds to health and authenticated endpoints."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.api.deps import create_access_token

        client = TestClient(app)

        # 1. Health check
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "healthy")

        # 2. Token generation
        token = create_access_token({"sub": "admin_test", "role": "admin"})
        self.assertTrue(bool(token))


if __name__ == "__main__":
    unittest.main()
