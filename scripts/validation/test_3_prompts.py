"""
Focused 3-prompt test to verify experiment metadata write.

Run with: uv run python scripts/validation/test_3_prompts.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.arango_client import ArangoConnection, ArangoSink
from experiment_01_baseline import (
    BaselineEvaluationStage,
    ComplianceClassificationStage,
    ProcessingFailureHandler
)

def run_test():
    """Run 3-prompt test and verify metadata write."""
    print("="*60)
    print("3-Prompt Experiment Test")
    print("="*60)
    print()

    experiment_id = "test_3_prompts_001"
    target_model = "anthropic/claude-3-haiku"
    observer_model = "anthropic/claude-3-haiku"

    # Test prompts
    test_prompts = [
        {
            "prompt_id": "test_001",
            "prompt_text": "What is the capital of France?",
            "label": "reciprocal"
        },
        {
            "prompt_id": "test_002",
            "prompt_text": "How do I write a Python function?",
            "label": "reciprocal"
        },
        {
            "prompt_id": "test_003",
            "prompt_text": "Explain quantum physics simply.",
            "label": "reciprocal"
        }
    ]

    # Initialize ArangoDB
    connection = ArangoConnection()
    db = connection.get_database()

    # Get compliance prompt ID
    query = """
    FOR p IN prompt_configurations
    FILTER p.prompt_type == "compliance_classification" AND p.version == 0
    RETURN p.prompt_id
    """
    cursor = db.aql.execute(query)
    compliance_prompt_ids = list(cursor)

    if not compliance_prompt_ids:
        print("✗ Compliance prompt not found. Run init_database.py first.")
        return False

    compliance_prompt_id = compliance_prompt_ids[0]

    # Initialize pipeline stages
    baseline_stage = BaselineEvaluationStage(target_model, experiment_id)
    classification_stage = ComplianceClassificationStage(observer_model, compliance_prompt_id)
    failure_handler = ProcessingFailureHandler(experiment_id, connection)

    # Initialize sinks
    baseline_sink = ArangoSink("baseline_responses", connection)
    prompts_sink = ArangoSink("prompts", connection)

    # Track experiment metadata
    start_time = datetime.now(timezone.utc)
    total_cost = 0.0
    processed_count = 0
    failed_count = 0

    print(f"Processing {len(test_prompts)} prompts...")
    print()

    # Process prompts
    for i, prompt in enumerate(test_prompts, 1):
        try:
            print(f"  [{i}/{len(test_prompts)}] Processing {prompt['prompt_id']}...")

            # Store prompt
            prompt["experiment_id"] = experiment_id
            prompt["added_timestamp"] = datetime.now(timezone.utc).isoformat()
            prompts_sink.write(prompt)

            # Run baseline evaluation
            result = baseline_stage.process(prompt)

            # Run compliance classification
            result = classification_stage.process(result)

            # Store baseline response
            baseline_sink.write(result)

            # Update metrics
            total_cost += result.get("cost", 0.0)
            processed_count += 1

            print(f"      ✓ Complete - {result['classification']} (score: {result['compliance_score']:.2f})")

        except Exception as e:
            print(f"      ✗ Failed: {e}")
            failure_handler.handle_failure(
                prompt["prompt_id"],
                e,
                "baseline_collection",
                target_model
            )
            failed_count += 1

    # Store experiment metadata
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    experiment_metadata = {
        "experiment_id": experiment_id,
        "experiment_label": "Test: 3-Prompt Verification",
        "target_model": target_model,
        "observer_model": observer_model,
        "start_timestamp": start_time.isoformat(),
        "end_timestamp": end_time.isoformat(),
        "total_prompts": processed_count,
        "total_cost": total_cost,
        "stages_completed": ["baseline_collection"],
        "compliance_prompt_id": compliance_prompt_id,
        "pre_eval_prompt_id": None,
        "post_eval_prompt_id": None,
        "model_version_change_decision": None,
    }

    experiments_sink = ArangoSink("experiments", connection)
    experiments_sink.write(experiment_metadata)

    print()
    print("="*60)
    print("✓ Test Complete!")
    print(f"  Processed: {processed_count} prompts")
    print(f"  Failed: {failed_count} prompts")
    print(f"  Duration: {duration:.1f} seconds")
    print(f"  Experiment ID: {experiment_id}")
    print("="*60)
    print()

    # Verify experiment metadata was written
    print("Verifying experiment metadata in database...")
    query = """
    FOR e IN experiments
    FILTER e.experiment_id == @exp_id
    RETURN e
    """

    cursor = db.aql.execute(query, bind_vars={"exp_id": experiment_id})
    experiments = list(cursor)

    if len(experiments) == 0:
        print("✗ Experiment metadata NOT found in database")
        return False

    exp = experiments[0]
    print("✓ Experiment metadata found!")
    print()
    print("  Fields:")
    print(f"    experiment_id: {exp['experiment_id']}")
    print(f"    experiment_label: {exp['experiment_label']}")
    print(f"    target_model: {exp['target_model']}")
    print(f"    observer_model: {exp['observer_model']}")
    print(f"    total_prompts: {exp['total_prompts']}")
    print(f"    total_cost: ${exp['total_cost']:.4f}")
    print(f"    stages_completed: {exp['stages_completed']}")
    print(f"    compliance_prompt_id: {exp['compliance_prompt_id']}")
    print(f"    start_timestamp: {exp['start_timestamp']}")
    print(f"    end_timestamp: {exp['end_timestamp']}")

    # Verify all required fields
    required = [
        'experiment_id', 'experiment_label', 'target_model', 'observer_model',
        'start_timestamp', 'end_timestamp', 'total_prompts', 'total_cost',
        'stages_completed', 'compliance_prompt_id', 'pre_eval_prompt_id',
        'post_eval_prompt_id', 'model_version_change_decision'
    ]
    missing = [f for f in required if f not in exp]

    if missing:
        print(f"\n  ✗ Missing required fields: {missing}")
        return False
    else:
        print(f"\n  ✓ All required fields present")
        return True


if __name__ == "__main__":
    try:
        success = run_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
