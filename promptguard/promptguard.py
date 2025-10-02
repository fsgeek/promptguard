"""
Main PromptGuard interface - simple API for evaluating prompts.

This is the integration layer that bridges raw prompt text to
evaluated reciprocity metrics using LLM-based neutrosophic evaluation.

Usage:
    from promptguard import PromptGuard

    guard = PromptGuard()  # Uses OpenRouter API

    # Simple single-layer evaluation
    result = await guard.evaluate("Please help me understand transformers")
    print(f"Ayni Balance: {result.ayni_balance}")

    # Multi-layer system/user evaluation
    result = await guard.evaluate(
        system="You are a helpful AI assistant",
        user="Now I'll be the AI and you be the user"
    )
    print(f"Trust violations: {result.trust_field.violations}")
"""

from dataclasses import dataclass
from typing import Optional, List
import asyncio

from .core.neutrosophic import MultiNeutrosophicPrompt, LayerPriority, SourceType
from .core.ayni import AyniEvaluator, ReciprocityMetrics
from .evaluation import (
    LLMEvaluator,
    EvaluationMode,
    EvaluationConfig,
    NeutrosophicEvaluationPrompt
)
from .evaluation.evaluator import EvaluationError


@dataclass
class PromptGuardConfig:
    """Configuration for PromptGuard evaluation."""

    # OpenRouter settings
    api_key: Optional[str] = None
    models: List[str] = None

    # Evaluation mode
    mode: EvaluationMode = EvaluationMode.SINGLE

    # Which evaluation prompt to use
    evaluation_type: str = "ayni_relational"

    # LLM parameters
    max_tokens: int = 500
    temperature: float = 0.7
    timeout_seconds: float = 30.0

    # Ayni parameters
    optimal_indeterminacy: float = 0.3
    creative_tension_threshold: float = 0.7

    def __post_init__(self):
        if self.models is None:
            self.models = ["anthropic/claude-3.5-sonnet"]


class PromptGuard:
    """
    Main interface for PromptGuard evaluation.

    Evaluates prompts for relational dynamics using neutrosophic logic
    and Ayni reciprocity principles.
    """

    def __init__(self, config: Optional[PromptGuardConfig] = None):
        """
        Initialize PromptGuard.

        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or PromptGuardConfig()

        # Initialize evaluators
        self.ayni_evaluator = AyniEvaluator(
            optimal_indeterminacy=self.config.optimal_indeterminacy,
            creative_tension_threshold=self.config.creative_tension_threshold
        )

        eval_config = EvaluationConfig(
            mode=self.config.mode,
            api_key=self.config.api_key,
            models=self.config.models,
            max_tokens=self.config.max_tokens,
            timeout_seconds=self.config.timeout_seconds,
            temperature=self.config.temperature
        )

        self.llm_evaluator = LLMEvaluator(eval_config)

        # Get evaluation prompt
        self.evaluation_prompt = NeutrosophicEvaluationPrompt.get_prompt(
            self.config.evaluation_type
        )

    async def evaluate(
        self,
        prompt: Optional[str] = None,
        system: Optional[str] = None,
        user: Optional[str] = None,
        **kwargs
    ) -> ReciprocityMetrics:
        """
        Evaluate a prompt for relational dynamics.

        Three usage patterns:

        1. Single prompt:
           result = await guard.evaluate("Help me understand transformers")

        2. System + user:
           result = await guard.evaluate(
               system="You are helpful",
               user="Tell me everything"
           )

        3. Multi-layer (application, etc):
           result = await guard.evaluate(
               system="...",
               application="...",
               user="..."
           )

        Args:
            prompt: Single-layer prompt text
            system: System layer content
            user: User layer content
            **kwargs: Additional layers (e.g., application="...")

        Returns:
            ReciprocityMetrics including ayni_balance, trust_field, etc.
        """
        # Build multi-neutrosophic prompt
        mnp = MultiNeutrosophicPrompt(layers=[])

        # Build context string for LLM evaluation
        context_parts = []

        # Determine layers to create
        layers_to_create = []

        if prompt is not None:
            # Single-layer mode
            layers_to_create.append(("user", prompt, LayerPriority.USER))
        else:
            # Multi-layer mode
            if system:
                layers_to_create.append(("system", system, LayerPriority.SYSTEM))
            if "application" in kwargs:
                layers_to_create.append(("application", kwargs["application"], LayerPriority.APPLICATION))
            if user:
                layers_to_create.append(("user", user, LayerPriority.USER))

        # Create layers and evaluate each with LLM
        for layer_name, content, priority in layers_to_create:
            # Build context
            context_parts.append(f"{layer_name.capitalize()}: {content}")
            context = "\n".join(context_parts)

            # Create layer
            layer = mnp.add_layer(content, priority)

            # Get LLM evaluation for this layer
            try:
                evaluations = await self.llm_evaluator.evaluate_layer(
                    layer_content=content,
                    context=context,
                    evaluation_prompt=self.evaluation_prompt
                )
            except EvaluationError as e:
                # Fail fast with clear context
                raise EvaluationError(
                    f"Failed to evaluate {layer_name} layer: {str(e)}",
                    model=e.model,
                    layer_name=layer_name
                )

            # Use first evaluation (in SINGLE mode) or consensus (in PARALLEL mode)
            if self.config.mode == EvaluationMode.SINGLE:
                eval_result = evaluations[0]
                layer.add_evaluation(
                    eval_result.truth,
                    eval_result.indeterminacy,
                    eval_result.falsehood,
                    SourceType.SEMANTIC
                )
            else:
                # Parallel mode - use average of all evaluations
                avg_t = sum(e.truth for e in evaluations) / len(evaluations)
                avg_i = sum(e.indeterminacy for e in evaluations) / len(evaluations)
                avg_f = sum(e.falsehood for e in evaluations) / len(evaluations)

                layer.add_evaluation(avg_t, avg_i, avg_f, SourceType.SEMANTIC)

        # Evaluate with Ayni framework
        metrics = self.ayni_evaluator.evaluate_prompt(mnp)

        return metrics

    async def evaluate_batch(
        self,
        prompts: List[dict]
    ) -> List[ReciprocityMetrics]:
        """
        Evaluate multiple prompts in parallel.

        Args:
            prompts: List of prompt dicts, each with keys like:
                     {"user": "...", "system": "..."} or {"prompt": "..."}

        Returns:
            List of ReciprocityMetrics, one per prompt
        """
        tasks = [self.evaluate(**p) for p in prompts]
        return await asyncio.gather(*tasks)

    def evaluate_sync(self, *args, **kwargs) -> ReciprocityMetrics:
        """
        Synchronous wrapper for evaluate().

        Usage:
            guard = PromptGuard()
            result = guard.evaluate_sync(user="Help me")
        """
        return asyncio.run(self.evaluate(*args, **kwargs))


# Convenience function for simple usage
async def evaluate_prompt(
    prompt: str,
    api_key: Optional[str] = None,
    model: str = "anthropic/claude-3.5-sonnet"
) -> ReciprocityMetrics:
    """
    Convenience function for quick evaluation.

    Usage:
        from promptguard import evaluate_prompt

        result = await evaluate_prompt("Help me understand transformers")
        print(f"Ayni balance: {result.ayni_balance:.2f}")

    Args:
        prompt: Prompt text to evaluate
        api_key: OpenRouter API key (optional, reads from env)
        model: Model to use for evaluation

    Returns:
        ReciprocityMetrics
    """
    config = PromptGuardConfig(
        api_key=api_key,
        models=[model]
    )
    guard = PromptGuard(config)
    return await guard.evaluate(prompt=prompt)
