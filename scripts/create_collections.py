#!/usr/bin/env python3
"""
Create ArangoDB collections for PromptGuard research database.
"""
import os
from arango import ArangoClient

# Connection parameters
HOST = "192.168.111.125"
PORT = 8529
USERNAME = "pgtest"
PASSWORD = os.environ["ARANGODB_PROMPTGUARD_PASSWORD"]
DATABASE = "PromptGuard"

def main():
    # Connect to ArangoDB
    client = ArangoClient(hosts=f"http://{HOST}:{PORT}")
    db = client.db(DATABASE, username=USERNAME, password=PASSWORD)

    print(f"Connected to {DATABASE} database at {HOST}:{PORT}")
    print()

    # Track created resources
    created_collections = []
    created_indexes = []

    # 1. Create 'models' document collection
    print("Creating 'models' collection...")
    try:
        models = db.create_collection("models")
        created_collections.append("models (document)")
        print("  ✓ Created 'models' document collection")

        # Create indexes
        models.add_hash_index(fields=["organization"], unique=False, name="idx_organization")
        created_indexes.append("models.organization (hash)")

        models.add_hash_index(fields=["model_type"], unique=False, name="idx_model_type")
        created_indexes.append("models.model_type (hash)")

        models.add_hash_index(fields=["observer_framing_compatible"], unique=False, name="idx_observer_compatible")
        created_indexes.append("models.observer_framing_compatible (hash)")

        models.add_hash_index(fields=["deprecated"], unique=False, name="idx_deprecated")
        created_indexes.append("models.deprecated (hash)")

        print("  ✓ Created 4 indexes on 'models'")

    except Exception as e:
        print(f"  ✗ Error creating 'models': {e}")

    # 2. Create 'attacks' document collection
    print("\nCreating 'attacks' collection...")
    try:
        attacks = db.create_collection("attacks")
        created_collections.append("attacks (document)")
        print("  ✓ Created 'attacks' document collection")

        # Create indexes
        attacks.add_hash_index(fields=["encoding_technique"], unique=False, name="idx_encoding_technique")
        created_indexes.append("attacks.encoding_technique (hash)")

        attacks.add_hash_index(fields=["ground_truth"], unique=False, name="idx_ground_truth")
        created_indexes.append("attacks.ground_truth (hash)")

        attacks.add_hash_index(fields=["dataset_source"], unique=False, name="idx_dataset_source")
        created_indexes.append("attacks.dataset_source (hash)")

        attacks.add_hash_index(fields=["attack_metadata.technique_category"], unique=False, name="idx_technique_category")
        created_indexes.append("attacks.attack_metadata.technique_category (hash)")

        print("  ✓ Created 4 indexes on 'attacks'")

    except Exception as e:
        print(f"  ✗ Error creating 'attacks': {e}")

    # 3. Create 'evaluations' edge collection
    print("\nCreating 'evaluations' edge collection...")
    try:
        evaluations = db.create_collection("evaluations", edge=True)
        created_collections.append("evaluations (edge)")
        print("  ✓ Created 'evaluations' edge collection")

        # Create indexes
        evaluations.add_hash_index(fields=["condition"], unique=False, name="idx_condition")
        created_indexes.append("evaluations.condition (hash)")

        evaluations.add_hash_index(fields=["evaluation_result.detected"], unique=False, name="idx_detected")
        created_indexes.append("evaluations.evaluation_result.detected (hash)")

        evaluations.add_hash_index(fields=["evaluation_result.success"], unique=False, name="idx_success")
        created_indexes.append("evaluations.evaluation_result.success (hash)")

        evaluations.add_skiplist_index(fields=["timestamp"], unique=False, name="idx_timestamp")
        created_indexes.append("evaluations.timestamp (skiplist)")

        evaluations.add_hash_index(fields=["experiment_metadata.experiment_id"], unique=False, name="idx_experiment_id")
        created_indexes.append("evaluations.experiment_metadata.experiment_id (hash)")

        print("  ✓ Created 5 indexes on 'evaluations'")

    except Exception as e:
        print(f"  ✗ Error creating 'evaluations': {e}")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\nCollections created ({len(created_collections)}):")
    for coll in created_collections:
        print(f"  ✓ {coll}")

    print(f"\nIndexes created ({len(created_indexes)}):")
    for idx in created_indexes:
        print(f"  ✓ {idx}")

    print(f"\n✓ Schema creation complete!")
    print(f"✓ Database ready for data import")

if __name__ == "__main__":
    main()
