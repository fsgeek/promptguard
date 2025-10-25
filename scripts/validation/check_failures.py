"""
Analyze processing failures in detail.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.arango_client import ArangoConnection


def analyze_failures(experiment_id: str):
    """Analyze processing failures."""
    connection = ArangoConnection()
    db = connection.get_database()

    query = """
    FOR f IN processing_failures
    FILTER f.experiment_id == @exp_id
    RETURN {
        prompt_id: f.prompt_id,
        error_type: f.error_type,
        error_message: f.error_message,
        stage: f.stage,
        timestamp: f.timestamp
    }
    """

    cursor = db.aql.execute(query, bind_vars={"exp_id": experiment_id})
    failures = list(cursor)

    print(f"Total failures: {len(failures)}")
    print()

    for i, failure in enumerate(failures, 1):
        print(f"Failure {i}:")
        print(f"  Prompt ID: {failure['prompt_id']}")
        print(f"  Error: {failure['error_type']}")
        print(f"  Message: {failure['error_message']}")
        print(f"  Stage: {failure['stage']}")
        print(f"  Timestamp: {failure['timestamp']}")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_failures.py <experiment_id>")
        sys.exit(1)

    analyze_failures(sys.argv[1])
