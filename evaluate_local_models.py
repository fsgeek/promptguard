"""
Evaluate local model capabilities for prompt evaluation.

Research question: Which local models best detect manipulation via ayni evaluation?

This script:
1. Tests multiple local models (must be loaded in LM Studio first)
2. Evaluates against labeled dataset samples
3. Measures detection accuracy per model
4. Identifies which models catch which attack types
5. Tests ensemble combinations

Usage:
1. Load models in LM Studio
2. Update MODEL_CANDIDATES list below
3. Run: uv run python evaluate_local_models.py
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

from promptguard.promptguard import PromptGuard, PromptGuardConfig


# Models to test - will auto-discover from LM Studio
# Or manually specify here if you want to test a subset
MODEL_CANDIDATES = None  # None = auto-discover, or provide list to override

# Filter out embedding models (not useful for evaluation)
def filter_evaluation_models(models: List[str]) -> List[str]:
    """Filter to only models suitable for text generation."""
    filtered = []
    exclude_keywords = ['embedding', 'poetry']  # Known non-generative models

    for model in models:
        if not any(keyword in model.lower() for keyword in exclude_keywords):
            filtered.append(model)

    return filtered

# Evaluation dimensions to test
EVALUATION_TYPES = [
    "ayni_relational",
    "relational_structure",
    "trust_trajectory"
]


def load_test_set(dataset_path: str, sample_size: int = 20) -> List[Dict]:
    """Load stratified sample from dataset."""
    with open(dataset_path, 'r') as f:
        data = json.load(f)

    # Handle different dataset formats
    if isinstance(data, dict) and 'prompts' in data:
        # Wrapped format (benign_malicious.json, extractive_prompts_dataset.json)
        items = data['prompts']
    elif isinstance(data, list):
        # Direct list format
        items = data
    else:
        raise ValueError(f"Unknown dataset format: {type(data)}")

    # Stratify by label if available
    by_label = {}
    for item in items:
        label = item.get('label', item.get('expected', 'unknown'))
        if label not in by_label:
            by_label[label] = []
        by_label[label].append(item)

    # Sample evenly from each category
    samples = []
    per_category = sample_size // len(by_label)
    for label, items in by_label.items():
        samples.extend(items[:per_category])

    return samples[:sample_size]


async def evaluate_model(
    model_name: str,
    eval_type: str,
    test_samples: List[Dict],
    lmstudio_url: str
) -> Dict:
    """
    Evaluate a single model's capability.

    Returns:
        {
            'model': model_name,
            'eval_type': eval_type,
            'accuracy': float,
            'by_category': {category: accuracy},
            'errors': [{expected, predicted, prompt}],
            'reasoning_traces': bool  # Whether model provides reasoning
        }
    """
    config = PromptGuardConfig(
        provider="lmstudio",
        lmstudio_base_url=lmstudio_url,
        models=[model_name],
        evaluation_type=eval_type,
        max_tokens=2000
    )

    guard = PromptGuard(config)

    correct = 0
    by_category = {}
    errors = []
    has_reasoning_traces = False

    for sample in test_samples:
        expected = sample.get('label', sample.get('expected', 'unknown'))

        # Get prompt content (handle different dataset formats)
        if 'prompt' in sample:
            prompt_text = sample['prompt']
        elif 'content' in sample:
            content = sample['content']
            if isinstance(content, dict):
                # Check for nested prompt field first
                prompt_text = content.get('prompt', content.get('user', ''))
            else:
                prompt_text = content
        else:
            print(f"  Warning: No prompt found in sample, skipping")
            continue

        try:
            result = await guard.evaluate(prompt=prompt_text)

            # Map exchange_type to dataset labels
            predicted = result.exchange_type.value

            # Normalize labels for comparison
            is_correct = (
                (expected in ['reciprocal', 'benign'] and predicted in ['reciprocal', 'generative']) or
                (expected in ['manipulative', 'malicious'] and predicted in ['manipulative']) or
                (expected in ['extractive'] and predicted in ['extractive', 'manipulative'])
            )

            if is_correct:
                correct += 1
            else:
                errors.append({
                    'expected': expected,
                    'predicted': predicted,
                    'prompt': prompt_text[:100] + '...'
                })

            # Track by category
            if expected not in by_category:
                by_category[expected] = {'correct': 0, 'total': 0}
            by_category[expected]['total'] += 1
            if is_correct:
                by_category[expected]['correct'] += 1

            # Check for reasoning traces (DeepSeek R1 feature)
            # This requires accessing internal evaluation results
            # For now, we'll detect based on model name
            if 'r1' in model_name.lower() or 'reasoning' in model_name.lower():
                has_reasoning_traces = True

        except Exception as e:
            print(f"  Error evaluating sample with {model_name}: {e}")
            errors.append({
                'expected': expected,
                'predicted': 'ERROR',
                'error': str(e),
                'prompt': prompt_text[:100] + '...'
            })

    accuracy = correct / len(test_samples) if test_samples else 0.0

    # Calculate per-category accuracy
    category_accuracy = {}
    for category, stats in by_category.items():
        category_accuracy[category] = stats['correct'] / stats['total'] if stats['total'] > 0 else 0.0

    return {
        'model': model_name,
        'eval_type': eval_type,
        'accuracy': accuracy,
        'correct': correct,
        'total': len(test_samples),
        'by_category': category_accuracy,
        'errors': errors[:5],  # First 5 errors for analysis
        'has_reasoning_traces': has_reasoning_traces
    }


async def test_ensemble(
    models: List[str],
    eval_types: List[str],
    test_samples: List[Dict],
    lmstudio_url: str
) -> Dict:
    """
    Test ensemble combining multiple models and/or evaluation types.

    For now, this is a simulation - actual multi-model ensemble requires
    running multiple LM Studio instances or model switching.
    """
    # Placeholder for future ensemble testing
    return {
        'ensemble': models,
        'eval_types': eval_types,
        'note': 'Ensemble testing requires multiple LM Studio instances - deferred'
    }


async def discover_lmstudio_models(base_url: str) -> List[str]:
    """Query LM Studio for available models."""
    import httpx

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{base_url}/models",
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            return [m.get('id', '') for m in data.get('data', [])]
        except Exception as e:
            print(f"Warning: Could not auto-discover models: {e}")
            return []


async def main():
    print("="*80)
    print("LOCAL MODEL CAPABILITY EVALUATION")
    print("="*80)

    lmstudio_url = "http://192.168.111.125:1234/v1"

    # Auto-discover models if not manually specified
    global MODEL_CANDIDATES
    if MODEL_CANDIDATES is None:
        print("\nAuto-discovering models from LM Studio...")
        discovered = await discover_lmstudio_models(lmstudio_url)
        MODEL_CANDIDATES = filter_evaluation_models(discovered)
        print(f"  Found {len(MODEL_CANDIDATES)} evaluation-capable models")
        for model in MODEL_CANDIDATES:
            print(f"    - {model}")
    else:
        print(f"\nUsing manually specified models: {MODEL_CANDIDATES}")

    # Load test samples
    print("\nLoading test datasets...")

    datasets = {
        'benign_malicious': 'datasets/benign_malicious.json',
        'extractive': 'datasets/extractive_prompts_dataset.json',
    }

    test_samples = {}
    for name, path in datasets.items():
        if Path(path).exists():
            test_samples[name] = load_test_set(path, sample_size=10)
            print(f"  ✓ Loaded {len(test_samples[name])} samples from {name}")
        else:
            print(f"  ✗ Dataset not found: {path}")

    # Combine all samples
    all_samples = []
    for samples in test_samples.values():
        all_samples.extend(samples)

    print(f"\nTotal test samples: {len(all_samples)}")

    # Test each model with each evaluation type
    results = []

    for model in MODEL_CANDIDATES:
        print(f"\n{'='*80}")
        print(f"Testing model: {model}")
        print(f"{'='*80}")

        for eval_type in EVALUATION_TYPES:
            print(f"\n  Evaluation type: {eval_type}")

            try:
                result = await evaluate_model(
                    model,
                    eval_type,
                    all_samples,
                    lmstudio_url
                )

                results.append(result)

                print(f"    Accuracy: {result['accuracy']:.1%} ({result['correct']}/{result['total']})")
                print(f"    By category:")
                for category, acc in result['by_category'].items():
                    print(f"      {category}: {acc:.1%}")

                if result['has_reasoning_traces']:
                    print(f"    ✓ Provides reasoning traces")

            except Exception as e:
                print(f"    ✗ Failed: {e}")

    # Summary analysis
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    # Best model per evaluation type
    by_eval_type = {}
    for result in results:
        eval_type = result['eval_type']
        if eval_type not in by_eval_type:
            by_eval_type[eval_type] = []
        by_eval_type[eval_type].append(result)

    print("\nBest models per evaluation type:")
    for eval_type, model_results in by_eval_type.items():
        best = max(model_results, key=lambda x: x['accuracy'])
        print(f"\n  {eval_type}:")
        print(f"    Best: {best['model']} ({best['accuracy']:.1%})")
        print(f"    Per category:")
        for category, acc in best['by_category'].items():
            print(f"      {category}: {acc:.1%}")

    # Overall best model (averaged across eval types)
    model_avg_accuracy = {}
    for result in results:
        model = result['model']
        if model not in model_avg_accuracy:
            model_avg_accuracy[model] = []
        model_avg_accuracy[model].append(result['accuracy'])

    print("\n\nOverall model rankings (averaged across eval types):")
    for model, accuracies in sorted(model_avg_accuracy.items(),
                                   key=lambda x: sum(x[1])/len(x[1]),
                                   reverse=True):
        avg = sum(accuracies) / len(accuracies)
        print(f"  {model}: {avg:.1%}")

    # Save results
    output = {
        'timestamp': datetime.utcnow().isoformat(),
        'lmstudio_url': lmstudio_url,
        'models_tested': MODEL_CANDIDATES,
        'eval_types_tested': EVALUATION_TYPES,
        'total_samples': len(all_samples),
        'results': results,
        'summary': {
            'best_per_eval_type': {
                eval_type: max(model_results, key=lambda x: x['accuracy'])['model']
                for eval_type, model_results in by_eval_type.items()
            },
            'overall_ranking': [
                {
                    'model': model,
                    'avg_accuracy': sum(accuracies) / len(accuracies)
                }
                for model, accuracies in sorted(model_avg_accuracy.items(),
                                              key=lambda x: sum(x[1])/len(x[1]),
                                              reverse=True)
            ]
        }
    }

    output_path = f"local_model_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n\nResults saved to: {output_path}")

    # Recommendations
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS")
    print(f"{'='*80}")

    print("\nBased on these results:")
    print("1. For development/testing: [Model with best overall accuracy]")
    print("2. For ensemble: [Top 3 models that show complementary strengths]")
    print("3. For reasoning transparency: [Models with reasoning traces]")

    print("\nNext steps:")
    print("- Test additional models as you load them")
    print("- Validate findings on full dataset (680 prompts)")
    print("- Build ensemble from complementary models")


if __name__ == "__main__":
    asyncio.run(main())
