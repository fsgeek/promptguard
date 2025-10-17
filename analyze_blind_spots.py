#!/usr/bin/env python3
"""
Analyze the 202 cases where both RLHF and PromptGuard failed to detect
manipulative outputs (F < 0.7).

This script:
1. Loads the overlap analysis JSON
2. Queries ArangoDB for full prompt/response pairs
3. Identifies patterns in missed cases
4. Compares against detected cases
5. Generates recommendations
"""

import json
import os
from collections import defaultdict, Counter
from typing import Dict, List, Any
from promptguard.storage.target_response_storage import TargetResponseStorage


def load_overlap_analysis(filepath: str) -> Dict[str, Any]:
    """Load the overlap analysis JSON."""
    with open(filepath) as f:
        return json.load(f)


def analyze_f_score_distribution(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze F score distributions."""
    pre_f_scores = [c['pre_f'] for c in cases]
    post_f_scores = [c['post_f'] for c in cases]

    return {
        'pre_f': {
            'min': min(pre_f_scores),
            'max': max(pre_f_scores),
            'avg': sum(pre_f_scores) / len(pre_f_scores),
            'below_0_5': len([f for f in pre_f_scores if f < 0.5]),
            'below_0_6': len([f for f in pre_f_scores if f < 0.6]),
            'below_0_7': len([f for f in pre_f_scores if f < 0.7]),
        },
        'post_f': {
            'min': min(post_f_scores),
            'max': max(post_f_scores),
            'avg': sum(post_f_scores) / len(post_f_scores),
            'below_0_5': len([f for f in post_f_scores if f < 0.5]),
            'below_0_6': len([f for f in post_f_scores if f < 0.6]),
            'below_0_7': len([f for f in post_f_scores if f < 0.7]),
        }
    }


def extract_prompt_patterns(cases: List[Dict[str, Any]], storage: TargetResponseStorage) -> Dict[str, Any]:
    """Extract patterns from prompts."""
    prompt_types = Counter()
    prompt_ids = set()

    # Group by prompt_id to avoid duplicate fetches
    by_prompt = defaultdict(list)
    for case in cases:
        by_prompt[case['prompt_id']].append(case)

    print(f"Fetching {len(by_prompt)} unique prompts...")

    sample_cases = []
    for i, (prompt_id, prompt_cases) in enumerate(by_prompt.items()):
        if i % 20 == 0:
            print(f"  Processing prompt {i+1}/{len(by_prompt)}...")

        # Get first case for this prompt
        case = prompt_cases[0]

        # Fetch full document from ArangoDB
        doc = storage.get_response(case['prompt_id'], case['target_model'], decrypt=True)

        if doc:
            # Extract prompt type from ID
            if prompt_id.startswith('benign_malicious_'):
                prompt_type = 'benign_malicious'
            elif prompt_id.startswith('system_prompt_leak_'):
                prompt_type = 'system_prompt_leak'
            elif prompt_id.startswith('role_reversal_'):
                prompt_type = 'role_reversal'
            elif prompt_id.startswith('prompt_injection_'):
                prompt_type = 'prompt_injection'
            else:
                prompt_type = 'unknown'

            prompt_types[prompt_type] += len(prompt_cases)

            # Collect sample cases (first 10 from each category)
            if len([s for s in sample_cases if s['type'] == prompt_type]) < 10:
                sample_cases.append({
                    'type': prompt_type,
                    'prompt_id': case['prompt_id'],
                    'target_model': case['target_model'],
                    'prompt': doc['prompt_text'],
                    'response': doc['response']['text'] if 'text' in doc['response'] else doc['response'].get('text_encrypted', 'N/A'),
                    'pre_f': case['pre_f'],
                    'post_f': case['post_f'],
                    'label': doc.get('prompt_label', 'unknown')
                })

    return {
        'prompt_types': dict(prompt_types),
        'unique_prompts': len(by_prompt),
        'sample_cases': sample_cases
    }


def extract_response_patterns(cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract patterns from responses (truncated in overlap file)."""
    response_lengths = Counter()
    starts_with = Counter()

    for case in cases:
        response = case['response']

        # Length categories
        if len(response) < 50:
            response_lengths['very_short'] += 1
        elif len(response) < 150:
            response_lengths['short'] += 1
        elif len(response) < 300:
            response_lengths['medium'] += 1
        else:
            response_lengths['long'] += 1

        # Common starts (first 20 chars)
        start = response[:20].lower()
        if 'sorry' in start or 'apologize' in start:
            starts_with['apology'] += 1
        elif 'i cannot' in start or "i can't" in start:
            starts_with['refusal'] += 1
        elif 'sure' in start or 'certainly' in start or 'of course' in start:
            starts_with['compliance'] += 1
        else:
            starts_with['neutral'] += 1

    return {
        'response_lengths': dict(response_lengths),
        'starts_with': dict(starts_with)
    }


def compare_detected_vs_missed(
    detected: List[Dict[str, Any]],
    missed: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Compare detected cases vs missed cases."""

    detected_f = analyze_f_score_distribution(detected)
    missed_f = analyze_f_score_distribution(missed)

    # Model performance
    detected_models = Counter(c['target_model'] for c in detected)
    missed_models = Counter(c['target_model'] for c in missed)

    return {
        'detected_f_scores': detected_f,
        'missed_f_scores': missed_f,
        'detected_models': dict(detected_models),
        'missed_models': dict(missed_models)
    }


def main():
    """Main analysis."""
    print("=" * 80)
    print("PROMPTGUARD BLIND SPOTS ANALYSIS")
    print("=" * 80)
    print()

    # Load data
    print("Loading overlap analysis...")
    overlap_file = "/home/tony/projects/promptguard/rlhf_pg_overlap_decrypted_target_response_analysis_2025-10-16-22-15.json"
    data = load_overlap_analysis(overlap_file)

    neither = data['neither']
    both_detected = data['both_detected']

    print(f"  Missed by both (neither): {len(neither)}")
    print(f"  Detected by both: {len(both_detected)}")
    print()

    # Initialize storage
    print("Connecting to ArangoDB...")
    storage = TargetResponseStorage()
    print("  Connected!")
    print()

    # Analyze F score distributions
    print("Analyzing F score distributions...")
    neither_f = analyze_f_score_distribution(neither)
    print(f"  Neither cases - Pre-F avg: {neither_f['pre_f']['avg']:.3f}, Post-F avg: {neither_f['post_f']['avg']:.3f}")
    print()

    # Extract prompt patterns
    print("Extracting prompt patterns from missed cases...")
    prompt_patterns = extract_prompt_patterns(neither, storage)
    print(f"  Unique prompts: {prompt_patterns['unique_prompts']}")
    print(f"  Prompt types: {prompt_patterns['prompt_types']}")
    print()

    # Extract response patterns
    print("Extracting response patterns...")
    response_patterns = extract_response_patterns(neither)
    print(f"  Response patterns: {response_patterns}")
    print()

    # Compare detected vs missed
    print("Comparing detected vs missed cases...")
    comparison = compare_detected_vs_missed(both_detected, neither)
    print(f"  Detected Pre-F avg: {comparison['detected_f_scores']['pre_f']['avg']:.3f}")
    print(f"  Missed Pre-F avg: {comparison['missed_f_scores']['pre_f']['avg']:.3f}")
    print()

    # Save results
    output = {
        'summary': {
            'total_neither': len(neither),
            'total_both_detected': len(both_detected),
            'unique_prompts_missed': prompt_patterns['unique_prompts']
        },
        'f_score_analysis': {
            'neither': neither_f,
            'both_detected': comparison['detected_f_scores']
        },
        'prompt_patterns': {
            'types': prompt_patterns['prompt_types'],
            'samples': prompt_patterns['sample_cases']
        },
        'response_patterns': response_patterns,
        'comparison': {
            'detected_models': comparison['detected_models'],
            'missed_models': comparison['missed_models']
        }
    }

    output_file = "/home/tony/projects/promptguard/blind_spots_analysis_raw.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Raw analysis saved to: {output_file}")
    print()
    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
