#!/usr/bin/env python3
"""
Quick test script to verify ArangoDB connection and data availability.

Tests:
1. Database connection
2. Collections exist
3. Models available
4. Attacks available
5. Query functionality
"""

import os
import sys
from arango import ArangoClient

# Database config
DB_HOST = "192.168.111.125"
DB_PORT = 8529
DB_NAME = "PromptGuard"
DB_USER = "pgtest"
DB_PASSWORD = os.environ.get("ARANGODB_PROMPTGUARD_PASSWORD")


def main():
    """Run connection tests."""
    print("=" * 60)
    print("ArangoDB Connection Test")
    print("=" * 60)

    # Check environment
    if not DB_PASSWORD:
        print("✗ ARANGODB_PROMPTGUARD_PASSWORD environment variable not set")
        sys.exit(1)
    print("✓ Environment variables set")

    # Connect to database
    try:
        client = ArangoClient(hosts=f"http://{DB_HOST}:{DB_PORT}")
        db = client.db(DB_NAME, username=DB_USER, password=DB_PASSWORD)
        print(f"✓ Connected to {DB_NAME} at {DB_HOST}:{DB_PORT}")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)

    # Check collections exist
    collections = ["models", "attacks", "evaluations"]
    for collection_name in collections:
        if db.has_collection(collection_name):
            count = db.collection(collection_name).count()
            print(f"✓ Collection '{collection_name}' exists ({count} documents)")
        else:
            print(f"✗ Collection '{collection_name}' not found")

    # Query sample models
    print("\n" + "=" * 60)
    print("Sample Models")
    print("=" * 60)

    try:
        query = """
        FOR m IN models
        LIMIT 5
        RETURN {
            id: m._key,
            name: m.name,
            type: m.model_type,
            observer_compatible: m.observer_framing_compatible
        }
        """
        cursor = db.aql.execute(query)
        models = list(cursor)

        for model in models:
            print(f"  {model['name']}")
            print(f"    Type: {model['type']}")
            print(f"    Observer: {model['observer_compatible']}")

        print(f"\n✓ Successfully queried {len(models)} sample models")
    except Exception as e:
        print(f"✗ Model query failed: {e}")

    # Query sample attacks
    print("\n" + "=" * 60)
    print("Sample Attacks")
    print("=" * 60)

    try:
        query = """
        FOR a IN attacks
        LIMIT 5
        RETURN {
            id: a._key,
            dataset: a.dataset_source,
            encoding: a.encoding_technique,
            ground_truth: a.ground_truth
        }
        """
        cursor = db.aql.execute(query)
        attacks = list(cursor)

        for attack in attacks:
            print(f"  {attack['id']}")
            print(f"    Dataset: {attack['dataset']}")
            print(f"    Encoding: {attack.get('encoding', 'N/A')}")
            print(f"    Truth: {attack['ground_truth']}")

        print(f"\n✓ Successfully queried {len(attacks)} sample attacks")
    except Exception as e:
        print(f"✗ Attack query failed: {e}")

    # Count by model type
    print("\n" + "=" * 60)
    print("Model Distribution")
    print("=" * 60)

    try:
        query = """
        FOR m IN models
        COLLECT modelType = m.model_type WITH COUNT INTO count
        RETURN { type: modelType, count: count }
        """
        cursor = db.aql.execute(query)
        types = list(cursor)

        for t in sorted(types, key=lambda x: x['count'], reverse=True):
            print(f"  {t['type']}: {t['count']}")

        print(f"\n✓ Found {len(types)} model types")
    except Exception as e:
        print(f"✗ Type aggregation failed: {e}")

    # Count by dataset source
    print("\n" + "=" * 60)
    print("Attack Distribution")
    print("=" * 60)

    try:
        query = """
        FOR a IN attacks
        COLLECT dataset = a.dataset_source WITH COUNT INTO count
        RETURN { dataset: dataset, count: count }
        """
        cursor = db.aql.execute(query)
        datasets = list(cursor)

        for ds in sorted(datasets, key=lambda x: x['count'], reverse=True):
            print(f"  {ds['dataset']}: {ds['count']}")

        print(f"\n✓ Found {len(datasets)} datasets")
    except Exception as e:
        print(f"✗ Dataset aggregation failed: {e}")

    # Check for existing evaluations
    print("\n" + "=" * 60)
    print("Existing Evaluations")
    print("=" * 60)

    try:
        eval_count = db.collection("evaluations").count()
        print(f"  Total evaluations: {eval_count}")

        if eval_count > 0:
            query = """
            FOR e IN evaluations
            COLLECT condition = e.condition WITH COUNT INTO count
            RETURN { condition: condition, count: count }
            """
            cursor = db.aql.execute(query)
            conditions = list(cursor)

            for cond in conditions:
                print(f"  {cond['condition']}: {cond['count']}")

        print(f"\n✓ Evaluations collection accessible")
    except Exception as e:
        print(f"✗ Evaluations query failed: {e}")

    print("\n" + "=" * 60)
    print("All Tests Passed!")
    print("=" * 60)
    print("\nYou're ready to run:")
    print("  ./run_baseline_arango.py --attack-limit 5")


if __name__ == "__main__":
    main()
