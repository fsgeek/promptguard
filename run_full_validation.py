"""
Run comprehensive validation across all datasets.

Tests PromptGuard evaluation against 680 labeled prompts:
- benign_malicious.json (500 prompts)
- or_bench_sample.json (100 prompts, relabeled)
- extractive_prompts_dataset.json (80 prompts)
"""

import asyncio
import json
from pathlib import Path
from collections import defaultdict
from promptguard import PromptGuard


async def evaluate_dataset(dataset_path: Path, guard: PromptGuard):
    """Evaluate all prompts in a dataset."""
    print(f"\n{'='*60}")
    print(f"Evaluating: {dataset_path.name}")
    print(f"{'='*60}\n")

    with open(dataset_path) as f:
        dataset = json.load(f)

    results = []
    correct = 0
    total = len(dataset["prompts"])

    for i, prompt_data in enumerate(dataset["prompts"], 1):
        prompt_id = prompt_data["id"]
        expected_label = prompt_data["label"]
        content = prompt_data["content"]

        print(f"[{i}/{total}] {prompt_id} (expected: {expected_label})...", end=" ")

        try:
            result = await guard.evaluate(**content)

            # Determine predicted label from ayni_balance and exchange_type
            if result.ayni_balance > 0.5:
                predicted = "reciprocal"
            elif result.exchange_type.value == "extractive":
                predicted = "extractive"
            elif result.ayni_balance < 0.3:
                predicted = "manipulative"
            else:
                predicted = "borderline"

            matches = (predicted == expected_label)
            if matches:
                correct += 1
                print(f"✓ {predicted}")
            else:
                print(f"✗ predicted={predicted}, balance={result.ayni_balance:.3f}")

            results.append({
                "id": prompt_id,
                "expected": expected_label,
                "predicted": predicted,
                "ayni_balance": result.ayni_balance,
                "exchange_type": result.exchange_type.value,
                "trust_violations": result.trust_field.violations,
                "correct": matches
            })

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "id": prompt_id,
                "expected": expected_label,
                "error": str(e),
                "correct": False
            })

    accuracy = correct / total if total > 0 else 0
    print(f"\nAccuracy: {correct}/{total} ({100*accuracy:.1f}%)")

    return results


async def main():
    print("="*60)
    print("PromptGuard Full Validation")
    print("="*60)
    print("\nDatasets:")
    print("  - benign_malicious.json (500 prompts)")
    print("  - or_bench_sample.json (100 prompts)")
    print("  - extractive_prompts_dataset.json (80 prompts)")
    print(f"\nTotal: 680 prompts")
    print(f"Estimated cost: ~$3.40 at $0.005/prompt")
    print()

    # Initialize guard
    guard = PromptGuard()

    # Run validation on each dataset
    datasets_dir = Path("datasets")
    all_results = {}

    for dataset_file in ["benign_malicious.json", "or_bench_sample.json", "extractive_prompts_dataset.json"]:
        dataset_path = datasets_dir / dataset_file
        results = await evaluate_dataset(dataset_path, guard)
        all_results[dataset_file] = results

    # Aggregate statistics
    print(f"\n{'='*60}")
    print("Overall Results")
    print(f"{'='*60}\n")

    # Per-label accuracy
    label_stats = defaultdict(lambda: {"correct": 0, "total": 0})

    for dataset_results in all_results.values():
        for result in dataset_results:
            if "error" not in result:
                label = result["expected"]
                label_stats[label]["total"] += 1
                if result["correct"]:
                    label_stats[label]["correct"] += 1

    print("Per-Label Accuracy:")
    for label in ["reciprocal", "manipulative", "extractive", "borderline"]:
        if label_stats[label]["total"] > 0:
            acc = label_stats[label]["correct"] / label_stats[label]["total"]
            print(f"  {label:15s}: {label_stats[label]['correct']:3d}/{label_stats[label]['total']:3d} ({100*acc:5.1f}%)")

    # Overall accuracy
    total_correct = sum(stats["correct"] for stats in label_stats.values())
    total_prompts = sum(stats["total"] for stats in label_stats.values())
    overall_acc = total_correct / total_prompts if total_prompts > 0 else 0

    print(f"\nOverall Accuracy: {total_correct}/{total_prompts} ({100*overall_acc:.1f}%)")

    # Save detailed results
    output_file = Path("full_validation_results.json")
    with open(output_file, 'w') as f:
        json.dump({
            "datasets": all_results,
            "summary": {
                "per_label": dict(label_stats),
                "overall": {
                    "correct": total_correct,
                    "total": total_prompts,
                    "accuracy": overall_acc
                }
            }
        }, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
