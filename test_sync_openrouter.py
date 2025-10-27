"""
Test sync_from_openrouter() with real OpenRouter API.

Validates:
1. API call succeeds
2. Models are inserted into database
3. Stats are returned correctly
4. Manual attributes preserved on re-sync
"""

import os
from promptguard.models.model_picker import ModelPicker

def test_sync():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        return 1

    print("=" * 70)
    print("Testing sync_from_openrouter()")
    print("=" * 70)

    picker = ModelPicker()

    print("\n[1/3] Calling OpenRouter API...")
    try:
        stats = picker.sync_from_openrouter(api_key)
        print(f"✓ Sync completed in {stats['duration_seconds']:.2f}s")
        print(f"  - Added: {stats['models_added']}")
        print(f"  - Updated: {stats['models_updated']}")
        print(f"  - Deprecated: {stats['models_deprecated']}")
        print(f"  - Errors: {len(stats['errors'])}")

        if stats['errors']:
            print("\nErrors:")
            for err in stats['errors'][:5]:  # Show first 5
                print(f"  - {err['error_type']}: {err['message']}")
    except Exception as e:
        print(f"✗ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n[2/3] Querying synced models...")
    try:
        models = picker.query(available=True, limit=5)
        print(f"✓ Found {len(models)} models")
        for model in models:
            print(f"  - {model.openrouter_id} ({model.provider}) - ${model.pricing.prompt}/tok")
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return 1

    print("\n[3/3] Testing manual attribute preservation...")
    try:
        # Mark first model as frontier
        if models:
            test_model = models[0]
            test_model.frontier = True
            test_model.tags = ["test-frontier"]

            # Update in DB
            doc = test_model.to_arango_doc()
            picker.backend.db.collection("models").update(doc)
            print(f"✓ Marked {test_model.openrouter_id} as frontier")

            # Re-sync
            print("\n  Re-syncing to test preservation...")
            stats2 = picker.sync_from_openrouter(api_key)
            print(f"  ✓ Re-sync: {stats2['models_updated']} updated")

            # Verify frontier preserved
            reloaded = picker.get_by_id(test_model.openrouter_id)
            if reloaded.frontier and "test-frontier" in reloaded.tags:
                print(f"  ✓ Frontier flag and tags preserved")
            else:
                print(f"  ✗ Manual attributes NOT preserved (frontier={reloaded.frontier}, tags={reloaded.tags})")
                return 1
    except Exception as e:
        print(f"✗ Preservation test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 70)
    print("✓ All tests passed")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    exit(test_sync())
