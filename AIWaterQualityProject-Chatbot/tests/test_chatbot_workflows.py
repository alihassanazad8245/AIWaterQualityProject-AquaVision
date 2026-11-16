import os
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from src.agents.chatbot.nodes import (
    _report_fact_answer,
    generation_node,
    get_llm,
    report_question_node,
)
from src.foundation import vector_store
from src.agents.reporter import nodes as reporter_nodes


class ChatbotWorkflowTests(unittest.TestCase):
    def test_chat_model_uses_low_reasoning_bounded_requests_and_retries(self):
        created = {}

        class FakeChat:
            def __init__(self, **kwargs):
                created.update(kwargs)

        fake_module = ModuleType("langchain_google_genai")
        fake_module.ChatGoogleGenerativeAI = FakeChat
        with (
            patch.dict(
                os.environ,
                {"GOOGLE_API_KEY": "test-key", "GEMINI_MODEL": "gemini-3.8-flash"},
            ),
            patch.dict(sys.modules, {"langchain_google_genai": fake_module}),
        ):
            get_llm()

        self.assertEqual(created["model"], "gemini-3.8-flash")
        self.assertEqual(created["thinking_level"], "low")
        self.assertEqual(created["request_timeout"], 45)
        self.assertEqual(created["retries"], 2)

    def test_chat_model_defaults_to_gemini_38_flash(self):
        created = {}

        class FakeChat:
            def __init__(self, **kwargs):
                created.update(kwargs)

        fake_module = ModuleType("langchain_google_genai")
        fake_module.ChatGoogleGenerativeAI = FakeChat
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=True),
            patch.dict(sys.modules, {"langchain_google_genai": fake_module}),
        ):
            get_llm()

        self.assertEqual(created["model"], "gemini-3.8-flash")

    def test_default_model_sequence_is_ordered_and_deduplicated(self):
        from src.agents.chatbot.nodes import _configured_gemini_models

        with patch.dict(
            os.environ,
            {
                "GEMINI_MODEL": "gemini-3.8-flash",
                "GEMINI_FALLBACK_MODELS": (
                    " gemini-3.6-flash,gemini-3.1-flash-lite,"
                    "gemini-3.8-flash, ,gemini-3.6-flash "
                ),
            },
            clear=True,
        ):
            self.assertEqual(
                _configured_gemini_models(),
                [
                    "gemini-3.8-flash",
                    "gemini-3.6-flash",
                    "gemini-3.1-flash-lite",
                ],
            )

    def test_legacy_single_fallback_setting_remains_supported(self):
        from src.agents.chatbot.nodes import _configured_gemini_models

        with patch.dict(
            os.environ,
            {
                "GEMINI_MODEL": "gemini-3.8-flash",
                "GEMINI_FALLBACK_MODEL": "gemini-3.1-flash-lite",
            },
            clear=True,
        ):
            self.assertEqual(
                _configured_gemini_models(),
                ["gemini-3.8-flash", "gemini-3.1-flash-lite"],
            )

    def test_general_query_flows_through_retrieval_and_generation(self):
        from src.agents.chatbot import graph as chatbot_graph

        def fake_retrieval(state):
            state["retrieved_docs"] = "WHO guideline source material"
            return state

        def fake_dataset(state):
            state["dataset_context"] = ""
            return state

        def fake_invoke(prompt):
            self.assertIn("WHO guideline source material", prompt)
            return SimpleNamespace(
                content="Here is the answer based on WHO guidance."
            )

        fake_llm = SimpleNamespace(invoke=fake_invoke)
        with (
            patch.object(chatbot_graph, "retrieval_node", fake_retrieval),
            patch.object(chatbot_graph, "dataset_node", fake_dataset),
            patch("src.agents.chatbot.nodes.get_llm", return_value=fake_llm),
        ):
            result = chatbot_graph.build_chatbot_graph().invoke({
                "query": "What does WHO say about drinking water pH?"
            })

        self.assertEqual(result["route"], "rag")
        self.assertEqual(
            result["final_response"],
            "Here is the answer based on WHO guidance.",
        )

    def test_general_query_surfaces_gemini_error_with_retrieved_context(self):
        with patch(
            "src.agents.chatbot.nodes.get_llm",
            side_effect=TimeoutError("simulated timeout details"),
        ):
            result = generation_node({
                "query": "What does WHO say about pH?",
                "retrieved_docs": "Retrieved WHO pH record",
            })

        self.assertIn("Retrieved WHO pH record", result["draft_response"])
        self.assertIn("TimeoutError", result["response_warning"])
        self.assertIn("simulated timeout details", result["response_warning"])
        self.assertIn(result["response_warning"], result["draft_response"])

    def test_transient_primary_failure_uses_gemini_fallback_model(self):
        primary_error = RuntimeError("503 UNAVAILABLE: high demand")
        fallback_llm = SimpleNamespace(
            invoke=lambda prompt: SimpleNamespace(content="Fallback answer.")
        )
        with patch(
            "src.agents.chatbot.nodes.get_llm",
            side_effect=[primary_error, primary_error, fallback_llm],
        ) as get_llm:
            result = generation_node({
                "query": "Explain the retrieved methodology.",
                "methodology_docs": "Methodology facts",
            })

        self.assertEqual(
            [entry.args[0] for entry in get_llm.call_args_list],
            ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite"],
        )
        self.assertIn("Fallback answer.", result["draft_response"])
        self.assertIn("gemini-3.1-flash-lite", result["response_warning"])
        self.assertIn("503 UNAVAILABLE", result["response_warning"])

    def test_all_transient_model_failures_are_reported(self):
        from src.agents.chatbot.nodes import _invoke_gemini

        with patch(
            "src.agents.chatbot.nodes.get_llm",
            side_effect=RuntimeError("503 UNAVAILABLE: high demand"),
        ) as get_llm:
            with self.assertRaisesRegex(RuntimeError, "model sequence") as raised:
                _invoke_gemini("test prompt")

        self.assertEqual(
            [entry.args[0] for entry in get_llm.call_args_list],
            ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite"],
        )
        self.assertIn("gemini-3.8-flash", str(raised.exception))
        self.assertIn("gemini-3.6-flash", str(raised.exception))
        self.assertIn("gemini-3.1-flash-lite", str(raised.exception))

    def test_non_transient_primary_failure_does_not_use_fallback(self):
        with patch(
            "src.agents.chatbot.nodes.get_llm",
            side_effect=ValueError("invalid request"),
        ) as get_llm:
            result = generation_node({
                "query": "Explain the retrieved methodology.",
                "methodology_docs": "Methodology facts",
            })

        get_llm.assert_called_once_with("gemini-3.8-flash")
        self.assertIn("invalid request", result["response_warning"])

    def test_generation_error_redacts_google_api_keys(self):
        from src.agents.chatbot.nodes import _generation_error

        warning = _generation_error(
            RuntimeError("request failed for key=AIza" + "A" * 35)
        )

        self.assertIn("[REDACTED_API_KEY]", warning)
        self.assertNotIn("AIza", warning)

    def test_empty_gemini_response_uses_fallback_and_explains_failure(self):
        with patch(
            "src.agents.chatbot.nodes.get_llm",
            return_value=SimpleNamespace(
                invoke=lambda prompt: SimpleNamespace(content="")
            ),
        ):
            result = generation_node({
                "query": "What does WHO say about pH?",
                "retrieved_docs": "Retrieved WHO pH record",
            })

        self.assertIn("Retrieved WHO pH record", result["draft_response"])
        self.assertIn("empty text response", result["response_warning"])

    def test_report_pH_question_is_answered_without_gemini(self):
        report = """## Table 1: Input Features (Raw Sample Measurements)
| S.No. | Parameter | Unit | Measured Value | Permissible Limit | Remark |
|---|---|---|---|---|---|
| 1 | pH |  | 7.2 | 6.5–8.5 | Within reported limit |
"""
        with patch(
            "src.agents.chatbot.nodes.get_llm",
            side_effect=AssertionError("Gemini should not be needed"),
        ):
            result = report_question_node({
                "query": "What is the pH value of the water sample?",
                "report_context": report,
            })

        self.assertIn("**7.2**", result["final_response"])

    def test_report_probability_table_is_answered_without_gemini(self):
        report = """*3b. Class probability distribution (primary target)*

| Class | Predicted Probability | Rank |
|---|:---:|:---:|
| **Good** | 59.0% | 1 |
"""
        result = _report_fact_answer(
            "What is the class probability distribution?", report
        )
        self.assertIsNotNone(result)
        self.assertIn("59.0%", result)


class ReporterFallbackTests(unittest.TestCase):
    def test_embeddings_accept_google_api_key_name(self):
        created = {}

        class FakeEmbeddings:
            def __init__(self, **kwargs):
                created.update(kwargs)

        fake_module = ModuleType("langchain_google_genai")
        fake_module.GoogleGenerativeAIEmbeddings = FakeEmbeddings
        with (
            patch.dict(
                os.environ,
                {"GOOGLE_API_KEY": "test-key", "GEMINI_API_KEY": ""},
            ),
            patch.dict(sys.modules, {"langchain_google_genai": fake_module}),
        ):
            vector_store._embedder()

        self.assertEqual(created["google_api_key"], "test-key")

    def test_explicit_measurements_skip_gemini_parsing(self):
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}),
            patch(
                "src.agents.reporter.nodes._llm_parse",
                side_effect=AssertionError("explicit readings need no API call"),
            ),
        ):
            result = reporter_nodes.query_parse_node({
                "query": "pH 7.2, TDS 450"
            })

        self.assertEqual(result["sample_data"]["pH"], 7.2)
        self.assertEqual(result["sample_data"]["TDS"], 450.0)

    def test_report_narrative_falls_back_when_gemini_fails(self):
        predictions = {
            "wqi_calculated": 25.0,
            "wqi_category": "Excellent",
            "classification_model": "Gradient Boosting",
            "final_water_quality_class": "Good",
            "classification_confidence": 60.0,
            "microbial_status": "Not reported",
        }
        state = {
            "model_outputs": {"predictions": predictions},
            "violations": [],
            "sample_data": {},
        }
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}),
            patch(
                "src.agents.reporter.nodes.get_llm",
                side_effect=TimeoutError("simulated timeout"),
            ),
        ):
            result = reporter_nodes.narrative_drafting_node(state)
        self.assertIn("WQI of 25.0", result["draft_narrative"])
        self.assertIn("TimeoutError", result["narrative_warning"])
        self.assertIn("TimeoutError", result["narrative_warning"])
        self.assertIn(
            "local model-based summary",
            result["narrative_source"].casefold(),
        )


if __name__ == "__main__":
    unittest.main()
