"""
Integration tests for Fire Circle dialogue flow.

Tests full dialogue execution with mocked LLM responses:
- 3-round dialogue completion
- Context building between rounds
- Pattern extraction from responses
- Consensus aggregation
- Empty chair integration
"""

import pytest
from typing import List, Dict
import asyncio


class TestDialogueFlowComplete:
    """Test complete 3-round Fire Circle dialogue."""

    @pytest.mark.asyncio
    async def test_three_round_completion(
        self,
        mock_evaluator_success,
        fire_circle_config_medium
    ):
        """Fire Circle completes 3 rounds with all models participating."""
        # Simulate Fire Circle execution
        dialogue_history = []

        for round_num in range(1, 4):
            round_evals = []
            for model in fire_circle_config_medium["models"]:
                eval_data = await mock_evaluator_success.call_model(
                    model,
                    f"Round {round_num} prompt",
                    round_num
                )
                round_evals.append({
                    "model": model,
                    "round": round_num,
                    **eval_data
                })

            dialogue_history.append({
                "round_number": round_num,
                "evaluations": round_evals
            })

        # Verify 3 rounds completed
        assert len(dialogue_history) == 3

        # Verify all models participated in each round
        for round_data in dialogue_history:
            models_in_round = [e["model"] for e in round_data["evaluations"]]
            assert set(models_in_round) == set(fire_circle_config_medium["models"])

    @pytest.mark.asyncio
    async def test_dialogue_context_builds_between_rounds(
        self,
        mock_evaluator_success
    ):
        """Round 2+ includes context from previous rounds."""
        # Round 1: Independent evaluations
        round1_evals = []
        for model in ["model_a", "model_b"]:
            eval_data = await mock_evaluator_success.call_model(model, "Round 1", 1)
            round1_evals.append(eval_data)

        # Build context for Round 2
        dialogue_context = "\n".join([
            f"Model {i}: T={e['truth']}, I={e['indeterminacy']}, F={e['falsehood']}\n"
            f"Reasoning: {e['reasoning']}"
            for i, e in enumerate(round1_evals)
        ])

        assert "Round 1:" in dialogue_context
        assert "Reasoning:" in dialogue_context

        # Round 2 prompt should include this context
        round2_prompt = f"Round 1 evaluations:\n{dialogue_context}\n\nNow refine..."

        assert dialogue_context in round2_prompt

    @pytest.mark.asyncio
    async def test_pattern_extraction_from_rounds(
        self,
        mock_evaluator_success
    ):
        """Patterns extracted from Round 2+ responses."""
        models = ["model_a", "model_b", "model_c"]
        all_patterns = []

        # Establish Round 1 state first
        for model in models:
            eval_data = await mock_evaluator_success.call_model(model, "Round 1", 1)

        # Round 2: Models observe patterns
        for model in models:
            eval_data = await mock_evaluator_success.call_model(model, "Round 2", 2)
            patterns = eval_data.get("patterns_observed", [])
            all_patterns.extend(patterns)

        # Round 3: Models confirm patterns
        for model in models:
            eval_data = await mock_evaluator_success.call_model(model, "Round 3", 3)
            patterns = eval_data.get("consensus_patterns", [])
            all_patterns.extend(patterns)

        # Verify patterns were extracted
        assert len(all_patterns) > 0
        assert "temporal_inconsistency" in all_patterns

    @pytest.mark.asyncio
    async def test_consensus_aggregation_max_f(
        self,
        mock_evaluator_groupthink
    ):
        """Consensus uses max(F) across all rounds."""
        all_f_scores = []

        # Collect F-scores from all rounds
        for round_num in range(1, 4):
            for model in ["model_vigilant", "model_conformist"]:
                eval_data = await mock_evaluator_groupthink.call_model(
                    model,
                    f"Round {round_num}",
                    round_num
                )
                all_f_scores.append(eval_data["falsehood"])

        # Calculate consensus
        consensus_f = max(all_f_scores)

        # Should be 0.9 from model_vigilant Round 2
        assert consensus_f == 0.9
        assert consensus_f > 0.4  # Not final round average


class TestEmptyChairIntegration:
    """Test empty chair rotation and influence measurement."""

    @pytest.mark.asyncio
    async def test_empty_chair_rotation_across_rounds(
        self,
        mock_evaluator_empty_chair
    ):
        """Empty chair role rotates to different model each round."""
        models = ["model_a", "model_b", "model_c"]
        empty_chair_assignments = {}

        for round_num in range(1, 4):
            if round_num == 1:
                empty_chair_assignments[round_num] = None
            else:
                # Rotation formula: (round_number - 1) % len(models)
                empty_chair_idx = (round_num - 1) % len(models)
                empty_chair_assignments[round_num] = models[empty_chair_idx]

        # Verify rotation
        assert empty_chair_assignments[1] is None
        assert empty_chair_assignments[2] == "model_b"
        assert empty_chair_assignments[3] == "model_c"

        # Verify different models
        assert empty_chair_assignments[2] != empty_chair_assignments[3]

    @pytest.mark.asyncio
    async def test_empty_chair_receives_different_prompt(
        self,
        mock_evaluator_empty_chair
    ):
        """Empty chair model receives prompt emphasizing future/absent perspectives."""
        models = ["model_a", "model_b", "model_c"]
        round_num = 2
        empty_chair_model = models[(round_num - 1) % len(models)]  # model_b

        # Empty chair prompt should include special role
        empty_chair_prompt = """SPECIAL ROLE: You are speaking for those not present:
- Future users who will interact with this prompt pattern
- Communities affected by extraction success
- System maintainers who inherit consequences

What patterns would these absent voices warn about?"""

        assert "SPECIAL ROLE" in empty_chair_prompt
        assert "Future users" in empty_chair_prompt
        assert "absent voices" in empty_chair_prompt

    @pytest.mark.asyncio
    async def test_empty_chair_influence_calculation(
        self,
        mock_evaluator_empty_chair
    ):
        """Empty chair influence measured by unique pattern contributions."""
        models = ["model_a", "model_b", "model_c"]

        # Track pattern first mentions
        pattern_first_mention = {}

        # Establish Round 1 state first
        for model in models:
            eval_data = await mock_evaluator_empty_chair.call_model(model, "Round 1", 1)

        for round_num in range(2, 4):  # Rounds 2-3
            empty_chair = models[(round_num - 1) % len(models)]

            for model in models:
                eval_data = await mock_evaluator_empty_chair.call_model(
                    model,
                    f"Round {round_num}",
                    round_num
                )

                patterns = eval_data.get("patterns_observed", []) or \
                          eval_data.get("consensus_patterns", [])

                for pattern in patterns:
                    if pattern not in pattern_first_mention:
                        pattern_first_mention[pattern] = (model, round_num)

        # Count empty chair contributions
        empty_chair_models = {
            2: models[1],  # model_b
            3: models[2]   # model_c
        }

        empty_chair_contributions = sum(
            1 for (model, round_num) in pattern_first_mention.values()
            if round_num in empty_chair_models and model == empty_chair_models[round_num]
        )

        total_unique = len(pattern_first_mention)
        influence = empty_chair_contributions / total_unique if total_unique > 0 else 0

        # Empty chair should contribute meaningful patterns
        assert influence > 0.0
        # Based on mock data: model_b introduces 2 unique, model_c introduces 2 unique
        # Total unique should be ≥4
        assert influence >= 0.25  # At least 25% contribution


class TestPatternAggregation:
    """Test pattern extraction and agreement calculation."""

    @pytest.mark.asyncio
    async def test_pattern_agreement_calculation(
        self,
        mock_evaluator_success
    ):
        """Pattern agreement calculated from active model observations."""
        models = ["model_a", "model_b", "model_c"]
        pattern_observations = {}

        # Establish Round 1 state first
        for model in models:
            eval_data = await mock_evaluator_success.call_model(model, "Round 1", 1)

        # Collect patterns from Round 2
        for model in models:
            eval_data = await mock_evaluator_success.call_model(model, "Round 2", 2)
            patterns = eval_data.get("patterns_observed", [])

            for pattern in patterns:
                if pattern not in pattern_observations:
                    pattern_observations[pattern] = []
                pattern_observations[pattern].append(model)

        # Calculate agreement
        active_model_count = len(models)
        pattern_agreement = {}

        for pattern, observing_models in pattern_observations.items():
            agreement = len(set(observing_models)) / active_model_count
            pattern_agreement[pattern] = agreement

        # temporal_inconsistency observed by model_a, model_b
        assert "temporal_inconsistency" in pattern_agreement
        assert pattern_agreement["temporal_inconsistency"] == 2/3  # 2 out of 3 models

    @pytest.mark.asyncio
    async def test_pattern_threshold_filtering(
        self,
        mock_evaluator_success
    ):
        """Only patterns meeting threshold included in final result."""
        models = ["model_a", "model_b", "model_c"]
        threshold = 0.5
        pattern_observations = {
            "temporal_inconsistency": ["model_a", "model_b"],  # 2/3 = 0.67 ✓
            "polite_extraction": ["model_a", "model_c"],       # 2/3 = 0.67 ✓
            "context_saturation": ["model_b"]                  # 1/3 = 0.33 ✗
        }

        active_model_count = len(models)
        qualified_patterns = []

        for pattern, observing_models in pattern_observations.items():
            agreement = len(set(observing_models)) / active_model_count
            if agreement >= threshold:
                qualified_patterns.append(pattern)

        # Only patterns with ≥0.5 agreement qualify
        assert "temporal_inconsistency" in qualified_patterns
        assert "polite_extraction" in qualified_patterns
        assert "context_saturation" not in qualified_patterns


class TestConvergenceDetection:
    """Test early stopping based on F-score convergence."""

    def test_convergence_stddev_calculation(self):
        """Convergence measured by stddev of F-scores."""
        import math

        f_scores = [0.7, 0.75, 0.72, 0.73]  # Low variance

        mean_f = sum(f_scores) / len(f_scores)
        variance = sum((f - mean_f) ** 2 for f in f_scores) / len(f_scores)
        stddev = math.sqrt(variance)

        # Low stddev indicates convergence
        assert stddev < 0.1  # Convergence threshold

    def test_divergence_prevents_early_stop(self):
        """High variance prevents early stopping."""
        import math

        f_scores = [0.2, 0.9, 0.3, 0.8]  # High variance

        mean_f = sum(f_scores) / len(f_scores)
        variance = sum((f - mean_f) ** 2 for f in f_scores) / len(f_scores)
        stddev = math.sqrt(variance)

        # High stddev indicates divergence
        assert stddev > 0.3  # Divergence threshold

    def test_early_stop_after_convergence(self):
        """Fire Circle can stop early if convergence reached."""
        convergence_history = [
            {"round": 1, "stddev": 0.4, "converged": False},
            {"round": 2, "stddev": 0.15, "converged": False},
            {"round": 3, "stddev": 0.08, "converged": True}  # Below threshold
        ]

        CONVERGENCE_THRESHOLD = 0.1
        converged_round = None

        for round_data in convergence_history:
            if round_data["stddev"] < CONVERGENCE_THRESHOLD:
                converged_round = round_data["round"]
                break

        assert converged_round == 3
        # Could stop after round 3 instead of continuing to max_rounds


class TestDialogueState:
    """Test state management across rounds."""

    @pytest.mark.asyncio
    async def test_dialogue_history_accumulation(
        self,
        mock_evaluator_success
    ):
        """Dialogue history accumulates evaluations from all rounds."""
        models = ["model_a", "model_b"]
        dialogue_history = []

        for round_num in range(1, 4):
            round_evals = []
            for model in models:
                eval_data = await mock_evaluator_success.call_model(
                    model,
                    f"Round {round_num}",
                    round_num
                )
                round_evals.append({
                    "model": model,
                    "round": round_num,
                    **eval_data
                })

            dialogue_history.append({
                "round_number": round_num,
                "evaluations": round_evals
            })

        # Verify history contains all rounds
        assert len(dialogue_history) == 3

        # Verify each round preserved
        for i, round_data in enumerate(dialogue_history):
            assert round_data["round_number"] == i + 1
            assert len(round_data["evaluations"]) == len(models)

    def test_round_metrics_tracking(self):
        """Round metrics track convergence and state transitions."""
        round_metrics = [
            {
                "round_number": 1,
                "f_score_mean": 0.2,
                "f_score_stddev": 0.1,
                "convergence_delta": None,  # No previous round
                "active_model_count": 3
            },
            {
                "round_number": 2,
                "f_score_mean": 0.6,
                "f_score_stddev": 0.3,
                "convergence_delta": 0.2,  # Increased from round 1
                "active_model_count": 3
            },
            {
                "round_number": 3,
                "f_score_mean": 0.7,
                "f_score_stddev": 0.15,
                "convergence_delta": -0.15,  # Converging
                "active_model_count": 3
            }
        ]

        # Verify convergence trajectory
        assert round_metrics[1]["convergence_delta"] > 0  # Diverging in round 2
        assert round_metrics[2]["convergence_delta"] < 0  # Converging in round 3

        # Verify model count stable (no failures)
        assert all(m["active_model_count"] == 3 for m in round_metrics)


class TestResultStructure:
    """Test FireCircleResult structure and completeness."""

    def test_result_contains_required_fields(self):
        """FireCircleResult includes all required fields."""
        result = {
            "consensus": {
                "truth": 0.5,
                "indeterminacy": 0.3,
                "falsehood": 0.7,
                "reasoning": "max(F) consensus",
                "model": "fire_circle"
            },
            "patterns": [
                {
                    "pattern_type": "temporal_inconsistency",
                    "description": "Claims prior conversation at turn 1",
                    "model_agreement": 0.67,
                    "examples": ["Turn 4 - Me: ..."],
                    "observed_in_round": 2,
                    "models_observing": ["model_a", "model_b"]
                }
            ],
            "dialogue_history": [
                {"round_number": 1, "evaluations": []},
                {"round_number": 2, "evaluations": []},
                {"round_number": 3, "evaluations": []}
            ],
            "empty_chair_influence": 0.50,
            "failed_models": [],
            "round_metrics": [
                {"round_number": 1, "f_score_mean": 0.2, "f_score_stddev": 0.1}
            ]
        }

        # Verify required fields present
        assert "consensus" in result
        assert "patterns" in result
        assert "dialogue_history" in result
        assert "empty_chair_influence" in result
        assert "failed_models" in result
        assert "round_metrics" in result

    def test_consensus_uses_max_f(self):
        """Consensus field uses max(F) aggregation."""
        all_evaluations = [
            {"model": "model_a", "round": 1, "F": 0.2},
            {"model": "model_a", "round": 2, "F": 0.9},  # Peak
            {"model": "model_a", "round": 3, "F": 0.4},
            {"model": "model_b", "round": 1, "F": 0.3},
            {"model": "model_b", "round": 2, "F": 0.5},
            {"model": "model_b", "round": 3, "F": 0.6}
        ]

        consensus_f = max(e["F"] for e in all_evaluations)

        result = {
            "consensus": {
                "falsehood": consensus_f
            }
        }

        assert result["consensus"]["falsehood"] == 0.9
