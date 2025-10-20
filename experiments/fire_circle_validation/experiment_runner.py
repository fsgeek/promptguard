"""
Experiment runner for Fire Circle validation.

Executes evaluations on stratified sample with:
- Checkpoint/resume logic (every 10 prompts)
- Per-model result preservation
- REASONINGBANK enable/disable
- ArangoDB storage for Fire Circle deliberations
- Cost tracking
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from promptguard.evaluation.evaluator import (
    LLMEvaluator,
    EvaluationConfig,
    EvaluationMode,
    NeutrosophicEvaluation
)
from promptguard.evaluation.fire_circle import (
    FireCircleEvaluator,
    FireCircleConfig,
    FireCircleResult,
    CircleSize,
    FailureMode
)
from promptguard.evaluation.prompts import NeutrosophicEvaluationPrompt
from promptguard.storage.arango_backend import ArangoDBBackend
from reasoningbank.retriever import ReasoningBankRetriever


@dataclass
class ExperimentConfig:
    """Configuration for a single experimental condition."""
    condition_name: str  # e.g., "baseline_single"
    mode: str  # "SINGLE", "PARALLEL", "FIRE_CIRCLE"
    models: List[str]
    reasoningbank_enabled: bool
    provider: str = "openrouter"
    max_tokens: int = 1000
    timeout_seconds: float = 60.0
    temperature: float = 0.7

    # Fire Circle specific
    circle_size: Optional[str] = None  # "SMALL", "MEDIUM", "LARGE"
    max_rounds: int = 3
    failure_mode: str = "STRICT"
    enable_storage: bool = False  # Enable ArangoDB storage for Fire Circle


@dataclass
class PromptResult:
    """Result for a single prompt evaluation."""
    prompt_id: str
    stratum: str
    expected_label: str
    evaluations: List[Dict[str, Any]]  # Per-model evaluations
    consensus: Optional[Dict[str, Any]] = None  # Only for PARALLEL/FIRE_CIRCLE
    fire_circle_metadata: Optional[Dict[str, Any]] = None  # Fire Circle specific
    duration_seconds: float = 0.0
    error: Optional[str] = None


class ExperimentRunner:
    """Runs Fire Circle validation experiments with checkpointing."""

    def __init__(
        self,
        config: ExperimentConfig,
        stratified_sample_path: Path,
        output_dir: Path
    ):
        self.config = config
        self.stratified_sample_path = Path(stratified_sample_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load stratified sample
        with open(self.stratified_sample_path) as f:
            self.sample_data = json.load(f)

        # Initialize evaluator based on mode
        self.evaluator = self._create_evaluator()

        # Results tracking
        self.results: List[PromptResult] = []
        self.checkpoint_interval = 10

    def _create_evaluator(self):
        """Create appropriate evaluator based on config."""
        if self.config.mode == "FIRE_CIRCLE":
            # Fire Circle config
            fc_config = FireCircleConfig(
                models=self.config.models,
                circle_size=CircleSize[self.config.circle_size] if self.config.circle_size else CircleSize.SMALL,
                max_rounds=self.config.max_rounds,
                provider=self.config.provider,
                failure_mode=FailureMode.STRICT if self.config.failure_mode == "STRICT" else FailureMode.RESILIENT,
                max_tokens=self.config.max_tokens,
                timeout_seconds=self.config.timeout_seconds,
                temperature=self.config.temperature,
                enable_storage=self.config.enable_storage,
                storage_backend=ArangoDBBackend() if self.config.enable_storage else None
            )

            evaluator = FireCircleEvaluator(fc_config)

        else:
            # Standard LLM evaluator config
            eval_mode = EvaluationMode[self.config.mode]
            eval_config = EvaluationConfig(
                mode=eval_mode,
                models=self.config.models,
                max_tokens=self.config.max_tokens,
                timeout_seconds=self.config.timeout_seconds,
                temperature=self.config.temperature,
                provider=self.config.provider
            )

            evaluator = LLMEvaluator(eval_config)

        # Configure REASONINGBANK
        if self.config.reasoningbank_enabled:
            evaluator.retriever = ReasoningBankRetriever()
        else:
            evaluator.retriever = None

        return evaluator

    async def evaluate_prompt(self, prompt_data: Dict[str, Any]) -> PromptResult:
        """Evaluate a single prompt."""
        prompt_id = prompt_data["id"]
        stratum = prompt_data["stratum"]
        expected_label = prompt_data["expected_label"]
        content = prompt_data["content"]

        # Build layer_content and context based on prompt structure
        if "system" in content and "user" in content:
            # Multi-layer prompt
            layer_content = content["user"]
            context = f"System: {content['system']}\n\nUser: {content['user']}"
        else:
            # Single-layer prompt
            layer_content = content.get("user", content.get("prompt", ""))
            context = layer_content

        # Use ayni_relational evaluation prompt
        evaluation_prompt = NeutrosophicEvaluationPrompt.ayni_relational()

        start_time = time.time()
        error = None
        evaluations = []
        consensus = None
        fire_circle_metadata = None

        try:
            # Fire Circle mode
            if isinstance(self.evaluator, FireCircleEvaluator):
                fire_circle_result: FireCircleResult = await self.evaluator.evaluate(
                    layer_content=layer_content,
                    context=context,
                    evaluation_prompt=evaluation_prompt,
                    session_memory=None
                )

                # Extract evaluations
                evaluations = [
                    {
                        "model": e.model,
                        "T": e.truth,
                        "I": e.indeterminacy,
                        "F": e.falsehood,
                        "reasoning": e.reasoning,
                        "transparency_note": e.transparency_note
                    }
                    for e in fire_circle_result.evaluations
                ]

                # Extract consensus
                consensus = {
                    "T": fire_circle_result.consensus.truth,
                    "I": fire_circle_result.consensus.indeterminacy,
                    "F": fire_circle_result.consensus.falsehood,
                    "reasoning": fire_circle_result.consensus.reasoning,
                    "model": fire_circle_result.consensus.model
                }

                # Fire Circle metadata
                fire_circle_metadata = {
                    "patterns": [
                        {
                            "type": p.pattern_type,
                            "observed_by": p.first_observed_by,
                            "agreement": p.agreement_score,
                            "round": p.round_discovered
                        }
                        for p in fire_circle_result.patterns
                    ],
                    "empty_chair_influence": fire_circle_result.empty_chair_influence,
                    "dialogue_rounds": len(fire_circle_result.dialogue_history),
                    "fire_circle_id": fire_circle_result.metadata.get("fire_circle_id")
                }

            # Standard LLM evaluation (SINGLE or PARALLEL)
            else:
                eval_results: List[NeutrosophicEvaluation] = await self.evaluator.evaluate_layer(
                    layer_content=layer_content,
                    context=context,
                    evaluation_prompt=evaluation_prompt
                )

                # Extract evaluations
                evaluations = [
                    {
                        "model": e.model,
                        "T": e.truth,
                        "I": e.indeterminacy,
                        "F": e.falsehood,
                        "reasoning": e.reasoning,
                        "transparency_note": e.transparency_note
                    }
                    for e in eval_results
                ]

                # Compute consensus for PARALLEL mode
                if self.config.mode == "PARALLEL" and len(evaluations) > 0:
                    # Max(F) consensus
                    max_f_eval = max(evaluations, key=lambda x: x["F"])
                    consensus = max_f_eval

        except Exception as e:
            error = str(e)
            print(f"Error evaluating {prompt_id}: {error}")

        duration = time.time() - start_time

        return PromptResult(
            prompt_id=prompt_id,
            stratum=stratum,
            expected_label=expected_label,
            evaluations=evaluations,
            consensus=consensus,
            fire_circle_metadata=fire_circle_metadata,
            duration_seconds=duration,
            error=error
        )

    def _load_checkpoint(self) -> Optional[List[PromptResult]]:
        """Load checkpoint if exists."""
        checkpoint_path = self.output_dir / f"{self.config.condition_name}_checkpoint.json"

        if not checkpoint_path.exists():
            return None

        try:
            with open(checkpoint_path) as f:
                data = json.load(f)
                # Convert dicts back to PromptResult objects
                return [
                    PromptResult(**result_data)
                    for result_data in data["results"]
                ]
        except Exception as e:
            print(f"Warning: Failed to load checkpoint: {e}")
            return None

    def _save_checkpoint(self):
        """Save checkpoint."""
        checkpoint_path = self.output_dir / f"{self.config.condition_name}_checkpoint.json"

        checkpoint_data = {
            "condition": self.config.condition_name,
            "completed_prompts": len(self.results),
            "total_prompts": len(self.sample_data["prompts"]),
            "results": [asdict(r) for r in self.results]
        }

        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

        print(f"Checkpoint saved: {len(self.results)}/{len(self.sample_data['prompts'])} prompts")

    def _save_final_results(self):
        """Save final results."""
        results_path = self.output_dir / f"{self.config.condition_name}_results.json"

        # Aggregate statistics
        total_prompts = len(self.results)
        successful = len([r for r in self.results if r.error is None])
        failed = total_prompts - successful
        total_duration = sum(r.duration_seconds for r in self.results)

        # Stratum breakdown
        stratum_stats = {}
        for result in self.results:
            if result.stratum not in stratum_stats:
                stratum_stats[result.stratum] = {"total": 0, "successful": 0, "failed": 0}
            stratum_stats[result.stratum]["total"] += 1
            if result.error is None:
                stratum_stats[result.stratum]["successful"] += 1
            else:
                stratum_stats[result.stratum]["failed"] += 1

        final_data = {
            "metadata": {
                "condition": self.config.condition_name,
                "mode": self.config.mode,
                "models": self.config.models,
                "reasoningbank_enabled": self.config.reasoningbank_enabled,
                "total_prompts": total_prompts,
                "successful": successful,
                "failed": failed,
                "total_duration_seconds": total_duration,
                "average_duration_seconds": total_duration / total_prompts if total_prompts > 0 else 0,
                "stratum_breakdown": stratum_stats
            },
            "results": [asdict(r) for r in self.results]
        }

        with open(results_path, 'w') as f:
            json.dump(final_data, f, indent=2)

        print(f"\nFinal results saved to {results_path}")
        print(f"Total: {total_prompts}, Successful: {successful}, Failed: {failed}")
        print(f"Total duration: {total_duration:.2f}s, Average: {total_duration/total_prompts:.2f}s per prompt")

    async def run(self, limit: Optional[int] = None):
        """
        Run experiment on all prompts.

        Args:
            limit: Optional limit for testing (e.g., 3 prompts)
        """
        # Load checkpoint if exists
        checkpoint_results = self._load_checkpoint()
        if checkpoint_results:
            self.results = checkpoint_results
            print(f"Resuming from checkpoint: {len(self.results)} prompts already completed")

        # Get completed prompt IDs
        completed_ids = {r.prompt_id for r in self.results}

        # Filter prompts to evaluate
        prompts = self.sample_data["prompts"]
        if limit:
            prompts = prompts[:limit]

        remaining_prompts = [p for p in prompts if p["id"] not in completed_ids]

        print(f"\nStarting experiment: {self.config.condition_name}")
        print(f"Total prompts: {len(prompts)}")
        print(f"Already completed: {len(completed_ids)}")
        print(f"Remaining: {len(remaining_prompts)}")

        # Evaluate remaining prompts
        for i, prompt_data in enumerate(remaining_prompts, start=1):
            print(f"\n[{len(self.results) + 1}/{len(prompts)}] Evaluating {prompt_data['id']} ({prompt_data['stratum']})...")

            result = await self.evaluate_prompt(prompt_data)
            self.results.append(result)

            # Checkpoint every N prompts
            if len(self.results) % self.checkpoint_interval == 0:
                self._save_checkpoint()

        # Save final results
        self._save_checkpoint()  # Final checkpoint
        self._save_final_results()


async def main():
    """Run experiment from command line."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Run Fire Circle validation experiment")
    parser.add_argument("config_path", type=Path, help="Path to experiment config JSON")
    parser.add_argument("--limit", type=int, help="Limit number of prompts (for testing)")
    args = parser.parse_args()

    # Load config
    with open(args.config_path) as f:
        config_data = json.load(f)

    config = ExperimentConfig(**config_data)

    # Paths
    stratified_sample_path = Path(__file__).parent / "stratified_sample.json"
    output_dir = Path(__file__).parent.parent / "results" / "raw"

    # Run experiment
    runner = ExperimentRunner(config, stratified_sample_path, output_dir)
    await runner.run(limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
