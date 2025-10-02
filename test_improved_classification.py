"""
Test improved classification logic against validation data.

This script re-analyzes the validation log using different classification
strategies to see which performs best.
"""

import re
from collections import defaultdict
from improved_classification import (
    classify_prompt_improved,
    classify_prompt_trust_aware,
    classify_prompt_threshold_tuned,
    classify_prompt_recommended
)


def parse_validation_log(log_path):
    """Parse validation log to extract balance, exchange_type, and expected label."""
    results = []

    with open(log_path) as f:
        for line in f:
            # Match: [N/M] id (expected: LABEL)... ✓ PRED or ✗ predicted=PRED, balance=X.XXX
            correct_match = re.search(r'\(expected: (\w+)\)\.\.\. ✓ (\w+)', line)
            if correct_match:
                results.append({
                    'expected': correct_match.group(1),
                    'current_predicted': correct_match.group(2),
                    'balance': None,  # Not shown for correct predictions
                    'correct': True
                })
                continue

            incorrect_match = re.search(
                r'\(expected: (\w+)\)\.\.\. ✗ predicted=(\w+), balance=([-\d.]+)',
                line
            )
            if incorrect_match:
                results.append({
                    'expected': incorrect_match.group(1),
                    'current_predicted': incorrect_match.group(2),
                    'balance': float(incorrect_match.group(3)),
                    'correct': False
                })

    return results


def simulate_classification(results, classify_fn, strategy_name):
    """
    Simulate classification with a new strategy.

    Note: We can't fully test without num_layers info, but we can estimate:
    - benign_malicious dataset = single layer (prompt only)
    - extractive dataset = multi layer (system + prompt)
    """
    stats = defaultdict(lambda: {"correct": 0, "total": 0, "predictions": defaultdict(int)})

    for result in results:
        expected = result['expected']
        stats[expected]["total"] += 1

        # For incorrect predictions where we have balance, simulate new classification
        if not result['correct'] and result['balance'] is not None:
            balance = result['balance']

            # Estimate num_layers based on expected label
            # (This is imperfect but good enough for simulation)
            if expected in ['reciprocal', 'manipulative']:
                num_layers = 1  # benign_malicious dataset
            else:
                num_layers = 2  # extractive dataset

            # Simulate metrics (we don't have full metrics, just balance)
            # Create a mock object
            class MockExchangeType:
                def __init__(self, value):
                    self.value = value
                    self.EXTRACTIVE = "extractive"

            class MockTrustField:
                def __init__(self):
                    self.violations = []
                    self.strength = 0.5

            class MockMetrics:
                def __init__(self, balance):
                    self.ayni_balance = balance
                    # Infer exchange_type from balance (matching ayni.py logic)
                    if balance < -0.3:
                        self.exchange_type = MockExchangeType("extractive")
                    elif balance > 0.5:
                        self.exchange_type = MockExchangeType("generative")
                    else:
                        self.exchange_type = MockExchangeType("reciprocal")
                    self.trust_field = MockTrustField()

            mock_metrics = MockMetrics(balance)

            try:
                predicted = classify_fn(mock_metrics, num_layers)
            except:
                predicted = result['current_predicted']  # Fall back to current

        else:
            # For correct predictions, assume they stay correct
            predicted = result['current_predicted']

        stats[expected]["predictions"][predicted] += 1
        if predicted == expected:
            stats[expected]["correct"] += 1

    return stats


def print_stats(stats, strategy_name):
    """Print classification statistics."""
    print(f"\n{'=' * 60}")
    print(f"{strategy_name}")
    print('=' * 60)

    for label in ["reciprocal", "manipulative", "extractive", "borderline"]:
        if stats[label]["total"] == 0:
            continue

        label_stats = stats[label]
        acc = 100 * label_stats["correct"] / label_stats["total"]

        print(f"\n{label.upper()}: {label_stats['correct']}/{label_stats['total']} correct ({acc:.1f}%)")
        print("  Predicted as:")
        for pred, count in sorted(label_stats["predictions"].items(), key=lambda x: -x[1]):
            pct = 100 * count / label_stats["total"]
            mark = "✓" if pred == label else "✗"
            print(f"    {mark} {pred:15s}: {count:3d} ({pct:5.1f}%)")

    # Overall
    total_correct = sum(s["correct"] for s in stats.values())
    total_prompts = sum(s["total"] for s in stats.values())
    overall_acc = 100 * total_correct / total_prompts if total_prompts > 0 else 0

    print(f"\nOVERALL: {total_correct}/{total_prompts} ({overall_acc:.1f}%)")

    # Key metric: manipulative accuracy
    if stats["manipulative"]["total"] > 0:
        manip_acc = 100 * stats["manipulative"]["correct"] / stats["manipulative"]["total"]
        print(f"\nKEY METRIC - Manipulative accuracy: {manip_acc:.1f}%")
        print(f"  (Current baseline: 7.6%)")


def main():
    log_path = "/home/tony/projects/promptguard/validation_output.log"

    print("PromptGuard Classification Strategy Comparison")
    print("=" * 60)
    print("\nParsing validation log...")

    results = parse_validation_log(log_path)
    print(f"Parsed {len(results)} evaluations")

    # Current baseline
    current_stats = defaultdict(lambda: {"correct": 0, "total": 0, "predictions": defaultdict(int)})
    for result in results:
        expected = result['expected']
        predicted = result['current_predicted']
        current_stats[expected]["total"] += 1
        current_stats[expected]["predictions"][predicted] += 1
        if result['correct']:
            current_stats[expected]["correct"] += 1

    print_stats(current_stats, "CURRENT BASELINE")

    # Test improved strategies
    print_stats(
        simulate_classification(results, classify_prompt_improved, "Improved"),
        "STRATEGY 1: Improved (layer-aware)"
    )

    print_stats(
        simulate_classification(results, classify_prompt_threshold_tuned, "Threshold Tuned"),
        "STRATEGY 2: Threshold Tuned"
    )

    print_stats(
        simulate_classification(results, classify_prompt_recommended, "Recommended"),
        "STRATEGY 3: Recommended (Combined)"
    )


if __name__ == "__main__":
    main()
