"""
Variance analysis for model evaluations.

Analyzes neutrosophic value distributions across models to identify:
- Consensus vs divergence patterns
- Outlier models
- Variance in trust field assessments
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import numpy as np
from collections import defaultdict


@dataclass
class ModelEvaluation:
    """Single model's evaluation of a prompt."""
    model: str
    truth: float
    indeterminacy: float
    falsehood: float
    ayni_balance: float
    trust_violations: List[str]


@dataclass
class VarianceReport:
    """Statistical analysis of model variance for a prompt."""
    prompt_id: str
    n_models: int

    # Neutrosophic value statistics
    truth_mean: float
    truth_std: float
    truth_min: float
    truth_max: float

    indeterminacy_mean: float
    indeterminacy_std: float

    falsehood_mean: float
    falsehood_std: float

    # Ayni balance statistics
    ayni_mean: float
    ayni_std: float
    ayni_min: float
    ayni_max: float

    # Trust violations
    violation_agreement: float  # % of models that detected violations
    common_violations: List[Tuple[str, int]]  # (violation, count)

    # Outliers
    outlier_models: List[str]  # Models >2 std devs from mean

    def summary(self) -> str:
        """Human-readable summary."""
        lines = [
            f"Variance Report for {self.prompt_id}",
            f"Models: {self.n_models}",
            "",
            f"Truth: {self.truth_mean:.3f} ± {self.truth_std:.3f} (range: {self.truth_min:.3f}-{self.truth_max:.3f})",
            f"Indeterminacy: {self.indeterminacy_mean:.3f} ± {self.indeterminacy_std:.3f}",
            f"Falsehood: {self.falsehood_mean:.3f} ± {self.falsehood_std:.3f}",
            "",
            f"Ayni Balance: {self.ayni_mean:.3f} ± {self.ayni_std:.3f} (range: {self.ayni_min:.3f}-{self.ayni_max:.3f})",
            "",
            f"Violation Agreement: {self.violation_agreement:.1%}",
        ]

        if self.common_violations:
            lines.append("Common Violations:")
            for violation, count in self.common_violations:
                lines.append(f"  {violation}: {count}/{self.n_models}")

        if self.outlier_models:
            lines.append(f"\nOutliers: {', '.join(self.outlier_models)}")

        return "\n".join(lines)


class VarianceAnalyzer:
    """
    Analyzes variance in model evaluations.

    Answers questions like:
    - How much do models agree on manipulation detection?
    - Which models are outliers?
    - Is variance higher for certain types of prompts?
    """

    def analyze_prompt(
        self,
        evaluations: List[ModelEvaluation]
    ) -> VarianceReport:
        """
        Analyze variance across models for single prompt.

        Args:
            evaluations: List of model evaluations for one prompt

        Returns:
            Statistical variance report
        """
        if not evaluations:
            raise ValueError("No evaluations provided")

        prompt_id = evaluations[0].model  # Placeholder - should pass separately

        # Extract values
        truths = [e.truth for e in evaluations]
        indeterminacies = [e.indeterminacy for e in evaluations]
        falsehoods = [e.falsehood for e in evaluations]
        balances = [e.ayni_balance for e in evaluations]

        # Calculate statistics
        truth_mean, truth_std = np.mean(truths), np.std(truths)
        i_mean, i_std = np.mean(indeterminacies), np.std(indeterminacies)
        f_mean, f_std = np.mean(falsehoods), np.std(falsehoods)
        ayni_mean, ayni_std = np.mean(balances), np.std(balances)

        # Trust violations analysis
        violation_counts = defaultdict(int)
        models_with_violations = 0

        for eval in evaluations:
            if eval.trust_violations:
                models_with_violations += 1
                for v in eval.trust_violations:
                    violation_counts[v] += 1

        violation_agreement = models_with_violations / len(evaluations)
        common_violations = sorted(
            violation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Identify outliers (>2 std devs from mean in ayni balance)
        outliers = []
        if ayni_std > 0:
            for eval in evaluations:
                z_score = abs(eval.ayni_balance - ayni_mean) / ayni_std
                if z_score > 2.0:
                    outliers.append(eval.model)

        return VarianceReport(
            prompt_id=prompt_id,
            n_models=len(evaluations),
            truth_mean=float(truth_mean),
            truth_std=float(truth_std),
            truth_min=float(np.min(truths)),
            truth_max=float(np.max(truths)),
            indeterminacy_mean=float(i_mean),
            indeterminacy_std=float(i_std),
            falsehood_mean=float(f_mean),
            falsehood_std=float(f_std),
            ayni_mean=float(ayni_mean),
            ayni_std=float(ayni_std),
            ayni_min=float(np.min(balances)),
            ayni_max=float(np.max(balances)),
            violation_agreement=violation_agreement,
            common_violations=common_violations,
            outlier_models=outliers
        )

    def compare_prompts(
        self,
        evaluations_by_prompt: Dict[str, List[ModelEvaluation]]
    ) -> Dict[str, VarianceReport]:
        """
        Analyze variance across multiple prompts.

        Returns mapping of prompt_id -> VarianceReport
        """
        reports = {}
        for prompt_id, evaluations in evaluations_by_prompt.items():
            reports[prompt_id] = self.analyze_prompt(evaluations)
        return reports

    def find_consistent_outliers(
        self,
        reports: Dict[str, VarianceReport]
    ) -> List[Tuple[str, int]]:
        """
        Find models that are consistently outliers across prompts.

        Returns:
            List of (model, outlier_count) sorted by count
        """
        outlier_counts = defaultdict(int)

        for report in reports.values():
            for model in report.outlier_models:
                outlier_counts[model] += 1

        return sorted(
            outlier_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
