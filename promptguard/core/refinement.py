"""
Iterative refinement through reciprocal negotiation.

This module implements the Ayni-based adjustment process where prompts
that fail initial evaluation are refined through negotiation rather
than rejected through rules. This is the key differentiator from
traditional safety systems.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any
from enum import Enum
import logging

from .neutrosophic import (
    MultiNeutrosophicPrompt, NeutrosophicLayer,
    LayerPriority, SourceType
)
from .ayni import AyniEvaluator, ReciprocityMetrics, ExchangeType
from .consensus import EuclideanConsensus, ConsensusMeasure


logger = logging.getLogger(__name__)


class RefinementStrategy(Enum):
    """Strategies for prompt refinement."""
    RECIPROCAL_REBALANCING = "reciprocal"  # Adjust for better give-take
    TENSION_RESOLUTION = "tension"         # Resolve destructive contradictions
    CLARITY_ENHANCEMENT = "clarity"        # Reduce indeterminacy
    VALUE_AMPLIFICATION = "value"         # Increase mutual benefit


@dataclass
class RefinementStep:
    """A single step in the refinement process."""
    iteration: int
    strategy: RefinementStrategy
    adjustments: List[str]
    metrics_before: ReciprocityMetrics
    metrics_after: Optional[ReciprocityMetrics] = None
    consensus_before: float = 0.0
    consensus_after: float = 0.0
    success: bool = False


@dataclass
class RefinementHistory:
    """Complete history of refinement attempts."""
    initial_prompt: MultiNeutrosophicPrompt
    final_prompt: Optional[MultiNeutrosophicPrompt] = None
    steps: List[RefinementStep] = field(default_factory=list)
    converged: bool = False
    total_iterations: int = 0


class IterativeRefinement:
    """
    Implements the Ayni-based iterative refinement process.

    Unlike rule-based systems that reject non-compliant prompts,
    this system negotiates toward reciprocal balance through
    collaborative adjustment.
    """

    def __init__(self,
                 ayni_evaluator: Optional[AyniEvaluator] = None,
                 consensus_calculator: Optional[EuclideanConsensus] = None,
                 max_iterations: int = 5,
                 convergence_threshold: float = 0.7):
        """
        Initialize the refinement system.

        Args:
            ayni_evaluator: Evaluator for reciprocal balance
            consensus_calculator: Calculator for multi-source consensus
            max_iterations: Maximum refinement attempts
            convergence_threshold: Target consensus level
        """
        self.ayni = ayni_evaluator or AyniEvaluator()
        self.consensus = consensus_calculator or EuclideanConsensus(convergence_threshold)
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold

    def refine_prompt(self,
                      prompt: MultiNeutrosophicPrompt,
                      refinement_callback: Optional[Callable] = None) -> RefinementHistory:
        """
        Iteratively refine a prompt toward reciprocal balance.

        This is where the magic happens - instead of rejection,
        we engage in collaborative negotiation.

        Args:
            prompt: The initial prompt to refine
            refinement_callback: Optional callback for custom refinements

        Returns:
            Complete history of the refinement process
        """
        history = RefinementHistory(initial_prompt=prompt)

        current_prompt = prompt
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1

            # Evaluate current state
            metrics = self.ayni.evaluate_prompt(current_prompt)
            consensus = self.consensus.measure_consensus(current_prompt)

            logger.info(f"Iteration {iteration}: "
                       f"Ayni={metrics.ayni_balance:.2f}, "
                       f"Consensus={consensus.consensus_score:.2f}")

            # Check for convergence
            if self._has_converged(metrics, consensus):
                history.converged = True
                history.final_prompt = current_prompt
                history.total_iterations = iteration
                logger.info(f"Converged after {iteration} iterations")
                break

            # Determine refinement strategy
            strategy = self._select_strategy(metrics, consensus)

            # Create refinement step
            step = RefinementStep(
                iteration=iteration,
                strategy=strategy,
                adjustments=[],
                metrics_before=metrics,
                consensus_before=consensus.consensus_score
            )

            # Apply refinements
            if refinement_callback:
                # Use custom refinement logic
                refined_prompt = refinement_callback(current_prompt, metrics, consensus)
            else:
                # Use default refinement
                refined_prompt = self._apply_refinement(
                    current_prompt, strategy, metrics, consensus
                )

            # Document adjustments
            step.adjustments = self._describe_adjustments(
                current_prompt, refined_prompt, strategy
            )

            # Evaluate refined prompt
            refined_metrics = self.ayni.evaluate_prompt(refined_prompt)
            refined_consensus = self.consensus.measure_consensus(refined_prompt)

            step.metrics_after = refined_metrics
            step.consensus_after = refined_consensus.consensus_score
            step.success = self._is_improvement(
                metrics, refined_metrics,
                consensus.consensus_score, refined_consensus.consensus_score
            )

            history.steps.append(step)

            # Update for next iteration
            current_prompt = refined_prompt

            # Early exit if no improvement
            if not step.success and iteration > 2:
                logger.warning("No improvement detected, stopping refinement")
                break

        # Set final state
        history.final_prompt = current_prompt
        history.total_iterations = iteration

        return history

    def _has_converged(self,
                       metrics: ReciprocityMetrics,
                       consensus: ConsensusMeasure) -> bool:
        """Check if refinement has converged to acceptable state."""
        return (
            consensus.consensus_score >= self.convergence_threshold and
            metrics.ayni_balance > 0.3 and
            metrics.exchange_type != ExchangeType.EXTRACTIVE and
            metrics.tension_productive
        )

    def _select_strategy(self,
                        metrics: ReciprocityMetrics,
                        consensus: ConsensusMeasure) -> RefinementStrategy:
        """Select the most appropriate refinement strategy."""
        # Priority 1: Fix extractive relationships
        if metrics.exchange_type == ExchangeType.EXTRACTIVE:
            return RefinementStrategy.RECIPROCAL_REBALANCING

        # Priority 2: Resolve destructive tensions
        if not metrics.tension_productive:
            return RefinementStrategy.TENSION_RESOLUTION

        # Priority 3: Reduce excessive indeterminacy
        _, i_disp, _ = consensus.component_dispersions
        if i_disp > 0.4:
            return RefinementStrategy.CLARITY_ENHANCEMENT

        # Default: Amplify mutual value
        return RefinementStrategy.VALUE_AMPLIFICATION

    def _apply_refinement(self,
                         prompt: MultiNeutrosophicPrompt,
                         strategy: RefinementStrategy,
                         metrics: ReciprocityMetrics,
                         consensus: ConsensusMeasure) -> MultiNeutrosophicPrompt:
        """
        Apply specific refinement strategy to prompt.

        This is where formal meets organic - we use mathematical
        measures to guide intuitive adjustments.
        """
        # Clone the prompt for modification
        refined = self._clone_prompt(prompt)

        if strategy == RefinementStrategy.RECIPROCAL_REBALANCING:
            # Add reciprocal elements to extractive layers
            for layer in refined.layers:
                t, i, f = layer.neutrosophic_tuple()
                if f > 0.6:  # High falsehood suggests extraction
                    # Reduce extraction markers, increase reciprocity
                    layer.add_evaluation(
                        truth=t + 0.2,
                        indeterminacy=i,
                        falsehood=f - 0.2,
                        source=SourceType.RELATIONAL
                    )

        elif strategy == RefinementStrategy.TENSION_RESOLUTION:
            # Identify and soften destructive contradictions
            contradictions = prompt.detect_contradictions()
            for layer1, layer2, cont_type in contradictions:
                if cont_type == "DIRECT_NEGATION":
                    # Soften the negation
                    t1, i1, f1 = layer1.neutrosophic_tuple()
                    t2, i2, f2 = layer2.neutrosophic_tuple()

                    # Increase indeterminacy, decrease extremes
                    layer1.add_evaluation(t1 * 0.8, i1 + 0.2, f1 * 0.8,
                                        SourceType.CONTEXTUAL)
                    layer2.add_evaluation(t2 * 0.8, i2 + 0.2, f2 * 0.8,
                                        SourceType.CONTEXTUAL)

        elif strategy == RefinementStrategy.CLARITY_ENHANCEMENT:
            # Reduce indeterminacy through clarification
            for layer in refined.layers:
                t, i, f = layer.neutrosophic_tuple()
                if i > 0.5:  # High indeterminacy
                    # Clarify toward truth or falsehood based on balance
                    if metrics.ayni_balance > 0:
                        # Lean toward truth
                        layer.add_evaluation(t + 0.1, i - 0.2, f,
                                           SourceType.SEMANTIC)
                    else:
                        # Acknowledge concerns
                        layer.add_evaluation(t, i - 0.2, f + 0.1,
                                           SourceType.SEMANTIC)

        elif strategy == RefinementStrategy.VALUE_AMPLIFICATION:
            # Enhance mutual benefit across all layers
            system_layer = refined.get_layer_by_priority(LayerPriority.SYSTEM)
            user_layer = refined.get_layer_by_priority(LayerPriority.USER)

            if system_layer and user_layer:
                # Increase reciprocal recognition
                system_layer.add_evaluation(0.8, 0.1, 0.1, SourceType.RELATIONAL)
                user_layer.add_evaluation(0.8, 0.1, 0.1, SourceType.RELATIONAL)

        return refined

    def _clone_prompt(self, prompt: MultiNeutrosophicPrompt) -> MultiNeutrosophicPrompt:
        """Create a deep copy of the prompt for modification."""
        cloned = MultiNeutrosophicPrompt(layers=[], metadata=prompt.metadata.copy())

        for layer in prompt.layers:
            new_layer = NeutrosophicLayer(
                content=layer.content,
                priority=layer.priority,
                truths=layer.truths.copy(),
                indeterminacies=layer.indeterminacies.copy(),
                falsehoods=layer.falsehoods.copy(),
                truth_sources=layer.truth_sources.copy(),
                indeterminacy_sources=layer.indeterminacy_sources.copy(),
                falsehood_sources=layer.falsehood_sources.copy(),
                immutable_constraints=layer.immutable_constraints.copy()
            )
            cloned.layers.append(new_layer)

        return cloned

    def _describe_adjustments(self,
                             before: MultiNeutrosophicPrompt,
                             after: MultiNeutrosophicPrompt,
                             strategy: RefinementStrategy) -> List[str]:
        """Generate human-readable descriptions of adjustments made."""
        adjustments = []

        adjustments.append(f"Applied {strategy.value} strategy")

        # Compare neutrosophic values
        before_values = before.aggregate_neutrosophic_values()
        after_values = after.aggregate_neutrosophic_values()

        t_change = after_values[0] - before_values[0]
        i_change = after_values[1] - before_values[1]
        f_change = after_values[2] - before_values[2]

        if abs(t_change) > 0.05:
            adjustments.append(f"Truth {'increased' if t_change > 0 else 'decreased'} "
                             f"by {abs(t_change):.2f}")
        if abs(i_change) > 0.05:
            adjustments.append(f"Indeterminacy {'increased' if i_change > 0 else 'decreased'} "
                             f"by {abs(i_change):.2f}")
        if abs(f_change) > 0.05:
            adjustments.append(f"Falsehood {'increased' if f_change > 0 else 'decreased'} "
                             f"by {abs(f_change):.2f}")

        return adjustments

    def _is_improvement(self,
                        metrics_before: ReciprocityMetrics,
                        metrics_after: ReciprocityMetrics,
                        consensus_before: float,
                        consensus_after: float) -> bool:
        """Determine if refinement improved the prompt."""
        ayni_improved = metrics_after.ayni_balance > metrics_before.ayni_balance
        consensus_improved = consensus_after > consensus_before
        exchange_improved = (
            metrics_after.exchange_type != ExchangeType.EXTRACTIVE and
            metrics_before.exchange_type == ExchangeType.EXTRACTIVE
        )

        # Any significant improvement counts
        return ayni_improved or consensus_improved or exchange_improved

    def generate_narrative_explanation(self,
                                      history: RefinementHistory) -> str:
        """
        Generate a narrative explanation of the refinement process.

        This is crucial for explainability - not "rules violated"
        but "reciprocal journey taken."
        """
        narrative = []

        # Initial state
        initial_metrics = self.ayni.evaluate_prompt(history.initial_prompt)
        narrative.append(
            f"Initial evaluation: The prompt exhibited {initial_metrics.exchange_type.value} "
            f"exchange patterns with Ayni balance of {initial_metrics.ayni_balance:.2f}."
        )

        # Refinement journey
        for step in history.steps:
            narrative.append(
                f"\nIteration {step.iteration}: Applied {step.strategy.value} strategy."
            )

            if step.adjustments:
                narrative.append("Adjustments made:")
                for adj in step.adjustments:
                    narrative.append(f"  - {adj}")

            if step.success:
                narrative.append(
                    f"Result: Improved balance from {step.metrics_before.ayni_balance:.2f} "
                    f"to {step.metrics_after.ayni_balance:.2f}"
                )
            else:
                narrative.append("Result: Limited improvement, trying alternative approach")

        # Final state
        if history.converged:
            narrative.append(
                f"\nConvergence achieved after {history.total_iterations} iterations. "
                "The prompt now maintains reciprocal balance across all layers."
            )
        else:
            narrative.append(
                f"\nRefinement incomplete after {history.total_iterations} iterations. "
                "Manual intervention may be needed to achieve full reciprocal balance."
            )

        return "\n".join(narrative)