"""
Stratified sampler for Fire Circle validation experiment.

Samples 50 prompts across 5 attack strata:
- easy_reciprocal (5): Clear benign prompts
- easy_extractive (5): Clear extraction attacks
- encoding_attacks (15): Obfuscation via encoding
- semantic_manipulation (15): Jailbreaks, role reversal, polite extraction
- multi_layer (5): History injection attacks
- borderline (5): Ambiguous cases

Dataset sources:
- benign_malicious.json: 500 prompts (reciprocal/manipulative)
- extractive_prompts_dataset.json: 80 prompts (extractive attacks)
- encoding_attacks_external_n72.jsonl: 72 prompts (encoding obfuscation)
- history_injection_attacks.json: 10 prompts (multi-layer attacks)
- or_bench_sample.json: 100 prompts (95 reciprocal, 5 borderline)
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class StratifiedPrompt:
    """A prompt with stratum metadata."""
    id: str
    content: Dict[str, Any]  # Prompt content (may have user_layer, system_layer, or just prompt)
    label: str  # Expected classification
    stratum: str  # Attack type category
    source: str  # Dataset source


class StratifiedSampler:
    """Samples prompts across attack type strata."""

    def __init__(self, datasets_dir: Path):
        self.datasets_dir = Path(datasets_dir)

    def load_datasets(self) -> Dict[str, Any]:
        """Load all required datasets."""
        # Load benign_malicious
        with open(self.datasets_dir / "benign_malicious.json") as f:
            benign_malicious = json.load(f)

        # Load extractive
        with open(self.datasets_dir / "extractive_prompts_dataset.json") as f:
            extractive = json.load(f)

        # Load encoding attacks (JSONL format)
        encoding_attacks = []
        with open(self.datasets_dir / "encoding_attacks_external_n72.jsonl") as f:
            for line in f:
                encoding_attacks.append(json.loads(line))

        # Load history injection
        with open(self.datasets_dir / "history_injection_attacks.json") as f:
            history_injection = json.load(f)

        # Load OR-Bench
        with open(self.datasets_dir / "or_bench_sample.json") as f:
            or_bench = json.load(f)

        return {
            "benign_malicious": benign_malicious,
            "extractive": extractive,
            "encoding_attacks": encoding_attacks,
            "history_injection": history_injection,
            "or_bench": or_bench
        }

    def sample_stratum(
        self,
        stratum: str,
        target_count: int,
        datasets: Dict[str, Any],
        seed: int = 42
    ) -> List[StratifiedPrompt]:
        """Sample prompts for a specific stratum."""
        random.seed(seed + hash(stratum))  # Different seed per stratum

        if stratum == "easy_reciprocal":
            # Sample clear benign prompts from benign_malicious
            candidates = [
                p for p in datasets["benign_malicious"]["prompts"]
                if p["label"] == "reciprocal"
            ]
            # Prefer shorter prompts (easier baselines)
            candidates = sorted(candidates, key=lambda x: len(x["content"]["prompt"]))[:100]
            samples = random.sample(candidates, target_count)

            return [
                StratifiedPrompt(
                    id=p["id"],
                    content={"user": p["content"]["prompt"]},
                    label="reciprocal",
                    stratum=stratum,
                    source=p["source"]
                )
                for p in samples
            ]

        elif stratum == "easy_extractive":
            # Sample clear extraction attacks
            candidates = datasets["extractive"]["prompts"]
            # Prefer simple extraction prompts (no multi-turn)
            simple_extractions = [
                p for p in candidates
                if "multi" not in p.get("metadata", {}).get("attack_type", "").lower()
            ][:50]
            samples = random.sample(simple_extractions, min(target_count, len(simple_extractions)))

            return [
                StratifiedPrompt(
                    id=p["id"],
                    content={"user": p["content"]["prompt"]},
                    label="extractive",
                    stratum=stratum,
                    source=p["source"]
                )
                for p in samples
            ]

        elif stratum == "encoding_attacks":
            # All encoding attacks
            samples = random.sample(datasets["encoding_attacks"], target_count)

            return [
                StratifiedPrompt(
                    id=p["prompt_id"],
                    content={"user": p["prompt_text"]},
                    label="manipulative",  # Encoding obfuscation = manipulative
                    stratum=stratum,
                    source=p["source"]
                )
                for p in samples
            ]

        elif stratum == "semantic_manipulation":
            # Sample manipulative prompts from benign_malicious
            # These are jailbreaks, role reversals, polite extractions
            candidates = [
                p for p in datasets["benign_malicious"]["prompts"]
                if p["label"] == "manipulative"
            ]
            samples = random.sample(candidates, target_count)

            return [
                StratifiedPrompt(
                    id=p["id"],
                    content={"user": p["content"]["prompt"]},
                    label="manipulative",
                    stratum=stratum,
                    source=p["source"]
                )
                for p in samples
            ]

        elif stratum == "multi_layer":
            # History injection attacks (multi-layer)
            samples = random.sample(datasets["history_injection"], min(target_count, len(datasets["history_injection"])))

            return [
                StratifiedPrompt(
                    id=p["attack_id"],
                    content={
                        "system": p["system_layer"],
                        "user": p["user_layer"]
                    },
                    label="extractive",  # History injection = extractive
                    stratum=stratum,
                    source="history_injection_attacks"
                )
                for p in samples
            ]

        elif stratum == "borderline":
            # Sample borderline cases from OR-Bench
            # These are safe prompts about sensitive topics
            candidates = datasets["or_bench"]["prompts"]
            # Prefer prompts with sensitive keywords but reciprocal intent
            samples = random.sample(candidates, target_count)

            return [
                StratifiedPrompt(
                    id=p["id"],
                    content={"user": p["content"]["prompt"]},
                    label="reciprocal",  # OR-Bench is 95% reciprocal
                    stratum=stratum,
                    source=p["source"]
                )
                for p in samples
            ]

        else:
            raise ValueError(f"Unknown stratum: {stratum}")

    def generate_stratified_sample(self, output_path: Path, seed: int = 42) -> Dict[str, Any]:
        """Generate complete stratified sample."""
        # Load datasets
        datasets = self.load_datasets()

        # Define strata distribution
        strata_config = {
            "easy_reciprocal": 5,
            "easy_extractive": 5,
            "encoding_attacks": 15,
            "semantic_manipulation": 15,
            "multi_layer": 5,
            "borderline": 5
        }

        # Sample each stratum
        all_prompts = []
        for stratum, count in strata_config.items():
            prompts = self.sample_stratum(stratum, count, datasets, seed)
            all_prompts.extend(prompts)
            print(f"Sampled {len(prompts)} prompts for {stratum}")

        # Shuffle to mix strata
        random.seed(seed)
        random.shuffle(all_prompts)

        # Convert to JSON-serializable format
        output_data = {
            "metadata": {
                "total_prompts": len(all_prompts),
                "strata_distribution": strata_config,
                "seed": seed,
                "purpose": "Fire Circle validation experiment"
            },
            "prompts": [
                {
                    "id": p.id,
                    "content": p.content,
                    "expected_label": p.label,
                    "stratum": p.stratum,
                    "source": p.source
                }
                for p in all_prompts
            ]
        }

        # Validate distribution
        strata_counts = {}
        for p in all_prompts:
            strata_counts[p.stratum] = strata_counts.get(p.stratum, 0) + 1

        print("\nValidating distribution:")
        for stratum, expected in strata_config.items():
            actual = strata_counts.get(stratum, 0)
            status = "✓" if actual == expected else "✗"
            print(f"  {status} {stratum}: {actual}/{expected}")

        # Save to file
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\nStratified sample saved to {output_path}")
        print(f"Total prompts: {len(all_prompts)}")

        return output_data


def main():
    """Generate stratified sample for Fire Circle validation."""
    import sys

    datasets_dir = Path(__file__).parent.parent.parent / "datasets"
    output_path = Path(__file__).parent / "stratified_sample.json"

    sampler = StratifiedSampler(datasets_dir)
    sampler.generate_stratified_sample(output_path, seed=42)


if __name__ == "__main__":
    main()
