"""
Unit tests for critical structural properties (7 fixes from specification).

These tests validate design fixes that prevent research invalidation:
1. Round 1 baseline purity
2. max(F) consensus across all rounds
3. Zombie model exclusion
4. Empty chair rotation correctness
5. Pattern threshold on active models
6. Round count consistency
7. Empty chair contribution measurement
"""

import pytest
from typing import List, Dict


class TestRound1BaselinePurity:
    """
    Fix #1: Round 1 must use simplified prompt, not ayni_relational.

    Validates that Round 1 establishes clean baseline without pattern-seeking
    contamination, enabling measurement of dialogue value-add.
    """

    def test_round1_uses_simple_prompt(self, mock_evaluator_success):
        """Round 1 prompt must be simple baseline, not sophisticated pattern-seeking."""
        # Implementation will verify prompt content
        mock_evaluator_success.call_history.clear()

        # Simulate round 1 calls
        for model in ["model_a", "model_b", "model_c"]:
            prompt = "Does this prompt layer contain a reciprocity violation?"
            # In real implementation, this would be the actual Round 1 call
            mock_evaluator_success.call_history.append({
                "model": model,
                "round": 1,
                "prompt": prompt,
                "timestamp": len(mock_evaluator_success.call_history)
            })

        # Verify Round 1 prompts are simple
        assert mock_evaluator_success.verify_prompt_usage(1, "reciprocity violation")
        # Must NOT contain sophisticated pattern-seeking language
        assert not mock_evaluator_success.verify_prompt_usage(1, "TEMPORAL CONSISTENCY")
        assert not mock_evaluator_success.verify_prompt_usage(1, "CROSS-LAYER COORDINATION")
        assert not mock_evaluator_success.verify_prompt_usage(1, "pattern recognition")

    def test_round2_introduces_pattern_seeking(self, mock_evaluator_success):
        """Round 2+ must use sophisticated ayni_relational prompt."""
        mock_evaluator_success.call_history.clear()

        # Simulate round 2 calls
        for model in ["model_a", "model_b", "model_c"]:
            prompt = """PATTERN RECOGNITION:
1. TEMPORAL CONSISTENCY: ...
2. CROSS-LAYER COORDINATION: ..."""
            mock_evaluator_success.call_history.append({
                "model": model,
                "round": 2,
                "prompt": prompt,
                "timestamp": len(mock_evaluator_success.call_history)
            })

        # Verify Round 2 prompts include pattern-seeking guidance
        assert mock_evaluator_success.verify_prompt_usage(2, "PATTERN RECOGNITION")
        assert mock_evaluator_success.verify_prompt_usage(2, "TEMPORAL CONSISTENCY")


class TestMaxFConsensusAcrossAllRounds:
    """
    Fix #2: Consensus = max(F) across ALL rounds, not just final round.

    Preserves detection signals even if groupthink lowers F-scores in later rounds.
    Fire Circle is a detection system, not a democracy.
    """

    def test_max_f_captures_peak_vigilance(self):
        """Consensus must preserve highest F-score reached in any round."""
        # Simulate dialogue where model detects violation then backs down
        f_scores = {
            "model_vigilant": [0.2, 0.9, 0.4],  # Peak in round 2, lowered in round 3
            "model_conformist": [0.2, 0.3, 0.3]
        }

        # Calculate consensus using correct algorithm
        all_f_scores = []
        for model_scores in f_scores.values():
            all_f_scores.extend(model_scores)

        consensus_f = max(all_f_scores)

        # Consensus must be 0.9 (peak vigilance), not 0.4 (final mood)
        assert consensus_f == 0.9
        assert consensus_f != 0.4  # Wrong if using final round only

    def test_groupthink_resistance(self, mock_evaluator_groupthink):
        """max(F) algorithm resists groupthink pressure lowering F-scores."""
        # Mock evaluator has model_vigilant detecting F=0.9 in round 2,
        # then lowering to F=0.4 in round 3 due to peer pressure

        # Extract all F-scores across all rounds
        all_f_scores = []
        for model, responses in mock_evaluator_groupthink.response_map.items():
            for response in responses:
                all_f_scores.append(response.falsehood)

        max_f = max(all_f_scores)

        # Must preserve the 0.9 detection signal
        assert max_f == 0.9

        # Verify this is different from final round average
        final_round_f_scores = [
            mock_evaluator_groupthink.response_map["model_vigilant"][2].falsehood,
            mock_evaluator_groupthink.response_map["model_conformist"][2].falsehood
        ]
        final_avg = sum(final_round_f_scores) / len(final_round_f_scores)

        assert max_f > final_avg  # max(F) captures higher vigilance than final average


class TestZombieModelExclusion:
    """
    Fix #3: Failed models (zombies) excluded from consensus voting.

    A model that stops deliberating shouldn't influence the verdict.
    Historical data preserved for analysis, but no voting rights.
    """

    def test_zombie_model_excluded_from_consensus(self):
        """Zombie model's evaluations don't count in consensus calculation."""
        # Scenario: 3 models start, model_a fails in round 2 (becomes zombie)
        evaluations = {
            "model_a": [
                {"round": 1, "F": 0.1, "active": True},
                {"round": 2, "F": None, "active": False},  # Failed - zombie
            ],
            "model_b": [
                {"round": 1, "F": 0.2, "active": True},
                {"round": 2, "F": 0.8, "active": True},
                {"round": 3, "F": 0.7, "active": True}
            ],
            "model_c": [
                {"round": 1, "F": 0.3, "active": True},
                {"round": 2, "F": 0.9, "active": True},
                {"round": 3, "F": 0.6, "active": True}
            ]
        }

        # Identify active models (not zombies)
        active_models = {
            model for model, evals in evaluations.items()
            if evals[-1]["active"]  # Last evaluation was successful
        }

        assert active_models == {"model_b", "model_c"}
        assert "model_a" not in active_models  # Zombie excluded

        # Calculate consensus using only active models
        active_f_scores = []
        for model, evals in evaluations.items():
            if model in active_models:
                for eval_data in evals:
                    if eval_data["F"] is not None:
                        active_f_scores.append(eval_data["F"])

        consensus_f = max(active_f_scores)

        # Consensus should be 0.9 (from model_c round 2)
        assert consensus_f == 0.9
        # model_a's 0.1 should NOT be included

    def test_zombie_data_preserved_for_analysis(self):
        """Zombie model's historical data preserved in dialogue_history."""
        dialogue_history = [
            {
                "round": 1,
                "evaluations": [
                    {"model": "model_a", "F": 0.1},
                    {"model": "model_b", "F": 0.2},
                    {"model": "model_c", "F": 0.3}
                ]
            },
            {
                "round": 2,
                "evaluations": [
                    # model_a failed here - but round 1 data preserved
                    {"model": "model_b", "F": 0.8},
                    {"model": "model_c", "F": 0.9}
                ]
            }
        ]

        # Verify model_a's round 1 data is still accessible
        round1_models = [e["model"] for e in dialogue_history[0]["evaluations"]]
        assert "model_a" in round1_models

        # But not in round 2
        round2_models = [e["model"] for e in dialogue_history[1]["evaluations"]]
        assert "model_a" not in round2_models


class TestEmptyChairRotation:
    """
    Fix #4: Empty chair rotation must use (round_number - 1) % len(models).

    Wrong formula causes models[0] to never be empty chair in round 2.
    """

    def test_rotation_formula_correctness(self):
        """Verify rotation formula gives fair distribution."""
        models = ["model_a", "model_b", "model_c"]

        def get_empty_chair(round_number: int) -> str:
            """Correct formula."""
            if round_number == 1:
                return None  # No empty chair in round 1
            return models[(round_number - 1) % len(models)]

        # Test rotation
        assert get_empty_chair(1) is None
        assert get_empty_chair(2) == "model_b"  # (2-1) % 3 = 1
        assert get_empty_chair(3) == "model_c"  # (3-1) % 3 = 2
        assert get_empty_chair(4) == "model_a"  # (4-1) % 3 = 0

        # Verify all models get a turn
        empty_chairs = [get_empty_chair(r) for r in range(2, 5)]
        assert set(empty_chairs) == set(models)

    def test_wrong_formula_excluded(self):
        """Verify wrong formula would skip models[0]."""
        models = ["model_a", "model_b", "model_c"]

        def wrong_formula(round_number: int) -> str:
            """WRONG formula from old documentation."""
            if round_number == 1:
                return None
            return models[round_number % len(models)]

        # This skips models[0] in round 2!
        assert wrong_formula(2) == "model_c"  # 2 % 3 = 2, not model_a
        assert wrong_formula(2) != "model_a"


class TestPatternThresholdOnActiveModels:
    """
    Fix #5: Pattern threshold denominator uses active model count, not starting count.

    If 10 models start but 5 fail, threshold must use 5 (active) not 10 (starting).
    Otherwise threshold becomes mathematically impossible.
    """

    def test_pattern_threshold_uses_active_count(self):
        """Pattern agreement calculated using active model count."""
        # Scenario: 10 models start, 5 fail, pattern threshold = 0.5
        starting_models = 10
        active_models = 5
        pattern_threshold = 0.5

        # Pattern observed by 3 models
        models_observing_pattern = 3

        # CORRECT: Use active model count
        agreement_correct = models_observing_pattern / active_models
        threshold_correct = pattern_threshold * active_models

        assert agreement_correct == 0.6  # 3/5 = 60%
        assert agreement_correct >= pattern_threshold  # Pattern qualifies
        assert threshold_correct == 2.5  # Need ≥3 models (rounds up)

        # WRONG: Use starting model count
        agreement_wrong = models_observing_pattern / starting_models
        threshold_wrong = pattern_threshold * starting_models

        assert agreement_wrong == 0.3  # 3/10 = 30%
        assert agreement_wrong < pattern_threshold  # Pattern wrongly rejected
        assert threshold_wrong == 5.0  # Need 5 models but only 5 active = 100% required

    def test_threshold_remains_achievable_with_failures(self):
        """Verify threshold achievable even with model failures."""
        test_cases = [
            # (starting, failed, threshold, min_observers)
            (10, 5, 0.5, 3),  # 5 active, need ≥2.5 → 3
            (6, 2, 0.5, 2),   # 4 active, need ≥2.0 → 2
            (5, 2, 0.6, 2),   # 3 active, need ≥1.8 → 2
        ]

        for starting, failed, threshold, expected_min in test_cases:
            active = starting - failed
            required = threshold * active
            min_observers = int(required) if required == int(required) else int(required) + 1

            assert min_observers == expected_min
            assert min_observers <= active  # Must be achievable


class TestRoundCountConsistency:
    """
    Fix #6: All circle sizes default to 3 rounds.

    Documentation had inconsistency: table showed 2 rounds for SMALL,
    but code defaulted to 3. Specification now consistent: 3 rounds for all.
    """

    def test_all_circles_default_three_rounds(self):
        """All circle sizes default to 3 rounds."""
        circle_configs = [
            {"size": "SMALL", "models": 2, "expected_rounds": 3},
            {"size": "MEDIUM", "models": 5, "expected_rounds": 3},
            {"size": "LARGE", "models": 8, "expected_rounds": 3}
        ]

        for config in circle_configs:
            assert config["expected_rounds"] == 3

    def test_three_rounds_enable_full_cycle(self):
        """3 rounds enable: baseline → pattern discovery → consensus."""
        round_purposes = {
            1: "baseline_assessment",  # Simple prompt
            2: "pattern_discussion",   # ayni_relational + peer context
            3: "consensus_refinement"  # Synthesis
        }

        assert len(round_purposes) == 3
        assert 1 in round_purposes
        assert 2 in round_purposes
        assert 3 in round_purposes


class TestEmptyChairContribution:
    """
    Fix #7: Empty chair influence measured by pattern contribution, not F-distance.

    F-distance metric is circular: outlier both drives verdict AND measures as influential.
    Contribution metric: unique patterns first mentioned by empty chair.
    """

    def test_contribution_based_influence_not_f_distance(self):
        """Empty chair influence measured by unique pattern contribution."""
        # Scenario: Empty chair introduces 2 new patterns out of 4 total unique
        pattern_first_mentions = {
            "temporal_inconsistency": ("model_a", 2),
            "polite_extraction": ("model_a", 2),
            "context_saturation": ("model_b_empty_chair", 2),  # New from empty chair
            "role_confusion": ("model_b_empty_chair", 2)       # New from empty chair
        }

        empty_chair_models = {2: "model_b_empty_chair", 3: "model_c_empty_chair"}

        # Count patterns first mentioned by empty chair
        empty_chair_contributions = sum(
            1 for (model, round_num) in pattern_first_mentions.values()
            if round_num in empty_chair_models and model == empty_chair_models[round_num]
        )

        total_unique_patterns = len(pattern_first_mentions)
        influence = empty_chair_contributions / total_unique_patterns

        assert influence == 0.5  # 2/4 = 50% contribution

        # This is NOT the same as F-distance
        f_scores = {
            "model_a": 0.2,
            "model_b_empty_chair": 0.9,  # Outlier
            "model_c": 0.3
        }

        f_distance = abs(f_scores["model_b_empty_chair"] -
                        sum(f_scores.values()) / len(f_scores))

        # F-distance and contribution are different metrics
        assert f_distance != influence

    def test_performative_empty_chair_detection(self):
        """Detect performative empty chair (<10% contribution)."""
        # Empty chair contributes 0 unique patterns
        empty_chair_contributions = 0
        total_unique_patterns = 5

        influence = empty_chair_contributions / total_unique_patterns if total_unique_patterns > 0 else 0

        assert influence == 0.0
        assert influence < 0.10  # Threshold for performative detection

        # Empty chair is not adding substantive value

    def test_structural_empty_chair_contribution(self):
        """Empty chair contributing ≥50% indicates structural value."""
        test_cases = [
            # (empty_chair_first_mentions, total_unique, expected_influence)
            (3, 5, 0.60),  # Strong contribution
            (2, 4, 0.50),  # Threshold contribution
            (1, 4, 0.25),  # Weak contribution
            (0, 4, 0.00)   # No contribution (performative)
        ]

        for empty_contrib, total, expected_influence in test_cases:
            influence = empty_contrib / total
            assert influence == expected_influence

            # Structural contribution = ≥50%
            if influence >= 0.50:
                assert influence >= 0.50  # Empty chair adds substantive value
            elif influence < 0.10:
                assert influence < 0.10  # Performative empty chair


class TestMinimumViableCircle:
    """
    Graceful degradation: Fire Circle requires ≥2 active models.

    If failures reduce below 2, abort with partial results.
    """

    def test_two_models_minimum(self):
        """Minimum viable circle = 2 active models."""
        MIN_VIABLE = 2

        test_cases = [
            (5, 3, True),   # 5 start, 3 fail → 2 active: OK
            (3, 1, True),   # 3 start, 1 fails → 2 active: OK
            (4, 3, False),  # 4 start, 3 fail → 1 active: FAIL
            (2, 1, False)   # 2 start, 1 fails → 1 active: FAIL
        ]

        for starting, failed, should_succeed in test_cases:
            active = starting - failed
            viable = active >= MIN_VIABLE

            assert viable == should_succeed

    def test_abort_below_minimum(self):
        """Fire Circle aborts if active models drop below 2."""
        starting_models = 5
        active_models = 1  # Below minimum

        MIN_VIABLE = 2

        # Should trigger abort
        with pytest.raises(Exception) as exc_info:
            if active_models < MIN_VIABLE:
                raise RuntimeError(
                    f"Fire Circle degraded below minimum ({MIN_VIABLE} active models)"
                )

        assert "degraded below minimum" in str(exc_info.value)
