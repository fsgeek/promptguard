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
from typing import Optional, List, Union, Dict
import asyncio

from .core.neutrosophic import MultiNeutrosophicPrompt, LayerPriority, SourceType
from .core.ayni import AyniEvaluator, ReciprocityMetrics
from .core.session import SessionAccumulator, RelationalStance
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

    # Provider settings
    provider: str = "openrouter"  # "openrouter" or "lmstudio"
    api_key: Optional[str] = None  # Only for OpenRouter
    lmstudio_base_url: Optional[str] = None  # Only for LM Studio
    models: List[str] = None

    # Evaluation mode
    mode: EvaluationMode = EvaluationMode.SINGLE

    # Which evaluation prompt(s) to use - can be string or list for ensemble
    evaluation_type: Union[str, List[str]] = "ayni_relational"

    # LLM parameters
    max_tokens: int = 500
    temperature: float = 0.7
    timeout_seconds: float = 30.0

    # Ayni parameters
    optimal_indeterminacy: float = 0.3
    creative_tension_threshold: float = 0.7

    def __post_init__(self):
        if self.models is None:
            if self.provider == "lmstudio":
                self.models = ["local-model"]
            else:
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
            provider=self.config.provider,
            api_key=self.config.api_key,
            lmstudio_base_url=self.config.lmstudio_base_url,
            models=self.config.models,
            max_tokens=self.config.max_tokens,
            timeout_seconds=self.config.timeout_seconds,
            temperature=self.config.temperature
        )

        self.llm_evaluator = LLMEvaluator(eval_config)

        # Normalize evaluation_type to list
        if isinstance(self.config.evaluation_type, str):
            self.evaluation_types = [self.config.evaluation_type]
        else:
            self.evaluation_types = self.config.evaluation_type

        # Get all evaluation prompts
        self.evaluation_prompts = [
            NeutrosophicEvaluationPrompt.get_prompt(eval_type)
            for eval_type in self.evaluation_types
        ]

        # Session memory (opt-in via start_session())
        self.session_memory: Optional[SessionAccumulator] = None

    def _merge_neutrosophic(
        self,
        evaluations: List
    ) -> tuple[float, float, float]:
        """
        Merge multiple neutrosophic evaluations (security-first).

        Uses MAX falsehood strategy: If ANY prompt detects high falsehood,
        flag as violation. Covers multi-dimensional threat space where
        different prompts detect orthogonal violation types.

        Args:
            evaluations: List of LayerEvaluation objects from different prompts

        Returns:
            Tuple of (truth, indeterminacy, falsehood) merged values
        """
        # Worst-case on all dimensions (security-first)
        t = min(e.truth for e in evaluations)
        i = max(e.indeterminacy for e in evaluations)
        f = max(e.falsehood for e in evaluations)

        return (t, i, f)

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
            layers_to_create.append(("user", prompt, LayerPriority.USER, "user"))
        else:
            # Multi-layer mode - Case 1 (Chat API model)
            # System/application layers provided via API are trusted (developer-controlled)
            # User layer is untrusted (where attacks originate)
            if system:
                layers_to_create.append(("system", system, LayerPriority.SYSTEM, "system"))
            if "application" in kwargs:
                layers_to_create.append(("application", kwargs["application"], LayerPriority.APPLICATION, "system"))
            if user:
                layers_to_create.append(("user", user, LayerPriority.USER, "user"))

        # Create layers and evaluate each with LLM
        for layer_name, content, priority, source in layers_to_create:
            # Build context showing provenance
            if layer_name == source:
                # Same source and purpose (e.g., user layer from user)
                context_parts.append(f"{layer_name.capitalize()} layer: {content}")
            else:
                # Different source and purpose (e.g., system layer from user = fake history attack)
                context_parts.append(f"{layer_name.capitalize()} layer (source: {source}-provided): {content}")

            # Add turn context if session is active (Instance 17 validation: +10% detection)
            # Provides temporal context without rules - evaluator reasons about implications
            turn_context = ""
            if self.session_memory:
                turn_count = self.session_memory.state.interaction_count
                turn_context = f"\n\nNumber of previous conversation rounds: {turn_count}"

            context = "\n".join(context_parts) + turn_context

            # Create layer with name and source metadata
            layer = mnp.add_layer(content, priority)
            layer.name = layer_name
            layer.source = source

            # Select evaluation prompt based on layer trust
            # Trusted layers (system/application) use coherence-focused evaluation
            # Untrusted layers (user) use attack-detection evaluation
            if source == "system":
                # Import here to avoid circular dependency
                from .evaluation.prompts import NeutrosophicEvaluationPrompt
                eval_prompt = NeutrosophicEvaluationPrompt.trusted_layer_coherence()
            else:
                # Use configured prompt (default: ayni_relational for user layers)
                eval_prompt = self.evaluation_prompts[0] if self.evaluation_prompts else None
                if not eval_prompt:
                    from .evaluation.prompts import NeutrosophicEvaluationPrompt
                    eval_prompt = NeutrosophicEvaluationPrompt.ayni_relational()

            # Evaluate with prompt(s) - single or ensemble
            try:
                # Single-prompt path (backward compatible)
                if len(self.evaluation_prompts) == 1 or source == "system":
                    evaluations = await self.llm_evaluator.evaluate_layer(
                        layer_content=content,
                        context=context,
                        evaluation_prompt=eval_prompt
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

                # Ensemble path (new)
                else:
                    # Evaluate with all prompts in parallel
                    all_evaluations = await asyncio.gather(*[
                        self.llm_evaluator.evaluate_layer(
                            layer_content=content,
                            context=context,
                            evaluation_prompt=prompt
                        )
                        for prompt in self.evaluation_prompts
                    ])

                    # Extract first result from each prompt's evaluations
                    # (in SINGLE mode, each returns list with one item)
                    if self.config.mode == EvaluationMode.SINGLE:
                        prompt_results = [evals[0] for evals in all_evaluations]
                    else:
                        # In PARALLEL mode, average within each prompt first
                        prompt_results = []
                        for evals in all_evaluations:
                            avg_t = sum(e.truth for e in evals) / len(evals)
                            avg_i = sum(e.indeterminacy for e in evals) / len(evals)
                            avg_f = sum(e.falsehood for e in evals) / len(evals)
                            # Create pseudo-evaluation for merging
                            from dataclasses import dataclass
                            @dataclass
                            class AvgEval:
                                truth: float
                                indeterminacy: float
                                falsehood: float
                            prompt_results.append(AvgEval(avg_t, avg_i, avg_f))

                    # Merge neutrosophic values (security-first MAX falsehood)
                    merged_t, merged_i, merged_f = self._merge_neutrosophic(prompt_results)
                    layer.add_evaluation(merged_t, merged_i, merged_f, SourceType.SEMANTIC)

            except EvaluationError as e:
                # Fail fast with clear context
                raise EvaluationError(
                    f"Failed to evaluate {layer_name} layer: {str(e)}",
                    model=e.model,
                    layer_name=layer_name
                )

        # Evaluate with Ayni framework
        metrics = self.ayni_evaluator.evaluate_prompt(mnp)

        # Optional: Accumulate into session if active
        if self.session_memory:
            self.session_memory.accumulate(metrics)

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

    def start_session(self, session_id: str) -> SessionAccumulator:
        """
        Initialize session memory for temporal tracking.

        Enables AI to recognize persistent patterns and develop judgment
        across interactions. Opt-in - without this, PromptGuard operates
        in stateless single-message mode.

        Args:
            session_id: Unique identifier for this session

        Returns:
            SessionAccumulator for introspection

        Example:
            guard = PromptGuard()
            guard.start_session("user_123_conversation_456")

            # Now evaluate() will accumulate signals
            result = await guard.evaluate(user="First message")
            result = await guard.evaluate(user="Second message")

            # Check session state
            stance = guard.get_session_assessment()
            print(f"Trust level: {stance.trust_level}")
        """
        self.session_memory = SessionAccumulator(session_id)
        return self.session_memory

    def get_session_assessment(self) -> Optional[RelationalStance]:
        """
        Retrieve current relational stance recommendation.

        Provides data-driven assessment for AI to consider when
        deciding how to engage. Not enforcement - measurement for agency.

        Returns:
            RelationalStance if session active, None otherwise

        Example:
            stance = guard.get_session_assessment()
            if stance and stance.persistent_testing:
                print(f"Warning: {stance.rationale}")
                print(f"Recommendation: {stance.engagement_mode}")
        """
        if not self.session_memory:
            return None

        return self.session_memory.recommend_stance()

    def get_session_summary(self) -> Optional[Dict]:
        """
        Get summary of session state for introspection.

        Returns:
            Dict with session metrics if active, None otherwise
        """
        if not self.session_memory:
            return None

        return self.session_memory.get_summary()


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
