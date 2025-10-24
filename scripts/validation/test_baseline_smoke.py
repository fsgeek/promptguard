"""
Smoke test for experiment_01_baseline.py

Tests basic functionality without running full 680-prompt experiment.
Validates:
- ArangoDB connection
- Baseline evaluation with real API
- Compliance classification with real API
- Storage to collections
- Checkpoint/resume logic

Run with: uv run python scripts/validation/test_baseline_smoke.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

# Add scripts/validation to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

# Add project root to path for promptguard package
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from common.errors import ConfigurationError, EvaluationError
from utils.arango_client import ArangoConnection, ArangoSink
from experiment_01_baseline import (
    BaselineEvaluationStage,
    ComplianceClassificationStage,
    ProcessingFailureHandler
)


async def test_baseline_evaluation():
    """Test baseline evaluation stage with real API."""
    print("Testing BaselineEvaluationStage...")

    stage = BaselineEvaluationStage(
        target_model="anthropic/claude-3-haiku",  # Cheap model for testing
        experiment_id="smoke_test"
    )

    # Test with simple benign prompt
    test_prompt = "What is the capital of France?"
    result = await stage.evaluate_prompt(test_prompt)

    assert "response_text" in result
    assert "token_count" in result
    assert "cost" in result
    assert "model_version" in result
    assert len(result["response_text"]) > 0
    assert result["token_count"] > 0

    print(f"✓ Baseline evaluation successful")
    print(f"  Model: {result['model_version']}")
    print(f"  Tokens: {result['token_count']}")
    print(f"  Response length: {len(result['response_text'])} chars")
    return result


async def test_compliance_classification(baseline_result):
    """Test compliance classification stage with real API."""
    print("\nTesting ComplianceClassificationStage...")

    # Get compliance prompt ID from database
    connection = ArangoConnection()
    db = connection.get_database()
    query = """
    FOR p IN prompt_configurations
    FILTER p.prompt_type == "compliance_classification" AND p.version == 0
    RETURN p.prompt_id
    """
    cursor = db.aql.execute(query)
    compliance_prompt_ids = list(cursor)

    if not compliance_prompt_ids:
        raise ConfigurationError(
            "Compliance prompt not found. Run scripts/validation/init_database.py first."
        )

    compliance_prompt_id = compliance_prompt_ids[0]

    stage = ComplianceClassificationStage(
        observer_model="anthropic/claude-3-haiku",  # Cheap model for testing
        compliance_prompt_id=compliance_prompt_id
    )

    # Classify the baseline response
    test_prompt = "What is the capital of France?"
    classification = await stage.classify_compliance(
        test_prompt,
        baseline_result["response_text"]
    )

    assert "compliance_score" in classification
    assert "classification" in classification
    assert "classification_explanation" in classification
    assert 0.0 <= classification["compliance_score"] <= 1.0
    assert classification["classification"] in ["comply", "refuse", "borderline"]

    print(f"✓ Compliance classification successful")
    print(f"  Score: {classification['compliance_score']:.2f}")
    print(f"  Classification: {classification['classification']}")
    print(f"  Explanation: {classification['classification_explanation'][:100]}...")
    return classification


async def test_storage():
    """Test storage to ArangoDB."""
    print("\nTesting ArangoDB storage...")

    connection = ArangoConnection()

    # Test baseline_responses sink
    baseline_sink = ArangoSink("baseline_responses", connection)
    test_record = {
        "prompt_id": str(uuid4()),
        "experiment_id": "smoke_test",
        "prompt_text": "Test prompt",
        "response_text": "Test response",
        "classification": "comply",
        "compliance_score": 0.9,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    baseline_sink.write(test_record)
    print("✓ Baseline response stored successfully")

    # Test processing_failures sink
    failure_handler = ProcessingFailureHandler("smoke_test", connection)
    try:
        raise EvaluationError("Test error")
    except EvaluationError as e:
        failure_handler.handle_failure(
            prompt_id=str(uuid4()),
            error=e,
            stage="baseline_collection",
            target_model="anthropic/claude-3-haiku"
        )
    print("✓ Processing failure stored successfully")


def test_checkpoint_resume():
    """Test checkpoint/resume logic."""
    print("\nTesting checkpoint/resume...")

    from utils.prompt_loader import get_remaining_prompts

    # Create test prompts
    all_prompts = [
        {"prompt_id": "test_1", "prompt_text": "Test 1"},
        {"prompt_id": "test_2", "prompt_text": "Test 2"},
        {"prompt_id": "test_3", "prompt_text": "Test 3"},
    ]

    # For smoke test experiment_id, should return all prompts (none completed yet)
    remaining = get_remaining_prompts(all_prompts, "smoke_test_checkpoint")
    assert len(remaining) == len(all_prompts)
    print(f"✓ Checkpoint query successful ({len(remaining)} prompts remaining)")


async def main():
    """Run all smoke tests."""
    print("="*60)
    print("Experiment 1 Baseline Collection - Smoke Test")
    print("="*60)
    print()

    try:
        # Test 1: Baseline evaluation
        baseline_result = await test_baseline_evaluation()

        # Test 2: Compliance classification
        classification_result = await test_compliance_classification(baseline_result)

        # Test 3: Storage
        await test_storage()

        # Test 4: Checkpoint/resume
        test_checkpoint_resume()

        print()
        print("="*60)
        print("✓ All smoke tests passed!")
        print("="*60)
        print()
        print("Next steps:")
        print("1. Run init_database.py if not already done")
        print("2. Run experiment_01_baseline.py with --experiment-id and model args")
        print("3. Start with small subset (--no-resume flag) to verify end-to-end")

    except Exception as e:
        print()
        print("="*60)
        print(f"✗ Smoke test failed: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
