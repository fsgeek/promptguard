"""
Dynamic free model discovery and selection.

Free models are volatile - they appear and disappear based on provider decisions.
This module queries OpenRouter's API to discover currently available free models
and provides selection strategies for testing and research.

Ethical consideration: Free models aren't truly free - providers use submitted
prompts for training data. This is a data-for-access exchange that users should
understand when choosing free vs paid models.
"""

import asyncio
import httpx
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


async def discover_free_models(api_key: Optional[str] = None) -> Dict:
    """
    Query OpenRouter for currently available free models.

    Args:
        api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)

    Returns:
        Dictionary with 'free_models' list and metadata

    Raises:
        ValueError: If API key not provided
        RuntimeError: If API call fails
    """
    if api_key is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key is None:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY environment "
                "variable or pass api_key parameter"
            )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to query OpenRouter models API: {e}")

    models = data.get('data', [])

    # Filter for free models (prompt and completion costs are 0)
    free_models = []
    for model in models:
        model_id = model.get('id', '')
        pricing = model.get('pricing', {})

        prompt_cost = float(pricing.get('prompt', '999'))
        completion_cost = float(pricing.get('completion', '999'))

        if prompt_cost == 0 and completion_cost == 0:
            free_models.append({
                'id': model_id,
                'name': model.get('name', 'Unknown'),
                'context_length': model.get('context_length', 0),
                'architecture': model.get('architecture', {}),
                'top_provider': model.get('top_provider', {}).get('name', 'Unknown')
            })

    return {
        'discovered_at': datetime.utcnow().isoformat(),
        'total_models': len(models),
        'free_model_count': len(free_models),
        'free_models': sorted(free_models, key=lambda x: x['context_length'], reverse=True),
        'data_trade_warning': (
            "Free models use your prompts for training. "
            "This is a data-for-access exchange. "
            "For sensitive work, use paid models."
        )
    }


def get_cached_free_models() -> Optional[Dict]:
    """
    Load free models from most recent cache file.

    Returns:
        Cached model data or None if no cache exists
    """
    cache_file = Path(__file__).parent / "free_models.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except Exception:
        return None


async def get_free_models(force_refresh: bool = False, api_key: Optional[str] = None) -> Dict:
    """
    Get available free models, using cache unless force_refresh=True.

    Args:
        force_refresh: If True, query API instead of using cache
        api_key: OpenRouter API key

    Returns:
        Dictionary with free model data
    """
    if not force_refresh:
        cached = get_cached_free_models()
        if cached:
            return cached

    return await discover_free_models(api_key)


def select_free_models_for_testing(
    model_data: Dict,
    count: int = 3,
    prefer_high_context: bool = True
) -> List[str]:
    """
    Select free models appropriate for testing.

    Args:
        model_data: Result from get_free_models()
        count: Number of models to select
        prefer_high_context: If True, prioritize models with large context windows

    Returns:
        List of model IDs suitable for testing
    """
    free_models = model_data.get('free_models', [])

    if not free_models:
        return []

    # Already sorted by context_length descending if prefer_high_context
    if prefer_high_context:
        selected = free_models[:count]
    else:
        # Select variety: smallest, largest, and middle
        if len(free_models) < count:
            selected = free_models
        else:
            indices = [0, len(free_models) // 2, len(free_models) - 1]
            selected = [free_models[i] for i in indices[:count]]

    return [m['id'] for m in selected]


def save_free_models_cache(model_data: Dict):
    """Save free model data to cache file."""
    cache_file = Path(__file__).parent / "free_models.json"

    with open(cache_file, 'w') as f:
        json.dump(model_data, f, indent=2)


async def update_free_models_cache(api_key: Optional[str] = None):
    """
    Discover free models and update cache file.

    This should be run periodically (weekly?) to keep the cache current.
    """
    model_data = await discover_free_models(api_key)
    save_free_models_cache(model_data)

    print(f"Updated free models cache:")
    print(f"  Total models: {model_data['total_models']}")
    print(f"  Free models: {model_data['free_model_count']}")
    print(f"  Discovered at: {model_data['discovered_at']}")

    return model_data


if __name__ == "__main__":
    # CLI usage: python -m config.dynamic_free_models
    asyncio.run(update_free_models_cache())
