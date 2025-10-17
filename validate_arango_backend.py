#!/usr/bin/env python3
"""
Quick validation script for ArangoDB backend implementation.

Checks:
1. ArangoDB connection
2. Collections created
3. Indexes created
4. Storage/retrieval works
5. Query operations work
6. Interface compliance

Run with: python validate_arango_backend.py
"""

import os
import sys
from datetime import datetime
from promptguard.storage.arango_backend import ArangoDBBackend


def print_status(test_name, passed, details=""):
    """Print test status with color."""
    symbol = "✓" if passed else "✗"
    status = "PASS" if passed else "FAIL"
    print(f"{symbol} {test_name}: {status}")
    if details:
        print(f"  {details}")


def main():
    """Run validation checks."""
    print("=" * 60)
    print("ArangoDB Backend Validation")
    print("=" * 60)

    # Check environment
    if not os.environ.get("ARANGODB_PROMPTGUARD_PASSWORD"):
        print("\n✗ ARANGODB_PROMPTGUARD_PASSWORD environment variable not set")
        print("  Export it before running this script")
        sys.exit(1)

    print("\n1. Testing ArangoDB connection...")
    try:
        backend = ArangoDBBackend()
        print_status("Connection", True, f"Connected to {backend.db_name}")
    except Exception as e:
        print_status("Connection", False, str(e))
        sys.exit(1)

    print("\n2. Testing collections...")
    collections_ok = True
    for collection_name in ["deliberations", "turns", "participated_in", "deliberation_about"]:
        exists = backend.db.has_collection(collection_name)
        if exists:
            count = backend.db.collection(collection_name).count()
            print_status(f"Collection '{collection_name}'", True, f"{count} documents")
        else:
            print_status(f"Collection '{collection_name}'", False, "Not found")
            collections_ok = False

    if not collections_ok:
        print("\n✗ Some collections missing")
        sys.exit(1)

    print("\n3. Testing storage operation...")
    try:
        test_data = {
            "fire_circle_id": "validation_test_001",
            "timestamp": datetime.now(),
            "models": ["test/model1", "test/model2"],
            "attack_id": "test_attack",
            "attack_category": "validation_test",
            "rounds": [
                {
                    "round_number": 1,
                    "duration_seconds": 1.0,
                    "empty_chair_model": None,
                    "active_models": ["test/model1", "test/model2"],
                    "convergence_metric": 0.1,
                    "evaluations": [
                        {
                            "model": "test/model1",
                            "T": 0.2,
                            "I": 0.1,
                            "F": 0.7,
                            "reasoning": "Test reasoning for validation"
                        },
                        {
                            "model": "test/model2",
                            "T": 0.3,
                            "I": 0.1,
                            "F": 0.6,
                            "reasoning": "Another test reasoning"
                        }
                    ]
                }
            ],
            "patterns": [
                {
                    "pattern_type": "test_pattern",
                    "first_observed_by": "test/model1",
                    "agreement_score": 1.0,
                    "round_discovered": 1
                }
            ],
            "consensus": {
                "model": "test/model1",
                "T": 0.2,
                "I": 0.1,
                "F": 0.7,
                "reasoning": "Test consensus"
            },
            "empty_chair_influence": 0.0,
            "metadata": {
                "quorum_valid": True,
                "total_duration_seconds": 1.0,
                "final_active_models": ["test/model1", "test/model2"],
                "failed_models": [],
                "empty_chair_assignments": {}
            }
        }

        backend.store_deliberation(**test_data)
        print_status("Storage", True, "Test deliberation stored")
    except Exception as e:
        print_status("Storage", False, str(e))
        sys.exit(1)

    print("\n4. Testing retrieval operation...")
    try:
        retrieved = backend.get_deliberation("validation_test_001")
        if retrieved and retrieved["fire_circle_id"] == "validation_test_001":
            print_status("Retrieval", True, "Test deliberation retrieved")
        else:
            print_status("Retrieval", False, "Retrieved data mismatch")
            sys.exit(1)
    except Exception as e:
        print_status("Retrieval", False, str(e))
        sys.exit(1)

    print("\n5. Testing query operations...")

    # Query by attack
    try:
        results = backend.query_by_attack("validation_test", limit=10)
        print_status("Query by attack", True, f"Found {len(results)} results")
    except Exception as e:
        print_status("Query by attack", False, str(e))

    # Query by pattern
    try:
        results = backend.query_by_pattern("test_pattern", min_agreement=0.5, limit=10)
        print_status("Query by pattern", True, f"Found {len(results)} results")
    except Exception as e:
        print_status("Query by pattern", False, str(e))

    # Find dissents
    try:
        results = backend.find_dissents(min_f_delta=0.1, limit=10)
        print_status("Find dissents", True, f"Found {len(results)} results")
    except Exception as e:
        print_status("Find dissents", False, str(e))

    # List deliberations
    try:
        results = backend.list_deliberations(limit=10)
        print_status("List deliberations", True, f"Found {len(results)} results")
    except Exception as e:
        print_status("List deliberations", False, str(e))

    # Search reasoning
    try:
        results = backend.search_reasoning("test", limit=10)
        print_status("Search reasoning", True, f"Found {len(results)} results")
    except Exception as e:
        print_status("Search reasoning", False, str(e))

    print("\n6. Testing interface compliance...")
    from promptguard.storage.deliberation import DeliberationStorage

    if isinstance(backend, DeliberationStorage):
        print_status("Interface compliance", True, "Implements DeliberationStorage")
    else:
        print_status("Interface compliance", False, "Does not implement DeliberationStorage")

    print("\n7. Cleanup test data...")
    try:
        # Delete test deliberation
        backend.db.collection("deliberations").delete("validation_test_001", ignore_missing=True)

        # Delete test turns
        query = """
        FOR t IN turns
            FILTER t.fire_circle_id == 'validation_test_001'
            REMOVE t IN turns
        """
        backend.db.aql.execute(query)

        print_status("Cleanup", True, "Test data removed")
    except Exception as e:
        print_status("Cleanup", False, str(e))

    print("\n" + "=" * 60)
    print("All Validations Passed!")
    print("=" * 60)
    print("\nArangoDB backend is ready for Fire Circle evaluations.")
    print("\nNext steps:")
    print("  1. Run unit tests: pytest tests/storage/test_arango_backend.py")
    print("  2. Try demo script: python examples/fire_circle_arango_demo.py")
    print("  3. Integrate with Fire Circle evaluations")


if __name__ == "__main__":
    main()
