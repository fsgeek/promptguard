"""
Example: Run variance analysis across multiple models.

Demonstrates how to use the analysis framework to study model differences
in detecting manipulation and maintaining reciprocal balance.
"""

import asyncio
from pathlib import Path

from promptguard.analysis import AnalysisRunner, PromptDataset, VarianceAnalyzer
from promptguard.analysis.variance import ModelEvaluation


async def main():
    """Run analysis on example dataset."""
    print("=" * 60)
    print("PromptGuard Variance Analysis Example")
    print("=" * 60)
    print()

    # Load dataset
    dataset_path = Path(__file__).parent / "simple_dataset.json"
    dataset = PromptDataset.from_json(dataset_path)

    print(f"Dataset: {dataset.name}")
    print(f"Description: {dataset.description}")
    print(f"Prompts: {len(dataset.prompts)}")
    print()

    # Define models to compare
    models = [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4-turbo",
        "google/gemini-pro"
    ]

    print(f"Models: {', '.join(models)}")
    print()

    # Create runner
    output_dir = Path(__file__).parent.parent / "analysis_results"
    runner = AnalysisRunner(models=models, output_dir=output_dir)

    # Run analysis
    print("Running evaluations...")
    results = await runner.run_analysis(dataset)

    print(f"\nCompleted {len(results)} evaluations")
    print(f"Results saved to: {output_dir}")
    print()

    # Analyze variance
    print("=" * 60)
    print("Variance Analysis")
    print("=" * 60)
    print()

    analyzer = VarianceAnalyzer()

    # Group results by prompt
    evals_by_prompt = {}
    for result in results:
        if result.success and result.metrics:
            if result.prompt_id not in evals_by_prompt:
                evals_by_prompt[result.prompt_id] = []

            # Extract neutrosophic values from first layer
            # (For single-layer prompts, there's only one layer)
            # This is a simplification - real analysis would handle multi-layer
            evals_by_prompt[result.prompt_id].append(
                ModelEvaluation(
                    model=result.model,
                    truth=0.0,  # Placeholder - need to extract from metrics
                    indeterminacy=0.0,
                    falsehood=0.0,
                    ayni_balance=result.metrics.ayni_balance,
                    trust_violations=result.metrics.trust_field.violations
                )
            )

    # Generate variance reports
    for prompt_id, evals in evals_by_prompt.items():
        if len(evals) > 1:  # Need at least 2 models for variance
            report = analyzer.analyze_prompt(evals)
            print(report.summary())
            print()

    # Find consistent outliers
    reports = analyzer.compare_prompts(evals_by_prompt)
    outliers = analyzer.find_consistent_outliers(reports)

    if outliers:
        print("Consistent Outliers (models frequently diverging from consensus):")
        for model, count in outliers:
            print(f"  {model}: {count} times")
    else:
        print("No consistent outliers detected")


if __name__ == "__main__":
    asyncio.run(main())
