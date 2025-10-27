"""
Seed initial frontier models from config/fire_circle_models.json.

This provides minimal working data for MVP without requiring OpenRouter sync.
"""

import json
from datetime import datetime

from promptguard.models.model_picker import (
    ModelMetadata,
    ModelPricing,
    ModelArchitecture,
    TopProvider,
)
from promptguard.storage.arango_backend import ArangoDBBackend


def seed_frontier_models():
    """Seed frontier models from fire_circle_models.json."""

    print("=" * 70)
    print("Seeding Frontier Models from config/fire_circle_models.json")
    print("=" * 70)

    # Load config
    print("\n[1/4] Loading fire_circle_models.json...")
    with open("config/fire_circle_models.json", "r") as f:
        config = json.load(f)

    available_models = [m for m in config["models"] if m["status"] == "available"]
    print(f"✓ Found {len(available_models)} available frontier models")

    # Initialize backend
    print("\n[2/4] Connecting to ArangoDB...")
    backend = ArangoDBBackend()
    models_collection = backend.db.collection("models")
    print("✓ Connected successfully")

    # Seed models
    print("\n[3/4] Seeding models...")
    seeded_count = 0
    updated_count = 0

    for model_config in available_models:
        model_id = model_config["id"]
        provider = model_id.split("/")[0]

        # Create minimal ModelMetadata
        # Note: Real implementation would fetch from OpenRouter API
        metadata = ModelMetadata(
            openrouter_id=model_id,
            provider=provider,
            name=f"{provider.title()}: {model_id.split('/')[1].replace('-', ' ').title()}",
            created=int(datetime(2025, 10, 24).timestamp()),  # Config last_updated date
            context_length=128000,  # Default assumption for frontier models
            description=f"Frontier model from {provider}",
            pricing=ModelPricing(
                prompt=str(model_config["pricing"]["input_per_mtok"] / 1_000_000),
                completion=str(model_config["pricing"]["output_per_mtok"] / 1_000_000),
            ),
            architecture=ModelArchitecture(
                modality="text->text",
                input_modalities=["text"],
                output_modalities=["text"],
                tokenizer=provider.title(),
            ),
            top_provider=TopProvider(
                context_length=128000,
                max_completion_tokens=4096,
                is_moderated=False,
            ),
            supported_parameters=["temperature", "max_tokens", "top_p"],
            frontier=True,  # Mark as frontier
            available=True,
            tags=["seeded", "fire-circle"],
        )

        # Insert or update
        doc = metadata.to_arango_doc()
        try:
            models_collection.insert(doc, overwrite=True)
            if models_collection.has(metadata._key):
                updated_count += 1
            else:
                seeded_count += 1
            print(f"  ✓ {model_id}")
        except Exception as e:
            print(f"  ✗ {model_id}: {e}")

    print(f"\n✓ Seeded {seeded_count} new models, updated {updated_count} existing")

    # Verify seeding
    print("\n[4/4] Verifying seeded data...")
    query = """
    FOR m IN models
        FILTER m.frontier == true
        SORT m.openrouter_id
        RETURN {id: m.openrouter_id, provider: m.provider, name: m.name}
    """

    cursor = backend.db.aql.execute(query)
    results = list(cursor)

    print(f"✓ Found {len(results)} frontier models in database:")
    for result in results:
        print(f"  - {result['id']} ({result['provider']})")

    print("\n" + "=" * 70)
    print("✓ Seeding complete")
    print("=" * 70)
    print("\nUsage example:")
    print("  from promptguard.models import ModelPicker")
    print("  picker = ModelPicker()")
    print("  models = picker.query(available=True, frontier=True, limit=3)")
    print("  print([m.openrouter_id for m in models])")
    print("=" * 70)


if __name__ == "__main__":
    seed_frontier_models()
