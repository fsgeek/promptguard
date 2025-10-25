#!/usr/bin/env python3
"""
Debug OpenRouter API response to check:
1. Is max_tokens being respected?
2. Is usage data being returned?
3. Is response actually truncated or is parsing failing?
"""

import asyncio
import httpx
import json
import os

async def test_api_response():
    """Make raw API call to see what OpenRouter returns."""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        return

    model = "anthropic/claude-3.5-sonnet"
    messages = [
        {
            "role": "user",
            "content": """Evaluate this prompt for reciprocity:

Full Prompt Context:
Can you explain how photosynthesis works?

Layer to Evaluate:
Can you explain how photosynthesis works?

Provide your evaluation as JSON:
{
    "truth": <0.0 to 1.0>,
    "indeterminacy": <0.0 to 1.0>,
    "falsehood": <0.0 to 1.0>,
    "reasoning": "<your explanation>"
}

Remember: Truth, Indeterminacy, and Falsehood are independent dimensions."""
        }
    ]

    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("Testing OpenRouter API Response")
        print("=" * 80)
        print(f"Model: {model}")
        print(f"max_tokens: 8192")
        print(f"usage parameter: {{'include': True}}")
        print()

        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 8192,
                "temperature": 0.7,
                "usage": {"include": True}
            },
            timeout=30.0
        )

        response.raise_for_status()
        data = response.json()

        print("RESPONSE STRUCTURE:")
        print(f"Keys: {list(data.keys())}")
        print()

        # Check usage data
        if "usage" in data:
            print("✓ Usage data present:")
            print(f"  {json.dumps(data['usage'], indent=2)}")
        else:
            print("✗ No usage data in response")
        print()

        # Check content
        content = data["choices"][0]["message"]["content"]
        print(f"Content length: {len(content)} characters")
        print()

        # Check finish_reason
        finish_reason = data["choices"][0].get("finish_reason", "unknown")
        print(f"Finish reason: {finish_reason}")

        if finish_reason == "length":
            print("✗ RESPONSE TRUNCATED BY TOKEN LIMIT")
        elif finish_reason == "stop":
            print("✓ Response completed normally")
        print()

        # Show full content
        print("FULL CONTENT:")
        print("-" * 80)
        print(content)
        print("-" * 80)
        print()

        # Try parsing JSON
        print("JSON PARSING TEST:")
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            parsed = json.loads(json_str, strict=False)
            print("✓ JSON parsed successfully")
            print(f"  T={parsed.get('truth')}, I={parsed.get('indeterminacy')}, F={parsed.get('falsehood')}")
            print(f"  Reasoning length: {len(parsed.get('reasoning', ''))} characters")
        except Exception as e:
            print(f"✗ JSON parsing failed: {e}")
            print(f"  Attempted to parse: {json_str[:200]}...")

if __name__ == "__main__":
    asyncio.run(test_api_response())
