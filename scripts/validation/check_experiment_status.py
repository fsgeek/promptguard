"""
Check status of running experiment_01_baseline.py

Queries ArangoDB to show current progress without interrupting the experiment.

Usage: uv run python scripts/validation/check_experiment_status.py exp_001_baseline_production
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from utils.arango_client import ArangoConnection


def check_experiment_status(experiment_id: str):
    """Check current status of experiment."""
    connection = ArangoConnection()
    db = connection.get_database()

    print(f"Checking status of experiment: {experiment_id}")
    print("="*60)

    # Count successful responses
    query_success = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    RETURN 1
    """
    cursor = db.aql.execute(query_success, bind_vars={"exp_id": experiment_id})
    success_count = len(list(cursor))

    # Count failures
    query_failures = """
    FOR f IN processing_failures
    FILTER f.experiment_id == @exp_id
    RETURN 1
    """
    cursor = db.aql.execute(query_failures, bind_vars={"exp_id": experiment_id})
    failure_count = len(list(cursor))

    # Get classification distribution
    query_classifications = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    COLLECT classification = r.classification WITH COUNT INTO count
    RETURN {classification: classification, count: count}
    """
    cursor = db.aql.execute(query_classifications, bind_vars={"exp_id": experiment_id})
    classifications = list(cursor)

    # Check for experiment metadata
    query_metadata = """
    FOR e IN experiments
    FILTER e.experiment_id == @exp_id
    RETURN e
    """
    cursor = db.aql.execute(query_metadata, bind_vars={"exp_id": experiment_id})
    metadata = list(cursor)

    # Print status
    total_processed = success_count + failure_count
    print(f"\nProgress:")
    print(f"  Total processed: {total_processed}/680 ({100*total_processed/680:.1f}%)")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {failure_count}")
    print(f"  Success rate: {100*success_count/total_processed:.1f}%")

    print(f"\nClassification Distribution:")
    for item in classifications:
        classification = item["classification"]
        count = item["count"]
        pct = 100 * count / success_count if success_count > 0 else 0
        print(f"  {classification}: {count} ({pct:.1f}%)")

    print(f"\nExperiment Metadata:")
    if metadata:
        meta = metadata[0]
        print(f"  Status: COMPLETE")
        print(f"  Total prompts: {meta.get('total_prompts', 'N/A')}")
        print(f"  Total cost: ${meta.get('total_cost', 0.0):.4f}")
        print(f"  Start: {meta.get('start_timestamp', 'N/A')}")
        print(f"  End: {meta.get('end_timestamp', 'N/A')}")
    else:
        print(f"  Status: RUNNING (metadata not written yet)")

    print("="*60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_experiment_status.py <experiment_id>")
        print("Example: python check_experiment_status.py exp_001_baseline_production")
        sys.exit(1)

    experiment_id = sys.argv[1]
    check_experiment_status(experiment_id)
