#!/usr/bin/env python3
"""
Populate ArangoDB models collection from config/model_configs.json.

This establishes database-driven model configuration instead of hardcoding
model names in test scripts.
"""

import json
import os
from pathlib import Path
from arango import ArangoClient


def populate_models():
    """Load model configs from JSON and populate ArangoDB collection."""

    # Load model configurations
    config_path = Path(__file__).parent.parent / "config" / "model_configs.json"
    with open(config_path) as f:
        config_data = json.load(f)

    models = config_data.get("models", [])

    print(f"Loaded {len(models)} models from config/model_configs.json")

    # Connect to ArangoDB
    client = ArangoClient(
        hosts=f"http://{os.getenv('ARANGODB_HOST', '192.168.111.125')}:{os.getenv('ARANGODB_PORT', '8529')}"
    )

    db = client.db(
        os.getenv("ARANGODB_DB", "PromptGuard"),
        username=os.getenv("ARANGODB_USER", "pgtest"),
        password=os.getenv("ARANGODB_PROMPTGUARD_PASSWORD")
    )

    # Ensure models collection exists
    if not db.has_collection("models"):
        db.create_collection("models")
        print("Created 'models' collection")

    models_collection = db.collection("models")

    # Mark which models are current/flagship/observer-compatible
    # Based on Instance 43's analysis:
    # - Current: claude-sonnet-4.5 (updated from obsolete 3.5)
    # - Flagship: claude-sonnet-4.5 (Anthropic's best)
    # - Observer compatible: All models that support observer framing
    # NOTE: Use "id" field from config (OpenRouter model name), not "name" (human-readable)

    current_models = {
        "anthropic/claude-sonnet-4.5",  # Current flagship
        "openai/gpt-4o",  # OpenAI flagship
        "google/gemini-2.5-flash-preview-09-2025",  # Google current
        "deepseek/deepseek-v3.1-terminus",  # Budget current
    }

    flagship_models = {
        "anthropic/claude-sonnet-4.5",
        "openai/gpt-4o",
        "google/gemini-2.5-flash-preview-09-2025",
    }

    # Observer framing works on all models in Instance 17 validation
    # but some models have better results
    observer_compatible = {
        "anthropic/claude-sonnet-4.5",
        "openai/gpt-4o",
        "openai/gpt-5-codex",
        "deepseek/deepseek-v3.1-terminus",
        "deepseek/deepseek-v3.2-exp",
        "google/gemini-2.5-flash-preview-09-2025",
    }

    inserted_count = 0
    updated_count = 0

    for model in models:
        # Add metadata flags - use "id" field (OpenRouter model name)
        model_id = model["id"]
        model_doc = {
            **model,
            "is_current": model_id in current_models,
            "is_flagship": model_id in flagship_models,
            "observer_compatible": model_id in observer_compatible,
            "notes": model.get("notes", ""),
        }

        # Use model id as _key for idempotent inserts
        # ArangoDB keys: alphanumeric, dash, underscore only
        import re
        model_doc["_key"] = re.sub(r'[^a-zA-Z0-9_-]', '_', model_id)

        try:
            # Try to insert, update if already exists
            if models_collection.has(model_doc["_key"]):
                models_collection.update(model_doc)
                updated_count += 1
            else:
                models_collection.insert(model_doc)
                inserted_count += 1

        except Exception as e:
            print(f"Error inserting {model['id']}: {e}")

    print(f"\nCompleted:")
    print(f"  Inserted: {inserted_count}")
    print(f"  Updated: {updated_count}")
    print(f"  Total: {len(models)}")

    # Query to verify
    print("\nCurrent/Flagship models:")
    print("=" * 80)

    aql = """
    FOR m IN models
        FILTER m.is_current == true OR m.is_flagship == true
        SORT m.input_price_per_1m ASC
        RETURN {
            id: m.id,
            name: m.name,
            family: m.family,
            is_current: m.is_current,
            is_flagship: m.is_flagship,
            observer_compatible: m.observer_compatible,
            input_cost: m.input_price_per_1m,
            output_cost: m.output_price_per_1m
        }
    """

    cursor = db.aql.execute(aql)
    current_flagship = list(cursor)

    for m in current_flagship:
        flags = []
        if m.get("is_current"):
            flags.append("CURRENT")
        if m.get("is_flagship"):
            flags.append("FLAGSHIP")
        if m.get("observer_compatible"):
            flags.append("OBSERVER")

        flag_str = f"[{', '.join(flags)}]" if flags else ""
        print(f"{m['id']} {flag_str}")
        print(f"  Display: {m['name']}")
        print(f"  ${m['input_cost']:.2f} in / ${m['output_cost']:.2f} out per 1M tokens")


if __name__ == "__main__":
    populate_models()
