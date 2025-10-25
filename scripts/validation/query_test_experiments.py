"""Query test experiments from database."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.arango_client import ArangoConnection

conn = ArangoConnection()
db = conn.get_database()

# Query for any recent experiments
query = """
FOR e IN experiments
FILTER e.experiment_id LIKE 'test%'
SORT e.start_timestamp DESC
LIMIT 5
RETURN e
"""

cursor = db.aql.execute(query)
experiments = list(cursor)

if experiments:
    print(f"Found {len(experiments)} test experiment(s):\n")
    for exp in experiments:
        print(f"  experiment_id: {exp.get('experiment_id')}")
        print(f"  experiment_label: {exp.get('experiment_label')}")
        print(f"  target_model: {exp.get('target_model')}")
        print(f"  observer_model: {exp.get('observer_model')}")
        print(f"  total_prompts: {exp.get('total_prompts')}")
        print(f"  total_cost: ${exp.get('total_cost', 0.0):.2f}")
        print(f"  stages_completed: {exp.get('stages_completed')}")
        print(f"  start_timestamp: {exp.get('start_timestamp')}")
        print(f"  end_timestamp: {exp.get('end_timestamp')}")

        # Verify all required fields
        required = [
            'experiment_id', 'experiment_label', 'target_model', 'observer_model',
            'start_timestamp', 'end_timestamp', 'total_prompts', 'total_cost',
            'stages_completed', 'compliance_prompt_id', 'pre_eval_prompt_id',
            'post_eval_prompt_id', 'model_version_change_decision'
        ]
        missing = [f for f in required if f not in exp]
        if missing:
            print(f"  ⚠ Missing fields: {missing}")
        else:
            print(f"  ✓ All required fields present")
        print()
else:
    print("No test experiments found in database")
