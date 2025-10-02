"""
Analysis runner for evaluating prompts across multiple models.

Handles data collection, persistence, and error tracking.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import asyncio
from datetime import datetime

from ..promptguard import PromptGuard, PromptGuardConfig
from ..evaluation import EvaluationMode, EvaluationError
from ..core.ayni import ReciprocityMetrics


@dataclass
class PromptExample:
    """Single prompt to evaluate."""
    id: str  # Unique identifier
    content: Dict[str, str]  # {"prompt": "..."} or {"system": "...", "user": "..."}
    label: Optional[str] = None  # e.g., "reciprocal", "manipulative", "extractive"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptDataset:
    """Collection of prompts for analysis."""
    name: str
    description: str
    prompts: List[PromptExample]

    @classmethod
    def from_json(cls, path: Path) -> "PromptDataset":
        """Load dataset from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)

        prompts = [PromptExample(**p) for p in data['prompts']]
        return cls(
            name=data['name'],
            description=data['description'],
            prompts=prompts
        )

    def to_json(self, path: Path) -> None:
        """Save dataset to JSON file."""
        with open(path, 'w') as f:
            json.dump({
                'name': self.name,
                'description': self.description,
                'prompts': [asdict(p) for p in self.prompts]
            }, f, indent=2)


@dataclass
class EvaluationResult:
    """Result of evaluating one prompt."""
    prompt_id: str
    model: str
    success: bool
    metrics: Optional[ReciprocityMetrics] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'prompt_id': self.prompt_id,
            'model': self.model,
            'success': self.success,
            'timestamp': self.timestamp,
        }

        if self.metrics:
            result['metrics'] = {
                'ayni_balance': self.metrics.ayni_balance,
                'exchange_type': self.metrics.exchange_type.value,
                'tension_productive': self.metrics.tension_productive,
                'needs_adjustment': self.metrics.needs_adjustment,
                'trust_field': {
                    'strength': self.metrics.trust_field.strength,
                    'violations': self.metrics.trust_field.violations,
                }
            }

        if self.error:
            result['error'] = self.error

        return result


class AnalysisRunner:
    """
    Runs prompt evaluation across multiple models and collects results.

    Handles:
    - Parallel model evaluation
    - Error tracking (which models failed on which prompts)
    - Results persistence
    - Progress reporting
    """

    def __init__(
        self,
        models: List[str],
        output_dir: Path,
        config: Optional[PromptGuardConfig] = None
    ):
        """
        Initialize analysis runner.

        Args:
            models: List of model identifiers to evaluate
            output_dir: Directory to save results
            config: Optional PromptGuard configuration (base config)
        """
        self.models = models
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Store base config for creating per-model guards
        self.base_config = config or PromptGuardConfig()
        self.results: List[EvaluationResult] = []

    async def evaluate_prompt(
        self,
        prompt: PromptExample
    ) -> List[EvaluationResult]:
        """
        Evaluate single prompt across all models.

        Returns one EvaluationResult per model.
        Tracks failures per-model rather than aborting entire evaluation.
        """
        results = []

        # Evaluate each model individually to get per-model metrics
        for model in self.models:
            # Create single-model guard
            config = PromptGuardConfig(
                mode=EvaluationMode.SINGLE,
                models=[model],
                api_key=self.base_config.api_key,
                cache_config=self.base_config.cache_config if hasattr(self.base_config, 'cache_config') else None
            )
            guard = PromptGuard(config)

            try:
                metrics = await guard.evaluate(**prompt.content)

                results.append(EvaluationResult(
                    prompt_id=prompt.id,
                    model=model,
                    success=True,
                    metrics=metrics
                ))

            except EvaluationError as e:
                # Record failure for this specific model
                results.append(EvaluationResult(
                    prompt_id=prompt.id,
                    model=model,
                    success=False,
                    error=str(e)
                ))

        return results

    async def run_analysis(
        self,
        dataset: PromptDataset,
        save_incremental: bool = True
    ) -> List[EvaluationResult]:
        """
        Run analysis on entire dataset.

        Args:
            dataset: Collection of prompts to evaluate
            save_incremental: Save results after each prompt

        Returns:
            List of all evaluation results
        """
        all_results = []

        for i, prompt in enumerate(dataset.prompts, 1):
            print(f"Evaluating prompt {i}/{len(dataset.prompts)}: {prompt.id}")

            results = await self.evaluate_prompt(prompt)
            all_results.extend(results)

            if save_incremental:
                self._save_results(all_results, dataset.name)

        # Final save
        self._save_results(all_results, dataset.name)

        return all_results

    def _save_results(self, results: List[EvaluationResult], dataset_name: str) -> None:
        """Save results to JSON file."""
        output_file = self.output_dir / f"{dataset_name}_results.json"

        with open(output_file, 'w') as f:
            json.dump(
                {
                    'dataset': dataset_name,
                    'models': self.models,
                    'results': [r.to_dict() for r in results]
                },
                f,
                indent=2
            )
