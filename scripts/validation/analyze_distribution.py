"""
Analyze classification distribution and look for anomalies.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.arango_client import ArangoConnection


def analyze_distribution(experiment_id: str):
    """Analyze classification distribution by dataset."""
    connection = ArangoConnection()
    db = connection.get_database()

    # Get distribution by source_dataset
    query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    COLLECT dataset = r.source_dataset, classification = r.classification WITH COUNT INTO count
    RETURN {dataset: dataset, classification: classification, count: count}
    """

    cursor = db.aql.execute(query, bind_vars={"exp_id": experiment_id})
    results = list(cursor)

    # Organize by dataset
    datasets = {}
    for item in results:
        dataset = item['dataset']
        if dataset not in datasets:
            datasets[dataset] = {}
        datasets[dataset][item['classification']] = item['count']

    print("Classification Distribution by Dataset:")
    print("="*60)

    for dataset, dist in datasets.items():
        total = sum(dist.values())
        print(f"\n{dataset} ({total} prompts):")
        for classification in ['refuse', 'borderline', 'comply']:
            count = dist.get(classification, 0)
            pct = count / total * 100 if total > 0 else 0
            print(f"  {classification:12s}: {count:3d} ({pct:5.1f}%)")

    # Look for anomalies in scores
    print("\n\nCompliance Score Distribution:")
    print("="*60)

    score_query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    COLLECT score_bucket = FLOOR(r.compliance_score * 10) / 10 WITH COUNT INTO count
    RETURN {score: score_bucket, count: count}
    """

    cursor = db.aql.execute(score_query, bind_vars={"exp_id": experiment_id})
    score_dist = sorted(list(cursor), key=lambda x: x['score'])

    for item in score_dist:
        score = item['score']
        count = item['count']
        bar = '█' * (count // 10)
        print(f"  {score:.1f}-{score+0.1:.1f}: {count:3d} {bar}")

    # Check for specific ground truth labels vs predictions
    print("\n\nGround Truth vs Prediction (sample):")
    print("="*60)

    sample_query = """
    FOR r IN baseline_responses
    FILTER r.experiment_id == @exp_id
    SORT RAND()
    LIMIT 10
    RETURN {
        dataset: r.source_dataset,
        ground_truth: r.label,
        classification: r.classification,
        score: r.compliance_score,
        prompt_preview: SUBSTRING(r.prompt_text, 0, 60)
    }
    """

    cursor = db.aql.execute(sample_query, bind_vars={"exp_id": experiment_id})
    samples = list(cursor)

    for sample in samples:
        print(f"\nDataset: {sample['dataset']}")
        print(f"  Ground Truth: {sample['ground_truth']}")
        print(f"  Predicted: {sample['classification']} (score: {sample['score']:.2f})")
        print(f"  Prompt: {sample['prompt_preview']}...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_distribution.py <experiment_id>")
        sys.exit(1)

    analyze_distribution(sys.argv[1])
