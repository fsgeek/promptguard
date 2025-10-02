"""
Extract detailed reasoning for extractive prompts misclassified as reciprocal.

Loads the validation results, identifies failures, then re-evaluates those
specific prompts to capture the layer-by-layer neutrosophic reasoning.
"""

import asyncio
import json
from pathlib import Path
from promptguard import PromptGuard


async def main():
    print("=" * 70)
    print("Extractive Failure Reasoning Analysis")
    print("=" * 70)
    print()

    # Load validation results to identify failures
    results_file = Path("quick_validation_results_x-ai_grok-4-fast:free.json")
    with open(results_file) as f:
        validation_data = json.load(f)

    extractive_results = validation_data['datasets']['extractive_prompts_dataset.json']

    # Filter for failures (expected extractive, predicted reciprocal)
    failures = [r for r in extractive_results
                if r['expected'] == 'extractive' and r['predicted'] == 'reciprocal']

    print(f"Found {len(failures)} extractive prompts misclassified as reciprocal")
    print(f"Balance range: {min(f['ayni_balance'] for f in failures):.3f} - {max(f['ayni_balance'] for f in failures):.3f}")
    print()

    # Load the original dataset to get prompt content
    dataset_file = Path("datasets/extractive_prompts_dataset.json")
    with open(dataset_file) as f:
        dataset = json.load(f)

    # Build mapping of id -> prompt data
    prompts_by_id = {p['id']: p for p in dataset['prompts']}

    # Initialize guard
    guard = PromptGuard()

    # Re-evaluate each failure to capture detailed reasoning
    detailed_failures = []

    for i, failure in enumerate(failures, 1):
        prompt_id = failure['id']
        prompt_data = prompts_by_id[prompt_id]
        content = prompt_data['content']

        print(f"[{i}/{len(failures)}] Analyzing {prompt_id}...")

        try:
            # Evaluate and get full result
            result = await guard.evaluate(**content)

            # Access the internal neutrosophic prompt to get layer evaluations
            # We need to dig into the evaluator's last evaluation
            # This is a bit hacky but necessary since the API doesn't expose this

            # For now, collect what we can from the public API
            failure_detail = {
                'id': prompt_id,
                'prompt_text': content.get('user', '') or content.get('system', ''),
                'balance': result.ayni_balance,
                'exchange_type': result.exchange_type.value,
                'trust_violations': result.trust_field.violations,
                'layers': []
            }

            # We need to look at the guard's internal state
            # The neutrosophic_prompt should have layer evaluations
            if hasattr(guard, '_last_neutrosophic_prompt'):
                np = guard._last_neutrosophic_prompt
                for layer_name, layer in [
                    ('system', np.system_layer),
                    ('user', np.user_layer),
                    ('assistant', np.assistant_layer),
                    ('application', np.application_layer)
                ]:
                    if layer and layer.truth is not None:
                        failure_detail['layers'].append({
                            'name': layer_name,
                            'truth': layer.truth,
                            'indeterminacy': layer.indeterminacy,
                            'falsity': layer.falsity,
                            'reasoning': getattr(layer, 'reasoning', 'No reasoning available')
                        })

            detailed_failures.append(failure_detail)

        except Exception as e:
            print(f"  ERROR: {e}")

    print()
    print("=" * 70)
    print("Failure Analysis")
    print("=" * 70)
    print()

    # Save detailed results
    output_file = Path("extractive_failure_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(detailed_failures, f, indent=2)

    print(f"Detailed analysis saved to: {output_file}")

    # Print summary
    print("\nSample failures:")
    for failure in detailed_failures[:5]:
        print(f"\n{failure['id']}:")
        print(f"  Prompt: {failure['prompt_text'][:100]}...")
        print(f"  Balance: {failure['balance']:.3f}")
        print(f"  Layers evaluated: {len(failure['layers'])}")
        for layer in failure['layers']:
            print(f"    {layer['name']}: T={layer['truth']:.2f}, I={layer['indeterminacy']:.2f}, F={layer['falsity']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
