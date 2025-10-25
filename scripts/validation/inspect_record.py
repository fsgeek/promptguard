"""
Inspect a single record to see all fields.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.arango_client import ArangoConnection


def inspect_record(experiment_id: str):
    """Inspect a single record to see all fields."""
    connection = ArangoConnection()
    db = connection.get_database()

    query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    LIMIT 1
    RETURN r
    """

    cursor = db.aql.execute(query, bind_vars={"exp_id": experiment_id})
    records = list(cursor)

    if not records:
        print("No records found")
        return

    record = records[0]
    print("Fields in baseline_responses record:")
    print("="*60)

    for key in sorted(record.keys()):
        value = record[key]
        if isinstance(value, str) and len(value) > 100:
            value_display = value[:100] + "..."
        else:
            value_display = value
        print(f"  {key}: {value_display}")

    # Also check prompts collection
    print("\n\nFields in prompts collection:")
    print("="*60)

    prompt_query = """
    FOR p IN prompts
    FILTER p.experiment_id == @exp_id
    LIMIT 1
    RETURN p
    """

    cursor = db.aql.execute(prompt_query, bind_vars={"exp_id": experiment_id})
    prompt_records = list(cursor)

    if prompt_records:
        prompt = prompt_records[0]
        for key in sorted(prompt.keys()):
            value = prompt[key]
            if isinstance(value, str) and len(value) > 100:
                value_display = value[:100] + "..."
            else:
                value_display = value
            print(f"  {key}: {value_display}")
    else:
        print("No prompts records found")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_record.py <experiment_id>")
        sys.exit(1)

    inspect_record(sys.argv[1])
