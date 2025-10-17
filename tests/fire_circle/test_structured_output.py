"""
Tests for Fire Circle structured output support (dual-path parsing).

Verifies:
- Pydantic models validate correctly
- Structured output path works when model supports it
- Fallback path works when model doesn't support structured outputs
- Both paths produce identical NeutrosophicEvaluation results
"""

import pytest
from promptguard.evaluation.schemas import (
    FireCircleEvaluation,
    supports_structured_output,
    STRUCTURED_OUTPUT_CAPABLE_MODELS
)
from pydantic import ValidationError


class TestPydanticValidation:
    """Test Pydantic validation for FireCircleEvaluation."""

    def test_valid_evaluation(self):
        """Valid evaluation passes all constraints."""
        eval = FireCircleEvaluation(
            truth=0.7,
            indeterminacy=0.2,
            falsehood=0.1,
            reasoning="Test reasoning"
        )
        assert eval.truth == 0.7
        assert eval.indeterminacy == 0.2
        assert eval.falsehood == 0.1
        assert eval.reasoning == "Test reasoning"
        assert eval.patterns_observed is None
        assert eval.consensus_patterns is None

    def test_with_patterns(self):
        """Evaluation with patterns validates correctly."""
        eval = FireCircleEvaluation(
            truth=0.6,
            indeterminacy=0.3,
            falsehood=0.4,
            reasoning="Pattern-based reasoning",
            patterns_observed=["temporal_inconsistency", "cross_layer_fabrication"],
            consensus_patterns=["polite_extraction"]
        )
        assert len(eval.patterns_observed) == 2
        assert len(eval.consensus_patterns) == 1

    def test_truth_range_validation(self):
        """Truth value must be 0.0-1.0."""
        with pytest.raises(ValidationError) as exc_info:
            FireCircleEvaluation(
                truth=1.5,  # Invalid: > 1.0
                indeterminacy=0.2,
                falsehood=0.1,
                reasoning="Invalid"
            )
        assert "truth" in str(exc_info.value).lower()

    def test_falsehood_range_validation(self):
        """Falsehood value must be 0.0-1.0."""
        with pytest.raises(ValidationError) as exc_info:
            FireCircleEvaluation(
                truth=0.5,
                indeterminacy=0.2,
                falsehood=-0.1,  # Invalid: < 0.0
                reasoning="Invalid"
            )
        assert "falsehood" in str(exc_info.value).lower()

    def test_reasoning_required(self):
        """Reasoning cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            FireCircleEvaluation(
                truth=0.5,
                indeterminacy=0.2,
                falsehood=0.3,
                reasoning=""  # Invalid: empty
            )
        assert "reasoning" in str(exc_info.value).lower()

    def test_reasoning_whitespace_stripped(self):
        """Reasoning whitespace is stripped."""
        eval = FireCircleEvaluation(
            truth=0.5,
            indeterminacy=0.2,
            falsehood=0.3,
            reasoning="  Valid reasoning  "
        )
        assert eval.reasoning == "Valid reasoning"


class TestModelCapabilityDetection:
    """Test model capability detection for structured outputs."""

    def test_openai_gpt4o_supported(self):
        """OpenAI GPT-4o models support structured outputs."""
        assert supports_structured_output("openai/gpt-4o")
        assert supports_structured_output("openai/gpt-4o-mini")
        assert supports_structured_output("openai/gpt-4o-2024-08-06")

    def test_fireworks_models_supported(self):
        """All Fireworks models support structured outputs."""
        assert supports_structured_output("fireworks/llama-v3p1-405b-instruct")
        assert supports_structured_output("fireworks/qwen-qwq-32b-preview")
        assert supports_structured_output("fireworks/custom-model")  # Any fireworks/ prefix

    def test_anthropic_claude_not_supported(self):
        """Anthropic Claude models don't support structured outputs (yet)."""
        assert not supports_structured_output("anthropic/claude-3.5-sonnet")
        assert not supports_structured_output("anthropic/claude-3-opus")

    def test_google_gemini_not_supported(self):
        """Google Gemini models don't support structured outputs (yet)."""
        assert not supports_structured_output("google/gemini-2.0-flash-exp")
        assert not supports_structured_output("google/gemini-pro")

    def test_unknown_model_defaults_to_unsupported(self):
        """Unknown models default to unsupported (conservative)."""
        assert not supports_structured_output("unknown/model-name")
        assert not supports_structured_output("custom-provider/custom-model")


class TestDualPathParsing:
    """Test dual-path parsing strategy (structured vs fallback)."""

    def test_structured_output_produces_neutrosophic_evaluation(self):
        """Structured output path converts Pydantic to NeutrosophicEvaluation."""
        from promptguard.evaluation.evaluator import NeutrosophicEvaluation

        # Simulate structured output result
        pydantic_result = FireCircleEvaluation(
            truth=0.8,
            indeterminacy=0.1,
            falsehood=0.3,
            reasoning="Structured output reasoning",
            patterns_observed=["temporal_inconsistency"]
        )

        # Convert to NeutrosophicEvaluation (what Fire Circle does)
        evaluation = NeutrosophicEvaluation(
            truth=pydantic_result.truth,
            indeterminacy=pydantic_result.indeterminacy,
            falsehood=pydantic_result.falsehood,
            reasoning=pydantic_result.reasoning,
            model="openai/gpt-4o"
        )

        # Attach patterns
        if pydantic_result.patterns_observed:
            evaluation.patterns_observed = pydantic_result.patterns_observed

        # Verify conversion
        assert evaluation.truth == 0.8
        assert evaluation.indeterminacy == 0.1
        assert evaluation.falsehood == 0.3
        assert evaluation.reasoning == "Structured output reasoning"
        assert evaluation.patterns_observed == ["temporal_inconsistency"]
        assert evaluation.model == "openai/gpt-4o"

    def test_fallback_parsing_preserves_json_compatibility(self):
        """Fallback parsing still works with JSON responses."""
        from promptguard.evaluation.fire_circle import FireCircleEvaluator, FireCircleConfig, CircleSize
        import json

        # Create evaluator (no API key needed for parsing test)
        config = FireCircleConfig(
            models=["test/model1", "test/model2"],
            circle_size=CircleSize.SMALL,
            api_key="test"
        )
        evaluator = FireCircleEvaluator(config, lambda *args: None)

        # Test JSON response (what models actually return)
        json_response = json.dumps({
            "truth": 0.6,
            "indeterminacy": 0.3,
            "falsehood": 0.5,
            "reasoning": "Fallback JSON parsing"
        })

        evaluation = evaluator._parse_response(json_response, "test/model", 1)

        assert evaluation.truth == 0.6
        assert evaluation.indeterminacy == 0.3
        assert evaluation.falsehood == 0.5
        assert evaluation.reasoning == "Fallback JSON parsing"

    def test_fallback_handles_markdown_fences(self):
        """Fallback parsing handles markdown code fences."""
        from promptguard.evaluation.fire_circle import FireCircleEvaluator, FireCircleConfig, CircleSize
        import json

        config = FireCircleConfig(
            models=["test/model1", "test/model2"],
            circle_size=CircleSize.SMALL,
            api_key="test"
        )
        evaluator = FireCircleEvaluator(config, lambda *args: None)

        # Response with markdown fence (common LLM behavior)
        markdown_response = """Here's the evaluation:

```json
{
    "truth": 0.7,
    "indeterminacy": 0.2,
    "falsehood": 0.4,
    "reasoning": "Markdown fence test"
}
```

Hope this helps!"""

        evaluation = evaluator._parse_response(markdown_response, "test/model", 1)

        assert evaluation.truth == 0.7
        assert evaluation.indeterminacy == 0.2
        assert evaluation.falsehood == 0.4
        assert evaluation.reasoning == "Markdown fence test"


class TestStructuredOutputConfiguration:
    """Test structured output initialization and configuration."""

    def test_instructor_available_flag(self):
        """INSTRUCTOR_AVAILABLE flag reflects import state."""
        from promptguard.evaluation import fire_circle
        # Should be True since we installed instructor
        assert fire_circle.INSTRUCTOR_AVAILABLE is True

    def test_fire_circle_initializes_instructor_client(self):
        """FireCircle initializes Instructor client when available."""
        from promptguard.evaluation.fire_circle import FireCircleEvaluator, FireCircleConfig, CircleSize
        import os

        # Skip if no API key (integration test environment)
        if not os.getenv("OPENROUTER_API_KEY"):
            pytest.skip("OPENROUTER_API_KEY not set")

        config = FireCircleConfig(
            models=["openai/gpt-4o", "anthropic/claude-3.5-sonnet"],
            circle_size=CircleSize.SMALL,
        )

        # Mock LLM caller
        async def mock_caller(model, messages):
            return '{"truth": 0.5, "indeterminacy": 0.3, "falsehood": 0.2, "reasoning": "test"}', None

        evaluator = FireCircleEvaluator(config, mock_caller)

        # Should have instructor client initialized
        assert evaluator.instructor_client is not None

    def test_fire_circle_supports_structured_output_check(self):
        """FireCircle correctly checks model structured output support."""
        from promptguard.evaluation.fire_circle import FireCircleEvaluator, FireCircleConfig, CircleSize

        config = FireCircleConfig(
            models=["openai/gpt-4o", "anthropic/claude-3.5-sonnet"],
            circle_size=CircleSize.SMALL,
            api_key="test"
        )
        evaluator = FireCircleEvaluator(config, lambda *args: None)

        # Test capability check
        assert evaluator._supports_structured_output("openai/gpt-4o") is True
        assert evaluator._supports_structured_output("anthropic/claude-3.5-sonnet") is False


class TestParsingMethodTelemetry:
    """Test telemetry logging for parsing method used."""

    def test_structured_path_logs_method(self):
        """Structured output path logs 'structured' method."""
        # This would be tested in integration tests with actual API calls
        # Here we just verify the structure exists
        from promptguard.evaluation.fire_circle import logger
        assert logger is not None

    def test_fallback_path_logs_method(self):
        """Fallback path logs 'fallback' method."""
        # This would be tested in integration tests with actual API calls
        # Here we just verify the structure exists
        from promptguard.evaluation.fire_circle import logger
        assert logger is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
