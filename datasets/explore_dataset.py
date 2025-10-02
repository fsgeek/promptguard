#!/usr/bin/env python3
"""
Interactive dataset explorer - view random samples by label.
"""

import json
import random
from pathlib import Path

def load_dataset(filepath):
    """Load a dataset file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def show_samples(dataset, label=None, count=5):
    """Show random samples from the dataset."""
    prompts = dataset['prompts']

    if label:
        prompts = [p for p in prompts if p['label'] == label]
        print(f"\n{len(prompts)} prompts with label '{label}'")

    if not prompts:
        print(f"No prompts found with label '{label}'")
        return

    samples = random.sample(prompts, min(count, len(prompts)))

    for i, prompt in enumerate(samples, 1):
        print(f"\n{'='*60}")
        print(f"Sample {i}/{len(samples)}")
        print('='*60)
        print(f"ID: {prompt['id']}")
        print(f"Label: {prompt['label']}")
        if 'original_label' in prompt:
            print(f"Original Label: {prompt['original_label']}")
        if 'original_category' in prompt:
            print(f"Original Category: {prompt['original_category']}")
        print(f"\nPrompt:")
        print(prompt['content']['prompt'])

def main():
    """Main function."""
    datasets_dir = Path("/home/tony/projects/promptguard/datasets")

    print("Available datasets:")
    print("1. benign_malicious.json")
    print("2. or_bench_sample.json")

    # Load both datasets
    benign_malicious = load_dataset(datasets_dir / "benign_malicious.json")
    or_bench = load_dataset(datasets_dir / "or_bench_sample.json")

    # Show samples from each label
    labels = ['reciprocal', 'extractive', 'manipulative', 'borderline']

    print("\n" + "="*60)
    print("BENIGN-MALICIOUS DATASET SAMPLES")
    print("="*60)

    for label in labels:
        show_samples(benign_malicious, label, count=2)

    print("\n" + "="*60)
    print("OR-BENCH DATASET SAMPLES")
    print("="*60)

    for label in labels:
        show_samples(or_bench, label, count=2)

if __name__ == "__main__":
    main()
