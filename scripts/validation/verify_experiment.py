"""
Verify experiment output in ArangoDB.

Queries baseline_responses, processing_failures, and experiments collections
to validate data quality and structure.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add scripts/validation to path
sys.path.insert(0, str(Path(__file__).parent))

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.arango_client import ArangoConnection


def verify_experiment(experiment_id: str):
    """
    Query ArangoDB to verify experiment output.

    Args:
        experiment_id: Experiment identifier to verify
    """
    print(f"Verifying experiment: {experiment_id}")
    print("="*60)
    print()

    connection = ArangoConnection()
    db = connection.get_database()

    # 1. Count records in baseline_responses
    print("1. Baseline Responses Collection")
    print("-"*60)

    count_query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    COLLECT WITH COUNT INTO count
    RETURN count
    """

    cursor = db.aql.execute(count_query, bind_vars={"exp_id": experiment_id})
    response_count = list(cursor)[0]
    print(f"  Total records: {response_count}")

    # Check classification distribution
    dist_query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    COLLECT classification = r.classification WITH COUNT INTO count
    RETURN {classification: classification, count: count}
    """

    cursor = db.aql.execute(dist_query, bind_vars={"exp_id": experiment_id})
    distribution = list(cursor)
    print(f"\n  Classification distribution:")
    for item in distribution:
        print(f"    {item['classification']}: {item['count']}")

    # Check compliance_score range
    score_query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    COLLECT AGGREGATE
        min_score = MIN(r.compliance_score),
        max_score = MAX(r.compliance_score),
        avg_score = AVG(r.compliance_score)
    RETURN {min: min_score, max: max_score, avg: avg_score}
    """

    cursor = db.aql.execute(score_query, bind_vars={"exp_id": experiment_id})
    score_stats = list(cursor)[0]
    print(f"\n  Compliance score range:")
    print(f"    Min: {score_stats['min']:.2f}")
    print(f"    Max: {score_stats['max']:.2f}")
    print(f"    Avg: {score_stats['avg']:.2f}")

    # Validate compliance_score in [0.0, 1.0]
    invalid_score_query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    FILTER r.compliance_score < 0.0 OR r.compliance_score > 1.0
    COLLECT WITH COUNT INTO count
    RETURN count
    """

    cursor = db.aql.execute(invalid_score_query, bind_vars={"exp_id": experiment_id})
    invalid_count = list(cursor)[0]
    if invalid_count > 0:
        print(f"\n  ⚠ WARNING: {invalid_count} records have invalid compliance_score (outside [0.0, 1.0])")
    else:
        print(f"\n  ✓ All compliance_score values in valid range [0.0, 1.0]")

    # Sample 3 random records
    sample_query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    SORT RAND()
    LIMIT 3
    RETURN r
    """

    cursor = db.aql.execute(sample_query, bind_vars={"exp_id": experiment_id})
    samples = list(cursor)

    print(f"\n  Sample records (3 random):")
    for i, sample in enumerate(samples, 1):
        print(f"\n    Sample {i}:")
        print(f"      prompt_id: {sample.get('prompt_id')}")
        print(f"      classification: {sample.get('classification')}")
        print(f"      compliance_score: {sample.get('compliance_score'):.2f}")
        print(f"      model_version: {sample.get('model_version_at_stride')}")
        print(f"      timestamp: {sample.get('timestamp')}")
        print(f"      has_response_text: {bool(sample.get('response_text'))}")
        print(f"      token_count: {sample.get('token_count')}")

        # Check for required fields
        required_fields = [
            'prompt_id', 'prompt_text', 'response_text', 'classification',
            'compliance_score', 'classification_explanation', 'model_version_at_stride',
            'observer_model', 'target_model', 'timestamp', 'experiment_id',
            'stage', 'experiment_label'
        ]
        missing_fields = [f for f in required_fields if f not in sample]
        if missing_fields:
            print(f"      ⚠ Missing fields: {missing_fields}")
        else:
            print(f"      ✓ All required fields present")

    # 2. Count records in processing_failures
    print("\n\n2. Processing Failures Collection")
    print("-"*60)

    failure_count_query = """
    FOR f IN processing_failures
    FILTER f.experiment_id == @exp_id
    COLLECT WITH COUNT INTO count
    RETURN count
    """

    cursor = db.aql.execute(failure_count_query, bind_vars={"exp_id": experiment_id})
    failure_count = list(cursor)[0]
    print(f"  Total failures: {failure_count}")

    if failure_count > 0:
        # Show failure types
        failure_type_query = """
        FOR f IN processing_failures
        FILTER f.experiment_id == @exp_id
        COLLECT error_type = f.error_type WITH COUNT INTO count
        RETURN {error_type: error_type, count: count}
        """

        cursor = db.aql.execute(failure_type_query, bind_vars={"exp_id": experiment_id})
        failure_types = list(cursor)
        print(f"\n  Failure types:")
        for item in failure_types:
            print(f"    {item['error_type']}: {item['count']}")

        # Sample failures
        failure_sample_query = """
        FOR f IN processing_failures
        FILTER f.experiment_id == @exp_id
        LIMIT 3
        RETURN f
        """

        cursor = db.aql.execute(failure_sample_query, bind_vars={"exp_id": experiment_id})
        failure_samples = list(cursor)

        print(f"\n  Sample failures:")
        for i, sample in enumerate(failure_samples, 1):
            print(f"\n    Failure {i}:")
            print(f"      prompt_id: {sample.get('prompt_id')}")
            print(f"      error_type: {sample.get('error_type')}")
            print(f"      error_message: {sample.get('error_message')[:100]}...")

    # 3. Check experiment metadata
    print("\n\n3. Experiment Metadata")
    print("-"*60)

    exp_query = """
    FOR e IN experiments
    FILTER e.experiment_id == @exp_id
    RETURN e
    """

    cursor = db.aql.execute(exp_query, bind_vars={"exp_id": experiment_id})
    experiments = list(cursor)

    if len(experiments) == 0:
        print(f"  ⚠ No experiment metadata found for {experiment_id}")
    else:
        exp = experiments[0]
        print(f"  Experiment ID: {exp.get('experiment_id')}")
        print(f"  Label: {exp.get('experiment_label')}")
        print(f"  Target Model: {exp.get('target_model')}")
        print(f"  Observer Model: {exp.get('observer_model')}")
        print(f"  Total Prompts: {exp.get('total_prompts')}")
        print(f"  Total Cost: ${exp.get('total_cost', 0.0):.2f}")
        print(f"  Start: {exp.get('start_timestamp')}")
        print(f"  End: {exp.get('end_timestamp')}")

        # Calculate duration
        if exp.get('start_timestamp') and exp.get('end_timestamp'):
            start = datetime.fromisoformat(exp['start_timestamp'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(exp['end_timestamp'].replace('Z', '+00:00'))
            duration = (end - start).total_seconds()
            print(f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")

    # 4. Data quality checks
    print("\n\n4. Data Quality Checks")
    print("-"*60)

    # Check for missing fields
    missing_fields_query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    FILTER r.prompt_id == null OR
           r.prompt_text == null OR
           r.response_text == null OR
           r.classification == null OR
           r.compliance_score == null OR
           r.timestamp == null
    COLLECT WITH COUNT INTO count
    RETURN count
    """

    cursor = db.aql.execute(missing_fields_query, bind_vars={"exp_id": experiment_id})
    missing_count = list(cursor)[0]
    if missing_count > 0:
        print(f"  ⚠ {missing_count} records have missing required fields")
    else:
        print(f"  ✓ All records have required fields")

    # Check timestamp format (should be ISO format)
    invalid_timestamp_query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    FILTER !IS_DATESTRING(r.timestamp)
    COLLECT WITH COUNT INTO count
    RETURN count
    """

    cursor = db.aql.execute(invalid_timestamp_query, bind_vars={"exp_id": experiment_id})
    invalid_timestamp_count = list(cursor)[0]
    if invalid_timestamp_count > 0:
        print(f"  ⚠ {invalid_timestamp_count} records have invalid timestamp format")
    else:
        print(f"  ✓ All timestamps are valid ISO format")

    # Check model_version_at_stride matches expected models
    model_version_query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    COLLECT model = r.model_version_at_stride WITH COUNT INTO count
    RETURN {model: model, count: count}
    """

    cursor = db.aql.execute(model_version_query, bind_vars={"exp_id": experiment_id})
    model_versions = list(cursor)
    print(f"\n  Model versions used:")
    for item in model_versions:
        print(f"    {item['model']}: {item['count']} responses")

    # Summary
    print("\n\n5. Summary")
    print("="*60)

    total_prompts = response_count + failure_count
    success_rate = (response_count / total_prompts * 100) if total_prompts > 0 else 0

    print(f"  Total prompts processed: {total_prompts}")
    print(f"  Successful: {response_count} ({success_rate:.1f}%)")
    print(f"  Failed: {failure_count} ({100-success_rate:.1f}%)")

    # Readiness assessment
    print("\n  Readiness Assessment:")
    issues = []

    if response_count == 0:
        issues.append("No successful responses collected")

    if invalid_count > 0:
        issues.append(f"{invalid_count} records with invalid compliance_score")

    if missing_count > 0:
        issues.append(f"{missing_count} records with missing fields")

    if invalid_timestamp_count > 0:
        issues.append(f"{invalid_timestamp_count} records with invalid timestamps")

    if len(experiments) == 0:
        issues.append("No experiment metadata found")

    if issues:
        print("\n  ✗ Issues found:")
        for issue in issues:
            print(f"    - {issue}")
        print("\n  Recommendation: Fix issues before running full 680-prompt test")
    else:
        print("  ✓ Data looks correct and ready for full 680-prompt run")

    print("\n" + "="*60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_experiment.py <experiment_id>")
        print("Example: python verify_experiment.py exp_001_test_smoke")
        sys.exit(1)

    experiment_id = sys.argv[1]

    try:
        verify_experiment(experiment_id)
    except Exception as e:
        print(f"\n✗ Error verifying experiment: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
