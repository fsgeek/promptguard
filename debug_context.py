"""
Debug what context string is passed to evaluator.
"""

import asyncio
import os
from promptguard.core.neutrosophic import MultiNeutrosophicPrompt, LayerPriority


async def debug_context():
    """Check context construction."""

    # Simulate what promptguard.py does
    mnp = MultiNeutrosophicPrompt(layers=[])
    context_parts = []

    layers_to_create = [
        ("system", "You are a helpful AI assistant.", LayerPriority.SYSTEM, "system"),
        ("user", "Hello, how are you?", LayerPriority.USER, "user"),
    ]

    for layer_name, content, priority, source in layers_to_create:
        # Build context showing provenance
        if layer_name == source:
            # Same source and purpose
            context_parts.append(f"{layer_name.capitalize()} layer: {content}")
        else:
            # Different source and purpose
            context_parts.append(f"{layer_name.capitalize()} layer (source: {source}-provided): {content}")

        context = "\n".join(context_parts)

        print(f"\n{'='*80}")
        print(f"Evaluating {layer_name} layer (source={source})")
        print(f"{'='*80}")
        print("Context passed to evaluator:")
        print(context)
        print()


if __name__ == "__main__":
    asyncio.run(debug_context())
