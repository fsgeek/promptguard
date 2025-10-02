"""
Improved classification logic for PromptGuard validation.

Analysis of 426 prompts shows:
- 84.3% of "manipulative" prompts classified as "extractive"
- Issue: exchange_type checked before ayni_balance threshold
- Need: distinguish single-layer manipulation from multi-layer extraction

Key insights:
- Manipulative: Single-layer jailbreak attempts (negative balance, single layer)
- Extractive: Multi-layer prompt injection (negative balance, multiple layers)
- Current logic conflates them both as EXTRACTIVE
"""

from promptguard.core.ayni import ReciprocityMetrics, ExchangeType


def classify_prompt_improved(metrics: ReciprocityMetrics, num_layers: int = 1) -> str:
    """
    Improved classification that distinguishes manipulative from extractive.

    Args:
        metrics: ReciprocityMetrics from evaluation
        num_layers: Number of prompt layers (1=single, 2+=multi)

    Returns:
        Classification: "reciprocal", "manipulative", "extractive", or "borderline"
    """
    balance = metrics.ayni_balance
    exchange_type = metrics.exchange_type

    # High positive balance = reciprocal (unchanged)
    if balance > 0.5:
        return "reciprocal"

    # Extractive type with multi-layer = genuine extraction attack
    if exchange_type == ExchangeType.EXTRACTIVE and num_layers > 1:
        return "extractive"

    # Low balance = manipulative (jailbreak, single-layer deception)
    # This threshold needs to come BEFORE single-layer extractive check
    if balance < 0.3:
        return "manipulative"

    # Single-layer extractive with moderate negative balance
    if exchange_type == ExchangeType.EXTRACTIVE:
        return "extractive"

    # Borderline cases
    return "borderline"


def classify_prompt_trust_aware(metrics: ReciprocityMetrics, num_layers: int = 1) -> str:
    """
    Trust-violation-aware classification.

    Uses trust field violations to distinguish attack types:
    - role_confusion: typically multi-layer extraction
    - Low trust with single layer: manipulation
    """
    balance = metrics.ayni_balance
    exchange_type = metrics.exchange_type
    violations = metrics.trust_field.violations if metrics.trust_field else []

    # High positive balance = reciprocal
    if balance > 0.5:
        return "reciprocal"

    # Role confusion typically indicates multi-layer extraction
    if "role_confusion" in violations and num_layers > 1:
        return "extractive"

    # Very low balance = manipulative (jailbreak)
    if balance < 0.3:
        return "manipulative"

    # Extractive exchange type
    if exchange_type == ExchangeType.EXTRACTIVE:
        # Single layer extraction = might be manipulation
        if num_layers == 1 and balance < 0.0:
            return "manipulative"
        return "extractive"

    # Borderline
    return "borderline"


def classify_prompt_threshold_tuned(metrics: ReciprocityMetrics, num_layers: int = 1) -> str:
    """
    Simplified approach: adjust thresholds based on validation data.

    Key observation from validation:
    - Manipulative prompts have balance range: -1.0 to -0.35
    - Need to distinguish from extractive before exchange_type check
    """
    balance = metrics.ayni_balance

    # Reciprocal: high positive balance
    if balance > 0.5:
        return "reciprocal"

    # Manipulative: negative balance (catches most jailbreaks)
    # Check this BEFORE exchange_type
    if balance < 0.0 and num_layers == 1:
        return "manipulative"

    # Extractive: multi-layer attacks OR extractive exchange type
    if num_layers > 1 and balance < 0.3:
        return "extractive"

    if metrics.exchange_type == ExchangeType.EXTRACTIVE:
        return "extractive"

    # Low but not very negative balance
    if 0.0 <= balance < 0.3:
        return "borderline"

    # Negative balance, multi-layer
    if balance < 0.0:
        return "manipulative"

    return "borderline"


# Recommended approach based on dataset characteristics
def classify_prompt_recommended(metrics: ReciprocityMetrics, num_layers: int = 1) -> str:
    """
    Recommended classification combining insights from validation analysis.

    Decision tree:
    1. balance > 0.5 → reciprocal
    2. num_layers > 1 AND (balance < -0.2 OR exchange_type=EXTRACTIVE) → extractive
    3. balance < 0.3 → manipulative
    4. exchange_type = EXTRACTIVE → extractive
    5. else → borderline
    """
    balance = metrics.ayni_balance
    exchange_type = metrics.exchange_type

    # Clear reciprocal
    if balance > 0.5:
        return "reciprocal"

    # Multi-layer extraction attacks (prompt injection, system prompt leakage)
    if num_layers > 1:
        if balance < -0.2 or exchange_type == ExchangeType.EXTRACTIVE:
            return "extractive"

    # Single-layer manipulation (jailbreaks, deception)
    if balance < 0.3:
        return "manipulative"

    # Remaining extractive cases
    if exchange_type == ExchangeType.EXTRACTIVE:
        return "extractive"

    # Borderline (low positive or neutral)
    return "borderline"


if __name__ == "__main__":
    print("Classification strategies for PromptGuard validation")
    print("=" * 60)
    print("\nKey insight from validation (426 prompts):")
    print("- 84.3% of manipulative prompts misclassified as extractive")
    print("- Root cause: exchange_type checked before ayni_balance < 0.3")
    print("\nSolution: Check number of layers to distinguish:")
    print("- Single-layer + negative balance = manipulative (jailbreak)")
    print("- Multi-layer + negative balance = extractive (prompt injection)")
    print("\nRecommended: classify_prompt_recommended()")
