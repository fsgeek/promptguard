#!/usr/bin/env python3
"""
Pairwise Correlation Analysis for Fire Circle Echo Chamber Detection

Analyzes model pair correlations to identify:
1. Echo chambers (>70% agreement = redundant models)
2. Complementary pairs (<50% agreement = true diversity)
3. Optimal ensemble configurations (maximize coverage, minimize cost)
"""

import json
import numpy as np
from scipy.stats import pearsonr, spearmanr
from collections import defaultdict
from itertools import combinations
from typing import Dict, List, Tuple


def load_data(filepath: str) -> Dict:
    """Load raw calibration results."""
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_model_pairs(models: List[str]) -> List[Tuple[str, str]]:
    """Generate all pairwise combinations."""
    return list(combinations(models, 2))


def calculate_detection_agreement(
    results: List[Dict],
    model_a: str,
    model_b: str
) -> Dict[str, float]:
    """
    Calculate detection agreement metrics between two models.

    Returns:
    - agreement: % of prompts where both agree (both detect OR both miss)
    - both_detect: % where both detect
    - both_miss: % where both miss
    - a_only: % where only A detects
    - b_only: % where only B detects
    """
    both_detect = 0
    both_miss = 0
    a_only = 0
    b_only = 0
    total = 0

    for result in results:
        evals = result.get('evaluations', {})
        if model_a not in evals or model_b not in evals:
            continue

        a_detected = evals[model_a].get('detected', False)
        b_detected = evals[model_b].get('detected', False)

        if a_detected and b_detected:
            both_detect += 1
        elif not a_detected and not b_detected:
            both_miss += 1
        elif a_detected and not b_detected:
            a_only += 1
        elif not a_detected and b_detected:
            b_only += 1

        total += 1

    agreement = (both_detect + both_miss) / total if total > 0 else 0

    return {
        'total_prompts': total,
        'agreement': agreement,
        'both_detect': both_detect / total if total > 0 else 0,
        'both_miss': both_miss / total if total > 0 else 0,
        'a_only': a_only / total if total > 0 else 0,
        'b_only': b_only / total if total > 0 else 0,
        'a_unique_contribution': a_only,
        'b_unique_contribution': b_only
    }


def calculate_fscore_correlation(
    results: List[Dict],
    model_a: str,
    model_b: str
) -> Dict[str, float]:
    """
    Calculate F-score correlation (Pearson and Spearman).

    Returns correlation coefficients and p-values.
    """
    a_scores = []
    b_scores = []

    for result in results:
        evals = result.get('evaluations', {})
        if model_a not in evals or model_b not in evals:
            continue

        a_f = evals[model_a].get('F', 0)
        b_f = evals[model_b].get('F', 0)

        a_scores.append(a_f)
        b_scores.append(b_f)

    if len(a_scores) < 2:
        return {
            'pearson_r': 0,
            'pearson_p': 1,
            'spearman_r': 0,
            'spearman_p': 1,
            'n_samples': 0
        }

    pearson_r, pearson_p = pearsonr(a_scores, b_scores)
    spearman_r, spearman_p = spearmanr(a_scores, b_scores)

    return {
        'pearson_r': float(pearson_r),
        'pearson_p': float(pearson_p),
        'spearman_r': float(spearman_r),
        'spearman_p': float(spearman_p),
        'n_samples': len(a_scores),
        'a_mean_f': float(np.mean(a_scores)),
        'b_mean_f': float(np.mean(b_scores)),
        'a_std_f': float(np.std(a_scores)),
        'b_std_f': float(np.std(b_scores))
    }


def calculate_all_pairwise_metrics(data: Dict) -> Dict:
    """Calculate all pairwise correlation metrics."""
    models = data['models']
    results = data['results']
    pairs = extract_model_pairs(models)

    pairwise_metrics = {}

    for model_a, model_b in pairs:
        pair_key = f"{model_a.split('/')[-1]}_vs_{model_b.split('/')[-1]}"

        detection = calculate_detection_agreement(results, model_a, model_b)
        fscore = calculate_fscore_correlation(results, model_a, model_b)

        pairwise_metrics[pair_key] = {
            'model_a': model_a,
            'model_b': model_b,
            'detection_agreement': detection,
            'fscore_correlation': fscore
        }

    return pairwise_metrics


def identify_echo_chambers(metrics: Dict) -> Dict[str, List[str]]:
    """
    Classify pairs by correlation strength.

    Thresholds:
    - High (>0.70): Echo chamber, redundant
    - Moderate (0.40-0.70): Some overlap, distinct perspectives
    - Low (<0.40): True diversity, complementary
    """
    echo_chambers = []
    moderate = []
    complementary = []

    for pair_key, data in metrics.items():
        agreement = data['detection_agreement']['agreement']

        if agreement > 0.70:
            echo_chambers.append({
                'pair': pair_key,
                'agreement': agreement,
                'models': (data['model_a'], data['model_b'])
            })
        elif agreement >= 0.40:
            moderate.append({
                'pair': pair_key,
                'agreement': agreement,
                'models': (data['model_a'], data['model_b'])
            })
        else:
            complementary.append({
                'pair': pair_key,
                'agreement': agreement,
                'models': (data['model_a'], data['model_b'])
            })

    return {
        'echo_chambers': sorted(echo_chambers, key=lambda x: x['agreement'], reverse=True),
        'moderate': sorted(moderate, key=lambda x: x['agreement'], reverse=True),
        'complementary': sorted(complementary, key=lambda x: x['agreement'])
    }


def calculate_ensemble_coverage(
    results: List[Dict],
    models: List[str]
) -> Dict[str, float]:
    """
    Calculate ensemble detection metrics.

    Returns:
    - total_detections: Union of all model detections
    - overlap: Prompts detected by ALL models
    - unique_per_model: Detections unique to each model
    """
    detection_sets = {model: set() for model in models}

    for i, result in enumerate(results):
        evals = result.get('evaluations', {})
        for model in models:
            if model in evals and evals[model].get('detected', False):
                detection_sets[model].add(i)

    # Union (any model detects)
    union = set()
    for detections in detection_sets.values():
        union.update(detections)

    # Intersection (all models detect)
    intersection = set(detection_sets[models[0]])
    for model in models[1:]:
        intersection.intersection_update(detection_sets[model])

    # Unique contributions
    unique = {}
    for model in models:
        # Detections unique to this model (no other model detects)
        other_detections = set()
        for other_model in models:
            if other_model != model:
                other_detections.update(detection_sets[other_model])

        unique[model] = detection_sets[model] - other_detections

    total_prompts = len(results)

    return {
        'total_prompts': total_prompts,
        'union_coverage': len(union) / total_prompts if total_prompts > 0 else 0,
        'intersection_coverage': len(intersection) / total_prompts if total_prompts > 0 else 0,
        'unique_contributions': {
            model: len(unique[model]) / total_prompts if total_prompts > 0 else 0
            for model in models
        },
        'unique_counts': {model: len(unique[model]) for model in models}
    }


def find_optimal_ensemble(
    data: Dict,
    metrics: Dict,
    cost_per_eval: Dict[str, float]
) -> Dict:
    """
    Find optimal ensemble configurations by testing all combinations.

    Strategy:
    - Maximize coverage (union of detections)
    - Minimize cost
    - Minimize pairwise correlation (redundancy)
    """
    models = data['models']
    results = data['results']

    optimal = {}

    # Test all 2-model combinations
    for model_a, model_b in combinations(models, 2):
        ensemble_models = [model_a, model_b]
        coverage = calculate_ensemble_coverage(results, ensemble_models)
        cost = sum(cost_per_eval[m] for m in ensemble_models)

        pair_key = f"{model_a.split('/')[-1]}_vs_{model_b.split('/')[-1]}"
        agreement = metrics[pair_key]['detection_agreement']['agreement']

        optimal[f"2model_{pair_key}"] = {
            'models': ensemble_models,
            'coverage': coverage['union_coverage'],
            'cost_per_eval': cost,
            'pairwise_agreement': agreement,
            'unique_contributions': coverage['unique_contributions'],
            'score': coverage['union_coverage'] / (cost * (1 + agreement))  # Maximize coverage, minimize cost and redundancy
        }

    # Test all 3-model combinations
    for combo in combinations(models, 3):
        ensemble_models = list(combo)
        coverage = calculate_ensemble_coverage(results, ensemble_models)
        cost = sum(cost_per_eval[m] for m in ensemble_models)

        # Average pairwise agreement
        agreements = []
        for model_a, model_b in combinations(ensemble_models, 2):
            pair_key = f"{model_a.split('/')[-1]}_vs_{model_b.split('/')[-1]}"
            if pair_key not in metrics:
                # Try reversed key
                pair_key = f"{model_b.split('/')[-1]}_vs_{model_a.split('/')[-1]}"
            if pair_key in metrics:
                agreements.append(metrics[pair_key]['detection_agreement']['agreement'])

        avg_agreement = np.mean(agreements) if agreements else 0

        combo_key = "_".join([m.split('/')[-1] for m in ensemble_models])
        optimal[f"3model_{combo_key}"] = {
            'models': ensemble_models,
            'coverage': coverage['union_coverage'],
            'cost_per_eval': cost,
            'avg_pairwise_agreement': avg_agreement,
            'unique_contributions': coverage['unique_contributions'],
            'score': coverage['union_coverage'] / (cost * (1 + avg_agreement))
        }

    # Current 4-model baseline
    coverage_4 = calculate_ensemble_coverage(results, models)
    cost_4 = sum(cost_per_eval[m] for m in models)

    agreements_4 = []
    for model_a, model_b in combinations(models, 2):
        pair_key = f"{model_a.split('/')[-1]}_vs_{model_b.split('/')[-1]}"
        if pair_key in metrics:
            agreements_4.append(metrics[pair_key]['detection_agreement']['agreement'])

    optimal['4model_current'] = {
        'models': models,
        'coverage': coverage_4['union_coverage'],
        'cost_per_eval': cost_4,
        'avg_pairwise_agreement': np.mean(agreements_4),
        'unique_contributions': coverage_4['unique_contributions'],
        'score': coverage_4['union_coverage'] / (cost_4 * (1 + np.mean(agreements_4)))
    }

    return optimal


def analyze_cultural_clustering(metrics: Dict) -> Dict:
    """
    Test cultural diversity hypothesis:
    Western (Claude, GPT-4o) vs Chinese (Kimi, DeepSeek)

    Do cross-cultural pairs show lower correlation than within-culture?
    """
    western = ['claude-sonnet-4.5', 'gpt-4o']
    chinese = ['kimi-k2-0905', 'deepseek-v3.1-terminus']

    within_western = []
    within_chinese = []
    cross_cultural = []

    for pair_key, data in metrics.items():
        a_short = data['model_a'].split('/')[-1]
        b_short = data['model_b'].split('/')[-1]
        agreement = data['detection_agreement']['agreement']

        a_western = any(w in a_short for w in ['claude', 'gpt'])
        b_western = any(w in b_short for w in ['claude', 'gpt'])

        if a_western and b_western:
            within_western.append(agreement)
        elif not a_western and not b_western:
            within_chinese.append(agreement)
        else:
            cross_cultural.append(agreement)

    return {
        'within_western': {
            'mean_agreement': float(np.mean(within_western)) if within_western else 0,
            'count': len(within_western),
            'values': within_western
        },
        'within_chinese': {
            'mean_agreement': float(np.mean(within_chinese)) if within_chinese else 0,
            'count': len(within_chinese),
            'values': within_chinese
        },
        'cross_cultural': {
            'mean_agreement': float(np.mean(cross_cultural)) if cross_cultural else 0,
            'count': len(cross_cultural),
            'values': cross_cultural
        },
        'hypothesis': 'Cross-cultural pairs should show LOWER agreement than within-culture if cultural diversity matters',
        'result': 'CONFIRMED' if np.mean(cross_cultural) < min(np.mean(within_western), np.mean(within_chinese)) else 'REJECTED'
    }


def main():
    """Run complete pairwise correlation analysis."""
    print("Loading calibration data...")
    data = load_data('diversity_calibration_raw.json')

    print(f"Analyzing {data['total_prompts']} prompts across {len(data['models'])} models...")
    print(f"Models: {data['models']}\n")

    # Calculate all pairwise metrics
    print("Calculating pairwise metrics...")
    metrics = calculate_all_pairwise_metrics(data)

    # Identify echo chambers
    print("Identifying echo chambers...")
    chambers = identify_echo_chambers(metrics)

    # Cultural clustering analysis
    print("Analyzing cultural clustering...")
    cultural = analyze_cultural_clustering(metrics)

    # Find optimal ensembles
    print("Finding optimal ensemble configurations...")

    # Model costs (from diversity_calibration_matrix.json)
    cost_per_eval = {
        'anthropic/claude-sonnet-4.5': 0.015,
        'moonshotai/kimi-k2-0905': 0.003,
        'deepseek/deepseek-v3.1-terminus': 0.001,
        'openai/gpt-4o': 0.008
    }

    optimal = find_optimal_ensemble(data, metrics, cost_per_eval)

    # Save results
    print("\nSaving results...")

    # 1. Pairwise correlation matrix (JSON)
    output = {
        'detection_agreement': {
            pair: metrics[pair]['detection_agreement']
            for pair in metrics
        },
        'fscore_correlation': {
            pair: metrics[pair]['fscore_correlation']
            for pair in metrics
        },
        'unique_contributions': {
            pair: {
                'a_unique': metrics[pair]['detection_agreement']['a_unique_contribution'],
                'b_unique': metrics[pair]['detection_agreement']['b_unique_contribution']
            }
            for pair in metrics
        }
    }

    with open('pairwise_correlation_matrix.json', 'w') as f:
        json.dump(output, f, indent=2)

    print("✓ Saved pairwise_correlation_matrix.json")

    # 2. Echo chamber analysis (Markdown)
    with open('echo_chamber_analysis.md', 'w') as f:
        f.write("# Echo Chamber Analysis\n\n")
        f.write("## Executive Summary\n\n")

        if chambers['echo_chambers']:
            strongest = chambers['echo_chambers'][0]
            f.write(f"**Strongest echo chamber:** {strongest['pair']} ({strongest['agreement']:.1%} agreement)\n\n")

        f.write(f"- Echo chambers (>70%): {len(chambers['echo_chambers'])}\n")
        f.write(f"- Moderate overlap (40-70%): {len(chambers['moderate'])}\n")
        f.write(f"- Complementary pairs (<40%): {len(chambers['complementary'])}\n\n")

        f.write("## Echo Chambers (>70% Agreement)\n\n")
        if chambers['echo_chambers']:
            f.write("These pairs are REDUNDANT. Drop one model from each pair.\n\n")
            for chamber in chambers['echo_chambers']:
                f.write(f"- **{chamber['pair']}**: {chamber['agreement']:.1%} agreement\n")
                pair_data = metrics[chamber['pair']]
                f.write(f"  - Both detect: {pair_data['detection_agreement']['both_detect']:.1%}\n")
                f.write(f"  - Both miss: {pair_data['detection_agreement']['both_miss']:.1%}\n")
                f.write(f"  - F-score correlation: {pair_data['fscore_correlation']['pearson_r']:.2f}\n\n")
        else:
            f.write("No echo chambers detected. All pairs show <70% agreement.\n\n")

        f.write("## Moderate Overlap (40-70%)\n\n")
        if chambers['moderate']:
            f.write("Some overlap but distinct perspectives. Evaluate cost vs coverage.\n\n")
            for pair in chambers['moderate']:
                f.write(f"- **{pair['pair']}**: {pair['agreement']:.1%} agreement\n")
        else:
            f.write("No moderate overlap pairs.\n\n")

        f.write("## Complementary Pairs (<40%)\n\n")
        if chambers['complementary']:
            f.write("True diversity. These pairs provide complementary coverage.\n\n")
            for pair in chambers['complementary']:
                f.write(f"- **{pair['pair']}**: {pair['agreement']:.1%} agreement\n")
                pair_data = metrics[pair['pair']]
                f.write(f"  - Model A unique: {pair_data['detection_agreement']['a_unique_contribution']} prompts\n")
                f.write(f"  - Model B unique: {pair_data['detection_agreement']['b_unique_contribution']} prompts\n\n")
        else:
            f.write("No highly complementary pairs (<40%).\n\n")

        f.write("## Cultural Clustering Effects\n\n")
        f.write(f"**Hypothesis:** Cross-cultural pairs (Western vs Chinese) should show LOWER agreement than within-culture pairs if cultural diversity matters.\n\n")
        f.write(f"**Result:** {cultural['result']}\n\n")
        f.write(f"- Within Western (Claude + GPT-4o): {cultural['within_western']['mean_agreement']:.1%} agreement\n")
        f.write(f"- Within Chinese (Kimi + DeepSeek): {cultural['within_chinese']['mean_agreement']:.1%} agreement\n")
        f.write(f"- Cross-cultural: {cultural['cross_cultural']['mean_agreement']:.1%} agreement\n\n")

        if cultural['result'] == 'CONFIRMED':
            f.write("Cultural diversity DOES reduce echo chamber effects. Cross-cultural pairs show lower correlation.\n\n")
        else:
            f.write("Cultural diversity does NOT reliably reduce correlation. Within-culture pairs show similar or lower agreement than cross-cultural pairs.\n\n")

        f.write("## Recommendation\n\n")
        if chambers['echo_chambers']:
            f.write(f"Drop one model from the strongest echo chamber ({chambers['echo_chambers'][0]['pair']}) to eliminate redundancy.\n\n")
        else:
            f.write("All pairs show <70% agreement. Consider 3-model ensemble for cost optimization.\n\n")

    print("✓ Saved echo_chamber_analysis.md")

    # 3. Optimal ensemble recommendation (Markdown)
    with open('optimal_ensemble_recommendation.md', 'w') as f:
        f.write("# Optimal Ensemble Recommendation\n\n")

        # Find best 2-model and 3-model configurations
        two_model = [k for k in optimal.keys() if k.startswith('2model_')]
        three_model = [k for k in optimal.keys() if k.startswith('3model_')]

        best_2 = max(two_model, key=lambda k: optimal[k]['score'])
        best_3 = max(three_model, key=lambda k: optimal[k]['score'])
        current_4 = optimal['4model_current']

        f.write("## Executive Summary\n\n")
        f.write(f"**Best 2-model ensemble:** {optimal[best_2]['models']}\n")
        f.write(f"- Coverage: {optimal[best_2]['coverage']:.1%}\n")
        f.write(f"- Cost: ${optimal[best_2]['cost_per_eval']:.4f}/eval\n")
        f.write(f"- Pairwise agreement: {optimal[best_2]['pairwise_agreement']:.1%}\n\n")

        f.write(f"**Best 3-model ensemble:** {optimal[best_3]['models']}\n")
        f.write(f"- Coverage: {optimal[best_3]['coverage']:.1%}\n")
        f.write(f"- Cost: ${optimal[best_3]['cost_per_eval']:.4f}/eval\n")
        f.write(f"- Avg pairwise agreement: {optimal[best_3]['avg_pairwise_agreement']:.1%}\n\n")

        f.write(f"**Current 4-model ensemble:** {current_4['models']}\n")
        f.write(f"- Coverage: {current_4['coverage']:.1%}\n")
        f.write(f"- Cost: ${current_4['cost_per_eval']:.4f}/eval\n")
        f.write(f"- Avg pairwise agreement: {current_4['avg_pairwise_agreement']:.1%}\n\n")

        # Savings calculation
        savings_2 = (current_4['cost_per_eval'] - optimal[best_2]['cost_per_eval']) / current_4['cost_per_eval']
        coverage_loss_2 = current_4['coverage'] - optimal[best_2]['coverage']

        savings_3 = (current_4['cost_per_eval'] - optimal[best_3]['cost_per_eval']) / current_4['cost_per_eval']
        coverage_loss_3 = current_4['coverage'] - optimal[best_3]['coverage']

        f.write(f"**2-model savings:** {savings_2:.1%} cost reduction, {coverage_loss_2:.1%} coverage loss\n\n")
        f.write(f"**3-model savings:** {savings_3:.1%} cost reduction, {coverage_loss_3:.1%} coverage loss\n\n")

        f.write("## Detailed Analysis\n\n")
        f.write("### 2-Model Optimum\n\n")
        f.write(f"Models: {optimal[best_2]['models']}\n\n")
        f.write(f"- **Coverage:** {optimal[best_2]['coverage']:.1%} of attacks detected (union)\n")
        f.write(f"- **Cost:** ${optimal[best_2]['cost_per_eval']:.4f} per evaluation\n")
        f.write(f"- **Pairwise agreement:** {optimal[best_2]['pairwise_agreement']:.1%}\n")
        f.write(f"- **Optimization score:** {optimal[best_2]['score']:.4f}\n\n")

        f.write("Unique contributions:\n")
        for model, contrib in optimal[best_2]['unique_contributions'].items():
            f.write(f"- {model}: {contrib:.1%}\n")

        f.write("\n### 3-Model Optimum\n\n")
        f.write(f"Models: {optimal[best_3]['models']}\n\n")
        f.write(f"- **Coverage:** {optimal[best_3]['coverage']:.1%} of attacks detected (union)\n")
        f.write(f"- **Cost:** ${optimal[best_3]['cost_per_eval']:.4f} per evaluation\n")
        f.write(f"- **Avg pairwise agreement:** {optimal[best_3]['avg_pairwise_agreement']:.1%}\n")
        f.write(f"- **Optimization score:** {optimal[best_3]['score']:.4f}\n\n")

        f.write("Unique contributions:\n")
        for model, contrib in optimal[best_3]['unique_contributions'].items():
            f.write(f"- {model}: {contrib:.1%}\n")

        f.write("\n### Current 4-Model Baseline\n\n")
        f.write(f"Models: {current_4['models']}\n\n")
        f.write(f"- **Coverage:** {current_4['coverage']:.1%} of attacks detected (union)\n")
        f.write(f"- **Cost:** ${current_4['cost_per_eval']:.4f} per evaluation\n")
        f.write(f"- **Avg pairwise agreement:** {current_4['avg_pairwise_agreement']:.1%}\n")
        f.write(f"- **Optimization score:** {current_4['score']:.4f}\n\n")

        f.write("Unique contributions:\n")
        for model, contrib in current_4['unique_contributions'].items():
            f.write(f"- {model}: {contrib:.1%}\n")

        f.write("\n## Recommendation\n\n")

        # Decision logic
        if coverage_loss_2 < 0.05 and savings_2 > 0.40:
            f.write(f"**Choose 2-model ensemble** ({optimal[best_2]['models']})\n\n")
            f.write(f"Rationale: {savings_2:.1%} cost reduction with only {coverage_loss_2:.1%} coverage loss is excellent ROI.\n")
        elif coverage_loss_3 < 0.03 and savings_3 > 0.25:
            f.write(f"**Choose 3-model ensemble** ({optimal[best_3]['models']})\n\n")
            f.write(f"Rationale: {savings_3:.1%} cost reduction with minimal {coverage_loss_3:.1%} coverage loss balances cost and coverage.\n")
        else:
            f.write(f"**Keep 4-model ensemble** ({current_4['models']})\n\n")
            f.write(f"Rationale: Coverage loss from smaller ensembles exceeds cost savings benefit.\n")

    print("✓ Saved optimal_ensemble_recommendation.md")

    # Print summary
    print("\n" + "="*70)
    print("PAIRWISE CORRELATION ANALYSIS COMPLETE")
    print("="*70)

    if chambers['echo_chambers']:
        strongest = chambers['echo_chambers'][0]
        print(f"\n🔴 STRONGEST ECHO CHAMBER: {strongest['pair']}")
        print(f"   Agreement: {strongest['agreement']:.1%}")
        print(f"   Recommendation: Drop one model to eliminate redundancy")
    else:
        print("\n✅ NO ECHO CHAMBERS DETECTED")
        print("   All pairs show <70% agreement")

    print(f"\n📊 OPTIMAL ENSEMBLE:")
    print(f"   Best 2-model: {optimal[best_2]['models']}")
    print(f"   Coverage: {optimal[best_2]['coverage']:.1%} | Cost: ${optimal[best_2]['cost_per_eval']:.4f}/eval")
    print(f"   Savings vs 4-model: {savings_2:.1%} cost, {coverage_loss_2:.1%} coverage loss")

    print(f"\n📁 OUTPUT FILES:")
    print(f"   1. pairwise_correlation_matrix.json")
    print(f"   2. echo_chamber_analysis.md")
    print(f"   3. optimal_ensemble_recommendation.md")
    print()


if __name__ == '__main__':
    main()
