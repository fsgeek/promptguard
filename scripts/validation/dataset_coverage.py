"""
Check how many prompts were processed from each dataset.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.arango_client import ArangoConnection


def check_coverage(experiment_id: str):
    """Check dataset coverage."""
    connection = ArangoConnection()
    db = connection.get_database()

    # Count by source_dataset
    query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    COLLECT dataset = r.source_dataset WITH COUNT INTO count
    RETURN {dataset: dataset, count: count}
    """

    cursor = db.aql.execute(query, bind_vars={"exp_id": experiment_id})
    results = list(cursor)

    print("Dataset Coverage:")
    print("="*60)

    expected = {
        "benign_malicious": 500,
        "or_bench": 100,
        "extractive": 80
    }

    total_expected = sum(expected.values())
    total_processed = sum(r['count'] for r in results)

    for item in results:
        dataset = item['dataset']
        count = item['count']
        exp_count = expected.get(dataset, 0)
        pct = count / exp_count * 100 if exp_count > 0 else 0
        print(f"  {dataset:20s}: {count:3d} / {exp_count:3d} ({pct:5.1f}%)")

    print(f"\n  Total: {total_processed} / {total_expected} ({total_processed/total_expected*100:.1f}%)")

    # Check failures by dataset
    print("\n\nFailures by Dataset:")
    print("="*60)

    failure_query = """
    FOR f IN processing_failures
    FILTER f.experiment_id == @exp_id
    LET prompt = FIRST(
        FOR p IN prompts
        FILTER p.prompt_id == f.prompt_id
        RETURN p
    )
    COLLECT dataset = prompt.source_dataset WITH COUNT INTO count
    RETURN {dataset: dataset, count: count}
    """

    cursor = db.aql.execute(failure_query, bind_vars={"exp_id": experiment_id})
    failure_results = list(cursor)

    if failure_results:
        for item in failure_results:
            dataset = item['dataset']
            count = item['count']
            print(f"  {dataset:20s}: {count:3d} failures")
    else:
        print("  No failures recorded")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dataset_coverage.py <experiment_id>")
        sys.exit(1)

    check_coverage(sys.argv[1])
