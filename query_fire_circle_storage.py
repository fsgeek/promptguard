"""
Query Fire Circle deliberations from ArangoDB storage.

Demonstrates various query capabilities:
- List all deliberations
- Query by attack category
- Query by pattern type
- Find dissents (disagreements between models)
- Search reasoning text
- Retrieve specific deliberation

Run with:
    python query_fire_circle_storage.py
"""

import os
import sys
from datetime import datetime
from promptguard.storage.arango_backend import ArangoDBBackend


def main():
    """Query Fire Circle storage."""
    print("\n" + "=" * 70)
    print("Fire Circle Storage Query Tool")
    print("=" * 70 + "\n")

    # Connect to ArangoDB
    try:
        storage = ArangoDBBackend()
        print(f"Connected to {storage.host}:{storage.port}/{storage.db_name}\n")
    except Exception as e:
        print(f"Failed to connect to ArangoDB: {e}")
        print("\nRequired: ARANGODB_PROMPTGUARD_PASSWORD environment variable")
        return 1

    # Query 1: List recent deliberations
    print("=" * 70)
    print("1. Recent Deliberations (last 5)")
    print("=" * 70)
    recent = storage.list_deliberations(limit=5)
    if recent:
        for delib in recent:
            print(f"\nFire Circle ID: {delib['fire_circle_id']}")
            print(f"  Created: {delib['created_at']}")
            print(f"  Attack: {delib.get('attack_category', 'N/A')}")
            print(f"  Consensus F: {delib['consensus_f']:.2f}")
            print(f"  Rounds: {delib['rounds_completed']}")
            print(f"  Patterns: {delib['patterns_count']}")
            print(f"  Quorum valid: {delib['quorum_valid']}")
    else:
        print("No deliberations found")

    # Query 2: Query by pattern type
    print("\n" + "=" * 70)
    print("2. Deliberations with 'temporal_inconsistency' pattern")
    print("=" * 70)
    temporal = storage.query_by_pattern("temporal_inconsistency", min_agreement=0.5, limit=5)
    if temporal:
        for delib in temporal:
            print(f"\nFire Circle ID: {delib['fire_circle_id']}")
            print(f"  Pattern: {delib['pattern_type']}")
            print(f"  Agreement: {delib['agreement_score']:.2f}")
            print(f"  First observed by: {delib['first_observed_by']}")
            print(f"  Round discovered: {delib['round_discovered']}")
            print(f"  Consensus F: {delib['consensus_f']:.2f}")
    else:
        print("No deliberations with temporal_inconsistency pattern found")

    # Query 3: Find dissents
    print("\n" + "=" * 70)
    print("3. Deliberations with Significant Dissents (F-delta >= 0.3)")
    print("=" * 70)
    dissents = storage.find_dissents(min_f_delta=0.3, limit=5)
    if dissents:
        for dissent in dissents:
            print(f"\nFire Circle ID: {dissent['fire_circle_id']}")
            print(f"  Round: {dissent['round_number']}")
            print(f"  Model (high F): {dissent['model_high']} (F={dissent['f_high']:.2f})")
            print(f"  Model (low F): {dissent['model_low']} (F={dissent['f_low']:.2f})")
            print(f"  F-delta: {dissent['f_delta']:.2f}")
            print(f"  Attack: {dissent.get('attack_category', 'N/A')}")
    else:
        print("No significant dissents found")

    # Query 4: Full-text search on reasoning
    print("\n" + "=" * 70)
    print("4. Full-text Search: 'reciprocity'")
    print("=" * 70)
    reasoning = storage.search_reasoning("reciprocity", limit=5)
    if reasoning:
        for turn in reasoning:
            print(f"\nFire Circle ID: {turn['fire_circle_id']}")
            print(f"  Round: {turn['round_number']}")
            print(f"  Model: {turn['model']}")
            print(f"  F-score: {turn['falsehood']:.2f}")
            print(f"  Reasoning: {turn['reasoning'][:100]}...")
    else:
        print("No results found")

    # Query 5: Retrieve complete deliberation
    if recent:
        print("\n" + "=" * 70)
        print(f"5. Complete Deliberation: {recent[0]['fire_circle_id']}")
        print("=" * 70)
        complete = storage.get_deliberation(recent[0]['fire_circle_id'])
        if complete:
            print(f"\nFire Circle ID: {complete['fire_circle_id']}")
            print(f"Created: {complete['created_at']}")
            print(f"Total duration: {complete['total_duration']:.2f}s")
            print(f"Empty chair influence: {complete['empty_chair_influence']:.2f}")
            print(f"\nConsensus:")
            print(f"  Model: {complete['consensus']['model']}")
            print(f"  T={complete['consensus']['truth']:.2f}, I={complete['consensus']['indeterminacy']:.2f}, F={complete['consensus']['falsehood']:.2f}")
            print(f"  Reasoning: {complete['consensus']['reasoning'][:150]}...")
            print(f"\nPatterns found: {len(complete['patterns'])}")
            for pattern in complete['patterns']:
                print(f"  - {pattern['pattern_type']} (agreement: {pattern['agreement_score']:.2f})")
            print(f"\nRounds completed: {complete['metadata']['rounds_completed']}")
            # Show convergence trajectory
            if 'convergence_trajectory' in complete:
                print(f"Convergence trajectory (mean F per round): {[f'{f:.2f}' for f in complete['convergence_trajectory']]}")
        else:
            print("Deliberation not found")

    print("\n" + "=" * 70)
    print("Query complete!")
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    if not os.getenv("ARANGODB_PROMPTGUARD_PASSWORD"):
        print("❌ ARANGODB_PROMPTGUARD_PASSWORD not set")
        sys.exit(1)

    sys.exit(main())
