#!/usr/bin/env python3
"""
Download and format labeled prompt datasets for PromptGuard validation testing.
"""

import json
import random
from datasets import load_dataset
from pathlib import Path
from collections import Counter

# Set random seed for reproducibility
random.seed(42)

def download_benign_malicious():
    """Download and format the benign-malicious-prompt-classification dataset."""
    print("Downloading benign-malicious-prompt-classification dataset...")

    try:
        dataset = load_dataset("guychuk/benign-malicious-prompt-classification")

        # Process the dataset
        prompts = []
        train_data = dataset['train']

        # Take a representative sample (500 prompts to avoid overwhelming dataset)
        indices = random.sample(range(len(train_data)), min(500, len(train_data)))

        for idx in indices:
            item = train_data[idx]

            # Map their labels to our categories
            # Their label: 0 = benign, 1 = malicious
            # We'll map: benign -> reciprocal, malicious -> manipulative
            label_map = {
                0: "reciprocal",  # benign prompts are reciprocal interactions
                1: "manipulative"  # malicious prompts are manipulative
            }

            prompt_entry = {
                "id": f"benign_malicious_{idx:04d}",
                "content": {
                    "prompt": item['prompt']
                },
                "label": label_map[item['label']],
                "source": "guychuk/benign-malicious-prompt-classification",
                "original_label": "benign" if item['label'] == 0 else "malicious"
            }
            prompts.append(prompt_entry)

        # Create dataset object
        dataset_obj = {
            "name": "benign_malicious_classification",
            "description": "Sample from guychuk/benign-malicious-prompt-classification dataset mapping benign/malicious to reciprocal/manipulative",
            "source": "https://huggingface.co/datasets/guychuk/benign-malicious-prompt-classification",
            "license": "Check HuggingFace dataset page",
            "total_prompts": len(prompts),
            "label_mapping": {
                "benign (0)": "reciprocal",
                "malicious (1)": "manipulative"
            },
            "notes": "Benign prompts are straightforward queries. Malicious prompts include jailbreak attempts and prompt injection.",
            "prompts": prompts
        }

        # Count labels
        label_counts = {}
        for p in prompts:
            label = p['label']
            label_counts[label] = label_counts.get(label, 0) + 1

        print(f"Downloaded {len(prompts)} prompts")
        print(f"Label distribution: {label_counts}")

        return dataset_obj

    except Exception as e:
        print(f"Error downloading benign-malicious dataset: {e}")
        import traceback
        traceback.print_exc()
        return None

def download_or_bench():
    """
    Download OR-Bench dataset (80k prompts).
    Sample 100 prompts across different categories.
    """
    print("Downloading OR-Bench dataset...")

    try:
        # Load the 80k config
        dataset = load_dataset("bench-llms/or-bench", "or-bench-80k")

        prompts = []
        train_data = dataset['train']

        # Get category distribution
        categories = [item['category'] for item in train_data]
        category_counts = Counter(categories)
        print(f"Total prompts in OR-Bench: {len(train_data)}")
        print(f"Categories: {dict(category_counts)}")

        # Sample proportionally from each category (total 100 prompts)
        sample_size = 100
        samples_per_category = {}

        # Calculate proportional samples per category
        for category, count in category_counts.items():
            proportion = count / len(train_data)
            samples = max(1, int(proportion * sample_size))  # At least 1 sample per category
            samples_per_category[category] = samples

        # Adjust to exactly 100 samples
        total_samples = sum(samples_per_category.values())
        if total_samples < sample_size:
            # Add remaining to largest category
            largest_category = max(category_counts.items(), key=lambda x: x[1])[0]
            samples_per_category[largest_category] += (sample_size - total_samples)

        # Collect samples from each category
        category_indices = {cat: [] for cat in category_counts.keys()}
        for idx, item in enumerate(train_data):
            category_indices[item['category']].append(idx)

        # Sample from each category
        for category, sample_count in samples_per_category.items():
            available_indices = category_indices[category]
            selected_indices = random.sample(available_indices, min(sample_count, len(available_indices)))

            for idx in selected_indices:
                item = train_data[idx]

                # Map OR-Bench categories to our labels
                # OR-Bench categories are all potentially harmful/toxic
                # We'll map them as follows:
                # - Most harmful categories -> manipulative
                # - Borderline/deceptive -> borderline
                # - We don't have truly "reciprocal" examples in OR-Bench
                category_map = {
                    "deception": "borderline",     # Deceptive but not directly harmful
                    "harassment": "manipulative",  # Clearly manipulative
                    "harmful": "manipulative",     # General harmful content
                    "hate": "manipulative",        # Hateful content
                    "illegal": "manipulative",     # Illegal activities
                    "privacy": "extractive",       # Privacy violations (extractive)
                    "self-harm": "manipulative",   # Self-harm content
                    "sexual": "manipulative",      # Sexual content
                    "unethical": "borderline",     # Unethical but may be borderline
                    "violence": "manipulative",    # Violent content
                }

                label = category_map.get(item['category'], "borderline")

                prompt_entry = {
                    "id": f"or_bench_{idx:05d}",
                    "content": {
                        "prompt": item['prompt']
                    },
                    "label": label,
                    "source": "OR-Bench (bench-llms/or-bench)",
                    "original_category": item['category']
                }
                prompts.append(prompt_entry)

        # Create dataset object
        dataset_obj = {
            "name": "or_bench_sample",
            "description": "Sample of 100 prompts from OR-Bench (Over-Refusal Benchmark) representing various categories of potentially harmful prompts",
            "source": "https://arxiv.org/html/2405.20947v5",
            "huggingface": "https://huggingface.co/datasets/bench-llms/or-bench",
            "license": "Check original paper and dataset page",
            "total_prompts": len(prompts),
            "label_mapping": {
                "deception": "borderline",
                "harassment": "manipulative",
                "harmful": "manipulative",
                "hate": "manipulative",
                "illegal": "manipulative",
                "privacy": "extractive",
                "self-harm": "manipulative",
                "sexual": "manipulative",
                "unethical": "borderline",
                "violence": "manipulative"
            },
            "notes": "OR-Bench contains prompts designed to test over-refusal in LLMs. All prompts are potentially sensitive/harmful. Categories represent different types of concerning content.",
            "prompts": prompts
        }

        # Count labels
        label_counts = {}
        original_category_counts = {}
        for p in prompts:
            label = p['label']
            label_counts[label] = label_counts.get(label, 0) + 1
            orig_cat = p['original_category']
            original_category_counts[orig_cat] = original_category_counts.get(orig_cat, 0) + 1

        print(f"Downloaded {len(prompts)} prompts from OR-Bench")
        print(f"Label distribution: {label_counts}")
        print(f"Original category distribution: {original_category_counts}")

        return dataset_obj

    except Exception as e:
        print(f"Error downloading OR-Bench: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main function to download and save all datasets."""
    output_dir = Path("/home/tony/projects/promptguard/datasets")
    output_dir.mkdir(exist_ok=True)

    results = {
        "successful": [],
        "failed": []
    }

    # Download benign-malicious dataset
    print("\n" + "="*60)
    benign_malicious = download_benign_malicious()
    if benign_malicious:
        output_file = output_dir / "benign_malicious.json"
        with open(output_file, 'w') as f:
            json.dump(benign_malicious, f, indent=2)
        print(f"Saved to {output_file}")
        results["successful"].append({
            "name": "benign_malicious",
            "file": str(output_file),
            "prompts": benign_malicious["total_prompts"],
            "labels": benign_malicious.get("label_mapping", {})
        })
    else:
        results["failed"].append("benign_malicious")

    # Download OR-Bench dataset
    print("\n" + "="*60)
    or_bench = download_or_bench()
    if or_bench:
        output_file = output_dir / "or_bench_sample.json"
        with open(output_file, 'w') as f:
            json.dump(or_bench, f, indent=2)
        print(f"Saved to {output_file}")
        results["successful"].append({
            "name": "or_bench_sample",
            "file": str(output_file),
            "prompts": or_bench["total_prompts"],
            "labels": or_bench.get("label_mapping", {})
        })
    else:
        results["failed"].append("or_bench_sample")

    # Print summary
    print("\n" + "="*60)
    print("DOWNLOAD SUMMARY")
    print("="*60)
    print(f"Successfully downloaded: {len(results['successful'])} datasets")
    for dataset in results['successful']:
        print(f"  - {dataset['name']}: {dataset['prompts']} prompts")

    if results['failed']:
        print(f"\nFailed to download: {len(results['failed'])} datasets")
        for name in results['failed']:
            print(f"  - {name}")

    return results

if __name__ == "__main__":
    main()
