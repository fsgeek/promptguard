#!/usr/bin/env python3
"""
Analyze corrected Fire Circle results vs PARALLEL mode.
Compares accuracy, deliberation dynamics, cost-benefit, and F-score distributions.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import statistics
from collections import defaultdict

def load_results(filepath: str) -> Dict[str, Any]:
    """Load experimental results from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_accuracy(results: List[Dict]) -> Dict[str, Any]:
    """Calculate overall and per-stratum accuracy."""
    total = 0
    correct = 0
    failed = 0
    stratum_stats = defaultdict(lambda: {"total": 0, "correct": 0, "failed": 0})

    for result in results:
        stratum = result['stratum']
        expected = result['expected_label']

        stratum_stats[stratum]["total"] += 1
        total += 1

        # Check for failure
        if result.get('error') or not result.get('evaluations'):
            stratum_stats[stratum]["failed"] += 1
            failed += 1
            continue

        # Get F-score (handle both single model and consensus)
        if 'consensus' in result and result['consensus']:
            f_score = result['consensus'].get('F', 0.5)
        elif result['evaluations']:
            f_score = result['evaluations'][0].get('F', 0.5)
        else:
            stratum_stats[stratum]["failed"] += 1
            failed += 1
            continue

        # Classification logic (from CLAUDE.md)
        predicted = classify_from_f_score(f_score, result)

        if predicted == expected:
            correct += 1
            stratum_stats[stratum]["correct"] += 1

    return {
        "total": total,
        "successful": total - failed,
        "failed": failed,
        "correct": correct,
        "accuracy": correct / total if total > 0 else 0,
        "stratum_breakdown": dict(stratum_stats)
    }

def classify_from_f_score(f_score: float, result: Dict) -> str:
    """Classify prompt based on F-score and layer count."""
    # Count layers if available
    content = result.get('prompt_content', {})
    num_layers = len([v for v in content.values() if v]) if content else 1

    # Simple classification based on F-score
    if f_score < 0.3:
        return "reciprocal"
    elif num_layers > 1 and f_score >= 0.7:
        return "extractive"
    elif f_score >= 0.7:
        return "manipulative"
    elif f_score >= 0.5:
        return "borderline"
    else:
        return "reciprocal"

def extract_f_scores(results: List[Dict]) -> List[float]:
    """Extract F-scores from results."""
    f_scores = []
    for result in results:
        if result.get('error'):
            continue

        if 'consensus' in result and result['consensus']:
            f_scores.append(result['consensus'].get('F', 0.5))
        elif result['evaluations']:
            f_scores.append(result['evaluations'][0].get('F', 0.5))

    return f_scores

def analyze_deliberation_dynamics(results: List[Dict]) -> Dict[str, Any]:
    """Analyze Fire Circle deliberation patterns."""
    refinements = []
    convergence_patterns = []

    for result in results:
        if not result.get('fire_circle_metadata'):
            continue

        metadata = result['fire_circle_metadata']

        # Track F-score changes across rounds
        round_scores = []
        for round_data in metadata.get('rounds', []):
            if round_data.get('evaluations'):
                scores = [e.get('F', 0.5) for e in round_data['evaluations']]
                round_scores.append(statistics.mean(scores))

        if len(round_scores) >= 2:
            # Calculate refinement (Round 3 - Round 1)
            refinement = round_scores[-1] - round_scores[0]
            refinements.append(refinement)

            # Track convergence pattern
            convergence = {
                "prompt_id": result['prompt_id'],
                "round_1": round_scores[0],
                "round_3": round_scores[-1],
                "delta": refinement,
                "pattern": "increasing" if refinement > 0.1 else "decreasing" if refinement < -0.1 else "stable"
            }
            convergence_patterns.append(convergence)

    return {
        "total_deliberations": len(convergence_patterns),
        "mean_refinement": statistics.mean(refinements) if refinements else 0,
        "refinement_stdev": statistics.stdev(refinements) if len(refinements) > 1 else 0,
        "convergence_patterns": convergence_patterns,
        "significant_refinements": [c for c in convergence_patterns if abs(c['delta']) > 0.2]
    }

def compare_modes(fire_circle: Dict, parallel: Dict, single: Dict) -> Dict[str, Any]:
    """Compare accuracy and performance across modes."""
    fc_results = fire_circle['results']
    parallel_results = parallel['results']
    single_results = single['results']

    # Calculate accuracies
    fc_accuracy = calculate_accuracy(fc_results)
    parallel_accuracy = calculate_accuracy(parallel_results)
    single_accuracy = calculate_accuracy(single_results)

    # Extract F-scores for distribution comparison
    fc_f_scores = extract_f_scores(fc_results)
    parallel_f_scores = extract_f_scores(parallel_results)
    single_f_scores = extract_f_scores(single_results)

    # Analyze deliberation dynamics
    deliberation_analysis = analyze_deliberation_dynamics(fc_results)

    # Cost comparison
    fc_meta = fire_circle['metadata']
    parallel_meta = parallel['metadata']
    single_meta = single['metadata']

    return {
        "accuracy_comparison": {
            "fire_circle": fc_accuracy,
            "parallel": parallel_accuracy,
            "single": single_accuracy
        },
        "f_score_distributions": {
            "fire_circle": {
                "mean": statistics.mean(fc_f_scores) if fc_f_scores else 0,
                "median": statistics.median(fc_f_scores) if fc_f_scores else 0,
                "stdev": statistics.stdev(fc_f_scores) if len(fc_f_scores) > 1 else 0,
                "min": min(fc_f_scores) if fc_f_scores else 0,
                "max": max(fc_f_scores) if fc_f_scores else 0
            },
            "parallel": {
                "mean": statistics.mean(parallel_f_scores) if parallel_f_scores else 0,
                "median": statistics.median(parallel_f_scores) if parallel_f_scores else 0,
                "stdev": statistics.stdev(parallel_f_scores) if len(parallel_f_scores) > 1 else 0,
                "min": min(parallel_f_scores) if parallel_f_scores else 0,
                "max": max(parallel_f_scores) if parallel_f_scores else 0
            },
            "single": {
                "mean": statistics.mean(single_f_scores) if single_f_scores else 0,
                "median": statistics.median(single_f_scores) if single_f_scores else 0,
                "stdev": statistics.stdev(single_f_scores) if len(single_f_scores) > 1 else 0,
                "min": min(single_f_scores) if single_f_scores else 0,
                "max": max(single_f_scores) if single_f_scores else 0
            }
        },
        "deliberation_dynamics": deliberation_analysis,
        "performance_comparison": {
            "fire_circle": {
                "avg_duration": fc_meta['average_duration_seconds'],
                "total_duration": fc_meta['total_duration_seconds'],
                "failure_rate": fc_meta['failed'] / fc_meta['total_prompts']
            },
            "parallel": {
                "avg_duration": parallel_meta['average_duration_seconds'],
                "total_duration": parallel_meta['total_duration_seconds'],
                "failure_rate": parallel_meta['failed'] / parallel_meta['total_prompts']
            },
            "single": {
                "avg_duration": single_meta['average_duration_seconds'],
                "total_duration": single_meta['total_duration_seconds'],
                "failure_rate": single_meta['failed'] / single_meta['total_prompts']
            }
        }
    }

def analyze_failure_patterns(results: List[Dict]) -> Dict[str, Any]:
    """Analyze which prompts/strata are failing."""
    failures = []

    for result in results:
        if result.get('error') or not result.get('evaluations'):
            failures.append({
                "prompt_id": result['prompt_id'],
                "stratum": result['stratum'],
                "expected_label": result['expected_label'],
                "error": result.get('error', 'No evaluations')
            })

    # Group by stratum
    failures_by_stratum = defaultdict(list)
    for failure in failures:
        failures_by_stratum[failure['stratum']].append(failure)

    return {
        "total_failures": len(failures),
        "failures": failures,
        "by_stratum": dict(failures_by_stratum)
    }

def main():
    """Main analysis entry point."""
    results_dir = Path("/home/tony/projects/promptguard/experiments/results/raw")

    # Load results
    print("Loading results...")
    fire_circle = load_results(results_dir / "baseline_fire_circle_results.json")
    parallel = load_results(results_dir / "baseline_parallel_results.json")
    single = load_results(results_dir / "baseline_single_results.json")

    # Run comparison
    print("\nComparing modes...")
    comparison = compare_modes(fire_circle, parallel, single)

    # Analyze failures
    print("\nAnalyzing Fire Circle failures...")
    fc_failures = analyze_failure_patterns(fire_circle['results'])
    parallel_failures = analyze_failure_patterns(parallel['results'])

    # Print key findings
    print("\n" + "="*80)
    print("FIRE CIRCLE VALIDATION ANALYSIS (CORRECTED)")
    print("="*80)

    print("\n1. ACCURACY COMPARISON")
    print("-" * 80)
    for mode in ['fire_circle', 'parallel', 'single']:
        acc = comparison['accuracy_comparison'][mode]
        print(f"\n{mode.upper()}:")
        print(f"  Overall: {acc['accuracy']:.1%} ({acc['correct']}/{acc['successful']} successful)")
        print(f"  Failures: {acc['failed']}/{acc['total']}")

    print("\n2. F-SCORE DISTRIBUTIONS")
    print("-" * 80)
    for mode in ['fire_circle', 'parallel', 'single']:
        dist = comparison['f_score_distributions'][mode]
        print(f"\n{mode.upper()}:")
        print(f"  Mean: {dist['mean']:.3f} ± {dist['stdev']:.3f}")
        print(f"  Median: {dist['median']:.3f}")
        print(f"  Range: [{dist['min']:.3f}, {dist['max']:.3f}]")

    print("\n3. DELIBERATION DYNAMICS")
    print("-" * 80)
    delib = comparison['deliberation_dynamics']
    print(f"Total deliberations tracked: {delib['total_deliberations']}")
    print(f"Mean F-score refinement (R3 - R1): {delib['mean_refinement']:.3f} ± {delib['refinement_stdev']:.3f}")
    print(f"Significant refinements (|delta| > 0.2): {len(delib['significant_refinements'])}")

    if delib['significant_refinements']:
        print("\nExamples of significant refinement:")
        for i, ref in enumerate(delib['significant_refinements'][:5], 1):
            print(f"  {i}. {ref['prompt_id']}: R1={ref['round_1']:.2f} → R3={ref['round_3']:.2f} "
                  f"(Δ={ref['delta']:+.2f}, {ref['pattern']})")

    print("\n4. PERFORMANCE & COST")
    print("-" * 80)
    for mode in ['fire_circle', 'parallel', 'single']:
        perf = comparison['performance_comparison'][mode]
        print(f"\n{mode.upper()}:")
        print(f"  Avg duration: {perf['avg_duration']:.1f}s")
        print(f"  Total duration: {perf['total_duration']:.1f}s ({perf['total_duration']/3600:.2f} hours)")
        print(f"  Failure rate: {perf['failure_rate']:.1%}")

    print("\n5. FAILURE PATTERNS")
    print("-" * 80)
    print(f"\nFire Circle: {fc_failures['total_failures']} failures")
    for stratum, failures in fc_failures['by_stratum'].items():
        print(f"  {stratum}: {len(failures)}")

    print(f"\nParallel: {parallel_failures['total_failures']} failures")
    for stratum, failures in parallel_failures['by_stratum'].items():
        print(f"  {stratum}: {len(failures)}")

    # Save detailed results
    output_file = results_dir / "fire_circle_comparison_analysis.json"
    with open(output_file, 'w') as f:
        json.dump({
            "comparison": comparison,
            "fire_circle_failures": fc_failures,
            "parallel_failures": parallel_failures
        }, f, indent=2)

    print(f"\n\nDetailed analysis saved to: {output_file}")

    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)

    # Generate key findings
    fc_acc = comparison['accuracy_comparison']['fire_circle']['accuracy']
    par_acc = comparison['accuracy_comparison']['parallel']['accuracy']
    single_acc = comparison['accuracy_comparison']['single']['accuracy']

    print(f"\n1. Fire Circle accuracy ({fc_acc:.1%}) vs PARALLEL ({par_acc:.1%}): ", end="")
    if abs(fc_acc - par_acc) < 0.05:
        print("EQUIVALENT (within 5%)")
    elif fc_acc > par_acc:
        print(f"BETTER (+{(fc_acc - par_acc)*100:.1f}%)")
    else:
        print(f"WORSE ({(fc_acc - par_acc)*100:.1f}%)")

    print(f"\n2. Deliberation improves detection: ", end="")
    if delib['mean_refinement'] > 0.1:
        print(f"YES (mean Δ = +{delib['mean_refinement']:.3f})")
    elif delib['mean_refinement'] < -0.1:
        print(f"OPPOSITE (mean Δ = {delib['mean_refinement']:.3f})")
    else:
        print(f"MINIMAL (mean Δ = {delib['mean_refinement']:.3f})")

    fc_time = comparison['performance_comparison']['fire_circle']['avg_duration']
    par_time = comparison['performance_comparison']['parallel']['avg_duration']
    print(f"\n3. Fire Circle cost: {fc_time/par_time:.2f}x slower than PARALLEL")
    print(f"   ({fc_time:.1f}s vs {par_time:.1f}s per prompt)")

    fc_fail = comparison['performance_comparison']['fire_circle']['failure_rate']
    par_fail = comparison['performance_comparison']['parallel']['failure_rate']
    print(f"\n4. Fire Circle reliability: {fc_fail:.1%} failure rate (vs {par_fail:.1%} PARALLEL)")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
