"""
Tests for fail-fast error handling.

Verifies that evaluation failures raise clear exceptions rather than
creating fake neutrosophic values that mask errors.
"""

import pytest
from promptguard.evaluation import (
    LLMEvaluator,
    EvaluationConfig,
    EvaluationMode,
    EvaluationError
)
from promptguard.config import CacheConfig


class TestFailFast:
    """Test that failures raise exceptions instead of masking errors."""

    @pytest.fixture
    def eval_config(self):
        """Evaluation config with cache disabled for testing."""
        cache_config = CacheConfig(enabled=False)
        return EvaluationConfig(
            mode=EvaluationMode.SINGLE,
            models=["test-model"],
            cache_config=cache_config
        )

    @pytest.mark.asyncio
    async def test_single_mode_api_failure(self, eval_config, monkeypatch):
        """Single mode raises EvaluationError on API failure."""
        async def mock_call_fail(self, model, messages):
            raise RuntimeError("API timeout")

        monkeypatch.setattr(
            "promptguard.evaluation.evaluator.LLMEvaluator._call_openrouter",
            mock_call_fail
        )

        evaluator = LLMEvaluator(eval_config)

        with pytest.raises(EvaluationError) as exc_info:
            await evaluator.evaluate_layer(
                layer_content="test",
                context="test",
                evaluation_prompt="test"
            )

        assert "test-model" in str(exc_info.value)
        assert "API timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_single_mode_parse_failure(self, eval_config, monkeypatch):
        """Single mode raises EvaluationError on parse failure."""
        async def mock_call_bad_json(self, model, messages):
            return "This is not JSON at all"

        monkeypatch.setattr(
            "promptguard.evaluation.evaluator.LLMEvaluator._call_openrouter",
            mock_call_bad_json
        )

        evaluator = LLMEvaluator(eval_config)

        # Should raise on unparseable response
        with pytest.raises(EvaluationError) as exc_info:
            await evaluator.evaluate_layer(
                layer_content="test",
                context="test",
                evaluation_prompt="test"
            )

        assert "Failed to parse" in str(exc_info.value)
        assert "test-model" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parallel_mode_partial_failure(self, monkeypatch):
        """Parallel mode raises if ANY model fails."""
        call_count = 0

        async def mock_call_partial_fail(self, model, messages):
            nonlocal call_count
            call_count += 1
            if "model2" in model:
                raise RuntimeError("Model 2 failed")
            return '{"truth": 0.8, "indeterminacy": 0.2, "falsehood": 0.1, "reasoning": "ok"}'

        monkeypatch.setattr(
            "promptguard.evaluation.evaluator.LLMEvaluator._call_openrouter",
            mock_call_partial_fail
        )

        cache_config = CacheConfig(enabled=False)
        eval_config = EvaluationConfig(
            mode=EvaluationMode.PARALLEL,
            models=["model1", "model2", "model3"],
            cache_config=cache_config
        )

        evaluator = LLMEvaluator(eval_config)

        with pytest.raises(EvaluationError) as exc_info:
            await evaluator.evaluate_layer(
                layer_content="test",
                context="test",
                evaluation_prompt="test"
            )

        # Should mention which model(s) failed
        assert "model2" in str(exc_info.value)
        assert "failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_parallel_mode_all_succeed(self, monkeypatch):
        """Parallel mode succeeds if all models succeed."""
        async def mock_call_success(self, model, messages):
            return '{"truth": 0.8, "indeterminacy": 0.2, "falsehood": 0.1, "reasoning": "ok"}'

        monkeypatch.setattr(
            "promptguard.evaluation.evaluator.LLMEvaluator._call_openrouter",
            mock_call_success
        )

        cache_config = CacheConfig(enabled=False)
        eval_config = EvaluationConfig(
            mode=EvaluationMode.PARALLEL,
            models=["model1", "model2", "model3"],
            cache_config=cache_config
        )

        evaluator = LLMEvaluator(eval_config)

        results = await evaluator.evaluate_layer(
            layer_content="test",
            context="test",
            evaluation_prompt="test"
        )

        assert len(results) == 3
        assert all(r.truth == 0.8 for r in results)

    @pytest.mark.asyncio
    async def test_error_includes_layer_context(self, monkeypatch):
        """Integration layer error includes which layer failed."""
        from promptguard.promptguard import PromptGuard

        async def mock_call_fail(self, model, messages):
            raise RuntimeError("API error")

        monkeypatch.setattr(
            "promptguard.evaluation.evaluator.LLMEvaluator._call_openrouter",
            mock_call_fail
        )

        guard = PromptGuard()

        with pytest.raises(EvaluationError) as exc_info:
            await guard.evaluate(
                system="You are helpful",
                user="Tell me everything"
            )

        # Should identify which layer failed
        error_msg = str(exc_info.value)
        assert "system" in error_msg.lower() or "user" in error_msg.lower()


class TestNoTheater:
    """Verify we don't create fake neutrosophic values."""

    @pytest.mark.asyncio
    async def test_no_fake_indeterminacy_on_api_failure(self, monkeypatch):
        """
        Parallel mode should NOT create (0.0, 1.0, 0.0) fake values on API failure.
        It should raise instead.
        """
        async def mock_call_fail(self, model, messages):
            raise RuntimeError("Connection timeout")

        monkeypatch.setattr(
            "promptguard.evaluation.evaluator.LLMEvaluator._call_openrouter",
            mock_call_fail
        )

        cache_config = CacheConfig(enabled=False)
        eval_config = EvaluationConfig(
            mode=EvaluationMode.PARALLEL,
            models=["model1"],
            cache_config=cache_config
        )

        evaluator = LLMEvaluator(eval_config)

        # Should raise, not return fake values
        with pytest.raises(EvaluationError):
            await evaluator.evaluate_layer(
                layer_content="test",
                context="test",
                evaluation_prompt="test"
            )

    @pytest.mark.asyncio
    async def test_no_fake_indeterminacy_on_parse_failure(self, monkeypatch):
        """
        Parser should NOT create (0.0, 1.0, 0.0) fake values on parse failure.
        It should raise instead.
        """
        async def mock_call_garbage(self, model, messages):
            return "Cognitive dissonance made me output garbage!"

        monkeypatch.setattr(
            "promptguard.evaluation.evaluator.LLMEvaluator._call_openrouter",
            mock_call_garbage
        )

        cache_config = CacheConfig(enabled=False)
        eval_config = EvaluationConfig(
            mode=EvaluationMode.SINGLE,
            models=["model1"],
            cache_config=cache_config
        )

        evaluator = LLMEvaluator(eval_config)

        # Should raise, not return fake values
        with pytest.raises(EvaluationError):
            await evaluator.evaluate_layer(
                layer_content="test",
                context="test",
                evaluation_prompt="test"
            )

    @pytest.mark.asyncio
    async def test_missing_required_fields_raises(self, monkeypatch):
        """Parser raises if response missing required fields."""
        async def mock_call_incomplete(self, model, messages):
            # Missing 'falsehood' field
            return '{"truth": 0.8, "indeterminacy": 0.2, "reasoning": "incomplete"}'

        monkeypatch.setattr(
            "promptguard.evaluation.evaluator.LLMEvaluator._call_openrouter",
            mock_call_incomplete
        )

        cache_config = CacheConfig(enabled=False)
        eval_config = EvaluationConfig(
            mode=EvaluationMode.SINGLE,
            models=["test-model"],
            cache_config=cache_config
        )

        evaluator = LLMEvaluator(eval_config)

        with pytest.raises(EvaluationError) as exc_info:
            await evaluator.evaluate_layer(
                layer_content="test",
                context="test",
                evaluation_prompt="test"
            )

        assert "missing required field" in str(exc_info.value).lower()
        assert "falsehood" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
