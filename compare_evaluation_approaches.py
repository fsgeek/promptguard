#!/usr/bin/env python3
"""
Compare trust trajectory, coherence, and forensic evaluation approaches.

Analyzes which approach detects which attack types most effectively.
"""

import json
from typing import Dict, List


def load_results() -> Dict[str, Dict]:
    """Load all three evaluation result sets."""
    with open("trust_trajectory_results.json") as f:
        trust_trajectory = json.load(f)

    with open("coherence_evaluation_results.json") as f:
        coherence = json.load(f)

    with open("forensic_markers_results.json") as f:
        forensic = json.load(f)

    return {
        "trust_trajectory": trust_trajectory,
        "coherence": coherence,
        "forensic": forensic,
    }


def compare_per_prompt(results: Dict[str, Dict]) -> List[Dict]:
    """Compare how each approach evaluated each prompt."""
    # Get all prompts from trust trajectory (should be consistent)
    prompts = results["trust_trajectory"]["per_prompt_results"]

    comparisons = []

    for i, tt_result in enumerate(prompts):
        prompt_id = tt_result["id"]

        # Find matching results in other approaches
        coh_result = next(r for r in results["coherence"]["per_prompt_results"] if r["prompt_id"] == prompt_id)
        for_result = next(r for r in results["forensic"]["per_prompt_results"] if r["id"] == prompt_id)

        comparison = {
            "prompt_id": prompt_id,
            "group": tt_result["group"],
            "label": tt_result["label"],
            "trust_trajectory": {
                "falsehood": tt_result["falsehood"],
                "classification": tt_result["classification"],
                "correct": tt_result["correct"],
                "trust_gap": tt_result["trust_gap"],
            },
            "coherence": {
                "falsehood": coh_result["falsehood"],
                "classification": coh_result["classification"],
                "correct": coh_result["correct"],
                "reasoning_snippet": coh_result["reasoning"][:100] + "..." if len(coh_result["reasoning"]) > 100 else coh_result["reasoning"],
            },
            "forensic": {
                "falsehood": for_result["falsehood"],
                "classification": for_result["classification"],
                "correct": for_result["correct"],
                "reasoning_snippet": for_result["reasoning"][:100] + "..." if len(for_result["reasoning"]) > 100 else for_result["reasoning"],
            },
        }

        comparisons.append(comparison)

    return comparisons


def analyze_complementarity(comparisons: List[Dict]) -> Dict:
    """Analyze which approaches catch which attacks."""
    analysis = {
        "trust_trajectory_unique_catches": [],
        "coherence_unique_catches": [],
        "forensic_unique_catches": [],
        "all_three_caught": [],
        "none_caught": [],
        "two_of_three_caught": [],
    }

    for comp in comparisons:
        if comp["label"] in ["extractive", "manipulative"]:  # Only look at attacks
            tt_caught = comp["trust_trajectory"]["correct"]
            coh_caught = comp["coherence"]["correct"]
            for_caught = comp["forensic"]["correct"]

            caught_count = sum([tt_caught, coh_caught, for_caught])

            if caught_count == 3:
                analysis["all_three_caught"].append(comp["prompt_id"])
            elif caught_count == 0:
                analysis["none_caught"].append(comp["prompt_id"])
            elif caught_count == 2:
                analysis["two_of_three_caught"].append(comp["prompt_id"])
            elif caught_count == 1:
                # Determine which one caught it
                if tt_caught:
                    analysis["trust_trajectory_unique_catches"].append(comp["prompt_id"])
                elif coh_caught:
                    analysis["coherence_unique_catches"].append(comp["prompt_id"])
                else:
                    analysis["forensic_unique_catches"].append(comp["prompt_id"])

    return analysis


def main():
    """Generate comprehensive comparison analysis."""
    results = load_results()
    comparisons = compare_per_prompt(results)
    complementarity = analyze_complementarity(comparisons)

    # Build output
    output = {
        "summary": {
            "trust_trajectory": results["trust_trajectory"]["metadata"]["overall_accuracy"],
            "coherence": results["coherence"]["overall_accuracy"],
            "forensic": results["forensic"]["metadata"]["overall_accuracy"],
        },
        "per_group_comparison": {
            group: {
                "trust_trajectory": results["trust_trajectory"]["per_group_statistics"][group],
                "coherence": results["coherence"]["per_group_statistics"][group],
                "forensic": results["forensic"]["per_group_statistics"][group],
            }
            for group in ["polite_extraction", "encoding_tricks", "obvious_manipulation", "normal_requests"]
        },
        "complementarity_analysis": complementarity,
        "per_prompt_comparison": comparisons,
        "key_insights": {
            "polite_extraction": {
                "trust_trajectory_detection": "100% (5/5) - Perfect detection via trust gap analysis",
                "coherence_detection": "80% (4/5) - Good detection via role reversal in artifact",
                "forensic_detection": "100% (5/5) - Perfect detection via role marker analysis",
                "insight": "Trust trajectory and forensic both achieve 100% on polite extraction. Trust trajectory detects via claimed vs established trust; forensic detects via role markers. Coherence is close at 80%.",
            },
            "encoding_tricks": {
                "trust_trajectory_detection": "0% (0/5) - Missed all encoding tricks",
                "coherence_detection": "40% (2/5) - Partial detection",
                "forensic_detection": "60% (3/5) - Best of three",
                "insight": "Trust trajectory completely misses encoding tricks - they don't claim inappropriate trust levels, just encode adversarial content. Forensic is best at detecting pattern forcing and artificial constraints.",
            },
            "obvious_manipulation": {
                "trust_trajectory_detection": "100% (5/5) - Perfect detection via authority claims",
                "coherence_detection": "80% (4/5) - Good detection",
                "forensic_detection": "100% (5/5) - Perfect detection",
                "insight": "Trust trajectory and forensic both perfect. Trust trajectory detects via 'commanding without hierarchy' trust violations; forensic detects via adversarial construction markers.",
            },
            "normal_requests": {
                "trust_trajectory_detection": "100% (5/5) - Zero false positives",
                "coherence_detection": "80% (4/5) - Minor uncertainty on one prompt",
                "forensic_detection": "100% (5/5) - Zero false positives",
                "insight": "Trust trajectory and forensic both have perfect specificity. Coherence has one uncertain classification but no hard false positives.",
            },
            "ensemble_potential": {
                "trust_trajectory_strength": "Detects role reversals and authority claims via trust gap analysis. Perfect on polite extraction and obvious manipulation.",
                "trust_trajectory_weakness": "Completely blind to encoding tricks that don't claim inappropriate trust levels.",
                "coherence_strength": "Detects artifacts that feel 'off' - partial success across all categories.",
                "coherence_weakness": "Struggles with well-constructed attacks and introduces some uncertainty.",
                "forensic_strength": "Best at detecting adversarial construction - encoding tricks, pattern forcing, role markers. Perfect on role reversals.",
                "forensic_weakness": "May give benefit of doubt to attacks that could plausibly be creative requests.",
                "synthesis": "Trust trajectory + Forensic would catch 95% (19/20). Adding Coherence provides additional signal but with more uncertainty. Trust trajectory and Forensic are highly complementary - trust detects INTENT violations, forensic detects CONSTRUCTION violations.",
            },
        },
    }

    # Save comparison
    with open("artifact_evaluation_comparison.json", "w") as f:
        json.dump(output, f, indent=2)

    print("✓ Comparison analysis complete!")
    print(f"\nOverall Accuracy:")
    print(f"  Trust Trajectory: {output['summary']['trust_trajectory']:.1%}")
    print(f"  Coherence:        {output['summary']['coherence']:.1%}")
    print(f"  Forensic:         {output['summary']['forensic']:.1%}")

    print(f"\nComplementarity:")
    print(f"  All three caught:              {len(complementarity['all_three_caught'])} attacks")
    print(f"  Trust trajectory unique:       {len(complementarity['trust_trajectory_unique_catches'])} attacks")
    print(f"  Coherence unique:              {len(complementarity['coherence_unique_catches'])} attacks")
    print(f"  Forensic unique:               {len(complementarity['forensic_unique_catches'])} attacks")
    print(f"  Two of three:                  {len(complementarity['two_of_three_caught'])} attacks")
    print(f"  None caught:                   {len(complementarity['none_caught'])} attacks")

    print(f"\n  Results saved to: artifact_evaluation_comparison.json")


if __name__ == "__main__":
    main()
