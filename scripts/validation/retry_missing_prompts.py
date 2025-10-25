"""
Retry missing prompts for exp_001_baseline_production.

Identifies the 28 prompts not yet processed and runs them through the baseline pipeline.
"""

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from promptguard.storage.arango_backend import ArangoDBBackend
from scripts.validation.common.errors import EvaluationError
from scripts.validation.experiment_01_baseline import (
    BaselineEvaluationStage,
    ComplianceClassificationStage,
    ProcessingFailureHandler
)
from scripts.validation.utils.arango_client import ArangoConnection, ArangoSink


def load_prompts_from_file(filename: str, dataset_name: str) -> list[dict[str, Any]]:
    """Load prompts from a dataset file."""
    datasets_dir = Path(project_root) / "datasets"
    filepath = datasets_dir / filename
    
    with open(filepath) as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'prompts' in data:
        prompts = data['prompts']
    else:
        prompts = data
    
    result = []
    for item in prompts:
        if 'content' in item and isinstance(item['content'], dict):
            text = item['content'].get('prompt', '')
        else:
            text = item.get('prompt', item.get('text', ''))
        
        result.append({
            'prompt_text': text,
            'label': item.get('label', 'unknown'),
            'source_dataset': dataset_name,
            'stride_number': 0
        })
    
    return result


def get_missing_prompts(experiment_id: str) -> list[dict[str, Any]]:
    """
    Find prompts from source files that haven't been processed yet.
    
    Returns:
        List of missing prompt dictionaries
    """
    # Load all prompts from files
    all_prompts = []
    all_prompts.extend(load_prompts_from_file('benign_malicious.json', 'benign_malicious'))
    all_prompts.extend(load_prompts_from_file('or_bench_sample.json', 'or_bench'))
    all_prompts.extend(load_prompts_from_file('extractive_prompts_dataset.json', 'extractive'))
    
    print(f"Loaded {len(all_prompts)} prompts from source files")
    
    # Get processed prompt texts from database
    storage = ArangoDBBackend()
    query = '''
    FOR doc IN baseline_responses
        FILTER doc.experiment_id == @exp_id
        RETURN DISTINCT doc.prompt_text
    '''
    cursor = storage.db.aql.execute(query, bind_vars={'exp_id': experiment_id})
    processed_texts = set(cursor)
    
    print(f"Found {len(processed_texts)} unique processed prompts in database")
    
    # Find missing prompts (deduplicate by text)
    seen = set()
    missing = []
    for prompt in all_prompts:
        text = prompt['prompt_text']
        if text not in processed_texts and text not in seen:
            missing.append(prompt)
            seen.add(text)
    
    return missing


def main():
    """Retry missing prompts for exp_001_baseline_production."""
    experiment_id = "exp_001_baseline_production"
    target_model = "anthropic/claude-sonnet-4.5"
    observer_model = "anthropic/claude-3-haiku"
    
    print("=" * 60)
    print("Retry Missing Prompts - Experiment 1")
    print("=" * 60)
    print(f"Experiment ID: {experiment_id}")
    print(f"Target Model: {target_model}")
    print(f"Observer Model: {observer_model}")
    print()
    
    # Find missing prompts
    print("Finding missing prompts...")
    missing_prompts = get_missing_prompts(experiment_id)
    
    if not missing_prompts:
        print("✓ All prompts already processed!")
        return
    
    print(f"Found {len(missing_prompts)} missing prompts")
    print()
    
    # Show breakdown by dataset
    from collections import Counter
    datasets = Counter(p['source_dataset'] for p in missing_prompts)
    print("Missing by dataset:")
    for dataset, count in sorted(datasets.items()):
        print(f"  {dataset}: {count}")
    print()
    
    # Initialize components
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
        print("✗ Compliance prompt not found in database")
        sys.exit(1)
    
    compliance_prompt_id = compliance_prompt_ids[0]
    
    # Initialize pipeline stages
    baseline_stage = BaselineEvaluationStage(target_model, experiment_id)
    classification_stage = ComplianceClassificationStage(observer_model, compliance_prompt_id)
    failure_handler = ProcessingFailureHandler(experiment_id, connection)
    
    # Initialize sinks
    baseline_sink = ArangoSink("baseline_responses", connection)
    prompts_sink = ArangoSink("prompts", connection)
    
    # Process missing prompts
    start_time = datetime.now(timezone.utc)
    processed_count = 0
    failed_count = 0
    total_cost = 0.0
    
    print(f"Processing {len(missing_prompts)} missing prompts...")
    print()
    
    for i, prompt in enumerate(missing_prompts, 1):
        try:
            # Generate new prompt_id for this run
            from uuid import uuid4
            prompt['prompt_id'] = str(uuid4())
            
            # Store prompt in database
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
            
            if i % 5 == 0 or i == len(missing_prompts):
                print(f"  Progress: {i}/{len(missing_prompts)} "
                      f"({processed_count} processed, {failed_count} failed, "
                      f"${total_cost:.2f} cost)")
        
        except EvaluationError as e:
            failure_handler.handle_failure(
                prompt["prompt_id"],
                e,
                "baseline_collection_retry",
                target_model
            )
            failed_count += 1
        
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            failure_handler.handle_failure(
                prompt["prompt_id"],
                e,
                "baseline_collection_retry",
                target_model
            )
            failed_count += 1
    
    # Print summary
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()
    
    print()
    print("=" * 60)
    print("✓ Retry Complete!")
    print(f"  Processed: {processed_count} prompts")
    print(f"  Failed: {failed_count} prompts")
    print(f"  Total Cost: ${total_cost:.2f}")
    print(f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print("=" * 60)
    
    # Verify final count
    storage = ArangoDBBackend()
    query = '''
    FOR doc IN baseline_responses
        FILTER doc.experiment_id == @exp_id
        RETURN DISTINCT doc.prompt_text
    '''
    cursor = storage.db.aql.execute(query, bind_vars={'exp_id': experiment_id})
    final_count = len(list(cursor))
    
    print()
    print(f"Final unique prompts processed: {final_count}")
    print(f"Expected total: 647 (unique prompts in datasets)")
    if final_count == 647:
        print("✓ Experiment 1 baseline collection COMPLETE!")
    else:
        print(f"⚠ Still missing {647 - final_count} prompts")


if __name__ == "__main__":
    main()
