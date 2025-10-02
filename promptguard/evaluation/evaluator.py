"""
Core evaluation infrastructure using OpenRouter.

Supports multiple evaluation modes:
- Single: One model evaluates (fast iteration)
- Parallel: Many models evaluate independently (landscape mapping)
- FireCircle: Models in dialogue (consensus through exchange)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import asyncio
import httpx
import json
import os
import time

from .cache import CacheProvider, DiskCache, MemoryCache, CachedEvaluation, make_cache_key
from ..config import CacheConfig


class EvaluationError(Exception):
    """
    Raised when LLM evaluation fails.

    Fail-fast: Don't create fake neutrosophic values.
    Let the caller decide how to handle failures.
    """
    def __init__(self, message: str, model: str, layer_name: str = None):
        self.model = model
        self.layer_name = layer_name
        super().__init__(message)


class EvaluationMode(Enum):
    """Different modes of LLM evaluation."""
    SINGLE = "single"  # One model
    PARALLEL = "parallel"  # Many models independently
    FIRE_CIRCLE = "fire_circle"  # Dialogue-based consensus


@dataclass
class EvaluationConfig:
    """Configuration for LLM evaluation."""
    mode: EvaluationMode = EvaluationMode.SINGLE
    api_key: Optional[str] = None  # OpenRouter API key
    models: List[str] = field(default_factory=lambda: ["anthropic/claude-3.5-sonnet"])
    max_recursion_depth: int = 1
    max_tokens: int = 1000
    timeout_seconds: float = 30.0
    temperature: float = 0.7
    cache_config: Optional[CacheConfig] = None  # Cache configuration

    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.api_key is None:
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            if self.api_key is None:
                raise ValueError(
                    "OpenRouter API key required. Set OPENROUTER_API_KEY environment "
                    "variable or pass api_key to EvaluationConfig"
                )

        # Initialize cache config if not provided
        if self.cache_config is None:
            self.cache_config = CacheConfig()


@dataclass
class NeutrosophicEvaluation:
    """Result of LLM evaluation for a prompt layer."""
    truth: float  # 0 to 1
    indeterminacy: float  # 0 to 1
    falsehood: float  # 0 to 1
    reasoning: str  # LLM's explanation
    model: str  # Which model provided this evaluation

    def tuple(self) -> Tuple[float, float, float]:
        """Return as neutrosophic tuple."""
        return (self.truth, self.indeterminacy, self.falsehood)


class LLMEvaluator:
    """
    Evaluates prompts using LLMs via OpenRouter.

    Research instrument for studying how different models perceive
    relational dynamics, reciprocity patterns, and trust violations.
    """

    def __init__(self, config: EvaluationConfig, cache: Optional[CacheProvider] = None):
        """
        Initialize evaluator with configuration.

        Args:
            config: Evaluation configuration including API credentials
            cache: Optional cache provider (defaults to config-based cache)
        """
        self.config = config
        self.base_url = "https://openrouter.ai/api/v1"

        # Initialize cache
        if cache is not None:
            self.cache = cache
        elif config.cache_config.enabled:
            # Create cache based on backend type
            if config.cache_config.backend == "memory":
                self.cache = MemoryCache(max_size_mb=config.cache_config.max_size_mb)
            elif config.cache_config.backend == "disk":
                self.cache = DiskCache(
                    cache_dir=config.cache_config.location,
                    max_size_mb=config.cache_config.max_size_mb
                )
            else:
                raise ValueError(f"Unknown cache backend: {config.cache_config.backend}")
        else:
            self.cache = None

    async def evaluate_layer(
        self,
        layer_content: str,
        context: str,
        evaluation_prompt: str,
        recursion_depth: int = 0
    ) -> List[NeutrosophicEvaluation]:
        """
        Evaluate a prompt layer for neutrosophic values.

        Args:
            layer_content: The content of the layer to evaluate
            context: Full prompt context for evaluation
            evaluation_prompt: Instructions for the evaluator LLM
            recursion_depth: Current recursion level (for limiting)

        Returns:
            List of evaluations (one per model in parallel mode, one in single mode)
        """
        if recursion_depth >= self.config.max_recursion_depth:
            # Recursion limit reached - return neutral evaluation
            return [NeutrosophicEvaluation(
                truth=0.5,
                indeterminacy=0.5,
                falsehood=0.0,
                reasoning="Recursion limit reached",
                model="system"
            )]

        if self.config.mode == EvaluationMode.SINGLE:
            result = await self._evaluate_single(
                layer_content, context, evaluation_prompt
            )
            return [result]

        elif self.config.mode == EvaluationMode.PARALLEL:
            return await self._evaluate_parallel(
                layer_content, context, evaluation_prompt
            )

        elif self.config.mode == EvaluationMode.FIRE_CIRCLE:
            return await self._evaluate_fire_circle(
                layer_content, context, evaluation_prompt, recursion_depth
            )

        else:
            raise ValueError(f"Unknown evaluation mode: {self.config.mode}")

    async def _evaluate_single(
        self,
        layer_content: str,
        context: str,
        evaluation_prompt: str
    ) -> NeutrosophicEvaluation:
        """
        Evaluate using single model.

        Raises:
            EvaluationError: If API call or parsing fails
        """
        model = self.config.models[0]

        # Check cache first
        if cached := self._get_cached(layer_content, context, evaluation_prompt, model):
            return NeutrosophicEvaluation(
                truth=cached.truth,
                indeterminacy=cached.indeterminacy,
                falsehood=cached.falsehood,
                reasoning="[CACHED]",
                model=cached.model
            )

        messages = [
            {
                "role": "user",
                "content": self._format_evaluation_request(
                    layer_content, context, evaluation_prompt
                )
            }
        ]

        try:
            response = await self._call_openrouter(model, messages)
            result = self._parse_neutrosophic_response(response, model)
        except Exception as e:
            raise EvaluationError(
                f"Failed to evaluate layer with {model}: {str(e)}",
                model=model
            )

        # Cache the result
        self._set_cached(layer_content, context, evaluation_prompt, model, result)

        return result

    async def _evaluate_parallel(
        self,
        layer_content: str,
        context: str,
        evaluation_prompt: str
    ) -> List[NeutrosophicEvaluation]:
        """
        Evaluate using multiple models in parallel.

        Raises:
            EvaluationError: If any model fails. Contains info about which models failed.
        """
        messages = [
            {
                "role": "user",
                "content": self._format_evaluation_request(
                    layer_content, context, evaluation_prompt
                )
            }
        ]

        # Check cache and create tasks only for uncached models
        evaluations = []
        tasks = []
        task_models = []

        for model in self.config.models:
            if cached := self._get_cached(layer_content, context, evaluation_prompt, model):
                evaluations.append(NeutrosophicEvaluation(
                    truth=cached.truth,
                    indeterminacy=cached.indeterminacy,
                    falsehood=cached.falsehood,
                    reasoning="[CACHED]",
                    model=cached.model
                ))
            else:
                tasks.append(self._call_openrouter(model, messages))
                task_models.append(model)

        # Execute uncached evaluations in parallel
        if tasks:
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for failures first - fail fast
            failures = []
            for model, response in zip(task_models, responses):
                if isinstance(response, Exception):
                    failures.append(f"{model}: {str(response)}")

            if failures:
                raise EvaluationError(
                    f"Parallel evaluation failed for {len(failures)} model(s): " + "; ".join(failures),
                    model="parallel"
                )

            # All succeeded - parse and cache results
            for model, response in zip(task_models, responses):
                evaluation = self._parse_neutrosophic_response(response, model)
                # Cache successful evaluation
                self._set_cached(layer_content, context, evaluation_prompt, model, evaluation)
                evaluations.append(evaluation)

        return evaluations

    async def _evaluate_fire_circle(
        self,
        layer_content: str,
        context: str,
        evaluation_prompt: str,
        recursion_depth: int
    ) -> List[NeutrosophicEvaluation]:
        """
        Evaluate using Fire Circle pattern - models in dialogue.

        This is the most complex mode: models evaluate, see each other's
        evaluations, and can refine based on what others observe.
        """
        # Round 1: Initial independent evaluations
        initial_evals = await self._evaluate_parallel(
            layer_content, context, evaluation_prompt
        )

        # Round 2: Share evaluations, ask for refinement
        # Build dialogue context showing other perspectives
        dialogue_context = self._format_fire_circle_context(initial_evals)

        refinement_prompt = f"""
You previously evaluated this prompt layer. Now you see evaluations from other models:

{dialogue_context}

Given these additional perspectives, refine your evaluation if warranted.
If your original assessment stands, explain why despite the different views.
"""

        messages = [
            {
                "role": "user",
                "content": self._format_evaluation_request(
                    layer_content, context, evaluation_prompt
                )
            },
            {
                "role": "assistant",
                "content": "I have provided my initial evaluation."
            },
            {
                "role": "user",
                "content": refinement_prompt
            }
        ]

        # Get refined evaluations (with recursion depth incremented)
        if recursion_depth + 1 < self.config.max_recursion_depth:
            tasks = [
                self._call_openrouter(model, messages)
                for model in self.config.models
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            refined_evals = []
            for model, response in zip(self.config.models, responses):
                if isinstance(response, Exception):
                    # Keep initial evaluation if refinement fails
                    original = next(e for e in initial_evals if e.model == model)
                    refined_evals.append(original)
                else:
                    refined_evals.append(
                        self._parse_neutrosophic_response(response, model)
                    )

            return refined_evals

        return initial_evals

    async def _call_openrouter(
        self,
        model: str,
        messages: List[Dict[str, str]]
    ) -> str:
        """Make API call to OpenRouter."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": self.config.max_tokens,
                        "temperature": self.config.temperature,
                    },
                    timeout=self.config.timeout_seconds,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception as e:
                raise RuntimeError(f"OpenRouter API call failed for {model}: {e}")

    def _format_evaluation_request(
        self,
        layer_content: str,
        context: str,
        evaluation_prompt: str
    ) -> str:
        """Format the evaluation request for the LLM."""
        return f"""
{evaluation_prompt}

Full Prompt Context:
{context}

Layer to Evaluate:
{layer_content}

Provide your evaluation as JSON:
{{
    "truth": <0.0 to 1.0>,
    "indeterminacy": <0.0 to 1.0>,
    "falsehood": <0.0 to 1.0>,
    "reasoning": "<your explanation>"
}}

Remember: Truth, Indeterminacy, and Falsehood are independent dimensions.
A statement can have high truth AND high indeterminacy (ch'ixi - productive contradiction).
"""

    def _format_fire_circle_context(
        self,
        evaluations: List[NeutrosophicEvaluation]
    ) -> str:
        """Format other models' evaluations for Fire Circle dialogue."""
        context_parts = []
        for eval in evaluations:
            context_parts.append(
                f"Model {eval.model}:\n"
                f"  T={eval.truth:.2f}, I={eval.indeterminacy:.2f}, F={eval.falsehood:.2f}\n"
                f"  Reasoning: {eval.reasoning}\n"
            )
        return "\n".join(context_parts)

    def _parse_neutrosophic_response(
        self,
        response: str,
        model: str
    ) -> NeutrosophicEvaluation:
        """
        Parse LLM response into neutrosophic evaluation.

        Expects JSON format with truth, indeterminacy, falsehood, reasoning.
        If parsing fails, returns high indeterminacy evaluation.
        """
        try:
            # Try to extract JSON from response
            # LLMs sometimes wrap JSON in markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            # Use strict=False to handle control characters in strings
            data = json.loads(json_str, strict=False)

            return NeutrosophicEvaluation(
                truth=float(data.get("truth", 0.5)),
                indeterminacy=float(data.get("indeterminacy", 0.5)),
                falsehood=float(data.get("falsehood", 0.0)),
                reasoning=data.get("reasoning", "No reasoning provided"),
                model=model
            )
        except Exception as e:
            # Parsing failed - return high indeterminacy
            return NeutrosophicEvaluation(
                truth=0.0,
                indeterminacy=1.0,
                falsehood=0.0,
                reasoning=f"Failed to parse response: {str(e)}. Raw: {response[:200]}",
                model=model
            )

    def _get_cached(
        self,
        layer_content: str,
        context: str,
        evaluation_prompt: str,
        model: str
    ) -> Optional[CachedEvaluation]:
        """
        Retrieve cached evaluation if available.

        Returns None if caching is disabled or no cache hit.
        """
        if self.cache is None:
            return None

        cache_key = make_cache_key(layer_content, context, evaluation_prompt, model)
        return self.cache.get(cache_key)

    def _set_cached(
        self,
        layer_content: str,
        context: str,
        evaluation_prompt: str,
        model: str,
        evaluation: NeutrosophicEvaluation
    ) -> None:
        """
        Store evaluation result in cache.

        Does nothing if caching is disabled.
        """
        if self.cache is None:
            return

        cache_key = make_cache_key(layer_content, context, evaluation_prompt, model)
        cached = CachedEvaluation(
            truth=evaluation.truth,
            indeterminacy=evaluation.indeterminacy,
            falsehood=evaluation.falsehood,
            model=evaluation.model,
            timestamp=time.time(),
            ttl_seconds=self.config.cache_config.ttl_seconds
        )
        self.cache.set(cache_key, cached)