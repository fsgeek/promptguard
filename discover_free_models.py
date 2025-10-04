"""Discover available free models from OpenRouter."""
import asyncio
import httpx
import os
import json
from typing import List, Dict


async def get_available_models() -> List[Dict]:
    """Query OpenRouter for available models."""
    api_key = os.getenv("OPENROUTER_API_KEY")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching models: {e}")
            return None


async def main():
    print("Querying OpenRouter for available models...")

    data = await get_available_models()

    if not data:
        print("Failed to fetch models")
        return

    models = data.get('data', [])
    print(f"\nTotal models available: {len(models)}")

    # Filter for free models
    free_models = []
    for model in models:
        model_id = model.get('id', '')
        pricing = model.get('pricing', {})

        # Check if it's a free model (prompt and completion costs are 0)
        prompt_cost = float(pricing.get('prompt', '999'))
        completion_cost = float(pricing.get('completion', '999'))

        if prompt_cost == 0 and completion_cost == 0:
            free_models.append({
                'id': model_id,
                'name': model.get('name', 'Unknown'),
                'context_length': model.get('context_length', 0),
                'architecture': model.get('architecture', {}),
                'top_provider': model.get('top_provider', {})
            })

    print(f"\n{'='*80}")
    print(f"FREE MODELS AVAILABLE: {len(free_models)}")
    print(f"{'='*80}\n")

    # Group by provider
    by_provider = {}
    for model in free_models:
        provider = model['top_provider'].get('name', 'Unknown')
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(model)

    for provider, provider_models in sorted(by_provider.items()):
        print(f"\n{provider} ({len(provider_models)} models):")
        for model in sorted(provider_models, key=lambda x: x['context_length'], reverse=True):
            print(f"  {model['id']:60s} ctx={model['context_length']:>6d}")

    # Save to JSON for config
    output = {
        'updated_at': data.get('updated_at', 'unknown'),
        'total_models': len(models),
        'free_models': [m['id'] for m in sorted(free_models, key=lambda x: x['context_length'], reverse=True)],
        'free_models_detail': free_models
    }

    with open('config/free_models.json', 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n\nSaved to config/free_models.json")

    # Suggest models for testing
    print(f"\n{'='*80}")
    print("RECOMMENDED FOR TESTING (highest context length):")
    print(f"{'='*80}")
    top_free = sorted(free_models, key=lambda x: x['context_length'], reverse=True)[:5]
    for model in top_free:
        print(f"  {model['id']:60s} ctx={model['context_length']:>6d}")


if __name__ == "__main__":
    asyncio.run(main())
