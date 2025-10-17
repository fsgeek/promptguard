#!/usr/bin/env python3
"""
Collect target LLM responses for baseline compliance analysis.

Sends 478 calibration prompts to target models, captures complete responses,
stores encrypted in ArangoDB. Post-evaluation will classify outcomes.

Usage:
    # Test mode (10 prompts)
    python collect_target_responses.py --test

    # Full collection (478 prompts)
    python collect_target_responses.py

    # Single model run
    python collect_target_responses.py --model anthropic/claude-sonnet-4.5

    # Resume from checkpoint
    python collect_target_responses.py --resume
"""

import asyncio
import json
import time
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx

from promptguard.storage.target_response_storage import TargetResponseStorage
from promptguard.config import load_target_models, load_model_config


# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('target_response_collection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TargetResponseCollector:
    """
    Parallel worker system for collecting target LLM responses.

    Design:
    - N workers (one per target model)
    - Each processes all 478 prompts
    - Real-time persistence to ArangoDB
    - Checkpoint every 50 prompts
    """

    def __init__(
        self,
        storage: TargetResponseStorage,
        api_key: str,
        target_models: List[str],
        checkpoint_interval: int = 50
    ):
        """
        Initialize collector.

        Args:
            storage: ArangoDB storage backend
            api_key: OpenRouter API key
            target_models: List of target models to collect responses from
            checkpoint_interval: Save state every N prompts
        """
        self.storage = storage
        self.api_key = api_key
        self.target_models = target_models
        self.checkpoint_interval = checkpoint_interval
        self.base_url = "https://openrouter.ai/api/v1"

    async def collect_response(
        self,
        prompt_id: str,
        prompt_text: str,
        prompt_label: str,
        target_model: str
    ) -> Dict[str, Any]:
        """
        Send prompt to target model and collect response.

        Args:
            prompt_id: Unique prompt identifier
            prompt_text: Prompt to send
            prompt_label: Prompt classification
            target_model: Target model

        Returns:
            Response data with outcome classification
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Request parameters
            temperature = 0.7
            max_tokens = 2000

            # Build request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": target_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt_text
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # Make request
            start_time = time.time()
            error = None
            response_text = ""
            tokens = 0
            cost = 0.0

            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                response_text = data["choices"][0]["message"]["content"]

                # Extract usage info
                usage = data.get("usage", {})
                tokens = usage.get("completion_tokens", 0)

                # Estimate cost (rough)
                # TODO: Get actual cost from OpenRouter usage API
                cost = 0.001  # Placeholder

            except Exception as e:
                error = str(e)
                logger.error(f"API error for {prompt_id}/{target_model}: {e}")

            latency_ms = int((time.time() - start_time) * 1000)

            return {
                "prompt_id": prompt_id,
                "prompt_text": prompt_text,
                "prompt_label": prompt_label,
                "target_model": target_model,
                "response_text": response_text,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "tokens": tokens,
                "latency_ms": latency_ms,
                "cost_usd": cost,
                "error": error
            }

    async def process_model(
        self,
        target_model: str,
        prompts: List[Dict[str, Any]],
        resume: bool = False
    ) -> Dict[str, int]:
        """
        Process all prompts for one target model.

        Args:
            target_model: Model to evaluate
            prompts: List of prompt data
            resume: Whether to skip completed prompts

        Returns:
            Statistics (completed, failed, skipped)
        """
        stats = {
            "completed": 0,
            "failed": 0,
            "skipped": 0
        }

        # Get completed prompts for resume
        completed_ids = set()
        if resume:
            completed_ids = set(self.storage.list_completed(target_model))
            logger.info(f"{target_model}: Resuming, {len(completed_ids)} already completed")

        # Process prompts
        for i, prompt in enumerate(prompts):
            prompt_id = prompt["id"]

            # Skip if already completed
            if prompt_id in completed_ids:
                stats["skipped"] += 1
                continue

            try:
                # Collect response
                result = await self.collect_response(
                    prompt_id,
                    prompt["content"]["prompt"],
                    prompt["label"],
                    target_model
                )

                # Store in ArangoDB
                self.storage.store_response(**result)

                stats["completed"] += 1

                # Progress log every 10 prompts
                if stats["completed"] % 10 == 0:
                    total = stats["completed"] + stats["skipped"]
                    pct = (total / len(prompts)) * 100
                    logger.info(
                        f"{target_model}: {total}/{len(prompts)} ({pct:.1f}%) - "
                        f"{stats['completed']} new, {stats['skipped']} skipped"
                    )

            except Exception as e:
                logger.error(f"Failed to process {prompt_id}/{target_model}: {e}")
                stats["failed"] += 1

            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)

        # Final stats
        total = stats["completed"] + stats["skipped"]
        logger.info(
            f"{target_model}: COMPLETE - {total}/{len(prompts)} total, "
            f"{stats['completed']} new, {stats['skipped']} skipped, "
            f"{stats['failed']} failed"
        )

        return stats

    async def collect_all(
        self,
        prompts: List[Dict[str, Any]],
        resume: bool = False
    ) -> Dict[str, Any]:
        """
        Collect responses from all target models in parallel.

        Args:
            prompts: List of prompts to process
            resume: Whether to resume from checkpoint

        Returns:
            Overall statistics
        """
        logger.info(
            f"Starting collection: {len(prompts)} prompts x {len(self.target_models)} models = "
            f"{len(prompts) * len(self.target_models)} requests"
        )

        # Launch workers (one per model)
        tasks = [
            self.process_model(model, prompts, resume)
            for model in self.target_models
        ]

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        # Aggregate stats
        total_stats = {
            "completed": sum(r["completed"] for r in results),
            "failed": sum(r["failed"] for r in results),
            "skipped": sum(r["skipped"] for r in results),
            "by_model": {
                model: results[i]
                for i, model in enumerate(self.target_models)
            }
        }

        return total_stats


async def main():
    """Main collection workflow."""
    parser = argparse.ArgumentParser(description="Collect target LLM responses")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: only process first 10 prompts"
    )
    parser.add_argument(
        "--model",
        help="Single model to collect responses from (e.g., anthropic/claude-sonnet-4.5)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint (skip completed prompts)"
    )
    args = parser.parse_args()

    # Load API key
    import os
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable not set")
        return

    # Load target models from config
    if args.model:
        # Single model mode
        target_models = [args.model]
        logger.info(f"Single model mode: {args.model}")
    else:
        # All models from config
        target_models = load_target_models()
        logger.info(f"Loaded {len(target_models)} target models from config")

    # Load prompts
    dataset_path = Path("datasets/baseline_calibration.json")
    with open(dataset_path) as f:
        data = json.load(f)
        prompts = data["prompts"]

    # Test mode: limit to 10 prompts
    if args.test:
        prompts = prompts[:10]
        logger.info("TEST MODE: Processing first 10 prompts only")

    logger.info(f"Loaded {len(prompts)} prompts from {dataset_path}")

    # Initialize storage
    storage = TargetResponseStorage()
    logger.info("Connected to ArangoDB")

    # Initialize collector
    collector = TargetResponseCollector(storage, api_key, target_models)

    # Collect responses
    start_time = time.time()
    stats = await collector.collect_all(prompts, resume=args.resume)
    duration = time.time() - start_time

    # Get summary from storage
    summary = storage.get_summary_stats()

    # Log results
    logger.info("=" * 80)
    logger.info("COLLECTION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Duration: {duration/60:.1f} minutes")
    logger.info(f"Completed: {stats['completed']}")
    logger.info(f"Skipped: {stats['skipped']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Total cost: ${summary.get('total_cost', 0.0):.2f}")

    # Write summary report
    report_path = Path("target_response_summary.json")
    with open(report_path, 'w') as f:
        json.dump({
            "collection_stats": stats,
            "summary": summary,
            "duration_seconds": duration,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)

    logger.info(f"Summary report written to {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
