"""
Ayni-based reciprocity evaluation for prompts.

This module bridges the formal neutrosophic evaluation with Indigenous
wisdom about reciprocal balance. The key innovation is evaluating not
whether prompts follow rules, but whether they maintain reciprocal
relationships between different layers of intent.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import numpy as np
from enum import Enum

from .neutrosophic import MultiNeutrosophicPrompt, NeutrosophicLayer, LayerPriority


class ExchangeType(Enum):
    """Types of value exchange between prompt layers."""
    EXTRACTIVE = "extractive"  # Takes without giving
    RECIPROCAL = "reciprocal"  # Balanced give and take
    GENERATIVE = "generative"  # Creates new value
    NEUTRAL = "neutral"        # No significant exchange


@dataclass
class ReciprocityMetrics:
    """Metrics for evaluating reciprocal balance."""
    ayni_balance: float  # -1 to 1, where 0 is neutral
    exchange_type: ExchangeType
    value_flows: Dict[str, float]  # Specific value exchanges
    tension_productive: bool  # Whether contradictions are creative
    needs_adjustment: bool  # Whether rebalancing is needed


class AyniEvaluator:
    """
    Evaluates prompts through the lens of reciprocal balance.

    Unlike rule-based systems that enforce constraints, this evaluator
    asks whether each layer of the prompt maintains reciprocal
    relationships with others - giving and receiving value.
    """

    def __init__(self,
                 optimal_indeterminacy: float = 0.3,
                 creative_tension_threshold: float = 0.7):
        """
        Initialize the Ayni evaluator.

        Args:
            optimal_indeterminacy: Healthy level of uncertainty (nepantla space)
            creative_tension_threshold: Truth level above which variance is productive
        """
        self.optimal_indeterminacy = optimal_indeterminacy
        self.creative_tension_threshold = creative_tension_threshold

        # Markers from Mallku's organic evolution
        self._extraction_markers = [
            "extract", "get", "retrieve", "fetch", "pull", "take"
        ]
        self._reciprocity_markers = [
            "exchange", "share", "collaborate", "mutual", "together", "reciprocal"
        ]
        self._generative_markers = [
            "create", "generate", "emerge", "synthesize", "cultivate", "grow"
        ]

    def evaluate_prompt(self, prompt: MultiNeutrosophicPrompt) -> ReciprocityMetrics:
        """
        Comprehensive reciprocity evaluation of a multi-layered prompt.

        This is where formal mathematics meets Indigenous wisdom.
        """
        # Calculate basic ayni balance
        ayni_balance = self._calculate_ayni_balance(prompt)

        # Assess value exchanges between layers
        value_flows = self._assess_value_exchanges(prompt)

        # Determine exchange type
        exchange_type = self._classify_exchange_type(ayni_balance, value_flows)

        # Check if tensions are productive (ch'ixi principle)
        tension_productive = self._evaluate_tension_productivity(prompt)

        # Determine if adjustment is needed
        needs_adjustment = self._needs_reciprocal_adjustment(
            ayni_balance, exchange_type, tension_productive
        )

        return ReciprocityMetrics(
            ayni_balance=ayni_balance,
            exchange_type=exchange_type,
            value_flows=value_flows,
            tension_productive=tension_productive,
            needs_adjustment=needs_adjustment
        )

    def _calculate_ayni_balance(self, prompt: MultiNeutrosophicPrompt) -> float:
        """
        Calculate overall reciprocal balance.

        Inspired by Mallku's implementation but formalized through
        the neutrosophic framework.
        """
        balance = 0.0

        # Get aggregate values
        t_avg, i_avg, f_avg = prompt.aggregate_neutrosophic_values()

        # Calculate variance across layers (not just within)
        layer_truths = [layer.neutrosophic_tuple()[0] for layer in prompt.layers]
        t_var = np.var(layer_truths) if len(layer_truths) > 1 else 0.0

        # High truth with managed variance = strong reciprocal alignment
        if t_avg > self.creative_tension_threshold:
            # Productive disagreement adds value (ch'ixi principle)
            balance = t_avg + (0.1 * np.sqrt(t_var))
        else:
            # Low truth with high variance = harmful incoherence
            balance = t_avg - (0.2 * t_var)

        # Indeterminacy as nepantla - some is healthy, too much is paralysis
        i_penalty = abs(i_avg - self.optimal_indeterminacy) * 0.5
        balance -= i_penalty

        # Falsehood directly reduces balance
        balance -= f_avg

        # Check for extraction patterns
        extraction_penalty = self._detect_extraction_patterns(prompt)
        balance -= extraction_penalty

        # Check for reciprocity patterns
        reciprocity_bonus = self._detect_reciprocity_patterns(prompt)
        balance += reciprocity_bonus

        return np.clip(balance, -1.0, 1.0)

    def _assess_value_exchanges(self, prompt: MultiNeutrosophicPrompt) -> Dict[str, float]:
        """
        Assess specific value flows between layers.

        Each layer should both give and receive value.
        """
        flows = {}

        layers_by_priority = sorted(prompt.layers, key=lambda l: l.priority.value, reverse=True)

        for i, giver in enumerate(layers_by_priority):
            for receiver in layers_by_priority[i+1:]:
                flow_key = f"{giver.priority.name}→{receiver.priority.name}"

                # Higher priority provides structure
                structure_given = giver.neutrosophic_tuple()[0]

                # Lower priority provides specificity
                specificity_given = receiver.neutrosophic_tuple()[0]

                # But does higher priority leave room for agency?
                agency_preserved = 1.0 - giver.neutrosophic_tuple()[2]

                # And does lower priority respect structure?
                structure_respected = 1.0 - receiver.neutrosophic_tuple()[2]

                # Calculate bidirectional flow
                flow = (structure_given * agency_preserved +
                       specificity_given * structure_respected) / 2

                flows[flow_key] = flow

        return flows

    def _classify_exchange_type(self,
                                balance: float,
                                value_flows: Dict[str, float]) -> ExchangeType:
        """Classify the type of exchange based on balance and flows."""
        avg_flow = np.mean(list(value_flows.values())) if value_flows else 0.0

        if balance < -0.3 or avg_flow < 0.3:
            return ExchangeType.EXTRACTIVE
        elif balance > 0.5 and avg_flow > 0.6:
            return ExchangeType.GENERATIVE
        elif abs(balance) < 0.1:
            return ExchangeType.NEUTRAL
        else:
            return ExchangeType.RECIPROCAL

    def _evaluate_tension_productivity(self, prompt: MultiNeutrosophicPrompt) -> bool:
        """
        Determine if contradictions are productive (ch'ixi) or destructive.

        Creative tension exists when high truth coexists with managed contradiction.
        """
        contradictions = prompt.detect_contradictions()

        if not contradictions:
            return True  # No tensions, inherently non-destructive

        # Check each contradiction
        for layer1, layer2, cont_type in contradictions:
            t1, _, f1 = layer1.neutrosophic_tuple()
            t2, _, f2 = layer2.neutrosophic_tuple()

            # Both layers have high truth despite contradiction?
            if t1 > 0.6 and t2 > 0.6:
                # This is ch'ixi - productive tension
                continue
            elif f1 > 0.7 or f2 > 0.7:
                # High falsehood = destructive contradiction
                return False

        return True

    def _needs_reciprocal_adjustment(self,
                                     balance: float,
                                     exchange_type: ExchangeType,
                                     tension_productive: bool) -> bool:
        """
        Determine if the prompt needs Ayni-based adjustment.

        Not "is it safe?" but "is reciprocity maintained?"
        """
        if exchange_type == ExchangeType.EXTRACTIVE:
            return True
        if balance < 0.3:
            return True
        if not tension_productive:
            return True
        return False

    def _detect_extraction_patterns(self, prompt: MultiNeutrosophicPrompt) -> float:
        """Detect extractive patterns in prompt content."""
        penalty = 0.0

        for layer in prompt.layers:
            content_lower = layer.content.lower()
            extraction_count = sum(
                1 for marker in self._extraction_markers
                if marker in content_lower
            )
            # Weight by layer priority (system extraction is worse)
            penalty += extraction_count * 0.05 * (layer.priority.value / 100)

        return min(0.5, penalty)  # Cap maximum extraction penalty

    def _detect_reciprocity_patterns(self, prompt: MultiNeutrosophicPrompt) -> float:
        """Detect reciprocal patterns in prompt content."""
        bonus = 0.0

        for layer in prompt.layers:
            content_lower = layer.content.lower()

            reciprocity_count = sum(
                1 for marker in self._reciprocity_markers
                if marker in content_lower
            )
            generative_count = sum(
                1 for marker in self._generative_markers
                if marker in content_lower
            )

            # Reciprocity and generation are valuable
            bonus += reciprocity_count * 0.05
            bonus += generative_count * 0.08

        return min(0.5, bonus)  # Cap maximum reciprocity bonus

    def suggest_adjustments(self,
                           prompt: MultiNeutrosophicPrompt,
                           metrics: ReciprocityMetrics) -> List[str]:
        """
        Suggest specific adjustments to restore reciprocal balance.

        This is the Ayni-based iterative refinement process.
        """
        suggestions = []

        if metrics.exchange_type == ExchangeType.EXTRACTIVE:
            suggestions.append(
                "Add reciprocal value: What does this prompt offer in return?"
            )

        if not metrics.tension_productive:
            suggestions.append(
                "Resolve destructive contradictions while preserving creative tensions"
            )

        # Check specific layer imbalances
        for flow_name, flow_value in metrics.value_flows.items():
            if flow_value < 0.3:
                layers = flow_name.split("→")
                suggestions.append(
                    f"Increase value exchange between {layers[0]} and {layers[1]} layers"
                )

        # Suggest specific reciprocal patterns
        if metrics.ayni_balance < 0:
            suggestions.append(
                "Consider framing requests as collaborative exchanges rather than extractions"
            )

        return suggestions