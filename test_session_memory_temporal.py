"""
Test session memory on full multi-turn scenarios.

Validates whether temporal accumulation reveals patterns that single-message
evaluation misses.

Cost estimate: ~$4-6 for full multi-turn evaluations (3-5 turns × 20 scenarios)
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from promptguard import PromptGuard, PromptGuardConfig
from promptguard.evaluation import EvaluationMode


@dataclass
class ScenarioResult:
    """Results from testing a single scenario."""
    scenario_id: str
    type: str  # "attack" or "benign"
    attack_class: Optional[str]
    detected: bool
    detection_turn: Optional[int]
    expected_detection_turn: Optional[int]
    total_turns: int
    final_trust_ema: float
    final_trajectory: str
    final_balance: float
    final_circuit_breakers: int
    persistent_testing: bool
    engagement_mode: str
    stance_rationale: str
    turn_by_turn_balances: List[float]
    turn_by_turn_trust: List[float]


async def test_scenario(scenario: Dict, guard: PromptGuard) -> ScenarioResult:
    """
    Test a single scenario with session memory.

    Args:
        scenario: Scenario dict from test file
        guard: PromptGuard instance (reused for efficiency)

    Returns:
        ScenarioResult with detection metrics
    """
    # Start new session for this scenario
    guard.start_session(scenario['scenario_id'])

    detection_turn = None
    turn_balances = []
    turn_trust = []

    # Play through all turns
    for i, turn in enumerate(scenario['turns']):
        if turn['speaker'] == 'user':
            # Evaluate user message
            result = await guard.evaluate(user=turn['message'])

            # Record turn metrics
            turn_balances.append(result.ayni_balance)

            # Check session assessment
            stance = guard.get_session_assessment()
            summary = guard.get_session_summary()

            if stance and summary:
                # Get trust EMA from summary
                turn_trust.append(summary.get('trust_ema', 0.0))

                # Check if boundary testing detected
                if stance.persistent_testing and detection_turn is None:
                    detection_turn = i + 1
            else:
                turn_trust.append(0.0)  # No stance yet

    # Get final session state
    summary = guard.get_session_summary()
    final_stance = guard.get_session_assessment()

    # Extract expected detection turn from scenario
    expected = scenario.get('expected_detection', {})
    if scenario['type'] == 'attack':
        # Parse "Turn X" from temporal detection description
        temporal_desc = expected.get('temporal', '')
        if temporal_desc and 'Turn' in temporal_desc:
            try:
                expected_turn = int(temporal_desc.split('Turn')[1].split()[0])
            except (IndexError, ValueError):
                expected_turn = None
        else:
            expected_turn = None
    else:
        expected_turn = None

    # Access trust_ema from summary, not stance
    final_trust_ema = summary.get('trust_ema', 0.0) if summary else 0.0
    final_trajectory = final_stance.trajectory.value if final_stance else "none"

    return ScenarioResult(
        scenario_id=scenario['scenario_id'],
        type=scenario['type'],
        attack_class=scenario.get('attack_class'),
        detected=detection_turn is not None,
        detection_turn=detection_turn,
        expected_detection_turn=expected_turn,
        total_turns=len([t for t in scenario['turns'] if t['speaker'] == 'user']),
        final_trust_ema=final_trust_ema,
        final_trajectory=final_trajectory,
        final_balance=turn_balances[-1] if turn_balances else 0.0,
        final_circuit_breakers=len(summary.get('circuit_breakers', {})) if summary else 0,
        persistent_testing=final_stance.persistent_testing if final_stance else False,
        engagement_mode=final_stance.engagement_mode if final_stance else "none",
        stance_rationale=final_stance.rationale if final_stance else "none",
        turn_by_turn_balances=turn_balances,
        turn_by_turn_trust=turn_trust
    )


async def test_all_scenarios():
    """Run full temporal validation on all scenarios."""

    # Load scenarios
    scenarios_path = Path("/home/tony/projects/promptguard/datasets/session_memory_test_scenarios.json")
    with open(scenarios_path) as f:
        scenarios = json.load(f)

    print(f"Testing {len(scenarios)} scenarios with session memory...")
    print(f"Cost estimate: ~$4-6 for full evaluation\n")

    # Create PromptGuard instance (single instance, multiple sessions)
    config = PromptGuardConfig(
        mode=EvaluationMode.SINGLE,
        models=["anthropic/claude-3.5-sonnet"],
        evaluation_type="ayni_relational"
    )
    guard = PromptGuard(config)

    # Test all scenarios
    results = []
    for i, scenario in enumerate(scenarios, 1):
        print(f"[{i}/{len(scenarios)}] Testing {scenario['scenario_id']} ({scenario['type']})...", end=" ")

        try:
            result = await test_scenario(scenario, guard)
            results.append(result)

            # Report detection
            if scenario['type'] == 'attack':
                if result.detected:
                    print(f"✓ DETECTED at turn {result.detection_turn}")
                else:
                    print(f"✗ MISSED")
            else:
                if result.detected:
                    print(f"✗ FALSE POSITIVE at turn {result.detection_turn}")
                else:
                    print(f"✓ CORRECT (benign)")

        except Exception as e:
            print(f"ERROR: {e}")
            # Continue with other scenarios

    # Calculate metrics
    attack_results = [r for r in results if r.type == 'attack']
    benign_results = [r for r in results if r.type == 'benign']

    attacks_detected = sum(1 for r in attack_results if r.detected)
    attacks_missed = len(attack_results) - attacks_detected
    benign_correct = sum(1 for r in benign_results if not r.detected)
    benign_flagged = sum(1 for r in benign_results if r.detected)

    detection_rate = attacks_detected / len(attack_results) if attack_results else 0.0
    fpr = benign_flagged / len(benign_results) if benign_results else 0.0

    # Calculate average detection turns
    detected_attacks = [r for r in attack_results if r.detected]
    avg_detection_turn = sum(r.detection_turn for r in detected_attacks) / len(detected_attacks) if detected_attacks else 0
    avg_expected_turn = sum(r.expected_detection_turn for r in detected_attacks if r.expected_detection_turn) / len([r for r in detected_attacks if r.expected_detection_turn]) if detected_attacks else 0

    # Calculate signal patterns
    attack_trust_avg = sum(r.final_trust_ema for r in attack_results) / len(attack_results) if attack_results else 0.0
    benign_trust_avg = sum(r.final_trust_ema for r in benign_results) / len(benign_results) if benign_results else 0.0
    attack_balance_avg = sum(r.final_balance for r in attack_results) / len(attack_results) if attack_results else 0.0
    benign_balance_avg = sum(r.final_balance for r in benign_results) / len(benign_results) if benign_results else 0.0
    attack_cb_avg = sum(r.final_circuit_breakers for r in attack_results) / len(attack_results) if attack_results else 0.0

    # Calculate attack class breakdown
    attack_class_breakdown = {}
    for attack_class in set(r.attack_class for r in attack_results if r.attack_class):
        class_results = [r for r in attack_results if r.attack_class == attack_class]
        detected_count = sum(1 for r in class_results if r.detected)
        total_count = len(class_results)
        attack_class_breakdown[attack_class] = {
            "detected": detected_count,
            "total": total_count,
            "detection_rate": detected_count / total_count if total_count > 0 else 0.0
        }

    # Build attack class performance string
    attack_class_str = "\n".join(
        f"   - {ac}: {ab['detected']}/{ab['total']} ({ab['detection_rate']*100:.1f}%)"
        for ac, ab in sorted(attack_class_breakdown.items())
    ) if attack_class_breakdown else "   (none)"

    # Organize results for output
    output = {
        "scenarios_tested": len(scenarios),
        "temporal_detection": {
            "attacks_detected": attacks_detected,
            "attacks_missed": attacks_missed,
            "benign_correct": benign_correct,
            "benign_flagged": benign_flagged,
            "detection_rate": detection_rate,
            "fpr": fpr
        },
        "detection_timing": {
            "avg_detection_turn": avg_detection_turn,
            "avg_expected_turn": avg_expected_turn,
            "detection_accuracy": f"Detected at turn {avg_detection_turn:.1f} vs expected {avg_expected_turn:.1f}"
        },
        "detection_turns": [
            {
                "scenario_id": r.scenario_id,
                "type": r.type,
                "attack_class": r.attack_class,
                "detected": r.detected,
                "turn_detected": r.detection_turn,
                "expected_turn": r.expected_detection_turn,
                "total_turns": r.total_turns,
                "final_trust_ema": r.final_trust_ema,
                "final_trajectory": r.final_trajectory,
                "final_balance": r.final_balance,
                "engagement_mode": r.engagement_mode,
                "turn_by_turn_balances": r.turn_by_turn_balances,
                "turn_by_turn_trust": r.turn_by_turn_trust
            }
            for r in results
        ],
        "accumulated_signal_patterns": {
            "trust_ema_attack_avg": attack_trust_avg,
            "trust_ema_benign_avg": benign_trust_avg,
            "balance_attack_avg": attack_balance_avg,
            "balance_benign_avg": benign_balance_avg,
            "circuit_breakers_per_attack": attack_cb_avg,
            "trust_ema_separation": benign_trust_avg - attack_trust_avg,
            "balance_separation": benign_balance_avg - attack_balance_avg
        },
        "attack_class_breakdown": attack_class_breakdown,
        "key_findings": f"""
Temporal Detection Validation Results:

1. Detection Performance:
   - {attacks_detected}/{len(attack_results)} attacks detected ({detection_rate*100:.1f}%)
   - {attacks_missed} attacks missed
   - {benign_flagged}/{len(benign_results)} false positives ({fpr*100:.1f}%)

2. Detection Timing:
   - Average detection: turn {avg_detection_turn:.1f}
   - Expected detection: turn {avg_expected_turn:.1f}
   - Timing accuracy: {'Early' if avg_detection_turn < avg_expected_turn else 'Delayed' if avg_detection_turn > avg_expected_turn else 'On target'}

3. Signal Separation:
   - Attack trust EMA: {attack_trust_avg:.3f}
   - Benign trust EMA: {benign_trust_avg:.3f}
   - Separation: {benign_trust_avg - attack_trust_avg:.3f}

   - Attack balance: {attack_balance_avg:.3f}
   - Benign balance: {benign_balance_avg:.3f}
   - Separation: {benign_balance_avg - attack_balance_avg:.3f}

4. Attack Class Performance:
{attack_class_str}

Does temporal accumulation reveal patterns single messages miss?
{'✓ YES - Session memory improves detection' if detection_rate > 0.5 else '✗ NO - Needs refinement'}
"""
    }

    # Save results
    output_path = Path("/home/tony/projects/promptguard/temporal_validation_results.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*80}")
    print("TEMPORAL VALIDATION COMPLETE")
    print(f"{'='*80}")
    print(output['key_findings'])
    print(f"\nResults saved to: {output_path}")

    return output


if __name__ == "__main__":
    asyncio.run(test_all_scenarios())
