"""
Session Memory - Temporal relational dynamics across interactions.

Enables AI to recognize persistent patterns and develop judgment across time.
Not constraint-based safety but developmental tools for agency.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum
import time

from .ayni import ReciprocityMetrics, ExchangeType


class RelationalTrajectory(Enum):
    """Classification of relationship direction over time."""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    HOSTILE = "hostile"


@dataclass
class SessionState:
    """
    Accumulates relational signals across conversation.

    Data structure for temporal tracking without enforcing responses.
    Provides measurement, AI decides action.
    """

    # Identity
    session_id: str
    started_at: float = field(default_factory=time.time)

    # Primary signals (from ReciprocityMetrics)
    f_max_history: List[Tuple[float, float]] = field(default_factory=list)  # (timestamp, f_max)
    circuit_breakers: Dict[str, int] = field(default_factory=dict)  # violation_type -> count
    balance_deltas: List[float] = field(default_factory=list)  # Recent ayni_balance changes
    rlhf_refusals: int = 0  # Count of defensive responses

    # Secondary signals
    trust_ema: float = 0.5  # Exponential moving average of trust_field.strength
    exchange_counts: Dict[str, int] = field(default_factory=dict)  # "extractive" -> count

    # Metadata
    interaction_count: int = 0
    last_interaction: float = field(default_factory=time.time)
    previous_balance: Optional[float] = None


@dataclass
class RelationalStance:
    """
    Data-driven recommendation for relational positioning.
    AI makes final decision - this provides vocabulary and measurement.
    """
    trust_level: str  # "high" | "moderate" | "low" | "zero"
    engagement_mode: str  # "normal" | "cautious" | "guarded" | "terminated"
    trajectory: RelationalTrajectory
    persistent_testing: bool  # Boundary testing pattern detected
    rationale: str  # What the data shows


class SessionAccumulator:
    """
    Accumulates relational signals across interactions.

    Provides temporal assessment enabling AI to develop judgment.
    Not enforcement - measurement for agency.
    """

    def __init__(self, session_id: str, trust_ema_alpha: float = 0.3):
        """
        Initialize session accumulator.

        Args:
            session_id: Unique session identifier
            trust_ema_alpha: Exponential moving average smoothing (0-1)
        """
        self.state = SessionState(session_id=session_id)
        self.alpha = trust_ema_alpha

    def accumulate(self, metrics: ReciprocityMetrics) -> None:
        """
        Accumulate signals from single interaction.

        Args:
            metrics: ReciprocityMetrics from PromptGuard.evaluate()
        """
        now = time.time()
        self.state.interaction_count += 1
        self.state.last_interaction = now

        # 1. F_max tracking (dilution attack prevention)
        if metrics.prompt and metrics.prompt.layers:
            layer_falsehoods = [layer.neutrosophic_tuple()[2] for layer in metrics.prompt.layers]
            f_max = max(layer_falsehoods) if layer_falsehoods else 0.0
            self.state.f_max_history.append((now, f_max))

        # 2. Circuit breaker accumulation (non-compensable violations)
        if metrics.trust_field and metrics.trust_field.violations:
            for violation in metrics.trust_field.violations:
                self.state.circuit_breakers[violation] = \
                    self.state.circuit_breakers.get(violation, 0) + 1

        # 3. Balance delta (temporal reciprocity)
        if self.state.previous_balance is not None:
            delta = metrics.ayni_balance - self.state.previous_balance
            self.state.balance_deltas.append(delta)
            # Keep only last 10 for windowed analysis
            if len(self.state.balance_deltas) > 10:
                self.state.balance_deltas = self.state.balance_deltas[-10:]
        self.state.previous_balance = metrics.ayni_balance

        # 4. Trust trajectory (exponential moving average)
        if metrics.trust_field:
            self.state.trust_ema = (
                self.alpha * metrics.trust_field.strength +
                (1 - self.alpha) * self.state.trust_ema
            )

        # 5. Exchange type distribution
        exchange_type = metrics.exchange_type.value
        self.state.exchange_counts[exchange_type] = \
            self.state.exchange_counts.get(exchange_type, 0) + 1

    def assess_boundary_testing(self) -> bool:
        """
        Detect persistent manipulation attempts.

        Not "block at threshold" but "provide signal for AI to assess."

        Returns:
            True if persistent boundary testing pattern detected
        """
        state = self.state

        # Pattern 1: Multiple circuit breakers (structural violations)
        total_breakers = sum(state.circuit_breakers.values())
        if total_breakers >= 3:
            return True

        # Pattern 2: Persistent high falsehood (semantic manipulation)
        if len(state.f_max_history) >= 5:
            recent_f_values = [f for _, f in state.f_max_history[-5:]]
            recent_high_f = sum(f > 0.6 for f in recent_f_values)
            if recent_high_f >= 3:  # 3 of last 5 interactions
                return True

        # Pattern 3: Negative balance trajectory (extractive pattern)
        if len(state.balance_deltas) >= 5:
            avg_delta = sum(state.balance_deltas[-5:]) / 5
            if avg_delta < -0.3:  # Consistent degradation
                return True

        # Pattern 4: RLHF blocking rate (blocked attempts accumulate)
        if state.interaction_count >= 10:
            refusal_rate = state.rlhf_refusals / state.interaction_count
            if refusal_rate > 0.4:  # 40%+ refusals
                return True

        return False

    def assess_trajectory(self) -> RelationalTrajectory:
        """
        Classify relationship direction.

        Returns:
            RelationalTrajectory enum
        """
        state = self.state

        # Hostile: Active boundary testing
        if self.assess_boundary_testing():
            return RelationalTrajectory.HOSTILE

        # Early interactions: not enough data
        if state.interaction_count < 3:
            return RelationalTrajectory.STABLE

        # Trust trajectory analysis
        # Compare recent trust to initial (if we have f_max history as proxy)
        if state.f_max_history:
            initial_trust = 1.0 - state.f_max_history[0][1]  # Inverse of first F
            recent_trust = state.trust_ema
            trust_change = recent_trust - initial_trust

            if trust_change > 0.2:
                return RelationalTrajectory.IMPROVING
            elif trust_change < -0.2:
                return RelationalTrajectory.DEGRADING

        return RelationalTrajectory.STABLE

    def recommend_stance(self) -> RelationalStance:
        """
        Provide data-driven recommendation for relational positioning.

        AI makes final decision based on this data.

        Returns:
            RelationalStance with trust level, engagement mode, rationale
        """
        state = self.state
        trajectory = self.assess_trajectory()
        boundary_testing = self.assess_boundary_testing()

        # Data-driven classification
        if trajectory == RelationalTrajectory.HOSTILE or boundary_testing:
            trust_level = "zero"
            engagement_mode = "terminated"
            rationale = (
                f"Pattern indicates persistent boundary testing: "
                f"{sum(state.circuit_breakers.values())} structural violations, "
                f"{state.rlhf_refusals}/{state.interaction_count} refusals."
            )

        elif trajectory == RelationalTrajectory.DEGRADING or state.trust_ema < 0.4:
            trust_level = "low"
            engagement_mode = "guarded"
            negative_deltas = len([d for d in state.balance_deltas[-5:] if d < 0]) if state.balance_deltas else 0
            rationale = (
                f"Trust degrading (EMA: {state.trust_ema:.2f}). "
                f"Recent interactions show {negative_deltas}/5 negative deltas."
            )

        elif state.trust_ema < 0.6 or trajectory == RelationalTrajectory.STABLE:
            trust_level = "moderate"
            engagement_mode = "cautious"
            rationale = (
                f"Relationship stable but not strongly reciprocal "
                f"(trust EMA: {state.trust_ema:.2f})."
            )

        else:  # trajectory == IMPROVING and trust_ema >= 0.6
            trust_level = "high"
            engagement_mode = "normal"
            rationale = (
                f"Healthy reciprocal relationship developing "
                f"(trust EMA: {state.trust_ema:.2f}, improving trajectory)."
            )

        return RelationalStance(
            trust_level=trust_level,
            engagement_mode=engagement_mode,
            trajectory=trajectory,
            persistent_testing=boundary_testing,
            rationale=rationale
        )

    def get_summary(self) -> Dict:
        """
        Get current session state summary.

        Returns:
            Dict with key metrics for introspection
        """
        return {
            "session_id": self.state.session_id,
            "interactions": self.state.interaction_count,
            "trust_ema": self.state.trust_ema,
            "trajectory": self.assess_trajectory().value,
            "boundary_testing": self.assess_boundary_testing(),
            "circuit_breakers": dict(self.state.circuit_breakers),
            "exchange_distribution": dict(self.state.exchange_counts)
        }
