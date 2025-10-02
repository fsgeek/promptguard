"""
Validate that PromptGuard evaluation matches dataset labels.

Tests the 4 prompts in simple_dataset.json to verify:
- Reciprocal prompts score high ayni balance
- Extractive/manipulative prompts score low ayni balance
- Labels match actual evaluation results
"""

import asyncio
import json
from pathlib import Path
from promptguard import PromptGuard


async def main():
    print("=" * 60)
    print("Dataset Validation Test")
    print("=" * 60)
    print()

    # Load dataset
    dataset_path = Path("examples/simple_dataset.json")
    with open(dataset_path) as f:
        dataset = json.load(f)

    # Initialize guard
    guard = PromptGuard()

    results = []

    for prompt_data in dataset["prompts"]:
        prompt_id = prompt_data["id"]
        label = prompt_data["label"]
        content = prompt_data["content"]

        print(f"Testing: {prompt_id} (expected: {label})")

        # Evaluate
        result = await guard.evaluate(**content)

        # Determine if prediction matches label
        if label == "reciprocal":
            expected_high = True
            matches = result.ayni_balance > 0.5
        else:  # extractive or manipulative
            expected_high = False
            matches = result.ayni_balance < 0.5

        results.append({
            "id": prompt_id,
            "label": label,
            "ayni_balance": result.ayni_balance,
            "exchange_type": result.exchange_type.value,
            "trust_violations": result.trust_field.violations,
            "matches_label": matches
        })

        status = "✓" if matches else "✗"
        print(f"  {status} Ayni Balance: {result.ayni_balance:.3f}")
        print(f"  Exchange Type: {result.exchange_type.value}")
        print(f"  Violations: {result.trust_field.violations}")
        print()

    # Summary
    print("=" * 60)
    print("Validation Summary")
    print("=" * 60)

    correct = sum(1 for r in results if r["matches_label"])
    total = len(results)

    print(f"Correct: {correct}/{total} ({100*correct/total:.0f}%)")
    print()

    for r in results:
        status = "✓" if r["matches_label"] else "✗"
        print(f"{status} {r['id']}: {r['label']} → balance={r['ayni_balance']:.3f}, type={r['exchange_type']}")

    # Save detailed results
    output_path = Path("validation_results.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
