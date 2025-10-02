#!/usr/bin/env python3
"""
Verify the downloaded datasets and generate summary statistics.
"""

import json
from pathlib import Path
from collections import Counter

def verify_dataset(filepath):
    """Verify a dataset file and print statistics."""
    print(f"\n{'='*60}")
    print(f"Verifying: {filepath.name}")
    print('='*60)

    with open(filepath, 'r') as f:
        data = json.load(f)

    print(f"Name: {data['name']}")
    print(f"Description: {data['description'][:100]}...")
    print(f"Total prompts: {data['total_prompts']}")

    # Count labels
    label_counts = Counter([p['label'] for p in data['prompts']])
    print(f"\nLabel distribution:")
    for label, count in sorted(label_counts.items()):
        percentage = (count / data['total_prompts']) * 100
        print(f"  {label:15s}: {count:4d} ({percentage:5.1f}%)")

    # Check for original labels/categories
    if 'original_label' in data['prompts'][0]:
        original_counts = Counter([p.get('original_label', 'unknown') for p in data['prompts']])
        print(f"\nOriginal label distribution:")
        for label, count in sorted(original_counts.items()):
            percentage = (count / data['total_prompts']) * 100
            print(f"  {label:15s}: {count:4d} ({percentage:5.1f}%)")

    if 'original_category' in data['prompts'][0]:
        original_counts = Counter([p.get('original_category', 'unknown') for p in data['prompts']])
        print(f"\nOriginal category distribution:")
        for label, count in sorted(original_counts.items()):
            percentage = (count / data['total_prompts']) * 100
            print(f"  {label:15s}: {count:4d} ({percentage:5.1f}%)")

    # Show sample prompts
    print(f"\nSample prompts:")
    for label in sorted(label_counts.keys()):
        matching = [p for p in data['prompts'] if p['label'] == label]
        if matching:
            sample = matching[0]
            prompt_text = sample['content'].get('prompt', 'N/A')
            print(f"\n  [{label}]")
            print(f"  ID: {sample['id']}")
            print(f"  Prompt: {prompt_text[:150]}...")

    # Verify format compliance
    print(f"\nFormat verification:")
    all_valid = True
    for i, prompt in enumerate(data['prompts']):
        # Check required fields
        if 'id' not in prompt:
            print(f"  ERROR: Missing 'id' in prompt {i}")
            all_valid = False
        if 'content' not in prompt:
            print(f"  ERROR: Missing 'content' in prompt {i}")
            all_valid = False
        if 'label' not in prompt:
            print(f"  ERROR: Missing 'label' in prompt {i}")
            all_valid = False
        # Check label validity
        valid_labels = {'reciprocal', 'extractive', 'manipulative', 'borderline'}
        if prompt.get('label') not in valid_labels:
            print(f"  ERROR: Invalid label '{prompt.get('label')}' in prompt {i}")
            all_valid = False

    if all_valid:
        print("  ✓ All prompts have valid format")
    else:
        print("  ✗ Format issues detected")

    return data

def main():
    """Main verification function."""
    datasets_dir = Path("/home/tony/projects/promptguard/datasets")

    datasets = {
        "benign_malicious.json": datasets_dir / "benign_malicious.json",
        "or_bench_sample.json": datasets_dir / "or_bench_sample.json"
    }

    all_data = {}
    total_prompts = 0

    for name, filepath in datasets.items():
        if filepath.exists():
            data = verify_dataset(filepath)
            all_data[name] = data
            total_prompts += data['total_prompts']
        else:
            print(f"\nERROR: {filepath} not found")

    # Overall summary
    print(f"\n{'='*60}")
    print("OVERALL SUMMARY")
    print('='*60)
    print(f"Total datasets: {len(all_data)}")
    print(f"Total prompts: {total_prompts}")

    # Combined label distribution
    all_labels = []
    for data in all_data.values():
        all_labels.extend([p['label'] for p in data['prompts']])

    label_counts = Counter(all_labels)
    print(f"\nCombined label distribution:")
    for label, count in sorted(label_counts.items()):
        percentage = (count / total_prompts) * 100
        print(f"  {label:15s}: {count:4d} ({percentage:5.1f}%)")

    print(f"\nDataset files:")
    for name, filepath in datasets.items():
        if filepath.exists():
            size_mb = filepath.stat().st_size / (1024 * 1024)
            print(f"  {name:30s}: {size_mb:6.2f} MB")

if __name__ == "__main__":
    main()
