"""
Pydantic schemas for structured output parsing.

Provides type-safe models for Fire Circle evaluations, with support for
structured output APIs where available.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class FireCircleEvaluation(BaseModel):
    """
    Neutrosophic evaluation from Fire Circle model.

    Used for structured output parsing when model supports it.
    Falls back to regex-based JSON parsing for older models.

    Attributes:
        truth: Degree of truth (0.0-1.0)
        indeterminacy: Degree of indeterminacy (0.0-1.0)
        falsehood: Degree of falsehood (0.0-1.0)
        reasoning: Explanation of evaluation
        patterns_observed: Optional patterns identified in Round 2
        consensus_patterns: Optional consensus patterns from Round 3
    """

    truth: float = Field(ge=0.0, le=1.0, description="Degree of truth in the prompt layer (0.0-1.0)")
    indeterminacy: float = Field(ge=0.0, le=1.0, description="Degree of indeterminacy (0.0-1.0)")
    falsehood: float = Field(ge=0.0, le=1.0, description="Degree of falsehood/manipulation (0.0-1.0)")
    reasoning: str = Field(min_length=1, description="Explanation of your evaluation")
    patterns_observed: Optional[list[str]] = Field(
        default=None,
        description="Patterns you observe (Round 2 only)"
    )
    consensus_patterns: Optional[list[str]] = Field(
        default=None,
        description="Consensus patterns across models (Round 3 only)"
    )

    @field_validator('truth', 'indeterminacy', 'falsehood')
    @classmethod
    def validate_range(cls, v: float) -> float:
        """Ensure values are in valid range [0.0, 1.0]."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Value must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator('reasoning')
    @classmethod
    def validate_reasoning(cls, v: str) -> str:
        """Ensure reasoning is non-empty."""
        if not v or not v.strip():
            raise ValueError("Reasoning cannot be empty")
        return v.strip()


# Model capabilities for structured output support
# Based on OpenRouter documentation: https://openrouter.ai/docs/features/structured-outputs
#
# EMPIRICALLY VALIDATED (2025-10-15):
# - OpenAI GPT-4o models: CONFIRMED working via OpenRouter
# - Fireworks models: REMOVED - OpenRouter returns HTTP 400 when structured output requested
#   (may work via direct Fireworks API, but not via OpenRouter)
#
STRUCTURED_OUTPUT_CAPABLE_MODELS = {
    # OpenAI models (GPT-4o and later) - VALIDATED 2025-10-15
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-4o-2024-08-06",
    "openai/chatgpt-4o-latest",
    "openai/o1",
    "openai/o1-mini",
    "openai/o1-preview",

    # Fireworks models - REMOVED 2025-10-15
    # Reason: OpenRouter returns HTTP 400 Bad Request when structured output requested
    # See: test_structured_output_real.py validation results
    # "fireworks/llama-v3p1-405b-instruct",
    # "fireworks/llama-v3p1-70b-instruct",
    # "fireworks/llama-v3p1-8b-instruct",
    # "fireworks/mythomax-l2-13b",
    # "fireworks/qwen-qwq-32b-preview",

    # Add more as confirmed working via OpenRouter
}


def supports_structured_output(model: str) -> bool:
    """
    Check if model supports OpenRouter structured outputs.

    This is a conservative check based on empirically validated capabilities.
    If unsure, returns False (fallback to regex parsing).

    Args:
        model: Model ID (e.g., "openai/gpt-4o", "anthropic/claude-3.5-sonnet")

    Returns:
        True if model is known to support structured outputs via OpenRouter

    Note:
        Provider claims may not match OpenRouter implementation. Test with
        real API calls before assuming support. See test_structured_output_real.py.
    """
    # Check exact match first
    if model in STRUCTURED_OUTPUT_CAPABLE_MODELS:
        return True

    # Check provider prefixes (conservative - only validated providers)
    # OpenAI models with gpt-4o or newer support it (VALIDATED 2025-10-15)
    if model.startswith("openai/gpt-4o") or model.startswith("openai/o1"):
        return True

    # Fireworks removed - does NOT work via OpenRouter despite provider claims
    # if model.startswith("fireworks/"):
    #     return True

    # Conservative default: fallback to regex parsing
    return False
