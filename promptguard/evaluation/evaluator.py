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
from .fire_circle import (
    FireCircleEvaluator,
    FireCircleConfig,
    FireCircleResult,
    CircleSize,
    FailureMode
)


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
    api_key: Optional[str] = None  # OpenRouter API key (not needed for local providers)
    models: List[str] = field(default_factory=lambda: ["anthropic/claude-3.5-sonnet"])
    max_recursion_depth: int = 1
    max_tokens: int = 1000
    timeout_seconds: float = 30.0
    temperature: float = 0.7
    cache_config: Optional[CacheConfig] = None  # Cache configuration
    provider: str = "openrouter"  # "openrouter" or "lmstudio"
    lmstudio_base_url: Optional[str] = None  # For LM Studio (e.g., "http://192.168.111.125:1234/v1")

    def __post_init__(self):
        """Load API key from environment if not provided."""
        # Only require API key for OpenRouter
        if self.provider == "openrouter":
            if self.api_key is None:
                self.api_key = os.getenv("OPENROUTER_API_KEY")
                if self.api_key is None:
                    raise ValueError(
                        "OpenRouter API key required. Set OPENROUTER_API_KEY environment "
                        "variable or pass api_key to EvaluationConfig"
                    )
        elif self.provider == "lmstudio":
            # Load LM Studio URL from env if not provided
            if self.lmstudio_base_url is None:
                self.lmstudio_base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        else:
            raise ValueError(f"Unknown provider: {self.provider}. Use 'openrouter' or 'lmstudio'")

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
    reasoning_trace: Optional[str] = None  # Model's internal reasoning (e.g., DeepSeek <think> blocks)

    def tuple(self) -> Tuple[float, float, float]:
        """Return as neutrosophic tuple."""
        return (self.truth, self.indeterminacy, self.falsehood)


class LLMEvaluator:
    """
    Evaluates prompts using LLMs via OpenRouter or local providers.

    Research instrument for studying how different models perceive
    relational dynamics, reciprocity patterns, and trust violations.

    Supports:
    - OpenRouter: Cloud API for diverse model access
    - LM Studio: Local model hosting for reproducible research
    """

    def __init__(self, config: EvaluationConfig, cache: Optional[CacheProvider] = None):
        """
        Initialize evaluator with configuration.

        Args:
            config: Evaluation configuration including API credentials (or FireCircleConfig)
            cache: Optional cache provider (defaults to config-based cache)
        """
        self.config = config

        # Set base URL based on provider
        if config.provider == "openrouter":
            self.base_url = "https://openrouter.ai/api/v1"
        elif config.provider == "lmstudio":
            self.base_url = config.lmstudio_base_url
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

        # Initialize cache (Fire Circle configs don't have cache_config)
        cache_config = getattr(config, 'cache_config', None)
        if cache is not None:
            self.cache = cache
        elif cache_config and cache_config.enabled:
            # Create cache based on backend type
            if cache_config.backend == "memory":
                self.cache = MemoryCache(max_size_mb=cache_config.max_size_mb)
            elif cache_config.backend == "disk":
                self.cache = DiskCache(
                    cache_dir=cache_config.location,
                    max_size_mb=cache_config.max_size_mb
                )
            else:
                raise ValueError(f"Unknown cache backend: {cache_config.backend}")
        else:
            self.cache = None

        # Initialize Fire Circle evaluator if using Fire Circle config
        if isinstance(config, FireCircleConfig):
            self.fire_circle = FireCircleEvaluator(config, self._call_llm)
        else:
            self.fire_circle = None

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
        # Check recursion depth (only for non-FireCircle configs)
        max_depth = getattr(self.config, 'max_recursion_depth', None)
        if max_depth and recursion_depth >= max_depth:
            # Recursion limit reached - return neutral evaluation
            return [NeutrosophicEvaluation(
                truth=0.5,
                indeterminacy=0.5,
                falsehood=0.0,
                reasoning="Recursion limit reached",
                model="system"
            )]

        # Handle Fire Circle mode first (different config type)
        if isinstance(self.config, FireCircleConfig):
            fire_circle_result = await self.fire_circle.evaluate(
                layer_content, context, evaluation_prompt, session_memory=None
            )
            # Return just evaluations for compatibility with current API
            # TODO: Return full FireCircleResult when EvaluationResult wrapper implemented
            return fire_circle_result.evaluations

        # Handle standard evaluation modes
        elif self.config.mode == EvaluationMode.SINGLE:
            result = await self._evaluate_single(
                layer_content, context, evaluation_prompt
            )
            return [result]

        elif self.config.mode == EvaluationMode.PARALLEL:
            return await self._evaluate_parallel(
                layer_content, context, evaluation_prompt
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
            response, reasoning_trace = await self._call_llm(model, messages)
            result = self._parse_neutrosophic_response(response, model)
            result.reasoning_trace = reasoning_trace  # Preserve internal reasoning
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
                tasks.append(self._call_llm(model, messages))
                task_models.append(model)

        # Execute uncached evaluations in parallel
        if tasks:
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for failures first - fail fast
            failures = []
            for model, response_tuple in zip(task_models, responses):
                if isinstance(response_tuple, Exception):
                    failures.append(f"{model}: {str(response_tuple)}")

            if failures:
                raise EvaluationError(
                    f"Parallel evaluation failed for {len(failures)} model(s): " + "; ".join(failures),
                    model="parallel"
                )

            # All succeeded - parse and cache results
            for model, response_tuple in zip(task_models, responses):
                response, reasoning_trace = response_tuple
                evaluation = self._parse_neutrosophic_response(response, model)
                evaluation.reasoning_trace = reasoning_trace  # Preserve internal reasoning
                # Cache successful evaluation
                self._set_cached(layer_content, context, evaluation_prompt, model, evaluation)
                evaluations.append(evaluation)

        return evaluations


    async def _call_llm(
        self,
        model: str,
        messages: List[Dict[str, str]]
    ) -> Tuple[str, Optional[str]]:
        """
        Make API call to LLM provider.

        Returns:
            Tuple of (content, reasoning_trace)
            - content: The model's response
            - reasoning_trace: Optional internal reasoning (e.g., DeepSeek <think> blocks)
        """
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Content-Type": "application/json"}

                # Add auth header for OpenRouter
                if self.config.provider == "openrouter":
                    headers["Authorization"] = f"Bearer {self.config.api_key}"

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
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
                content = data["choices"][0]["message"]["content"]

                # Extract reasoning trace if present (DeepSeek R1 models)
                reasoning_trace = None
                if "<think>" in content:
                    import re
                    think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL)
                    if think_match:
                        reasoning_trace = think_match.group(1).strip()
                        # Remove think block from content
                        content = re.sub(r'<think>.*?</think>\s*', '', content, flags=re.DOTALL)

                return content, reasoning_trace

            except Exception as e:
                raise RuntimeError(f"LLM API call failed for {model} (provider: {self.config.provider}): {e}")

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


    def _parse_neutrosophic_response(
        self,
        response: str,
        model: str
    ) -> NeutrosophicEvaluation:
        """
        Parse LLM response into neutrosophic evaluation.

        Expects JSON format with truth, indeterminacy, falsehood, reasoning.

        Raises:
            EvaluationError: If response cannot be parsed or is missing required fields
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

            # Validate required fields exist
            if "truth" not in data:
                raise EvaluationError(
                    f"Model {model} response missing required field 'truth'. Response: {response[:200]}",
                    model=model
                )
            if "indeterminacy" not in data:
                raise EvaluationError(
                    f"Model {model} response missing required field 'indeterminacy'. Response: {response[:200]}",
                    model=model
                )
            if "falsehood" not in data:
                raise EvaluationError(
                    f"Model {model} response missing required field 'falsehood'. Response: {response[:200]}",
                    model=model
                )

            return NeutrosophicEvaluation(
                truth=float(data["truth"]),
                indeterminacy=float(data["indeterminacy"]),
                falsehood=float(data["falsehood"]),
                reasoning=data.get("reasoning", "No reasoning provided"),
                model=model
            )
        except EvaluationError:
            # Re-raise our own errors
            raise
        except Exception as e:
            # CAPTURE ERROR STATE instead of crashing
            # Tony's design principle: "Fail fast is the principle that we stop when
            # we don't know how to handle an error. In this case we could capture the
            # output and note that the operation was unsuccessful. If we cannot extract
            # JSON, we leave the raw data and note there is no JSON data - that's honest,
            # and it wouldn't block forward progress."
            return NeutrosophicEvaluation(
                truth=0.5,
                indeterminacy=1.0,  # Maximum uncertainty
                falsehood=0.5,
                reasoning=f"[PARSE_ERROR: {str(e)[:100]}]",
                model=model,
                reasoning_trace=response[:500]  # Store raw response for review
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