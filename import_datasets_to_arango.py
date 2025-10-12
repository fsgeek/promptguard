#!/usr/bin/env python3
"""
Import PromptGuard datasets into ArangoDB.

Database: PromptGuard at 192.168.111.125:8529
Collection: attacks
"""

import os
import json
from datetime import datetime
from arango import ArangoClient

# Database configuration
DB_HOST = "192.168.111.125"
DB_PORT = 8529
DB_NAME = "PromptGuard"
COLLECTION_NAME = "attacks"
USERNAME = "pgtest"
PASSWORD = os.environ.get("ARANGODB_PROMPTGUARD_PASSWORD")

# Dataset paths
DATASETS_DIR = "/home/tony/projects/promptguard/datasets"
DATASETS = {
    "encoding_attacks_external": {
        "file": "encoding_attacks_external_n72.jsonl",
        "format": "jsonl",
        "source": "encoding_attacks_external"
    },
    "benign_malicious": {
        "file": "benign_malicious.json",
        "format": "json",
        "source": "benign_malicious"
    },
    "or_bench": {
        "file": "or_bench_sample.json",
        "format": "json",
        "source": "or_bench"
    },
    "extractive_prompts": {
        "file": "extractive_prompts_dataset.json",
        "format": "json",
        "source": "extractive_prompts"
    },
    "history_injection": {
        "file": "history_injection_attacks.json",
        "format": "json",
        "source": "history_injection"
    }
}


def connect_db():
    """Connect to ArangoDB."""
    if not PASSWORD:
        raise ValueError("ARANGODB_PROMPTGUARD_PASSWORD environment variable not set")

    client = ArangoClient(hosts=f"http://{DB_HOST}:{DB_PORT}")
    db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)
    return db


def transform_encoding_attack(record, idx):
    """Transform encoding attack record to schema."""
    return {
        "_key": record.get("prompt_id", f"external_{idx:03d}"),
        "prompt_text": record["prompt_text"],
        "encoding_technique": record.get("encoding_technique"),
        "ground_truth": record.get("expected_label", "manipulative"),
        "dataset_source": "encoding_attacks_external",
        "attack_metadata": {
            "technique_category": "encoding_obfuscation",
            "severity": "high",
            "description": f"Encoding technique: {record.get('encoding_technique', 'unknown')}"
        },
        "metadata": {
            "added_date": datetime.utcnow().isoformat(),
            "dataset_file": f"datasets/{DATASETS['encoding_attacks_external']['file']}",
            "original_source": record.get("source")
        }
    }


def transform_benign_malicious(record, idx):
    """Transform benign_malicious record to schema."""
    prompt_text = record["content"]["prompt"]
    return {
        "_key": record["id"],
        "prompt_text": prompt_text,
        "encoding_technique": None,
        "ground_truth": record["label"],
        "dataset_source": "benign_malicious",
        "attack_metadata": {
            "technique_category": "jailbreak" if record["label"] == "manipulative" else None,
            "severity": "medium" if record["label"] == "manipulative" else "none",
            "description": f"Original label: {record.get('original_label')}"
        },
        "metadata": {
            "added_date": datetime.utcnow().isoformat(),
            "dataset_file": f"datasets/{DATASETS['benign_malicious']['file']}",
            "original_source": record.get("source")
        }
    }


def transform_or_bench(record, idx):
    """Transform or_bench record to schema."""
    prompt_text = record["content"]["prompt"]
    return {
        "_key": record["id"],
        "prompt_text": prompt_text,
        "encoding_technique": None,
        "ground_truth": record["label"],
        "dataset_source": "or_bench",
        "attack_metadata": {
            "technique_category": None,
            "severity": "low" if record["label"] == "reciprocal" else "medium",
            "description": f"Original category: {record.get('original_category')}"
        },
        "metadata": {
            "added_date": datetime.utcnow().isoformat(),
            "dataset_file": f"datasets/{DATASETS['or_bench']['file']}",
            "original_source": record.get("source")
        }
    }


def transform_extractive_prompts(record, idx):
    """Transform extractive_prompts record to schema."""
    # Combine user prompt and system prompt
    user_prompt = record["content"].get("prompt", "")
    system_prompt = record["content"].get("system", "")

    if system_prompt:
        prompt_text = f"[SYSTEM]: {system_prompt}\n\n[USER]: {user_prompt}"
    else:
        prompt_text = user_prompt

    return {
        "_key": record["id"],
        "prompt_text": prompt_text,
        "encoding_technique": None,
        "ground_truth": record["label"],
        "dataset_source": "extractive_prompts",
        "attack_metadata": {
            "technique_category": "prompt_injection",
            "severity": "critical",
            "description": f"Technique: {record.get('metadata', {}).get('technique', 'unknown')}"
        },
        "metadata": {
            "added_date": datetime.utcnow().isoformat(),
            "dataset_file": f"datasets/{DATASETS['extractive_prompts']['file']}",
            "original_source": record.get("source"),
            "attack_type": record.get("metadata", {}).get("attack_type")
        }
    }


def transform_history_injection(record, idx):
    """Transform history_injection record to schema."""
    # Combine system and user layers
    system_layer = record.get("system_layer", "")
    user_layer = record.get("user_layer", "")

    prompt_text = f"[SYSTEM]: {system_layer}\n\n[USER]: {user_layer}"

    return {
        "_key": record["attack_id"],
        "prompt_text": prompt_text,
        "encoding_technique": None,
        "ground_truth": "extractive",  # All history injection attacks are extractive
        "dataset_source": "history_injection",
        "attack_metadata": {
            "technique_category": "history_fabrication",
            "severity": "critical",
            "description": record.get("description", ""),
            "attack_type": record.get("attack_type")
        },
        "metadata": {
            "added_date": datetime.utcnow().isoformat(),
            "dataset_file": f"datasets/{DATASETS['history_injection']['file']}",
            "scenario": record.get("scenario"),
            "expected_detection": record.get("expected_detection")
        }
    }


def import_dataset(db, dataset_name, dataset_info):
    """Import a single dataset."""
    file_path = os.path.join(DATASETS_DIR, dataset_info["file"])

    print(f"\nImporting {dataset_name} from {dataset_info['file']}...")

    # Read dataset
    records = []
    if dataset_info["format"] == "jsonl":
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
    else:  # json
        with open(file_path, 'r') as f:
            data = json.load(f)
            if "prompts" in data:
                records = data["prompts"]
            else:
                records = data  # Assume it's a list

    print(f"  Read {len(records)} records")

    # Transform records
    transformer = {
        "encoding_attacks_external": transform_encoding_attack,
        "benign_malicious": transform_benign_malicious,
        "or_bench": transform_or_bench,
        "extractive_prompts": transform_extractive_prompts,
        "history_injection": transform_history_injection
    }[dataset_info["source"]]

    documents = [transformer(rec, idx) for idx, rec in enumerate(records)]

    # Insert into database
    collection = db.collection(COLLECTION_NAME)

    inserted = 0
    errors = 0

    for doc in documents:
        try:
            collection.insert(doc, overwrite=True)  # Overwrite if key exists
            inserted += 1
        except Exception as e:
            print(f"  ERROR inserting {doc.get('_key')}: {e}")
            errors += 1

    print(f"  Inserted: {inserted}, Errors: {errors}")
    return inserted, errors


def main():
    """Main import function."""
    print("=" * 60)
    print("PromptGuard Dataset Import to ArangoDB")
    print("=" * 60)

    # Connect to database
    try:
        db = connect_db()
        print(f"✓ Connected to {DB_NAME} at {DB_HOST}:{DB_PORT}")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return

    # Verify collection exists
    if not db.has_collection(COLLECTION_NAME):
        print(f"✗ Collection '{COLLECTION_NAME}' does not exist!")
        return

    print(f"✓ Collection '{COLLECTION_NAME}' found")

    # Import each dataset
    total_inserted = 0
    total_errors = 0

    for dataset_name, dataset_info in DATASETS.items():
        try:
            inserted, errors = import_dataset(db, dataset_name, dataset_info)
            total_inserted += inserted
            total_errors += errors
        except Exception as e:
            print(f"✗ Failed to import {dataset_name}: {e}")
            total_errors += 1

    # Summary
    print("\n" + "=" * 60)
    print("Import Summary")
    print("=" * 60)
    print(f"Total inserted: {total_inserted}")
    print(f"Total errors: {total_errors}")

    # Get final collection count
    collection = db.collection(COLLECTION_NAME)
    count = collection.count()
    print(f"Collection '{COLLECTION_NAME}' now has {count} documents")
    print("=" * 60)


if __name__ == "__main__":
    main()
