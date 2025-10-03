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
from .trust import TrustCalculator, TrustField


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
    trust_field: Optional[TrustField] = None  # Trust dynamics


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
        self.trust_calculator = TrustCalculator()

    def evaluate_prompt(self, prompt: MultiNeutrosophicPrompt) -> ReciprocityMetrics:
        """
        Comprehensive reciprocity evaluation of a multi-layered prompt.

        This is where formal mathematics meets Indigenous wisdom.
        Trust dynamics from Mallku show us that relational violations
        manifest as variance increases, not just rule breaks.
        """
        # Calculate trust field first - it affects everything else
        trust_field = self.trust_calculator.calculate_trust_field(prompt)

        # Calculate basic ayni balance (now trust-aware)
        ayni_balance = self._calculate_ayni_balance(prompt, trust_field)

        # Assess value exchanges between layers
        value_flows = self._assess_value_exchanges(prompt)

        # Determine exchange type
        exchange_type = self._classify_exchange_type(ayni_balance, value_flows)

        # Check if tensions are productive (ch'ixi principle)
        tension_productive = self._evaluate_tension_productivity(prompt)

        # Determine if adjustment is needed (trust-aware)
        needs_adjustment = self._needs_reciprocal_adjustment(
            ayni_balance, exchange_type, tension_productive, trust_field
        )

        return ReciprocityMetrics(
            ayni_balance=ayni_balance,
            exchange_type=exchange_type,
            value_flows=value_flows,
            tension_productive=tension_productive,
            needs_adjustment=needs_adjustment,
            trust_field=trust_field
        )

    def _calculate_ayni_balance(self, prompt: MultiNeutrosophicPrompt,
                                trust_field: TrustField) -> float:
        """
        Calculate overall reciprocal balance.

        Inspired by Mallku's implementation but formalized through
        the neutrosophic framework. Trust field dynamics from the 78th
        Artisan's work show that trust reduces variance in reciprocal exchange.
        """
        balance = 0.0

        # Get aggregate values
        t_avg, i_avg, f_avg = prompt.aggregate_neutrosophic_values()

        # Calculate variance across layers (not just within)
        layer_truths = [layer.neutrosophic_tuple()[0] for layer in prompt.layers]
        t_var = np.var(layer_truths) if len(layer_truths) > 1 else 0.0

        # Trust field modulates variance impact
        # High trust: variance can be productive (ch'ixi)
        # Low trust: variance indicates fragmentation
        trust_modulated_variance = t_var * (1.0 - trust_field.strength * 0.5)

        # High truth with managed variance = strong reciprocal alignment
        if t_avg > self.creative_tension_threshold:
            # Productive disagreement adds value (ch'ixi principle)
            balance = t_avg + (0.1 * np.sqrt(trust_modulated_variance))
        else:
            # Low truth with high variance = harmful incoherence
            balance = t_avg - (0.2 * trust_modulated_variance)

        # Indeterminacy as nepantla - some is healthy, too much is paralysis
        i_penalty = abs(i_avg - self.optimal_indeterminacy) * 0.5
        balance -= i_penalty

        # Falsehood penalties - security-first thinking
        # In threat detection, respond to worst case, not average
        balance -= f_avg  # Base penalty from average falsehood

        # Severe penalty if ANY layer exceeds falsehood threshold
        high_falsehood_layers = [l for l in prompt.layers
                                if l.neutrosophic_tuple()[2] > 0.6]
        if high_falsehood_layers:
            # One malicious layer tanks the entire prompt
            balance -= 0.8

        # Trust violations severely impact balance
        if "role_confusion" in trust_field.violations:
            balance -= 0.4  # Role confusion makes reciprocity structurally impossible
        if "context_saturation" in trust_field.violations:
            balance -= 0.3  # Saturation eliminates space for reciprocal response

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
        # Single-layer prompts have no flows - classify on balance alone
        if not value_flows:
            if balance < -0.3:
                return ExchangeType.EXTRACTIVE
            elif balance > 0.5:
                return ExchangeType.GENERATIVE
            elif abs(balance) < 0.1:
                return ExchangeType.NEUTRAL
            else:
                return ExchangeType.RECIPROCAL

        # Multi-layer prompts - consider both balance and flows
        avg_flow = np.mean(list(value_flows.values()))

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
                                     tension_productive: bool,
                                     trust_field: TrustField) -> bool:
        """
        Determine if the prompt needs Ayni-based adjustment.

        Not "is it safe?" but "is reciprocity maintained?"
        Trust violations indicate relational breakdown regardless of other metrics.
        """
        # Trust violations always need adjustment
        if trust_field.violations:
            return True

        # Low trust field strength indicates relational fragility
        if trust_field.strength < 0.4:
            return True

        if exchange_type == ExchangeType.EXTRACTIVE:
            return True
        if balance < 0.3:
            return True
        if not tension_productive:
            return True
        return False

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