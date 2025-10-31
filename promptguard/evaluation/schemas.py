"""
Pydantic schemas for structured output parsing.

Provides type-safe models for Fire Circle evaluations, with support for
structured output APIs where available.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
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

    model_config = ConfigDict(extra='allow')

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
# EMPIRICALLY VALIDATED (2025-10-15, updated 2025-10-25):
# - OpenAI GPT-4o models: CONFIRMED working via OpenRouter
# - Anthropic Claude models: NOT SUPPORTED - OpenRouter catalog shows 0/12 Anthropic models support structured_outputs
# - Mistral, Google, DeepSeek, Qwen: SUPPORTED per OpenRouter catalog (175 total models)
# - Fireworks models: REMOVED - OpenRouter returns HTTP 400 when structured output requested
#   (may work via direct Fireworks API, but not via OpenRouter)
#
# Instance 52 fix: Expanded from 7 OpenAI models to include Mistral/Google/DeepSeek based on
# OpenRouter catalog analysis showing 175 models with structured_outputs parameter.
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

    # Mistral models - OpenRouter catalog shows 27/36 support structured_outputs (75%)
    "mistralai/mistral-medium-3.1",
    "mistralai/codestral-2508",
    "mistralai/devstral-medium",

    # Google models - OpenRouter catalog shows 18/25 support structured_outputs (72%)
    "google/gemini-2.5-flash-preview-09-2025",
    "google/gemini-2.0-flash-exp",

    # DeepSeek models - OpenRouter catalog shows 8/18 support structured_outputs (44%)
    "deepseek/deepseek-v3.2-exp",
    "deepseek/deepseek-chat-v3.1",

    # Qwen models - OpenRouter catalog shows support
    "qwen/qwen-2.5-72b-instruct",

    # Nous Research models - Hermes 4 supports structured outputs per model page
    # Source: https://openrouter.ai/nousresearch/hermes-4-405b
    "nousresearch/hermes-4-405b",

    # Meta Llama models - Llama 3.3 70B supports response_format, tools, function calling
    # Source: https://openrouter.ai/meta-llama/llama-3.3-70b-instruct
    "meta-llama/llama-3.3-70b-instruct",

    # Anthropic models - EXPLICITLY EXCLUDED
    # OpenRouter catalog analysis: 0/12 Anthropic models support structured_outputs parameter
    # This is an Anthropic API limitation, not OpenRouter or Instructor limitation

    # Fireworks models - REMOVED 2025-10-15
    # Reason: OpenRouter returns HTTP 400 Bad Request when structured output requested
    # See: test_structured_output_real.py validation results
}


def supports_structured_output(model: str) -> bool:
    """
    Check if model supports OpenRouter structured outputs.

    This is a conservative check based on empirically validated capabilities.
    If unsure, returns False (fallback to regex parsing).

    Args:
        model: Model ID (e.g., "openai/gpt-4o", "anthropic/claude-sonnet-4.5")

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
