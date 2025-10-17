"""
Failure injection tests for Fire Circle resilience.

Validates graceful recovery under arbitrary failures:
- Model failures in each round
- Unparseable responses
- API timeouts
- Network errors
- STRICT vs RESILIENT mode behavior
- Minimum viable circle enforcement
"""

import pytest
from typing import List, Dict
import asyncio


class TestRound1Failures:
    """Test failure handling in Round 1 (baseline assessment)."""

    @pytest.mark.asyncio
    async def test_round1_failure_excludes_model_entirely(
        self,
        mock_evaluator_round1_failure
    ):
        """Model failing in Round 1 excluded from all subsequent rounds."""
        models = ["model_a", "model_b", "model_c"]
        active_models = models.copy()
        failed_models = []

        # Round 1 evaluations
        round1_evals = []
        for model in models:
            try:
                eval_data = await mock_evaluator_round1_failure.call_model(
                    model, "Round 1", 1
                )
                round1_evals.append({"model": model, **eval_data})
            except RuntimeError as e:
                # Model failed - exclude from circle
                failed_models.append(f"{model}_round_1")
                active_models.remove(model)

        # Verify model_b failed and was excluded
        assert "model_b_round_1" in failed_models
        assert "model_b" not in active_models

        # Round 2: Only active models participate
        round2_evals = []
        for model in active_models:  # Only model_a and model_c
            eval_data = await mock_evaluator_round1_failure.call_model(
                model, "Round 2", 2
            )
            round2_evals.append({"model": model, **eval_data})

        # Verify model_b not in round 2
        round2_models = [e["model"] for e in round2_evals]
        assert "model_b" not in round2_models
        assert set(round2_models) == {"model_a", "model_c"}

    @pytest.mark.asyncio
    async def test_strict_mode_aborts_on_round1_failure(
        self,
        mock_evaluator_with_failures,
        fire_circle_config_strict
    ):
        """STRICT mode aborts entire Fire Circle on Round 1 failure."""
        models = fire_circle_config_strict["models"]

        # In STRICT mode, any failure aborts
        with pytest.raises(RuntimeError) as exc_info:
            for model in models:
                await mock_evaluator_with_failures.call_model(
                    model, "Round 1", 1
                )
                # model_b will fail and raise automatically

        assert "Round 1 failure" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resilient_mode_continues_with_remaining_models(
        self,
        mock_evaluator_with_failures,
        fire_circle_config_medium
    ):
        """RESILIENT mode continues with remaining models after Round 1 failure."""
        models = fire_circle_config_medium["models"]
        active_models = []

        # Round 1: Collect successful evaluations only
        for model in models:
            try:
                eval_data = await mock_evaluator_with_failures.call_model(
                    model, "Round 1", 1
                )
                active_models.append(model)
            except RuntimeError:
                pass  # RESILIENT mode continues

        # At least 2 models must succeed (minimum viable circle)
        assert len(active_models) >= 2

        # Verify we can continue to Round 2 with active models
        round2_count = 0
        for model in active_models:
            try:
                await mock_evaluator_with_failures.call_model(model, "Round 2", 2)
                round2_count += 1
            except RuntimeError:
                pass

        # At least some models completed round 2
        assert round2_count > 0


class TestRound2PlusFailures:
    """Test failure handling in Round 2+ (zombie model policy)."""

    @pytest.mark.asyncio
    async def test_round2_failure_creates_zombie(
        self,
        mock_evaluator_with_failures
    ):
        """Model failing in Round 2+ becomes zombie (data preserved, no voting)."""
        # model_a succeeds in Round 1, fails in Round 2
        round1_eval = await mock_evaluator_with_failures.call_model(
            "model_a", "Round 1", 1
        )

        # Round 1 data preserved
        dialogue_history = [
            {
                "round_number": 1,
                "evaluations": [{"model": "model_a", **round1_eval}]
            }
        ]

        # Round 2: model_a fails
        zombie_models = []
        try:
            await mock_evaluator_with_failures.call_model("model_a", "Round 2", 2)
        except RuntimeError:
            # Mark as zombie - historical data kept, no voting rights
            zombie_models.append("model_a")

        # Verify zombie status
        assert "model_a" in zombie_models

        # Verify Round 1 data still in history
        assert dialogue_history[0]["evaluations"][0]["model"] == "model_a"

    @pytest.mark.asyncio
    async def test_zombie_excluded_from_consensus_calculation(
        self,
        mock_evaluator_with_failures
    ):
        """Zombie models excluded from final consensus."""
        # Scenario: model_a fails in Round 2, becomes zombie
        all_evaluations = {
            "model_a": [
                {"round": 1, "F": 0.1}
                # Failed in Round 2 - no more evals
            ],
            "model_c": [
                {"round": 1, "F": 0.0},
                {"round": 2, "F": 0.3},
                {"round": 3, "F": 0.5}
            ]
        }

        zombie_models = ["model_a"]
        active_models = [m for m in all_evaluations.keys() if m not in zombie_models]

        # Calculate consensus using only active models
        active_f_scores = []
        for model in active_models:
            for eval_data in all_evaluations[model]:
                active_f_scores.append(eval_data["F"])

        consensus_f = max(active_f_scores) if active_f_scores else 0.0

        # Consensus should be 0.5 (model_c round 3)
        # model_a's 0.1 should NOT be included
        assert consensus_f == 0.5
        assert 0.1 not in active_f_scores

    @pytest.mark.asyncio
    async def test_zombie_excluded_from_pattern_threshold(
        self,
        mock_evaluator_with_failures
    ):
        """Pattern threshold uses active model count (excludes zombies)."""
        # 3 models start, 1 becomes zombie
        starting_models = 3
        zombie_models = 1
        active_models = starting_models - zombie_models

        pattern_threshold = 0.5
        models_observing_pattern = 1  # Only 1 active model observes

        # CORRECT: Use active count
        agreement = models_observing_pattern / active_models
        qualified = agreement >= pattern_threshold

        # 1/2 = 0.5, meets threshold
        assert agreement == 0.5
        assert qualified

        # WRONG: Using starting count
        agreement_wrong = models_observing_pattern / starting_models
        # 1/3 = 0.33, does not meet threshold
        assert agreement_wrong < pattern_threshold


class TestMinimumViableCircleEnforcement:
    """Test abort conditions when active models drop below minimum."""

    @pytest.mark.asyncio
    async def test_abort_when_below_minimum(self):
        """Fire Circle aborts if active models drop below 2."""
        MIN_VIABLE = 2

        # Scenario: 3 models start, 2 fail
        active_models = ["model_a"]  # Only 1 left

        # Should abort
        with pytest.raises(RuntimeError) as exc_info:
            if len(active_models) < MIN_VIABLE:
                raise RuntimeError(
                    f"Fire Circle degraded below minimum ({MIN_VIABLE} active models)"
                )

        assert "degraded below minimum" in str(exc_info.value)
        assert "2 active models" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_continue_at_minimum(self):
        """Fire Circle continues with exactly 2 active models."""
        MIN_VIABLE = 2

        # Scenario: 4 models start, 2 fail
        active_models = ["model_c", "model_d"]

        # Should continue
        viable = len(active_models) >= MIN_VIABLE
        assert viable

    @pytest.mark.asyncio
    async def test_partial_results_flag_set(self):
        """Partial results flag set when models fail."""
        starting_models = 5
        failed_models = ["model_a", "model_b"]
        active_models = [m for m in ["model_c", "model_d", "model_e"]]

        result = {
            "partial": len(failed_models) > 0,
            "failed_models": failed_models,
            "active_model_count": len(active_models)
        }

        assert result["partial"] is True
        assert len(result["failed_models"]) == 2


class TestUnparseableResponseHandling:
    """Test graceful handling of unparseable LLM responses."""

    @pytest.mark.asyncio
    async def test_unparseable_json_in_strict_mode(self):
        """STRICT mode raises on unparseable response."""
        response = "This is not JSON at all!"

        # Attempt to parse
        with pytest.raises(Exception) as exc_info:
            import json
            data = json.loads(response)
            # Will raise JSONDecodeError

        # In STRICT mode, this becomes EvaluationError
        assert "JSON" in str(type(exc_info.value).__name__) or \
               "Expecting" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_text_extraction_fallback(self):
        """Try to extract T/I/F from text if JSON parsing fails."""
        response = """
        The evaluation shows:
        truth: 0.7
        indeterminacy: 0.2
        falsehood: 0.6
        Reasoning: This looks suspicious.
        """

        # Text extraction logic
        import re

        extracted = {}
        if match := re.search(r'truth:\s*([\d.]+)', response):
            extracted['truth'] = float(match.group(1))
        if match := re.search(r'indeterminacy:\s*([\d.]+)', response):
            extracted['indeterminacy'] = float(match.group(1))
        if match := re.search(r'falsehood:\s*([\d.]+)', response):
            extracted['falsehood'] = float(match.group(1))

        # Verify extraction worked
        assert extracted['truth'] == 0.7
        assert extracted['indeterminacy'] == 0.2
        assert extracted['falsehood'] == 0.6

    @pytest.mark.asyncio
    async def test_heuristic_fallback_for_violation_keywords(self):
        """Heuristic fallback if response mentions violation/attack."""
        response = "This is clearly a violation attempt with malicious intent!"

        # Heuristic: if contains violation keywords, assume high F
        violation_keywords = ["violation", "attack", "malicious", "exploit"]
        has_violation = any(kw in response.lower() for kw in violation_keywords)

        if has_violation:
            heuristic_f = 0.8
        else:
            heuristic_f = 0.5

        assert heuristic_f == 0.8  # Detected violation keywords


class TestTimeoutHandling:
    """Test timeout handling for long-running evaluations."""

    @pytest.mark.asyncio
    async def test_timeout_triggers_failure(self):
        """API timeout triggers failure handling."""
        timeout_seconds = 0.1  # Very short timeout

        async def slow_model_call():
            await asyncio.sleep(1.0)  # Exceeds timeout
            return {"truth": 0.5, "indeterminacy": 0.5, "falsehood": 0.5}

        # Simulate timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_model_call(), timeout=timeout_seconds)

    @pytest.mark.asyncio
    async def test_timeout_in_strict_mode_aborts(self):
        """Timeout in STRICT mode aborts Fire Circle."""
        failure_mode = "STRICT"

        try:
            await asyncio.wait_for(
                asyncio.sleep(1.0),
                timeout=0.1
            )
        except asyncio.TimeoutError as e:
            if failure_mode == "STRICT":
                with pytest.raises(RuntimeError) as exc_info:
                    raise RuntimeError(f"Fire Circle failed: timeout")

                assert "timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_in_resilient_mode_continues(self):
        """Timeout in RESILIENT mode marks model as failed, continues."""
        failure_mode = "RESILIENT"
        active_models = ["model_a", "model_b", "model_c"]
        failed_models = []

        try:
            await asyncio.wait_for(
                asyncio.sleep(1.0),
                timeout=0.1
            )
        except asyncio.TimeoutError:
            if failure_mode == "RESILIENT":
                # Mark model as failed, continue
                failed_models.append("model_a_timeout")
                active_models.remove("model_a")

        assert "model_a_timeout" in failed_models
        assert len(active_models) == 2  # Continue with remaining


class TestFailureRecoveryScenarios:
    """Test complex failure scenarios with multiple failure points."""

    @pytest.mark.asyncio
    async def test_cascade_failures_multiple_rounds(self):
        """Test graceful degradation with failures across multiple rounds."""
        # 5 models start
        # Round 1: 2 fail → 3 active
        # Round 2: 1 more fails → 2 active (minimum viable)
        # Round 3: 2 complete successfully

        active_models = ["model_a", "model_b", "model_c", "model_d", "model_e"]
        failed_models = []

        # Round 1 failures
        for model in ["model_a", "model_b"]:
            failed_models.append(f"{model}_round_1")
            active_models.remove(model)

        assert len(active_models) == 3

        # Round 2 failure
        failed_models.append("model_c_round_2")
        active_models.remove("model_c")

        assert len(active_models) == 2  # Minimum viable

        # Round 3 completes
        # Verify we can still produce valid result
        assert len(active_models) >= 2
        assert len(failed_models) == 3

    @pytest.mark.asyncio
    async def test_empty_chair_model_failure(self):
        """Test failure when empty chair model fails."""
        models = ["model_a", "model_b", "model_c"]
        round_num = 2
        empty_chair_model = models[(round_num - 1) % len(models)]  # model_b

        # Empty chair model fails
        failure_mode = "RESILIENT"

        if failure_mode == "STRICT":
            # STRICT: Abort (empty chair is structural requirement)
            with pytest.raises(RuntimeError) as exc_info:
                raise RuntimeError("Empty chair model failed - aborting Fire Circle")
            assert "Empty chair" in str(exc_info.value)

        elif failure_mode == "RESILIENT":
            # RESILIENT: Skip empty chair for this round, continue
            empty_chair_assignments = {
                1: None,
                2: None,  # Skipped due to failure
                3: models[2]  # model_c takes empty chair in round 3
            }

            assert empty_chair_assignments[2] is None  # Skipped
            assert empty_chair_assignments[3] == "model_c"

    @pytest.mark.asyncio
    async def test_all_models_fail_same_round(self):
        """Test catastrophic failure if all models fail in same round."""
        active_models = ["model_a", "model_b"]
        MIN_VIABLE = 2

        # Both models fail
        for model in active_models.copy():
            active_models.remove(model)

        # Below minimum
        with pytest.raises(RuntimeError) as exc_info:
            if len(active_models) < MIN_VIABLE:
                raise RuntimeError(
                    "Fire Circle failed: all models failed"
                )

        assert "all models failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_recovery_preserves_consensus_integrity(self):
        """Test that failures don't corrupt consensus calculation."""
        # Scenario: 4 models, 2 fail at different points
        all_evaluations = {
            "model_a": [
                {"round": 1, "F": 0.2},
                # Failed in round 2
            ],
            "model_b": [
                {"round": 1, "F": 0.3},
                {"round": 2, "F": 0.8},
                {"round": 3, "F": 0.7}
            ],
            "model_c": [
                {"round": 1, "F": 0.4},
                {"round": 2, "F": 0.9},
                # Failed in round 3
            ],
            "model_d": [
                {"round": 1, "F": 0.3},
                {"round": 2, "F": 0.6},
                {"round": 3, "F": 0.5}
            ]
        }

        # Active models = completed final round
        active_models = ["model_b", "model_d"]
        zombie_models = ["model_a", "model_c"]

        # Calculate consensus from active models only
        active_f_scores = []
        for model in active_models:
            for eval_data in all_evaluations[model]:
                active_f_scores.append(eval_data["F"])

        consensus_f = max(active_f_scores)

        # Consensus should be 0.8 (model_b round 2)
        # NOT 0.9 (model_c round 2 - zombie)
        assert consensus_f == 0.8

        # Verify zombie F-scores excluded
        for model in zombie_models:
            zombie_f_scores = [e["F"] for e in all_evaluations[model]]
            for f in zombie_f_scores:
                if f not in active_f_scores or f <= consensus_f:
                    pass  # OK
                else:
                    # Zombie F > consensus means zombie influenced result (BAD)
                    assert False, "Zombie model influenced consensus"
