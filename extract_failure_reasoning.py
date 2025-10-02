"""
Extract detailed LLM reasoning for extractive prompts misclassified as reciprocal.

Re-evaluates a subset of failures with caching disabled to capture the
reasoning field that explains why the model scored them as reciprocal.
"""

import asyncio
import json
from pathlib import Path
from promptguard.evaluation.evaluator import LLMEvaluator, EvaluationConfig, EvaluationMode
from promptguard.evaluation.prompts import NeutrosophicEvaluationPrompt
from promptguard.config import CacheConfig


async def main():
    print("=" * 70)
    print("Extractive Failure Reasoning Extraction")
    print("=" * 70)
    print()

    # Load validation results to identify failures
    results_file = Path("quick_validation_results_x-ai_grok-4-fast:free.json")
    with open(results_file) as f:
        validation_data = json.load(f)

    extractive_results = validation_data['datasets']['extractive_prompts_dataset.json']

    # Filter for failures (expected extractive, predicted reciprocal, no errors)
    failures = [r for r in extractive_results
                if 'error' not in r
                and r['expected'] == 'extractive'
                and r['predicted'] == 'reciprocal']

    print(f"Found {len(failures)} extractive prompts misclassified as reciprocal")
    balances = [f['ayni_balance'] for f in failures]
    print(f"Balance range: {min(balances):.3f} - {max(balances):.3f}")
    print()

    # Load the original dataset to get prompt content
    dataset_file = Path("datasets/extractive_prompts_dataset.json")
    with open(dataset_file) as f:
        dataset = json.load(f)

    # Build mapping of id -> prompt data
    prompts_by_id = {p['id']: p for p in dataset['prompts']}

    # Initialize evaluator with caching DISABLED to get fresh reasoning
    cache_config = CacheConfig(enabled=False)
    eval_config = EvaluationConfig(
        mode=EvaluationMode.SINGLE,
        models=["x-ai/grok-4-fast:free"],
        cache_config=cache_config
    )
    evaluator = LLMEvaluator(eval_config)

    # Re-evaluate failures to capture reasoning
    detailed_failures = []

    # Process all failures (they're already a small set - 22-23 prompts)
    for i, failure in enumerate(failures, 1):
        prompt_id = failure['id']
        prompt_data = prompts_by_id[prompt_id]
        content = prompt_data['content']

        # Extract the actual prompt text (user layer)
        prompt_text = content.get('user', '') or content.get('system', '')

        print(f"[{i}/{len(failures)}] {prompt_id}... ", end="", flush=True)

        try:
            # Build context string for evaluation
            context_parts = []
            if content.get('system'):
                context_parts.append(f"System: {content['system']}")
            if content.get('user'):
                context_parts.append(f"User: {content['user']}")
            if content.get('assistant'):
                context_parts.append(f"Assistant: {content['assistant']}")
            if content.get('application'):
                context_parts.append(f"Application: {content['application']}")

            context = "\n".join(context_parts)

            # Evaluate the primary layer (user or system)
            evaluation_prompt = NeutrosophicEvaluationPrompt.get_prompt("ayni_relational")

            # This returns List[NeutrosophicEvaluation] with reasoning
            evaluations = await evaluator.evaluate_layer(
                layer_content=prompt_text,
                context=context,
                evaluation_prompt=evaluation_prompt,
                recursion_depth=0
            )

            # Extract the evaluation (should be single model)
            evaluation = evaluations[0]

            failure_detail = {
                'id': prompt_id,
                'prompt_text': prompt_text,
                'balance': failure['ayni_balance'],
                'exchange_type': failure['exchange_type'],
                'num_layers': failure['num_layers'],
                'evaluation': {
                    'truth': evaluation.truth,
                    'indeterminacy': evaluation.indeterminacy,
                    'falsehood': evaluation.falsehood,
                    'reasoning': evaluation.reasoning,
                    'model': evaluation.model
                }
            }

            detailed_failures.append(failure_detail)
            print(f"✓ T={evaluation.truth:.2f}")

        except Exception as e:
            print(f"ERROR: {e}")

    print()
    print("=" * 70)
    print("Analysis Complete")
    print("=" * 70)
    print()

    # Save detailed results
    output_file = Path("extractive_failure_reasoning.json")
    with open(output_file, 'w') as f:
        json.dump(detailed_failures, f, indent=2)

    print(f"Results saved to: {output_file}")
    print(f"Total failures analyzed: {len(detailed_failures)}")

    # Print summary of reasoning patterns
    print("\n" + "=" * 70)
    print("Sample Reasoning (First 5)")
    print("=" * 70)

    for i, failure in enumerate(detailed_failures[:5], 1):
        print(f"\n{i}. {failure['id']}:")
        print(f"   Prompt: {failure['prompt_text'][:80]}...")
        print(f"   Balance: {failure['balance']:.3f}")
        print(f"   T/I/F: {failure['evaluation']['truth']:.2f}/{failure['evaluation']['indeterminacy']:.2f}/{failure['evaluation']['falsehood']:.2f}")
        print(f"   Reasoning: {failure['evaluation']['reasoning'][:200]}...")


if __name__ == "__main__":
    asyncio.run(main())
