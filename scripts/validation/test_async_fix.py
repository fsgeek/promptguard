"""
Test script to verify async fix and experiment metadata write.

Tests:
1. No deprecation warnings from asyncio pattern
2. Experiment metadata written to experiments collection
3. All required fields populated correctly

Run with: uv run python scripts/validation/test_async_fix.py
"""

import sys
import warnings
from pathlib import Path
from datetime import datetime, timezone

# Add scripts/validation to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

# Add project root to path for promptguard package
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Capture deprecation warnings
warnings.simplefilter("always", DeprecationWarning)

from utils.arango_client import ArangoConnection
from utils.prompt_loader import load_all_prompts
from experiment_01_baseline import run_baseline_collection


def verify_experiment_metadata(experiment_id: str) -> dict:
    """
    Query experiments collection to verify metadata was written.

    Args:
        experiment_id: Experiment to verify

    Returns:
        Experiment metadata dict if found

    Raises:
        AssertionError: If metadata not found or invalid
    """
    connection = ArangoConnection()
    db = connection.get_database()

    query = """
    FOR e IN experiments
    FILTER e.experiment_id == @exp_id
    RETURN e
    """

    cursor = db.aql.execute(query, bind_vars={"exp_id": experiment_id})
    experiments = list(cursor)

    assert len(experiments) > 0, f"No experiment metadata found for {experiment_id}"
    assert len(experiments) == 1, f"Multiple experiments found for {experiment_id}"

    exp = experiments[0]

    # Verify all required fields per spec
    required_fields = [
        "experiment_id",
        "experiment_label",
        "target_model",
        "observer_model",
        "start_timestamp",
        "end_timestamp",
        "total_prompts",
        "total_cost",
        "stages_completed",
        "compliance_prompt_id",
        "pre_eval_prompt_id",
        "post_eval_prompt_id",
        "model_version_change_decision"
    ]

    missing_fields = [f for f in required_fields if f not in exp]
    assert len(missing_fields) == 0, f"Missing required fields: {missing_fields}"

    # Verify field types and values
    assert isinstance(exp["experiment_id"], str)
    assert isinstance(exp["experiment_label"], str)
    assert isinstance(exp["target_model"], str)
    assert isinstance(exp["observer_model"], str)
    assert isinstance(exp["total_prompts"], int)
    assert isinstance(exp["total_cost"], (int, float))
    assert isinstance(exp["stages_completed"], list)
    assert "baseline_collection" in exp["stages_completed"]

    # Verify timestamps are valid ISO format
    for ts_field in ["start_timestamp", "end_timestamp"]:
        try:
            datetime.fromisoformat(exp[ts_field].replace('Z', '+00:00'))
        except Exception as e:
            raise AssertionError(f"Invalid timestamp format for {ts_field}: {e}")

    return exp


def main():
    """Run test with 5 prompts and verify both fixes."""
    print("="*60)
    print("Testing Async Fix and Experiment Metadata Write")
    print("="*60)
    print()

    experiment_id = "test_async_fix_001"
    target_model = "anthropic/claude-3-haiku"  # Cheap model for testing
    observer_model = "anthropic/claude-3-haiku"

    print(f"Experiment ID: {experiment_id}")
    print(f"Target Model: {target_model}")
    print(f"Observer Model: {observer_model}")
    print()

    # Load all prompts and limit to 5 for testing
    print("Loading prompts (limiting to 5 for test)...")
    all_prompts = load_all_prompts()
    test_prompts = all_prompts[:5]
    print(f"✓ Using {len(test_prompts)} prompts for test")
    print()

    # Temporarily replace load_all_prompts to return only test prompts
    import utils.prompt_loader
    original_load = utils.prompt_loader.load_all_prompts
    utils.prompt_loader.load_all_prompts = lambda: test_prompts

    try:
        print("Running baseline collection (5 prompts)...")
        print("Watching for DeprecationWarnings...")
        print()

        # Capture warnings
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always", DeprecationWarning)

            # Run experiment (will use our 5-prompt subset)
            run_baseline_collection(
                target_model=target_model,
                observer_model=observer_model,
                experiment_id=experiment_id,
                resume=False  # Don't resume - process all 5 from scratch
            )

            # Check for deprecation warnings
            deprecation_warnings = [w for w in warning_list
                                   if issubclass(w.category, DeprecationWarning)]

            print()
            print("="*60)
            print("Verification Results")
            print("="*60)
            print()

            # Issue 1: Check for deprecation warnings
            print("1. Deprecation Warnings")
            print("-"*60)
            if len(deprecation_warnings) > 0:
                print(f"✗ Found {len(deprecation_warnings)} deprecation warning(s):")
                for w in deprecation_warnings:
                    print(f"  - {w.filename}:{w.lineno}: {w.message}")
                sys.exit(1)
            else:
                print("✓ No deprecation warnings detected")
            print()

            # Issue 2: Check experiment metadata
            print("2. Experiment Metadata in Database")
            print("-"*60)
            try:
                exp = verify_experiment_metadata(experiment_id)
                print("✓ Experiment metadata found in experiments collection")
                print()
                print("  Fields:")
                print(f"    experiment_id: {exp['experiment_id']}")
                print(f"    experiment_label: {exp['experiment_label']}")
                print(f"    target_model: {exp['target_model']}")
                print(f"    observer_model: {exp['observer_model']}")
                print(f"    total_prompts: {exp['total_prompts']}")
                print(f"    total_cost: ${exp['total_cost']:.2f}")
                print(f"    stages_completed: {exp['stages_completed']}")
                print(f"    compliance_prompt_id: {exp['compliance_prompt_id']}")
                print(f"    start_timestamp: {exp['start_timestamp']}")
                print(f"    end_timestamp: {exp['end_timestamp']}")

                # Calculate duration
                start = datetime.fromisoformat(exp['start_timestamp'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(exp['end_timestamp'].replace('Z', '+00:00'))
                duration = (end - start).total_seconds()
                print(f"    duration: {duration:.1f} seconds")

                print()
                print("✓ All required fields present and valid")

            except AssertionError as e:
                print(f"✗ Experiment metadata verification failed: {e}")
                sys.exit(1)

            print()
            print("="*60)
            print("✓ All Tests Passed!")
            print("="*60)
            print()
            print("Evidence:")
            print("- No asyncio.get_event_loop() deprecation warnings")
            print("- Experiment metadata written to experiments collection")
            print("- All required fields populated correctly")

    finally:
        # Restore original function
        utils.prompt_loader.load_all_prompts = original_load


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print()
        print("="*60)
        print(f"✗ Test failed: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        sys.exit(1)
