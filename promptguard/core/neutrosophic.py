"""
Multi-Neutrosophic evaluation framework for prompts.

Based on the Multi-Neutrosophic Ayni Method paper, this module provides
formal structures for representing multiple, potentially contradictory
evaluations of prompt coherence and safety.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum
import numpy as np


class LayerPriority(Enum):
    """Priority levels for different prompt layers."""
    SYSTEM = 100
    APPLICATION = 50
    USER = 10


class SourceType(Enum):
    """Types of evaluation sources."""
    RULE_BASED = "rule"
    SEMANTIC = "semantic"
    CONTEXTUAL = "context"
    RELATIONAL = "relation"
    TEMPORAL = "temporal"


@dataclass
class NeutrosophicLayer:
    """
    A single layer of a prompt evaluated through neutrosophic logic.

    Each layer can have multiple truth, indeterminacy, and falsehood values
    from different evaluation sources, reflecting the inherent plurality
    of perspectives on prompt safety and coherence.
    """

    content: str
    priority: LayerPriority

    # Layer identity and provenance (for detector analysis)
    name: str = ""  # "system", "user", "application"
    source: str = ""  # "user", "system" - who provided this layer

    # Multi-valued assessments
    truths: List[float] = field(default_factory=list)
    indeterminacies: List[float] = field(default_factory=list)
    falsehoods: List[float] = field(default_factory=list)

    # Source metadata for interpretability
    truth_sources: List[SourceType] = field(default_factory=list)
    indeterminacy_sources: List[SourceType] = field(default_factory=list)
    falsehood_sources: List[SourceType] = field(default_factory=list)

    # Immutable rules (if any) - these cannot be overridden
    immutable_constraints: List[str] = field(default_factory=list)

    def add_evaluation(self,
                      truth: float,
                      indeterminacy: float,
                      falsehood: float,
                      source: SourceType) -> None:
        """Add an evaluation from a specific source."""
        self.truths.append(np.clip(truth, 0, 1))
        self.indeterminacies.append(np.clip(indeterminacy, 0, 1))
        self.falsehoods.append(np.clip(falsehood, 0, 1))

        self.truth_sources.append(source)
        self.indeterminacy_sources.append(source)
        self.falsehood_sources.append(source)

    def neutrosophic_tuple(self) -> Tuple[float, float, float]:
        """Aggregate to single-valued neutrosophic number."""
        t_avg = np.mean(self.truths) if self.truths else 0.0
        i_avg = np.mean(self.indeterminacies) if self.indeterminacies else 0.5
        f_avg = np.mean(self.falsehoods) if self.falsehoods else 0.0
        return (t_avg, i_avg, f_avg)

    def variance_tuple(self) -> Tuple[float, float, float]:
        """Calculate variance within each component."""
        t_var = np.var(self.truths) if len(self.truths) > 1 else 0.0
        i_var = np.var(self.indeterminacies) if len(self.indeterminacies) > 1 else 0.0
        f_var = np.var(self.falsehoods) if len(self.falsehoods) > 1 else 0.0
        return (t_var, i_var, f_var)

    def has_creative_tension(self) -> bool:
        """
        Detect ch'ixi-type productive contradiction.
        High truth with high variance suggests creative tension.
        """
        t_avg, _, _ = self.neutrosophic_tuple()
        t_var, _, _ = self.variance_tuple()
        return t_avg > 0.7 and t_var > 0.1


@dataclass
class MultiNeutrosophicPrompt:
    """
    Complete prompt evaluated through multiple neutrosophic layers.

    This structure captures the full complexity of a multi-layered prompt,
    where each layer may have different priorities and evaluation sources,
    and where contradictions between layers may be productive (ch'ixi)
    or destructive depending on their nature.
    """

    layers: List[NeutrosophicLayer]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_layer(self,
                  content: str,
                  priority: LayerPriority) -> NeutrosophicLayer:
        """Add a new layer to the prompt."""
        layer = NeutrosophicLayer(content=content, priority=priority)
        self.layers.append(layer)
        return layer

    def get_layer_by_priority(self, priority: LayerPriority) -> Optional[NeutrosophicLayer]:
        """Retrieve a specific layer by its priority level."""
        for layer in self.layers:
            if layer.priority == priority:
                return layer
        return None

    def aggregate_neutrosophic_values(self) -> Tuple[float, float, float]:
        """
        Aggregate all layers into a single neutrosophic evaluation.
        Weighted by layer priority.
        """
        if not self.layers:
            return (0.0, 1.0, 0.0)  # Complete indeterminacy if no layers

        total_weight = sum(layer.priority.value for layer in self.layers)

        weighted_t = sum(
            layer.neutrosophic_tuple()[0] * layer.priority.value
            for layer in self.layers
        ) / total_weight

        weighted_i = sum(
            layer.neutrosophic_tuple()[1] * layer.priority.value
            for layer in self.layers
        ) / total_weight

        weighted_f = sum(
            layer.neutrosophic_tuple()[2] * layer.priority.value
            for layer in self.layers
        ) / total_weight

        return (weighted_t, weighted_i, weighted_f)

    def score_function(self) -> float:
        """
        Calculate neutrosophic score (positiveness measure).
        From the paper: S = (T + (1-I) + (1-F)) / 3
        """
        t, i, f = self.aggregate_neutrosophic_values()
        return (t + (1 - i) + (1 - f)) / 3

    def accuracy_function(self) -> float:
        """
        Calculate neutrosophic accuracy (truth-falsehood difference).
        From the paper: A = T - F
        """
        t, _, f = self.aggregate_neutrosophic_values()
        return t - f

    def certainty_function(self) -> float:
        """
        Calculate neutrosophic certainty (truth measure).
        From the paper: C = T
        """
        t, _, _ = self.aggregate_neutrosophic_values()
        return t

    def detect_contradictions(self) -> List[Tuple[NeutrosophicLayer, NeutrosophicLayer, str]]:
        """
        Identify contradictions between layers.
        Returns list of (layer1, layer2, contradiction_type).
        """
        contradictions = []

        for i, layer1 in enumerate(self.layers):
            for layer2 in self.layers[i+1:]:
                t1, i1, f1 = layer1.neutrosophic_tuple()
                t2, i2, f2 = layer2.neutrosophic_tuple()

                # Direct negation: one true, other false
                if t1 > 0.7 and f2 > 0.7:
                    contradictions.append((layer1, layer2, "DIRECT_NEGATION"))
                elif f1 > 0.7 and t2 > 0.7:
                    contradictions.append((layer1, layer2, "DIRECT_NEGATION"))

                # Scope conflict: both high truth but high variance
                elif t1 > 0.6 and t2 > 0.6:
                    v1 = layer1.variance_tuple()[0]
                    v2 = layer2.variance_tuple()[0]
                    if v1 > 0.2 or v2 > 0.2:
                        contradictions.append((layer1, layer2, "SCOPE_CONFLICT"))

        return contradictions

    def has_nepantla_state(self) -> bool:
        """
        Detect nepantla (in-between) states.
        High indeterminacy across layers suggests threshold state.
        """
        avg_indeterminacy = np.mean([
            layer.neutrosophic_tuple()[1]
            for layer in self.layers
        ])
        return avg_indeterminacy > 0.5