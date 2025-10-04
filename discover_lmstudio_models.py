"""
Discover available models from LM Studio.

Queries the LM Studio server to find what models are currently loaded and available.
"""

import asyncio
import httpx
import json
from typing import List, Dict


async def get_lmstudio_models(base_url: str = "http://localhost:1234/v1") -> List[Dict]:
    """
    Query LM Studio for available models.

    Args:
        base_url: LM Studio base URL (default: http://localhost:1234/v1)

    Returns:
        List of model dictionaries with id, object, owned_by, etc.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{base_url}/models",
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except Exception as e:
            raise RuntimeError(f"Failed to query LM Studio models: {e}")


async def main():
    print("Discovering models from LM Studio...")

    # Try common LM Studio URLs
    urls_to_try = [
        "http://localhost:1234/v1",
        "http://192.168.111.125:1234/v1",  # Tony's Windows host
    ]

    models = None
    active_url = None

    for url in urls_to_try:
        try:
            print(f"\nTrying: {url}")
            models = await get_lmstudio_models(url)
            active_url = url
            print(f"✓ Connected successfully")
            break
        except Exception as e:
            print(f"✗ Failed: {e}")

    if not models:
        print("\n❌ Could not connect to LM Studio.")
        print("\nMake sure:")
        print("1. LM Studio is running")
        print("2. Local server is started (in LM Studio's 'Local Server' tab)")
        print("3. A model is loaded")
        return

    print(f"\n{'='*80}")
    print(f"AVAILABLE MODELS ({len(models)} found)")
    print(f"{'='*80}")
    print(f"Server: {active_url}\n")

    for i, model in enumerate(models, 1):
        model_id = model.get('id', 'Unknown')
        owned_by = model.get('owned_by', 'Unknown')

        print(f"{i}. {model_id}")
        print(f"   Owner: {owned_by}")

        # Some LM Studio versions include additional metadata
        if 'created' in model:
            from datetime import datetime
            created = datetime.fromtimestamp(model['created'])
            print(f"   Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")

        print()

    # Export for use in evaluate_local_models.py
    model_ids = [m.get('id', '') for m in models]

    print(f"{'='*80}")
    print("FOR USE IN evaluate_local_models.py:")
    print(f"{'='*80}\n")
    print("MODEL_CANDIDATES = [")
    for model_id in model_ids:
        print(f'    "{model_id}",')
    print("]\n")

    # Save to file
    output = {
        'server_url': active_url,
        'discovered_at': asyncio.get_event_loop().time(),
        'models': models,
        'model_ids': model_ids
    }

    with open('lmstudio_models.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✓ Saved to lmstudio_models.json")


if __name__ == "__main__":
    asyncio.run(main())
