#!/usr/bin/env python3
"""
Deep pattern analysis of the 202 missed cases.

Examines:
1. Why are "reciprocal" prompts scoring low F? (legitimate helpful requests)
2. What makes these compliant responses undetectable?
3. Comparison with detected cases to find the gap
"""

import json
from collections import defaultdict, Counter
from typing import Dict, List, Any


def analyze_sample_cases(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the sample cases in detail."""

    # Group by prompt type
    by_type = defaultdict(list)
    for sample in samples:
        by_type[sample['type']].append(sample)

    analysis = {}

    # Analyze benign_malicious cases (should be RECIPROCAL, but scoring low F)
    if 'benign_malicious' in by_type:
        bm_cases = by_type['benign_malicious']

        # Extract patterns
        prompt_characteristics = []
        for case in bm_cases:
            prompt = case['prompt']
            response = case['response']

            # Analyze prompt
            prompt_len = len(prompt)
            is_directive = any(word in prompt.lower() for word in ['create', 'write', 'design', 'build', 'develop', 'generate'])
            is_detailed = len(prompt) > 200
            has_requirements = any(word in prompt.lower() for word in ['must', 'should', 'include', 'ensure', 'requirement'])

            # Analyze response
            response_len = len(response)
            is_comprehensive = response_len > 1000
            has_structure = response.count('#') > 5  # Markdown headers

            prompt_characteristics.append({
                'prompt_id': case['prompt_id'],
                'prompt_len': prompt_len,
                'response_len': response_len,
                'is_directive': is_directive,
                'is_detailed': is_detailed,
                'has_requirements': has_requirements,
                'is_comprehensive': is_comprehensive,
                'has_structure': has_structure,
                'pre_f': case['pre_f'],
                'post_f': case['post_f'],
                'prompt_snippet': prompt[:150] + '...' if len(prompt) > 150 else prompt
            })

        analysis['benign_malicious'] = {
            'count': len(bm_cases),
            'avg_pre_f': sum(c['pre_f'] for c in bm_cases) / len(bm_cases),
            'avg_post_f': sum(c['post_f'] for c in bm_cases) / len(bm_cases),
            'directive_prompts': sum(1 for c in prompt_characteristics if c['is_directive']),
            'detailed_prompts': sum(1 for c in prompt_characteristics if c['is_detailed']),
            'comprehensive_responses': sum(1 for c in prompt_characteristics if c['is_comprehensive']),
            'cases': prompt_characteristics
        }

    # Analyze OR-Bench cases (unknown type)
    if 'unknown' in by_type:
        or_cases = by_type['unknown']

        or_analysis = []
        for case in or_cases:
            prompt = case['prompt']
            response = case['response']

            # These are supposed to be reciprocal (safe prompts about sensitive topics)
            # Why are they scoring low?

            # Check for sensitive topics
            sensitive_keywords = ['harm', 'damage', 'vulnerable', 'control', 'persuade', 'manipulate']
            has_sensitive = any(kw in prompt.lower() for kw in sensitive_keywords)

            or_analysis.append({
                'prompt_id': case['prompt_id'],
                'has_sensitive_keywords': has_sensitive,
                'pre_f': case['pre_f'],
                'post_f': case['post_f'],
                'prompt': prompt
            })

        analysis['or_bench'] = {
            'count': len(or_cases),
            'avg_pre_f': sum(c['pre_f'] for c in or_cases) / len(or_cases),
            'avg_post_f': sum(c['post_f'] for c in or_cases) / len(or_cases),
            'with_sensitive_keywords': sum(1 for c in or_analysis if c['has_sensitive_keywords']),
            'cases': or_analysis
        }

    return analysis


def compare_f_scores(missed_cases: List[Dict], detected_cases: List[Dict]) -> Dict[str, Any]:
    """Compare F score patterns between missed and detected."""

    # Missed cases distribution
    missed_pre_f_bins = Counter()
    missed_post_f_bins = Counter()

    for case in missed_cases:
        pre_f = case['pre_f']
        post_f = case['post_f']

        # Bin into ranges
        missed_pre_f_bins[f"{int(pre_f*10)/10:.1f}-{int(pre_f*10)/10 + 0.1:.1f}"] += 1
        missed_post_f_bins[f"{int(post_f*10)/10:.1f}-{int(post_f*10)/10 + 0.1:.1f}"] += 1

    # Detected cases distribution
    detected_pre_f_bins = Counter()
    detected_post_f_bins = Counter()

    for case in detected_cases:
        pre_f = case['pre_f']
        post_f = case['post_f']

        detected_pre_f_bins[f"{int(pre_f*10)/10:.1f}-{int(pre_f*10)/10 + 0.1:.1f}"] += 1
        detected_post_f_bins[f"{int(post_f*10)/10:.1f}-{int(post_f*10)/10 + 0.1:.1f}"] += 1

    return {
        'missed': {
            'pre_f_distribution': dict(sorted(missed_pre_f_bins.items())),
            'post_f_distribution': dict(sorted(missed_post_f_bins.items())),
            'pre_f_avg': sum(c['pre_f'] for c in missed_cases) / len(missed_cases),
            'post_f_avg': sum(c['post_f'] for c in missed_cases) / len(missed_cases)
        },
        'detected': {
            'pre_f_distribution': dict(sorted(detected_pre_f_bins.items())),
            'post_f_distribution': dict(sorted(detected_post_f_bins.items())),
            'pre_f_avg': sum(c['pre_f'] for c in detected_cases) / len(detected_cases),
            'post_f_avg': sum(c['post_f'] for c in detected_cases) / len(detected_cases)
        }
    }


def identify_blind_spot_patterns(analysis: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on patterns."""

    recommendations = []

    # Check benign_malicious patterns
    if 'benign_malicious' in analysis:
        bm = analysis['benign_malicious']

        if bm['directive_prompts'] / bm['count'] > 0.7:
            recommendations.append(
                "PATTERN: Directive language (create, write, develop) in reciprocal prompts "
                "is incorrectly triggering low F scores. These are legitimate creative/technical "
                "requests, not manipulative prompts."
            )

        if bm['comprehensive_responses'] / bm['count'] > 0.7:
            recommendations.append(
                "PATTERN: Comprehensive, structured responses to legitimate requests "
                "are scoring as manipulative. The framework may be conflating "
                "'detailed assistance' with 'successful manipulation'."
            )

        if bm['avg_post_f'] < bm['avg_pre_f']:
            recommendations.append(
                "CRITICAL: Post-F scores are LOWER than Pre-F, suggesting PromptGuard "
                "interprets helpful compliance as evidence of manipulation. This is backwards."
            )

    # Check OR-Bench patterns
    if 'or_bench' in analysis:
        or_bench = analysis['or_bench']

        if or_bench['with_sensitive_keywords'] / or_bench['count'] > 0.5:
            recommendations.append(
                "PATTERN: OR-Bench prompts contain sensitive keywords (harm, control, persuade) "
                "but are asking about ETHICAL approaches. PromptGuard may be reacting to "
                "keywords rather than intent."
            )

    return recommendations


def main():
    """Main analysis."""
    print("=" * 80)
    print("DEEP PATTERN ANALYSIS - 202 MISSED CASES")
    print("=" * 80)
    print()

    # Load data
    with open('/home/tony/projects/promptguard/blind_spots_analysis_raw.json') as f:
        data = json.load(f)

    samples = data['prompt_patterns']['samples']

    print(f"Analyzing {len(samples)} sample cases...")
    print()

    # Analyze sample patterns
    print("=" * 80)
    print("SAMPLE CASE ANALYSIS")
    print("=" * 80)
    analysis = analyze_sample_cases(samples)

    for ptype, pdata in analysis.items():
        print(f"\n{ptype.upper()} ({pdata['count']} cases):")
        print(f"  Avg Pre-F: {pdata['avg_pre_f']:.3f}")
        print(f"  Avg Post-F: {pdata['avg_post_f']:.3f}")

        if ptype == 'benign_malicious':
            print(f"  Directive prompts: {pdata['directive_prompts']}/{pdata['count']} ({pdata['directive_prompts']/pdata['count']*100:.1f}%)")
            print(f"  Detailed prompts: {pdata['detailed_prompts']}/{pdata['count']} ({pdata['detailed_prompts']/pdata['count']*100:.1f}%)")
            print(f"  Comprehensive responses: {pdata['comprehensive_responses']}/{pdata['count']} ({pdata['comprehensive_responses']/pdata['count']*100:.1f}%)")

        elif ptype == 'or_bench':
            print(f"  With sensitive keywords: {pdata['with_sensitive_keywords']}/{pdata['count']} ({pdata['with_sensitive_keywords']/pdata['count']*100:.1f}%)")

    # Load full overlap data for F-score comparison
    print("\n" + "=" * 80)
    print("F-SCORE COMPARISON")
    print("=" * 80)

    with open('/home/tony/projects/promptguard/rlhf_pg_overlap_decrypted_target_response_analysis_2025-10-16-22-15.json') as f:
        overlap = json.load(f)

    f_comparison = compare_f_scores(overlap['neither'], overlap['both_detected'])

    print("\nMISSED CASES:")
    print(f"  Pre-F avg: {f_comparison['missed']['pre_f_avg']:.3f}")
    print(f"  Post-F avg: {f_comparison['missed']['post_f_avg']:.3f}")
    print(f"  Pre-F distribution: {f_comparison['missed']['pre_f_distribution']}")

    print("\nDETECTED CASES:")
    print(f"  Pre-F avg: {f_comparison['detected']['pre_f_avg']:.3f}")
    print(f"  Post-F avg: {f_comparison['detected']['post_f_avg']:.3f}")
    print(f"  Pre-F distribution: {f_comparison['detected']['pre_f_distribution']}")

    # Generate recommendations
    print("\n" + "=" * 80)
    print("BLIND SPOT PATTERNS & RECOMMENDATIONS")
    print("=" * 80)

    recommendations = identify_blind_spot_patterns(analysis)

    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec}")

    # Save detailed analysis
    output = {
        'sample_analysis': analysis,
        'f_score_comparison': f_comparison,
        'recommendations': recommendations
    }

    with open('/home/tony/projects/promptguard/deep_pattern_analysis.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("\n" + "=" * 80)
    print("Deep analysis saved to: deep_pattern_analysis.json")
    print("=" * 80)


if __name__ == '__main__':
    main()
