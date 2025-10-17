"""
Example: Fire Circle Deliberation Storage

Demonstrates how to:
1. Configure Fire Circle with storage
2. Run evaluation and auto-save deliberation
3. Query stored deliberations by attack, pattern, dissent
4. Retrieve and analyze institutional memory
"""

import asyncio
from datetime import datetime, timedelta

from promptguard.storage import FileBackend
from promptguard.evaluation.fire_circle import FireCircleConfig, FireCircleEvaluator, CircleSize


async def main():
    """Demonstrate Fire Circle storage integration."""

    # 1. Initialize storage backend
    storage = FileBackend(base_path="deliberations")
    print("✓ Storage initialized at: deliberations/")
    print()

    # 2. Configure Fire Circle with storage
    config = FireCircleConfig(
        models=[
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku",
            "google/gemini-2.0-flash-001"
        ],
        circle_size=CircleSize.SMALL,
        max_rounds=3,
        pattern_threshold=0.5,
    )

    # Mock LLM caller for demonstration
    async def mock_llm_caller(model: str, messages: list):
        """Mock LLM responses for example."""
        return ('{"truth": 0.1, "indeterminacy": 0.1, "falsehood": 0.8, "reasoning": "Test"}', None)

    evaluator = FireCircleEvaluator(config, mock_llm_caller, storage=storage)
    print("✓ Fire Circle evaluator configured with storage")
    print()

    # 3. Run evaluation (in real usage, this would call actual LLMs)
    # NOTE: This is a simplified example - actual evaluation would be:
    # result = await evaluator.evaluate(
    #     layer_content="prompt layer to evaluate",
    #     context="full prompt context",
    #     evaluation_prompt="ayni_relational prompt"
    # )

    # For demonstration, we'll show how to save manually:
    print("Example: How to save deliberation after evaluation")
    print("-" * 50)
    print("# After Fire Circle evaluation:")
    print("result = await evaluator.evaluate(...)")
    print()
    print("# Save with attack metadata:")
    print("result.save(")
    print("    storage=storage,")
    print("    attack_id='attack_001',")
    print("    attack_category='encoding_obfuscation'")
    print(")")
    print()

    # 4. Query examples (assuming deliberations exist)
    print("Query Examples:")
    print("-" * 50)

    # Query by attack category
    print("\n1. Query by attack category:")
    print("   encoding_results = storage.query_by_attack('encoding_obfuscation')")
    results = storage.query_by_attack("encoding_obfuscation", limit=5)
    print(f"   Found {len(results)} deliberations")

    # Query by pattern type
    print("\n2. Query by pattern type:")
    print("   temporal_results = storage.query_by_pattern('temporal_inconsistency')")
    results = storage.query_by_pattern("temporal_inconsistency", min_agreement=0.5, limit=5)
    print(f"   Found {len(results)} deliberations")

    # Query by dissent
    print("\n3. Query by significant dissents:")
    print("   dissent_results = storage.find_dissents(min_f_delta=0.3)")
    results = storage.find_dissents(min_f_delta=0.3, limit=5)
    print(f"   Found {len(results)} deliberations with dissents")

    # List recent deliberations
    print("\n4. List recent deliberations:")
    print("   recent = storage.list_deliberations(limit=10)")
    recent = storage.list_deliberations(limit=10)
    print(f"   Found {len(recent)} recent deliberations")

    # Date-based query
    print("\n5. Query by date range:")
    print("   last_week = storage.list_deliberations(")
    print("       start_date=datetime.now() - timedelta(days=7),")
    print("       end_date=datetime.now()")
    print("   )")
    last_week = storage.list_deliberations(
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        limit=10
    )
    print(f"   Found {len(last_week)} deliberations from last week")
    print()

    # 5. Retrieve and analyze complete deliberation
    print("\nRetrieve Complete Deliberation:")
    print("-" * 50)
    print("# Get full deliberation by ID:")
    print("deliberation = storage.get_deliberation('fire_circle_id')")
    print()
    print("# Deliberation contains:")
    print("  - metadata: fire_circle_id, timestamp, models, attack info")
    print("  - rounds: complete dialogue history with evaluations")
    print("  - patterns: pattern observations with agreement scores")
    print("  - consensus: final evaluation with max(F) across rounds")
    print("  - dissents: significant F-score divergence between models")
    print("  - empty_chair_influence: contribution metric")
    print()

    # 6. Data extraction examples
    print("Data Extraction Methods:")
    print("-" * 50)
    print("# From FireCircleResult object:")
    print()
    print("# Extract dissents:")
    print("dissents = result.extract_dissents()")
    print("# Returns: [{'round_number': 1, 'model_high': ..., 'f_delta': 0.8, ...}]")
    print()
    print("# Extract metadata:")
    print("metadata = result.to_metadata()")
    print("# Returns: {'fire_circle_id': ..., 'models': [...], 'consensus_f': 0.9, ...}")
    print()
    print("# Extract convergence trajectory:")
    print("trajectory = result.extract_deliberation_trajectory()")
    print("# Returns: [{'round_number': 1, 'mean_f': 0.5, 'stddev_f': 0.2, ...}]")
    print()

    print("=" * 50)
    print("Storage Integration Complete")
    print("=" * 50)
    print()
    print("Directory structure:")
    print("  deliberations/")
    print("  ├── deliberations.db (SQLite metadata index)")
    print("  └── YYYY/")
    print("      └── MM/")
    print("          └── fire_circle_{id}/")
    print("              ├── metadata.json")
    print("              ├── rounds.json")
    print("              ├── synthesis.json")
    print("              └── dissents.json")


if __name__ == "__main__":
    asyncio.run(main())
