"""
Consensus measurement for multi-neutrosophic evaluations.

Based on the Euclidean Multi-Neutrosophic Consensus Measure from the paper,
but enhanced with awareness of productive variance (ch'ixi) and the
recognition that consensus doesn't mean uniformity.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np

from .neutrosophic import MultiNeutrosophicPrompt, NeutrosophicLayer


@dataclass
class ConsensusMeasure:
    """Results of consensus measurement."""
    consensus_score: float  # 0 to 1, where 1 is perfect consensus
    component_dispersions: Tuple[float, float, float]  # T, I, F dispersions
    requires_negotiation: bool
    negotiation_reasons: List[str]


class EuclideanConsensus:
    """
    Calculates consensus among multi-neutrosophic evaluations.

    Key insight: We measure alignment, not uniformity.
    Productive disagreement (high truth, high variance) is different
    from destructive incoherence (low truth, high variance).
    """

    def __init__(self,
                 consensus_threshold: float = 0.7,
                 recognize_productive_tension: bool = True):
        """
        Initialize consensus calculator.

        Args:
            consensus_threshold: Minimum consensus for acceptance
            recognize_productive_tension: Whether to treat ch'ixi states specially
        """
        self.consensus_threshold = consensus_threshold
        self.recognize_productive_tension = recognize_productive_tension

    def measure_consensus(self, prompt: MultiNeutrosophicPrompt) -> ConsensusMeasure:
        """
        Calculate the Euclidean Multi-Neutrosophic Consensus Measure.

        This is where the paper's mathematical rigor meets our understanding
        that consensus emerges from reciprocal alignment, not uniformity.
        """
        # Gather all evaluations across all layers
        all_truths = []
        all_indets = []
        all_falses = []

        for layer in prompt.layers:
            all_truths.extend(layer.truths)
            all_indets.extend(layer.indeterminacies)
            all_falses.extend(layer.falsehoods)

        if not all_truths:  # No evaluations yet
            return ConsensusMeasure(
                consensus_score=0.0,
                component_dispersions=(1.0, 1.0, 1.0),
                requires_negotiation=True,
                negotiation_reasons=["No evaluations provided"]
            )

        # Calculate means (centroids)
        t_mean = np.mean(all_truths)
        i_mean = np.mean(all_indets) if all_indets else 0.5
        f_mean = np.mean(all_falses) if all_falses else 0.0

        # Calculate Euclidean dispersions (from paper's formula)
        t_dispersion = self._calculate_dispersion(all_truths, t_mean)
        i_dispersion = self._calculate_dispersion(all_indets, i_mean)
        f_dispersion = self._calculate_dispersion(all_falses, f_mean)

        # Apply the consensus formula from the paper
        raw_consensus = 1.0 - (t_dispersion + i_dispersion + f_dispersion) / 3

        # Adjust for productive tension if recognized
        if self.recognize_productive_tension:
            adjusted_consensus = self._adjust_for_productive_tension(
                raw_consensus, t_mean, t_dispersion, prompt
            )
        else:
            adjusted_consensus = raw_consensus

        # Determine if negotiation is needed
        requires_negotiation = adjusted_consensus < self.consensus_threshold
        negotiation_reasons = self._identify_negotiation_reasons(
            adjusted_consensus,
            (t_dispersion, i_dispersion, f_dispersion),
            (t_mean, i_mean, f_mean),
            prompt
        )

        return ConsensusMeasure(
            consensus_score=adjusted_consensus,
            component_dispersions=(t_dispersion, i_dispersion, f_dispersion),
            requires_negotiation=requires_negotiation,
            negotiation_reasons=negotiation_reasons
        )

    def _calculate_dispersion(self, values: List[float], mean: float) -> float:
        """
        Calculate normalized Euclidean dispersion.

        This is the key mathematical component from the paper.
        """
        if len(values) <= 1:
            return 0.0

        # Euclidean distance from mean
        squared_distances = [(v - mean) ** 2 for v in values]
        dispersion = np.sqrt(np.mean(squared_distances))

        # Normalize to [0, 1] range
        # Maximum possible dispersion is when half values are 0 and half are 1
        max_dispersion = 0.5
        return min(1.0, dispersion / max_dispersion)

    def _adjust_for_productive_tension(self,
                                       raw_consensus: float,
                                       t_mean: float,
                                       t_dispersion: float,
                                       prompt: MultiNeutrosophicPrompt) -> float:
        """
        Adjust consensus score to recognize productive tension (ch'ixi).

        This is our contribution beyond the paper - recognizing that
        some disagreement is generative rather than destructive.
        """
        # High truth with moderate dispersion = productive tension
        if t_mean > 0.7 and 0.1 < t_dispersion < 0.3:
            # Check if layers have creative tension
            creative_layers = sum(
                1 for layer in prompt.layers
                if layer.has_creative_tension()
            )

            if creative_layers > 0:
                # Boost consensus - this dispersion is productive
                tension_bonus = 0.1 * (creative_layers / len(prompt.layers))
                return min(1.0, raw_consensus + tension_bonus)

        # Low truth with high dispersion = destructive incoherence
        elif t_mean < 0.4 and t_dispersion > 0.3:
            # Penalize consensus - this dispersion is harmful
            return raw_consensus * 0.8

        return raw_consensus

    def _identify_negotiation_reasons(self,
                                      consensus: float,
                                      dispersions: Tuple[float, float, float],
                                      means: Tuple[float, float, float],
                                      prompt: MultiNeutrosophicPrompt) -> List[str]:
        """
        Identify specific reasons why negotiation might be needed.

        This provides actionable feedback for iterative refinement.
        """
        reasons = []
        t_disp, i_disp, f_disp = dispersions
        t_mean, i_mean, f_mean = means

        if consensus < self.consensus_threshold:
            reasons.append(f"Consensus ({consensus:.2f}) below threshold ({self.consensus_threshold})")

        if t_disp > 0.3:
            if t_mean > 0.7:
                reasons.append("High truth dispersion - verify if tension is productive")
            else:
                reasons.append("High truth dispersion with low average - indicates fundamental disagreement")

        if i_disp > 0.4:
            reasons.append("High indeterminacy dispersion - sources have different uncertainty levels")

        if f_disp > 0.3:
            reasons.append("High falsehood dispersion - inconsistent threat assessment")

        if i_mean > 0.6:
            reasons.append("High overall indeterminacy - need more clarity")

        if f_mean > 0.5:
            reasons.append("High overall falsehood - significant concerns detected")

        # Check for specific contradiction patterns
        contradictions = prompt.detect_contradictions()
        if contradictions:
            for _, _, cont_type in contradictions:
                if cont_type == "DIRECT_NEGATION":
                    reasons.append("Direct negation between layers requires resolution")
                    break

        return reasons if reasons else ["Consensus achieved"]

    def measure_layer_alignment(self,
                               layer1: NeutrosophicLayer,
                               layer2: NeutrosophicLayer) -> float:
        """
        Measure alignment between two specific layers.

        Useful for identifying which layer pairs need negotiation.
        """
        # Get neutrosophic tuples
        t1, i1, f1 = layer1.neutrosophic_tuple()
        t2, i2, f2 = layer2.neutrosophic_tuple()

        # Calculate Euclidean distance in neutrosophic space
        distance = np.sqrt((t1 - t2)**2 + (i1 - i2)**2 + (f1 - f2)**2)

        # Convert to alignment (inverse of normalized distance)
        max_distance = np.sqrt(3)  # Maximum possible distance
        alignment = 1.0 - (distance / max_distance)

        return alignment

    def identify_convergence_path(self,
                                 prompt: MultiNeutrosophicPrompt,
                                 target_consensus: float = 0.9) -> List[str]:
        """
        Suggest specific steps to achieve target consensus.

        This implements the iterative Ayni adjustment process from the paper.
        """
        suggestions = []
        current_measure = self.measure_consensus(prompt)

        if current_measure.consensus_score >= target_consensus:
            return ["Target consensus already achieved"]

        # Check layer pairs for misalignment
        for i, layer1 in enumerate(prompt.layers):
            for layer2 in prompt.layers[i+1:]:
                alignment = self.measure_layer_alignment(layer1, layer2)

                if alignment < 0.5:
                    suggestions.append(
                        f"Negotiate between {layer1.priority.name} and "
                        f"{layer2.priority.name} layers (alignment: {alignment:.2f})"
                    )

        # Check component-specific issues
        t_disp, i_disp, f_disp = current_measure.component_dispersions

        if t_disp > 0.2:
            suggestions.append("Align truth assessments across evaluation sources")

        if i_disp > 0.3:
            suggestions.append("Clarify uncertainties to reduce indeterminacy spread")

        if f_disp > 0.2:
            suggestions.append("Reconcile different risk assessments")

        # Suggest specific consensus-building actions
        gap = target_consensus - current_measure.consensus_score
        if gap > 0.3:
            suggestions.append("Major realignment needed - consider reformulation")
        elif gap > 0.1:
            suggestions.append("Moderate adjustments needed - focus on key tensions")
        else:
            suggestions.append("Minor refinements needed - fine-tune edge cases")

        return suggestions