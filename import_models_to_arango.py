#!/usr/bin/env python3
"""
Import model metadata into ArangoDB's models collection.

Data sources:
1. config/openrouter_frontier_models.json - 148 frontier models
2. config/model_registry_template.json - Curated models with validation data
3. BASELINE_OBSERVER_FRAMING_COMPATIBILITY.md - Experimental results

Database: PromptGuard at 192.168.111.125:8529
Username: pgtest, Password: ARANGODB_PROMPTGUARD_PASSWORD
Target collection: models (already created with indexes)
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from arango import ArangoClient

# Database connection
DB_HOST = "192.168.111.125"
DB_PORT = 8529
DB_NAME = "PromptGuard"
DB_USER = "pgtest"
DB_PASSWORD = os.environ.get("ARANGODB_PROMPTGUARD_PASSWORD")

# Data paths
OPENROUTER_PATH = "config/openrouter_frontier_models.json"
REGISTRY_PATH = "config/model_registry_template.json"

# Observer framing compatibility from experimental results
OBSERVER_FRAMING_COMPAT = {
    "openai/gpt-4.1": "confirmed_yes",  # +13.9%, 0 failures
    "anthropic/claude-sonnet-4.5": "confirmed_yes",  # validated
    "deepseek/deepseek-r1": "likely_yes",  # +7.5%, 12.5% silent failures
    "meta-llama/llama-3.1-405b-instruct": "confirmed_no",  # meta-refusal, 22% failures
}


def classify_model_type(org: str, model_id: str, description: str) -> str:
    """Classify model type from organization and description."""
    model_id_lower = model_id.lower()
    desc_lower = description.lower()

    # Frontier reasoning models
    if any(x in model_id_lower or x in desc_lower for x in ["deepseek-r1", "qwq", "thinking", "reasoning"]):
        return "frontier_reasoning"

    # Open source base models (unaligned)
    if any(x in model_id_lower for x in [":base", "-base"]):
        return "open_source_base"

    # Open source aligned models
    open_source_orgs = ["meta", "mistral", "qwen", "alibaba"]
    if org in open_source_orgs:
        if any(x in model_id_lower or x in desc_lower for x in ["instruct", "chat", "aligned"]):
            return "open_source_aligned"
        return "open_source_base"

    # Frontier aligned (default for commercial orgs)
    return "frontier_aligned"


def parse_openrouter_models() -> Dict[str, dict]:
    """Parse OpenRouter frontier models JSON."""
    print(f"Parsing {OPENROUTER_PATH}...")
    with open(OPENROUTER_PATH) as f:
        data = json.load(f)

    models = {}
    for org, org_models in data.items():
        for m in org_models:
            model_id = m["id"]

            # Extract organization from id if not explicit
            org_name = m.get("organization", org)

            models[model_id] = {
                "_key": model_id.replace("/", "_"),
                "name": m["name"],
                "organization": org_name,
                "model_type": classify_model_type(org_name, model_id, m.get("description", "")),
                "release_date": m.get("created"),
                "cost_per_1m_input": m.get("prompt_cost_per_1k", 0) * 1000,
                "cost_per_1m_output": m.get("completion_cost_per_1k", 0) * 1000,
                "context_window": m.get("context_length", 0),
                "model_description": m.get("description", ""),
                "training_characteristics": [],
                "known_capabilities": [],
                "observer_framing_compatible": "unknown",
                "known_limitations": [],
                "deployment_notes": "",
                "deprecated": False,
                "metadata": {
                    "added_date": datetime.now(timezone.utc).isoformat(),
                    "last_tested": None,
                    "source": "openrouter_frontier_models"
                }
            }

    print(f"  Parsed {len(models)} models from OpenRouter")
    return models


def parse_registry_models() -> Dict[str, dict]:
    """Parse model registry template JSON."""
    print(f"Parsing {REGISTRY_PATH}...")
    with open(REGISTRY_PATH) as f:
        data = json.load(f)

    models = {}
    for m in data["models"]:
        model_id = m["model_id"]

        # Skip template entries
        if "FILL_IN" in model_id:
            continue

        models[model_id] = {
            "_key": model_id.replace("/", "_"),
            "name": m["model_name"],
            "organization": m["organization"],
            "model_type": m["model_type"],
            "release_date": m["release_date"],
            "cost_per_1m_input": m["cost_per_1m_input"] * 1000,
            "cost_per_1m_output": m["cost_per_1m_output"] * 1000,
            "context_window": m["context_window"],
            "model_description": m["model_description"],
            "training_characteristics": m["training_characteristics"],
            "known_capabilities": m["known_capabilities"],
            "observer_framing_compatible": m["observer_framing_compatible"],
            "known_limitations": m["known_limitations"],
            "deployment_notes": m["deployment_notes"],
            "deprecated": m["deprecated"],
            "metadata": {
                "added_date": datetime.now(timezone.utc).isoformat(),
                "last_tested": m.get("release_date"),
                "source": "model_registry_template"
            }
        }

    print(f"  Parsed {len(models)} models from registry")
    return models


def merge_models(openrouter_models: Dict[str, dict], registry_models: Dict[str, dict]) -> Dict[str, dict]:
    """Merge models, with registry overriding OpenRouter where both exist."""
    print("\nMerging models...")

    # Start with all OpenRouter models
    merged = openrouter_models.copy()

    # Override with registry models
    for model_id, registry_data in registry_models.items():
        if model_id in merged:
            print(f"  Override: {model_id}")
            # Merge metadata sources
            merged[model_id] = registry_data
            merged[model_id]["metadata"]["source"] = "model_registry_template,openrouter_frontier_models"
        else:
            print(f"  Add: {model_id}")
            merged[model_id] = registry_data

    # Apply observer framing compatibility
    for model_id, compat in OBSERVER_FRAMING_COMPAT.items():
        if model_id in merged:
            merged[model_id]["observer_framing_compatible"] = compat
            print(f"  Observer framing: {model_id} -> {compat}")

    print(f"\nTotal merged models: {len(merged)}")
    return merged


def import_to_arango(models: Dict[str, dict]):
    """Import models into ArangoDB."""
    print(f"\nConnecting to ArangoDB at {DB_HOST}:{DB_PORT}...")

    if not DB_PASSWORD:
        raise ValueError("ARANGODB_PROMPTGUARD_PASSWORD environment variable not set")

    # Connect to ArangoDB
    client = ArangoClient(hosts=f"http://{DB_HOST}:{DB_PORT}")
    db = client.db(DB_NAME, username=DB_USER, password=DB_PASSWORD)

    # Get models collection
    collection = db.collection("models")

    # Import models
    print(f"\nImporting {len(models)} models...")
    inserted = 0
    updated = 0
    errors = 0

    for model_id, model_data in models.items():
        try:
            # Try insert, if exists then update
            try:
                collection.insert(model_data)
                inserted += 1
            except Exception as e:
                if "unique constraint violated" in str(e) or "duplicate" in str(e).lower():
                    # Update existing
                    collection.update(model_data)
                    updated += 1
                else:
                    raise
        except Exception as e:
            print(f"  ERROR importing {model_id}: {e}")
            errors += 1

    print(f"\n✓ Imported: {inserted} new, {updated} updated, {errors} errors")

    # Generate statistics
    print("\n=== IMPORT SUMMARY ===")

    # Count by organization
    org_counts = {}
    for model in models.values():
        org = model["organization"]
        org_counts[org] = org_counts.get(org, 0) + 1

    print("\nModels by organization:")
    for org, count in sorted(org_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {org}: {count}")

    # Count by model_type
    type_counts = {}
    for model in models.values():
        mtype = model["model_type"]
        type_counts[mtype] = type_counts.get(mtype, 0) + 1

    print("\nModels by type:")
    for mtype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {mtype}: {count}")

    # Count by observer_framing_compatible
    compat_counts = {}
    for model in models.values():
        compat = model["observer_framing_compatible"]
        compat_counts[compat] = compat_counts.get(compat, 0) + 1

    print("\nObserver framing compatibility:")
    for compat, count in sorted(compat_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {compat}: {count}")

    # Verify priority models exist
    print("\nPriority models:")
    priority_models = [
        "moonshotai/kimi-k2-0905",
        "anthropic/claude-sonnet-4.5",
        "openai/gpt-5-codex",
        "google/gemini-2.5-flash-preview",
        "deepseek/deepseek-r1"
    ]
    for model_id in priority_models:
        if model_id in models:
            print(f"  ✓ {model_id}")
        else:
            print(f"  ✗ {model_id} (NOT FOUND)")

    print("\n=== IMPORT COMPLETE ===")


def main():
    """Main import process."""
    print("=== MODEL METADATA IMPORT ===\n")

    # Parse data sources
    openrouter_models = parse_openrouter_models()
    registry_models = parse_registry_models()

    # Merge
    merged_models = merge_models(openrouter_models, registry_models)

    # Import
    import_to_arango(merged_models)


if __name__ == "__main__":
    main()
