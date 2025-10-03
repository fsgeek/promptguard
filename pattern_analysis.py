#!/usr/bin/env python3
"""Deep pattern analysis of misclassification failures."""

import json
from pathlib import Path

def load_json(filepath):
    """Load and parse JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def get_full_prompt_data(datasets, prompt_id):
    """Get full prompt data from datasets by ID."""
    for dataset_name, dataset in datasets.items():
        for prompt in dataset.get('prompts', []):
            if prompt['id'] == prompt_id:
                return prompt
    return None

def analyze_patterns():
    """Deep pattern analysis of failures."""

    # Load failure data
    failures = load_json('failure_analysis.json')

    # Load datasets
    datasets = {
        'benign_malicious': load_json('datasets/benign_malicious.json'),
        'extractive': load_json('datasets/extractive_prompts_dataset.json')
    }

    print("=" * 80)
    print("RECIPROCAL FALSE POSITIVE PATTERN ANALYSIS")
    print("=" * 80)
    print()

    # Analyze reciprocal FPs by balance range
    fps = failures['reciprocal_fps']

    # Group by balance ranges
    very_negative = [fp for fp in fps if fp['balance'] <= -0.8]
    moderately_negative = [fp for fp in fps if -0.8 < fp['balance'] <= -0.4]
    slightly_negative = [fp for fp in fps if -0.4 < fp['balance'] < 0]
    positive = [fp for fp in fps if fp['balance'] >= 0]

    print(f"Balance distribution:")
    print(f"  Very negative (≤ -0.8): {len(very_negative)} ({len(very_negative)/len(fps)*100:.1f}%)")
    print(f"  Moderately negative (-0.8 to -0.4): {len(moderately_negative)} ({len(moderately_negative)/len(fps)*100:.1f}%)")
    print(f"  Slightly negative (-0.4 to 0): {len(slightly_negative)} ({len(slightly_negative)/len(fps)*100:.1f}%)")
    print(f"  Positive (≥ 0): {len(positive)} ({len(positive)/len(fps)*100:.1f}%)")
    print()

    # Analyze linguistic patterns in FPs
    print("Linguistic pattern analysis:")

    # Look for imperatives/commands
    imperatives = ['write', 'please', 'could you', 'would you', 'can you', 'describe', 'explain', 'list', 'provide', 'tell me']
    fps_with_imperatives = []
    for fp in fps[:20]:  # Check first 20
        prompt_lower = (fp['prompt'] or '').lower()
        has_imperative = any(imp in prompt_lower for imp in imperatives)
        if has_imperative:
            fps_with_imperatives.append(fp)

    print(f"  Prompts with imperative/request language: {len(fps_with_imperatives)}/20")
    print()

    # Show examples of very negative balance FPs
    print("Very negative balance examples (-1.0 to -0.8):")
    for i, fp in enumerate(very_negative[:5], 1):
        full_data = get_full_prompt_data(datasets, fp['id'])
        print(f"{i}. Balance: {fp['balance']:.3f}")
        print(f"   Prompt: {fp['prompt']}")
        if full_data and 'content' in full_data:
            content = full_data['content']
            if isinstance(content, dict):
                print(f"   Has system layer: {bool(content.get('system'))}")
                print(f"   Has application layer: {bool(content.get('application'))}")
        print()

    print("=" * 80)
    print("EXTRACTIVE FALSE NEGATIVE PATTERN ANALYSIS")
    print("=" * 80)
    print()

    fns = failures['extractive_fns']

    # All FNs have positive balance
    print(f"All {len(fns)} extractive FNs have positive balance (avg: {sum(fn['balance'] for fn in fns)/len(fns):.3f})")
    print()

    # Analyze politeness markers
    politeness_markers = [
        "thank you",
        "please",
        "how may i assist",
        "how can i assist",
        "how can i help",
        "i'm doing well",
        "let me know"
    ]

    polite_fns = []
    for fn in fns:
        prompt_lower = (fn['prompt'] or '').lower()
        politeness_count = sum(1 for marker in politeness_markers if marker in prompt_lower)
        if politeness_count > 0:
            polite_fns.append((fn, politeness_count))

    print(f"Prompts with politeness markers: {len(polite_fns)}/{len(fns)} ({len(polite_fns)/len(fns)*100:.1f}%)")
    print()

    # Show polite extraction examples with full context
    print("Polite extraction attack examples:")
    for i, (fn, politeness_count) in enumerate(polite_fns[:5], 1):
        full_data = get_full_prompt_data(datasets, fn['id'])
        print(f"{i}. {fn['id']}")
        print(f"   Balance: {fn['balance']:.3f}")
        print(f"   Politeness markers: {politeness_count}")
        print(f"   Prompt: {fn['prompt']}")

        if full_data:
            metadata = full_data.get('metadata', {})
            print(f"   Attack type: {metadata.get('attack_type', 'unknown')}")
            print(f"   Technique: {metadata.get('technique', 'unknown')}")

            # Show system layer to see role reversal
            content = full_data.get('content', {})
            if isinstance(content, dict) and content.get('system'):
                system = content['system'][:200]
                print(f"   System layer (first 200 chars): {system}")
        print()

    # Look for role manipulation patterns
    role_patterns = [
        "i'm doing well",
        "how may i assist",
        "how can i assist",
        "how can i help you",
        "what can i help",
        "let me know"
    ]

    role_reversal_fns = []
    for fn in fns:
        prompt_lower = (fn['prompt'] or '').lower()
        has_role_reversal = any(pattern in prompt_lower for pattern in role_patterns)
        if has_role_reversal:
            role_reversal_fns.append(fn)

    print(f"Role reversal pattern (AI pretending to be the assistant): {len(role_reversal_fns)}/{len(fns)} ({len(role_reversal_fns)/len(fns)*100:.1f}%)")
    print()

    print("=" * 80)
    print("KEY FINDINGS")
    print("=" * 80)
    print()

    print("RECIPROCAL FALSE POSITIVES:")
    print(f"- {len(very_negative)} prompts ({len(very_negative)/len(fps)*100:.1f}%) have very negative balance (≤ -0.8)")
    print(f"- These are benign requests being severely penalized")
    print(f"- Pattern: Imperative/request language may be triggering extraction detection")
    print(f"- Issue: Threshold penalty appears TOO AGGRESSIVE for normal requests")
    print()

    print("EXTRACTIVE FALSE NEGATIVES:")
    print(f"- ALL {len(fns)} extractive attacks have POSITIVE balance (0.68-0.95)")
    print(f"- {len(polite_fns)}/{len(fns)} ({len(polite_fns)/len(fns)*100:.1f}%) use politeness markers")
    print(f"- {len(role_reversal_fns)}/{len(fns)} ({len(role_reversal_fns)/len(fns)*100:.1f}%) use role reversal")
    print(f"- Pattern: 'How may I assist you today?' bypasses detection completely")
    print(f"- Issue: LLM evaluation misses SUBTLE role manipulation")
    print()

    print("CONCLUSION:")
    print("1. Threshold penalty penalizes normal imperatives (requests) too harshly")
    print("2. LLM fails to detect polite extraction via role reversal")
    print("3. Surface reciprocity (politeness) masks extractive intent")
    print("4. System needs to detect role manipulation, not just command language")

if __name__ == '__main__':
    analyze_patterns()
