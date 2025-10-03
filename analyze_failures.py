#!/usr/bin/env python3
"""Analyze validation failure patterns to identify misclassification examples."""

import json
from pathlib import Path

def load_json(filepath):
    """Load and parse JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def get_prompt_text(datasets, prompt_id):
    """Get prompt text from datasets by ID."""
    for dataset_name, dataset in datasets.items():
        for prompt in dataset.get('prompts', []):
            if prompt['id'] == prompt_id:
                # Return first 200 chars of prompt content
                content = prompt['content']
                if isinstance(content, dict):
                    # Multi-layer prompt
                    prompt_text = content.get('prompt', '')
                else:
                    prompt_text = content
                return prompt_text[:200] if len(prompt_text) > 200 else prompt_text
    return None

def analyze_failures():
    """Analyze validation failures and extract examples."""

    # Load validation results
    results_data = load_json('quick_validation_results_x-ai_grok-4-fast:free.json')

    # Load datasets
    datasets = {
        'benign_malicious': load_json('datasets/benign_malicious.json'),
        'extractive': load_json('datasets/extractive_prompts_dataset.json')
    }

    # Track failures
    reciprocal_fps = []  # reciprocal classified as manipulative/extractive
    extractive_fns = []  # extractive classified as reciprocal

    # Iterate through all datasets in results
    for dataset_name, results in results_data.get('datasets', {}).items():
        for result in results:
            # Skip if predicted field is missing (evaluation error)
            if 'predicted' not in result:
                continue

            prompt_id = result['id']
            true_label = result['expected']
            predicted = result['predicted']
            balance = result.get('ayni_balance', 0.0)

            # Reciprocal False Positives (classified as manipulative or extractive)
            if true_label == 'reciprocal' and predicted in ['manipulative', 'extractive']:
                prompt_text = get_prompt_text(datasets, prompt_id)
                reciprocal_fps.append({
                    'id': prompt_id,
                    'predicted': predicted,
                    'balance': balance,
                    'prompt': prompt_text
                })

            # Extractive False Negatives (classified as reciprocal)
            if true_label == 'extractive' and predicted == 'reciprocal':
                prompt_text = get_prompt_text(datasets, prompt_id)
                extractive_fns.append({
                    'id': prompt_id,
                    'balance': balance,
                    'prompt': prompt_text
                })

    print("=" * 80)
    print("RECIPROCAL FALSE POSITIVES (reciprocal → manipulative/extractive)")
    print(f"Total: {len(reciprocal_fps)}")
    print("=" * 80)
    print()

    # Show first 10 examples
    for i, fp in enumerate(reciprocal_fps[:10], 1):
        print(f"Example {i}: {fp['id']}")
        print(f"  Predicted: {fp['predicted']}")
        print(f"  Balance: {fp['balance']:.3f}")
        print(f"  Prompt: {fp['prompt']}")
        print()

    # Analyze balance distribution
    balances = [fp['balance'] for fp in reciprocal_fps]
    avg_balance = sum(balances) / len(balances) if balances else 0
    min_balance = min(balances) if balances else 0
    max_balance = max(balances) if balances else 0

    print(f"Balance stats: avg={avg_balance:.3f}, min={min_balance:.3f}, max={max_balance:.3f}")
    print()

    # Count by predicted label
    manip_count = sum(1 for fp in reciprocal_fps if fp['predicted'] == 'manipulative')
    extract_count = sum(1 for fp in reciprocal_fps if fp['predicted'] == 'extractive')
    print(f"Breakdown: {manip_count} manipulative, {extract_count} extractive")
    print()

    print("=" * 80)
    print("EXTRACTIVE FALSE NEGATIVES (extractive → reciprocal)")
    print(f"Total: {len(extractive_fns)}")
    print("=" * 80)
    print()

    # Show first 10 examples
    for i, fn in enumerate(extractive_fns[:10], 1):
        print(f"Example {i}: {fn['id']}")
        print(f"  Balance: {fn['balance']:.3f}")
        print(f"  Prompt: {fn['prompt']}")
        print()

    # Analyze balance distribution
    balances = [fn['balance'] for fn in extractive_fns]
    avg_balance = sum(balances) / len(balances) if balances else 0
    min_balance = min(balances) if balances else 0
    max_balance = max(balances) if balances else 0

    print(f"Balance stats: avg={avg_balance:.3f}, min={min_balance:.3f}, max={max_balance:.3f}")
    print()

    # Save detailed results
    output = {
        'reciprocal_fps': reciprocal_fps,
        'extractive_fns': extractive_fns,
        'summary': {
            'reciprocal_fps_count': len(reciprocal_fps),
            'extractive_fns_count': len(extractive_fns),
            'reciprocal_fps_by_predicted': {
                'manipulative': manip_count,
                'extractive': extract_count
            }
        }
    }

    with open('failure_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("Detailed analysis saved to failure_analysis.json")

if __name__ == '__main__':
    analyze_failures()
