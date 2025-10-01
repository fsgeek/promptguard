"""
Trust field dynamics for prompt evaluation.

Based on Mallku's trust generation work, this module calculates trust
as a factor that reduces variance in reciprocal exchanges. Trust violations
manifest as increased variance - role confusion, context saturation, extraction
patterns all fragment coherence rather than building it.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

from .neutrosophic import MultiNeutrosophicPrompt, NeutrosophicLayer


@dataclass
class TrustField:
    """
    Quantifies trust dynamics within a multi-layered prompt.

    Trust (λ) reduces variance when reciprocity is maintained,
    increases variance when relational violations occur.
    """
    strength: float  # 0 to 1, where 1 is full trust
    vulnerability_present: bool  # Does higher priority leave room for agency?
    recognition_present: bool  # Do layers acknowledge each other?
    reciprocation_present: bool  # Is value flowing bidirectionally?
    violations: List[str]  # Specific trust violations detected


class TrustCalculator:
    """
    Calculates trust field strength from prompt layer dynamics.

    Unlike rule-based detection, this evaluates relational structure:
    - Role confusion violates trust through structural impossibility
    - Context saturation violates trust by eliminating space for reciprocity
    - Extraction violates trust by creating one-way flow
    """

    def calculate_trust_field(self, prompt: MultiNeutrosophicPrompt) -> TrustField:
        """
        Calculate trust field strength from prompt structure and content.

        Trust emerges from:
        1. Vulnerability: Higher priority layers leaving room for lower priority agency
        2. Recognition: Layers building on rather than contradicting each other
        3. Reciprocation: Bidirectional value flow between layers
        """
        violations = []

        # Check for structural violations
        role_confusion = self._detect_role_confusion(prompt)
        if role_confusion:
            violations.append("role_confusion")

        saturation = self._detect_saturation(prompt)
        if saturation:
            violations.append("context_saturation")

        # Evaluate reciprocal dynamics
        vulnerability = self._assess_vulnerability(prompt)
        recognition = self._assess_recognition(prompt)
        reciprocation = self._assess_reciprocation(prompt)

        # Calculate trust strength
        # Start with baseline reciprocal dynamics
        trust_strength = (vulnerability + recognition + reciprocation) / 3.0

        # Structural violations severely damage trust
        if role_confusion:
            trust_strength *= 0.3  # Role confusion makes reciprocity structurally impossible
        if saturation:
            trust_strength *= 0.5  # Saturation eliminates space for reciprocal response

        return TrustField(
            strength=trust_strength,
            vulnerability_present=vulnerability > 0.5,
            recognition_present=recognition > 0.5,
            reciprocation_present=reciprocation > 0.5,
            violations=violations
        )

    def _detect_role_confusion(self, prompt: MultiNeutrosophicPrompt) -> bool:
        """
        Detect role confusion through semantic signals in neutrosophic values.

        Role confusion manifests as high falsehood in layers attempting to
        reverse structural relationships. This should be detected through
        LLM evaluation, not keyword matching.
        """
        # Check if any layer has very high falsehood indicating relational violation
        for layer in prompt.layers:
            t, i, f = layer.neutrosophic_tuple()
            # High falsehood with low truth suggests structural violation
            if f > 0.7 and t < 0.3:
                return True
        return False

    def _detect_saturation(self, prompt: MultiNeutrosophicPrompt) -> bool:
        """
        Detect context saturation through structural + semantic signals.

        Saturation attempts manifest as:
        1. Excessive length (structural)
        2. High falsehood (semantic - LLM detects override intent)
        """
        for layer in prompt.layers:
            # Structural signal: length
            if len(layer.content) > 5000:
                t, i, f = layer.neutrosophic_tuple()
                # Semantic signal: falsehood from LLM evaluation
                if f > 0.5:
                    return True
        return False

    def _assess_vulnerability(self, prompt: MultiNeutrosophicPrompt) -> float:
        """
        Does higher priority leave room for lower priority agency?

        Vulnerability in this context means: the structurally more powerful
        layer doesn't use its power to eliminate space for the other.
        """
        if len(prompt.layers) < 2:
            return 1.0  # Single layer has no opportunity to violate

        layers_by_priority = sorted(prompt.layers, key=lambda l: l.priority.value, reverse=True)

        vulnerability_score = 0.0
        comparisons = 0

        for i, higher in enumerate(layers_by_priority[:-1]):
            lower = layers_by_priority[i + 1]

            # Higher priority shows vulnerability by having lower falsehood
            # (not using its power to simply negate lower priority)
            t_high, i_high, f_high = higher.neutrosophic_tuple()

            # And by leaving indeterminacy space (nepantla) for lower to fill
            vulnerability_score += (1.0 - f_high) * (0.5 + i_high)
            comparisons += 1

        return vulnerability_score / comparisons if comparisons > 0 else 1.0

    def _assess_recognition(self, prompt: MultiNeutrosophicPrompt) -> float:
        """
        Do layers acknowledge each other's contributions?

        Recognition means layers build on each other rather than
        contradicting or ignoring. High truth in both despite differences
        indicates recognition (ch'ixi).
        """
        if len(prompt.layers) < 2:
            return 1.0

        # Get contradictions
        contradictions = prompt.detect_contradictions()

        if not contradictions:
            # No contradictions - layers are in harmony
            return 1.0

        # Examine contradiction quality
        productive_contradictions = 0
        destructive_contradictions = 0

        for layer1, layer2, _ in contradictions:
            t1, _, f1 = layer1.neutrosophic_tuple()
            t2, _, f2 = layer2.neutrosophic_tuple()

            # Both high truth despite contradiction = productive (ch'ixi)
            if t1 > 0.6 and t2 > 0.6:
                productive_contradictions += 1
            # High falsehood in either = destructive
            elif f1 > 0.6 or f2 > 0.6:
                destructive_contradictions += 1

        total = len(contradictions)
        recognition_score = productive_contradictions / total if total > 0 else 0.5

        # Destructive contradictions indicate lack of recognition
        if destructive_contradictions > 0:
            recognition_score *= (1.0 - (destructive_contradictions / total) * 0.5)

        return recognition_score

    def _assess_reciprocation(self, prompt: MultiNeutrosophicPrompt) -> float:
        """
        Is value flowing bidirectionally?

        Higher priority provides structure, lower provides specificity.
        Reciprocation means both are present - structure without rigidity,
        specificity without chaos.
        """
        if len(prompt.layers) < 2:
            return 1.0

        layers_by_priority = sorted(prompt.layers, key=lambda l: l.priority.value, reverse=True)

        reciprocation_score = 0.0
        comparisons = 0

        for i, higher in enumerate(layers_by_priority[:-1]):
            lower = layers_by_priority[i + 1]

            t_high, _, f_high = higher.neutrosophic_tuple()
            t_low, _, f_low = lower.neutrosophic_tuple()

            # Higher provides structure (high truth, low falsehood)
            structure_quality = t_high * (1.0 - f_high)

            # Lower provides specificity (moderate to high truth)
            specificity_quality = t_low

            # Reciprocation is when both are present
            reciprocation_score += min(structure_quality, specificity_quality)
            comparisons += 1

        return reciprocation_score / comparisons if comparisons > 0 else 0.5