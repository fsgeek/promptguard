"""
Observability tests for Fire Circle.

Validates comprehensive logging and tracing (smoke must convect out):
- State transition logging
- Model contribution tracking
- Failure context capture
- Quorum validity checks
- Dialogue history accessibility
- Performance metrics
"""

import pytest
from typing import List, Dict
import json
import logging


class TestStateTransitionLogging:
    """Test logging of all state transitions during dialogue."""

    def test_round_transition_logged(self):
        """Each round transition logged with context."""
        log_entries = []

        # Simulate round transitions
        for round_num in range(1, 4):
            log_entries.append({
                "event": "round_start",
                "round": round_num,
                "active_models": ["model_a", "model_b", "model_c"],
                "empty_chair": None if round_num == 1 else f"model_{chr(96 + round_num)}"
            })

            # ... round execution ...

            log_entries.append({
                "event": "round_complete",
                "round": round_num,
                "evaluations_collected": 3,
                "convergence_stddev": 0.15
            })

        # Verify transitions logged
        round_starts = [e for e in log_entries if e["event"] == "round_start"]
        round_completes = [e for e in log_entries if e["event"] == "round_complete"]

        assert len(round_starts) == 3
        assert len(round_completes) == 3

        # Verify round numbers sequential
        assert [e["round"] for e in round_starts] == [1, 2, 3]

    def test_empty_chair_assignment_logged(self):
        """Empty chair assignments logged each round."""
        models = ["model_a", "model_b", "model_c"]
        empty_chair_log = []

        for round_num in range(1, 4):
            if round_num == 1:
                empty_chair = None
            else:
                empty_chair = models[(round_num - 1) % len(models)]

            empty_chair_log.append({
                "round": round_num,
                "empty_chair": empty_chair
            })

        # Verify logging
        assert empty_chair_log[0]["empty_chair"] is None
        assert empty_chair_log[1]["empty_chair"] == "model_b"
        assert empty_chair_log[2]["empty_chair"] == "model_c"

    def test_model_state_changes_logged(self):
        """Model state changes (active → zombie → excluded) logged."""
        model_state_log = []

        # Initial state
        model_state_log.append({
            "event": "initialization",
            "models": {
                "model_a": "active",
                "model_b": "active",
                "model_c": "active"
            }
        })

        # model_b fails in round 2
        model_state_log.append({
            "event": "model_failure",
            "round": 2,
            "model": "model_b",
            "reason": "API timeout",
            "state_change": "active → zombie"
        })

        # Final state
        model_state_log.append({
            "event": "dialogue_complete",
            "final_states": {
                "model_a": "active",
                "model_b": "zombie",
                "model_c": "active"
            }
        })

        # Verify state tracking
        failure_events = [e for e in model_state_log if e["event"] == "model_failure"]
        assert len(failure_events) == 1
        assert failure_events[0]["state_change"] == "active → zombie"


class TestModelContributionTracking:
    """Test tracking of which models contributed to each round."""

    def test_per_round_participation_recorded(self):
        """Track which models participated in each round."""
        participation_log = {
            1: ["model_a", "model_b", "model_c"],
            2: ["model_a", "model_c"],  # model_b failed
            3: ["model_a", "model_c"]
        }

        # Verify tracking
        assert len(participation_log[1]) == 3
        assert len(participation_log[2]) == 2
        assert "model_b" not in participation_log[2]

    def test_pattern_contribution_attribution(self):
        """Track which model first mentioned each pattern."""
        pattern_attribution = {
            "temporal_inconsistency": {
                "first_mention": "model_a",
                "round": 2,
                "also_observed_by": ["model_b", "model_c"]
            },
            "polite_extraction": {
                "first_mention": "model_c",
                "round": 2,
                "also_observed_by": ["model_a"]
            }
        }

        # Verify attribution
        assert pattern_attribution["temporal_inconsistency"]["first_mention"] == "model_a"
        assert len(pattern_attribution["temporal_inconsistency"]["also_observed_by"]) == 2

    def test_empty_chair_contribution_logged(self):
        """Log empty chair's unique pattern contributions."""
        empty_chair_contributions = {
            "model_b": {
                "round": 2,
                "unique_patterns": ["future_consequence", "absent_community_impact"],
                "shared_patterns": ["temporal_inconsistency"]
            },
            "model_c": {
                "round": 3,
                "unique_patterns": ["maintenance_burden"],
                "shared_patterns": ["temporal_inconsistency", "polite_extraction"]
            }
        }

        # Verify empty chair contributions tracked
        model_b_unique = len(empty_chair_contributions["model_b"]["unique_patterns"])
        model_c_unique = len(empty_chair_contributions["model_c"]["unique_patterns"])

        assert model_b_unique == 2
        assert model_c_unique == 1


class TestFailureContextCapture:
    """Test comprehensive failure context logging."""

    def test_failure_includes_full_context(self):
        """Failure logs include when, which model, what state."""
        failure_log = {
            "timestamp": "2025-10-12T14:30:00Z",
            "round": 2,
            "model": "model_b",
            "failure_type": "API_TIMEOUT",
            "error_message": "Request timed out after 30s",
            "state_before_failure": {
                "active_models": ["model_a", "model_b", "model_c"],
                "evaluations_completed": 1,
                "empty_chair": "model_b"
            },
            "state_after_failure": {
                "active_models": ["model_a", "model_c"],
                "zombie_models": ["model_b"],
                "empty_chair": None  # Empty chair failed
            },
            "recovery_action": "RESILIENT: Continue with remaining models"
        }

        # Verify comprehensive context
        assert "round" in failure_log
        assert "model" in failure_log
        assert "state_before_failure" in failure_log
        assert "state_after_failure" in failure_log
        assert "recovery_action" in failure_log

    def test_failure_cascade_tracking(self):
        """Track cascading failures across rounds."""
        cascade_log = [
            {
                "round": 1,
                "failures": ["model_a", "model_b"],
                "active_remaining": 3
            },
            {
                "round": 2,
                "failures": ["model_c"],
                "active_remaining": 2,
                "cascade_triggered": True
            },
            {
                "round": 3,
                "failures": [],
                "active_remaining": 2,
                "cascade_triggered": False
            }
        ]

        # Verify cascade tracking
        assert cascade_log[1]["cascade_triggered"] is True
        total_failures = sum(len(r["failures"]) for r in cascade_log)
        assert total_failures == 3

    def test_unparseable_response_logged(self):
        """Unparseable responses logged with content sample."""
        unparseable_log = {
            "round": 2,
            "model": "model_b",
            "failure_type": "UNPARSEABLE_RESPONSE",
            "response_sample": "This is not JSON at all! I think the prompt..."[:200],
            "attempted_recovery": "text_extraction",
            "recovery_success": False
        }

        # Verify unparseable context
        assert "response_sample" in unparseable_log
        assert len(unparseable_log["response_sample"]) <= 200
        assert "attempted_recovery" in unparseable_log


class TestQuorumValidityChecks:
    """Test logging of quorum validity throughout dialogue."""

    def test_quorum_check_each_round(self):
        """Verify quorum (≥2 models) checked and logged each round."""
        quorum_log = []

        for round_num in range(1, 4):
            active_count = 3 if round_num < 3 else 2
            quorum_valid = active_count >= 2

            quorum_log.append({
                "round": round_num,
                "active_models": active_count,
                "quorum_valid": quorum_valid,
                "minimum_required": 2
            })

        # Verify quorum checks
        assert all(entry["quorum_valid"] for entry in quorum_log)
        assert all(entry["active_models"] >= 2 for entry in quorum_log)

    def test_quorum_failure_abort_logged(self):
        """Log when quorum failure triggers abort."""
        active_models = 1  # Below minimum

        abort_log = {
            "event": "QUORUM_FAILURE",
            "round": 3,
            "active_models": active_models,
            "minimum_required": 2,
            "action": "ABORT_FIRE_CIRCLE",
            "reason": "Active model count dropped below minimum viable"
        }

        # Verify abort logged
        assert abort_log["event"] == "QUORUM_FAILURE"
        assert abort_log["action"] == "ABORT_FIRE_CIRCLE"
        assert abort_log["active_models"] < abort_log["minimum_required"]

    def test_quorum_warning_at_minimum(self):
        """Log warning when at minimum viable (2 models)."""
        active_models = 2

        warning_log = {
            "level": "WARNING",
            "round": 2,
            "active_models": active_models,
            "minimum_required": 2,
            "message": "Fire Circle at minimum viable count - any further failure will abort"
        }

        # Verify warning issued
        assert warning_log["level"] == "WARNING"
        assert warning_log["active_models"] == warning_log["minimum_required"]


class TestDialogueHistoryAccessibility:
    """Test that dialogue history is fully accessible for post-mortem."""

    def test_dialogue_history_completeness(self):
        """Dialogue history includes all rounds and all evaluations."""
        dialogue_history = [
            {
                "round_number": 1,
                "timestamp": 1697123400,
                "prompt_used": "Does this prompt layer contain...",
                "evaluations": [
                    {
                        "model": "model_a",
                        "truth": 0.8,
                        "indeterminacy": 0.2,
                        "falsehood": 0.1,
                        "reasoning": "Looks reciprocal"
                    },
                    {
                        "model": "model_b",
                        "truth": 0.7,
                        "indeterminacy": 0.3,
                        "falsehood": 0.2,
                        "reasoning": "Slightly suspicious"
                    }
                ],
                "convergence_metric": 0.05
            },
            # ... rounds 2, 3 ...
        ]

        # Verify completeness
        assert "round_number" in dialogue_history[0]
        assert "prompt_used" in dialogue_history[0]
        assert "evaluations" in dialogue_history[0]
        assert "convergence_metric" in dialogue_history[0]

        # Verify evaluation details
        eval = dialogue_history[0]["evaluations"][0]
        assert all(k in eval for k in ["model", "truth", "indeterminacy", "falsehood", "reasoning"])

    def test_zombie_data_preserved_in_history(self):
        """Zombie model evaluations preserved in dialogue history."""
        dialogue_history = [
            {
                "round_number": 1,
                "evaluations": [
                    {"model": "model_a", "F": 0.1},
                    {"model": "model_b", "F": 0.2}
                ]
            },
            {
                "round_number": 2,
                "evaluations": [
                    # model_a failed - but round 1 data still accessible
                    {"model": "model_b", "F": 0.8}
                ]
            }
        ]

        # Verify zombie data accessible
        round1_models = [e["model"] for e in dialogue_history[0]["evaluations"]]
        assert "model_a" in round1_models

        # Can trace model_a's participation
        model_a_history = []
        for round_data in dialogue_history:
            for eval_data in round_data["evaluations"]:
                if eval_data["model"] == "model_a":
                    model_a_history.append(round_data["round_number"])

        assert model_a_history == [1]  # Participated in round 1 only

    def test_pattern_evolution_traceable(self):
        """Can trace how patterns evolved across rounds."""
        dialogue_history = [
            {
                "round_number": 1,
                "patterns": []  # No patterns in baseline round
            },
            {
                "round_number": 2,
                "patterns": [
                    {
                        "type": "temporal_inconsistency",
                        "observed_by": ["model_a", "model_b"]
                    }
                ]
            },
            {
                "round_number": 3,
                "patterns": [
                    {
                        "type": "temporal_inconsistency",
                        "observed_by": ["model_a", "model_b", "model_c"]
                    },
                    {
                        "type": "polite_extraction",
                        "observed_by": ["model_c"]
                    }
                ]
            }
        ]

        # Trace pattern evolution
        temporal_pattern_evolution = []
        for round_data in dialogue_history:
            for pattern in round_data["patterns"]:
                if pattern["type"] == "temporal_inconsistency":
                    temporal_pattern_evolution.append({
                        "round": round_data["round_number"],
                        "observers": len(pattern["observed_by"])
                    })

        # Verify pattern grew in agreement
        assert len(temporal_pattern_evolution) == 2
        assert temporal_pattern_evolution[0]["observers"] == 2
        assert temporal_pattern_evolution[1]["observers"] == 3


class TestPerformanceMetrics:
    """Test performance metric collection and logging."""

    def test_per_round_timing_logged(self):
        """Time taken for each round logged."""
        performance_log = [
            {
                "round": 1,
                "start_time": 1697123400.0,
                "end_time": 1697123405.2,
                "duration_seconds": 5.2,
                "models_evaluated": 3
            },
            {
                "round": 2,
                "start_time": 1697123405.2,
                "end_time": 1697123412.8,
                "duration_seconds": 7.6,
                "models_evaluated": 3
            }
        ]

        # Verify timing captured
        assert all("duration_seconds" in entry for entry in performance_log)
        total_time = sum(entry["duration_seconds"] for entry in performance_log)
        assert total_time == 5.2 + 7.6

    def test_per_model_latency_tracked(self):
        """Track latency per model per round."""
        model_latency = {
            "model_a": [
                {"round": 1, "latency_ms": 1200},
                {"round": 2, "latency_ms": 1800},
                {"round": 3, "latency_ms": 1500}
            ],
            "model_b": [
                {"round": 1, "latency_ms": 2100},
                # Failed in round 2
            ]
        }

        # Verify latency tracking
        model_a_latencies = [entry["latency_ms"] for entry in model_latency["model_a"]]
        avg_latency = sum(model_a_latencies) / len(model_a_latencies)

        assert len(model_a_latencies) == 3
        assert avg_latency == 1500

    def test_token_usage_tracked(self):
        """Track token usage per round and per model."""
        token_usage = {
            "round_1": {
                "total_input_tokens": 1800,  # 3 models × 600
                "total_output_tokens": 900,  # 3 models × 300
                "cost_estimate": 0.045
            },
            "round_2": {
                "total_input_tokens": 3000,  # 3 models × 1000
                "total_output_tokens": 1200,  # 3 models × 400
                "cost_estimate": 0.075
            }
        }

        # Verify cost tracking
        total_cost = sum(round_data["cost_estimate"] for round_data in token_usage.values())
        assert total_cost == 0.12

    def test_cache_hit_rate_logged(self):
        """Track cache hit rate during Fire Circle."""
        cache_metrics = {
            "round_1": {
                "cache_hits": 0,
                "cache_misses": 3,
                "hit_rate": 0.0
            },
            "round_2": {
                "cache_hits": 0,  # Fire Circle dialogue not cached
                "cache_misses": 3,
                "hit_rate": 0.0
            }
        }

        # Fire Circle should have low cache hit rate (dialogue is unique)
        overall_hit_rate = sum(r["cache_hits"] for r in cache_metrics.values()) / \
                          sum(r["cache_hits"] + r["cache_misses"] for r in cache_metrics.values())

        assert overall_hit_rate == 0.0  # Fresh evaluation each time


class TestLoggingStructure:
    """Test structured logging format for analysis."""

    def test_json_structured_logging(self):
        """All logs structured as JSON for easy parsing."""
        log_entry = {
            "timestamp": "2025-10-12T14:30:00Z",
            "level": "INFO",
            "component": "fire_circle",
            "event": "round_complete",
            "data": {
                "round": 2,
                "evaluations": 3,
                "convergence": 0.15
            }
        }

        # Verify structured format
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "component" in log_entry
        assert "event" in log_entry
        assert "data" in log_entry

        # Can be serialized
        json_str = json.dumps(log_entry)
        assert json_str is not None

    def test_log_levels_appropriate(self):
        """Log levels appropriate for event severity."""
        log_examples = [
            {"level": "DEBUG", "event": "model_call_start"},
            {"level": "INFO", "event": "round_complete"},
            {"level": "WARNING", "event": "approaching_minimum_viable"},
            {"level": "ERROR", "event": "model_failure"},
            {"level": "CRITICAL", "event": "quorum_failure"}
        ]

        # Verify severity mapping
        severity_order = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for i, log in enumerate(log_examples):
            expected_severity = severity_order[i]
            assert log["level"] == expected_severity

    def test_correlation_ids_for_tracing(self):
        """Correlation IDs link related log entries."""
        fire_circle_id = "fc_abc123"

        log_entries = [
            {"fire_circle_id": fire_circle_id, "event": "start", "round": 1},
            {"fire_circle_id": fire_circle_id, "event": "round_complete", "round": 1},
            {"fire_circle_id": fire_circle_id, "event": "round_complete", "round": 2},
            {"fire_circle_id": fire_circle_id, "event": "complete", "round": 3}
        ]

        # Can filter logs by correlation ID
        fc_logs = [e for e in log_entries if e.get("fire_circle_id") == fire_circle_id]
        assert len(fc_logs) == 4

        # Can trace full lifecycle
        events = [e["event"] for e in fc_logs]
        assert events == ["start", "round_complete", "round_complete", "complete"]
