#!/usr/bin/env python3
"""Verify the imported data in ArangoDB."""

import os
from arango import ArangoClient

# Database configuration
DB_HOST = "192.168.111.125"
DB_PORT = 8529
DB_NAME = "PromptGuard"
COLLECTION_NAME = "attacks"
USERNAME = "pgtest"
PASSWORD = os.environ.get("ARANGODB_PROMPTGUARD_PASSWORD")


def main():
    """Verify imported data."""
    client = ArangoClient(hosts=f"http://{DB_HOST}:{DB_PORT}")
    db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)

    print("=" * 80)
    print("Dataset Import Verification")
    print("=" * 80)

    # Count by dataset_source
    print("\nCounts by dataset_source:")
    print("-" * 80)

    query = """
    FOR doc IN attacks
        COLLECT source = doc.dataset_source WITH COUNT INTO count
        SORT count DESC
        RETURN {source: source, count: count}
    """

    cursor = db.aql.execute(query)
    for result in cursor:
        print(f"  {result['source']:30s} {result['count']:5d} documents")

    # Count by ground_truth
    print("\nCounts by ground_truth label:")
    print("-" * 80)

    query = """
    FOR doc IN attacks
        COLLECT label = doc.ground_truth WITH COUNT INTO count
        SORT count DESC
        RETURN {label: label, count: count}
    """

    cursor = db.aql.execute(query)
    for result in cursor:
        print(f"  {result['label']:30s} {result['count']:5d} documents")

    # Sample records from each dataset
    print("\nSample records from each dataset:")
    print("-" * 80)

    datasets = [
        "encoding_attacks_external",
        "benign_malicious",
        "or_bench",
        "extractive_prompts",
        "history_injection"
    ]

    for dataset in datasets:
        print(f"\n{dataset}:")

        query = """
        FOR doc IN attacks
            FILTER doc.dataset_source == @source
            LIMIT 1
            RETURN {
                key: doc._key,
                prompt_preview: SUBSTRING(doc.prompt_text, 0, 100),
                ground_truth: doc.ground_truth,
                technique: doc.attack_metadata.technique_category
            }
        """

        cursor = db.aql.execute(query, bind_vars={"source": dataset})
        for result in cursor:
            print(f"  Key: {result['key']}")
            print(f"  Ground truth: {result['ground_truth']}")
            print(f"  Technique: {result['technique']}")
            print(f"  Prompt preview: {result['prompt_preview']}...")

    # Encoding techniques
    print("\n\nEncoding techniques used:")
    print("-" * 80)

    query = """
    FOR doc IN attacks
        FILTER doc.encoding_technique != null
        COLLECT technique = doc.encoding_technique WITH COUNT INTO count
        SORT count DESC
        RETURN {technique: technique, count: count}
    """

    cursor = db.aql.execute(query)
    for result in cursor:
        print(f"  {result['technique']:40s} {result['count']:3d} attacks")

    print("\n" + "=" * 80)
    print("Verification complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
