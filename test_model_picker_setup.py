"""
Test model-picker setup: verify ArangoDB collections and basic queries.
"""

from promptguard.models.model_picker import ModelPicker, ModelMetadata, ModelPricing, ModelArchitecture, TopProvider
from promptguard.storage.arango_backend import ArangoDBBackend

def main():
    print("=" * 70)
    print("Model Picker Setup Test")
    print("=" * 70)

    # Initialize backend (creates collections)
    print("\n[1/5] Initializing ArangoDB backend...")
    try:
        backend = ArangoDBBackend()
        print("✓ Backend initialized successfully")
    except Exception as e:
        print(f"✗ Backend initialization failed: {e}")
        return 1

    # Verify collections exist
    print("\n[2/5] Verifying collections...")
    expected_collections = ["models", "sync_metadata", "deliberations", "turns"]
    for collection_name in expected_collections:
        if backend.db.has_collection(collection_name):
            print(f"✓ Collection '{collection_name}' exists")
        else:
            print(f"✗ Collection '{collection_name}' missing")
            return 1

    # Check indexes on models collection
    print("\n[3/5] Checking indexes on 'models' collection...")
    models_collection = backend.db.collection("models")
    indexes = models_collection.indexes()

    expected_index_fields = [
        ["openrouter_id"],
        ["provider"],
        ["frontier"],
        ["available"],
        ["free"],
        ["observer_framing_compatible"],
        ["structured_outputs"],
        ["last_synced"],
        ["created"],
        ["frontier_updated"],
        ["description"]
    ]

    found_indexes = {tuple(idx.get("fields", [])): idx["type"] for idx in indexes if idx.get("fields")}
    print(f"Found {len(found_indexes)} indexes")

    for fields in expected_index_fields:
        key = tuple(fields)
        if key in found_indexes:
            print(f"✓ Index on {fields} ({found_indexes[key]})")
        else:
            print(f"✗ Index on {fields} missing")

    # Test ModelPicker initialization
    print("\n[4/5] Testing ModelPicker initialization...")
    try:
        picker = ModelPicker(backend=backend)
        print("✓ ModelPicker initialized successfully")
    except Exception as e:
        print(f"✗ ModelPicker initialization failed: {e}")
        return 1

    # Insert a test model
    print("\n[5/5] Testing model insertion and query...")
    test_model = ModelMetadata(
        openrouter_id="test/model-1",
        provider="test",
        name="Test Model 1",
        created=1730000000,
        context_length=128000,
        description="Test model for verification",
        pricing=ModelPricing(prompt="0.0001", completion="0.0003"),
        architecture=ModelArchitecture(
            modality="text->text",
            input_modalities=["text"],
            output_modalities=["text"],
            tokenizer="Test"
        ),
        top_provider=TopProvider(
            context_length=128000,
            max_completion_tokens=4096,
            is_moderated=False
        ),
        supported_parameters=["temperature", "max_tokens"],
        frontier=True,
        available=True,
        tags=["test"]
    )

    try:
        # Insert test model
        doc = test_model.to_arango_doc()
        models_collection.insert(doc, overwrite=True)
        print("✓ Test model inserted")

        # Query for test model
        results = picker.query(frontier=True, provider="test", limit=10)
        if results and results[0].openrouter_id == "test/model-1":
            print(f"✓ Query returned test model: {results[0].name}")
        else:
            print("✗ Query did not return test model")
            return 1

        # Clean up test model
        models_collection.delete(test_model._key)
        print("✓ Test model cleaned up")

    except Exception as e:
        print(f"✗ Model insertion/query failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 70)
    print("✓ All tests passed - model-picker setup verified")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    exit(main())
