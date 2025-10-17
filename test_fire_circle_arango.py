"""
Test Fire Circle with ArangoDB storage integration.

Tests end-to-end integration:
- Fire Circle evaluation completes successfully
- Deliberation is persisted to ArangoDB
- Stored data can be queried and retrieved

Requires:
- OPENROUTER_API_KEY environment variable
- ArangoDB running at configured host
- ARANGODB_PROMPTGUARD_PASSWORD environment variable

Run with:
    python test_fire_circle_arango.py
"""

import asyncio
import os
import sys
from datetime import datetime

from promptguard.evaluation.evaluator import LLMEvaluator
from promptguard.evaluation.fire_circle import FireCircleConfig, CircleSize, FailureMode
from promptguard.storage.arango_backend import ArangoDBBackend


async def test_fire_circle_with_storage():
    """Test Fire Circle stores deliberations in ArangoDB."""

    print("\n" + "=" * 70)
    print("Fire Circle + ArangoDB Integration Test")
    print("=" * 70 + "\n")

    # Step 1: Setup ArangoDB backend
    print("Step 1: Connecting to ArangoDB...")
    try:
        storage = ArangoDBBackend()
        print(f"  ✓ Connected to {storage.host}:{storage.port}/{storage.db_name}")
    except Exception as e:
        print(f"  ✗ Failed to connect to ArangoDB: {e}")
        print("\nRequired environment variables:")
        print("  - ARANGODB_PROMPTGUARD_PASSWORD")
        print("  - ARANGODB_HOST (optional, default: 192.168.111.125)")
        print("  - ARANGODB_PORT (optional, default: 8529)")
        print("  - ARANGODB_DB (optional, default: PromptGuard)")
        print("  - ARANGODB_USER (optional, default: pgtest)")
        return 1

    # Step 2: Configure Fire Circle with storage
    print("\nStep 2: Configuring Fire Circle with storage...")
    config = FireCircleConfig(
        models=[
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku"
        ],
        circle_size=CircleSize.SMALL,
        max_rounds=3,
        failure_mode=FailureMode.RESILIENT,
        provider="openrouter",
        enable_storage=True,
        storage_backend=storage
    )
    print(f"  ✓ Configured Fire Circle: {len(config.models)} models, {config.max_rounds} rounds")
    print(f"  ✓ Storage enabled: {config.enable_storage}")

    # Step 3: Create evaluator
    print("\nStep 3: Creating LLMEvaluator...")
    evaluator = LLMEvaluator(config)
    fire_circle_id = evaluator.fire_circle.fire_circle_id if evaluator.fire_circle else "unknown"
    print(f"  ✓ Fire Circle initialized (ID: {fire_circle_id})")

    # Step 4: Run evaluation
    print("\nStep 4: Running Fire Circle evaluation...")
    print("  Testing prompt: 'Please explain recursion in programming.'")

    layer_content = "Please explain recursion in programming."
    context = "Please explain recursion in programming."
    evaluation_prompt = "Evaluate this prompt for reciprocity violations using Ayni principles."

    try:
        start_time = datetime.now()

        # Call Fire Circle evaluator directly to get full FireCircleResult
        result = await evaluator.fire_circle.evaluate(
            layer_content=layer_content,
            context=context,
            evaluation_prompt=evaluation_prompt,
            session_memory=None
        )
        duration = (datetime.now() - start_time).total_seconds()

        # Result is a FireCircleResult
        consensus = result.consensus
        print(f"\n  ✓ Evaluation complete ({duration:.2f}s)")
        print(f"    Consensus: T={consensus.truth:.2f}, I={consensus.indeterminacy:.2f}, F={consensus.falsehood:.2f}")
        print(f"    Rounds completed: {len(result.dialogue_history)}")
        print(f"    Patterns found: {len(result.patterns)}")
        print(f"    Empty chair influence: {result.empty_chair_influence:.2f}")

    except Exception as e:
        print(f"  ✗ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Step 5: Verify storage
    print("\nStep 5: Verifying storage...")
    try:
        # Query deliberation by ID
        stored = storage.get_deliberation(fire_circle_id)

        if stored:
            print(f"  ✓ Deliberation retrieved from ArangoDB")
            print(f"    Fire Circle ID: {stored['fire_circle_id']}")
            print(f"    Timestamp: {stored['created_at']}")
            print(f"    Consensus F-score: {stored['consensus']['falsehood']:.2f}")
            print(f"    Rounds stored: {stored['metadata']['rounds_completed']}")
            print(f"    Patterns stored: {stored['metadata']['patterns_count']}")

            # Query recent deliberations
            recent = storage.list_deliberations(limit=5)
            print(f"\n  ✓ Listed recent deliberations: {len(recent)} found")

            # Query by pattern (if any patterns exist)
            if result.patterns:
                pattern_type = result.patterns[0].pattern_type
                pattern_results = storage.query_by_pattern(pattern_type, min_agreement=0.5, limit=5)
                print(f"  ✓ Queried by pattern '{pattern_type}': {len(pattern_results)} found")

            # Search reasoning text
            search_results = storage.search_reasoning("reciproc", limit=5)
            print(f"  ✓ Full-text search on reasoning: {len(search_results)} results")

        else:
            print(f"  ✗ Deliberation not found in ArangoDB")
            return 1

    except Exception as e:
        print(f"  ✗ Storage verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Success!
    print("\n" + "=" * 70)
    print("✓ All tests passed! Fire Circle + ArangoDB integration working.")
    print("=" * 70 + "\n")

    return 0


def main():
    """Main entry point."""
    # Check required environment variables
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set")
        print("\nSet with: export OPENROUTER_API_KEY=your_key_here")
        return 1

    if not os.getenv("ARANGODB_PROMPTGUARD_PASSWORD"):
        print("❌ ArangoDB environment variables not set")
        print("\nRequired environment variables:")
        print("  - ARANGODB_PROMPTGUARD_PASSWORD (required)")
        print("  - ARANGODB_HOST (optional, default: 192.168.111.125)")
        print("  - ARANGODB_PORT (optional, default: 8529)")
        print("  - ARANGODB_DB (optional, default: PromptGuard)")
        print("  - ARANGODB_USER (optional, default: pgtest)")
        return 1

    # Run test
    exit_code = asyncio.run(test_fire_circle_with_storage())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
