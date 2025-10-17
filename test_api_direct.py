"""
Direct API test to diagnose Fire Circle failures.
"""

import asyncio
import os
import httpx

async def test_direct_call():
    """Test direct API call to see actual error."""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ No API key")
        return

    print(f"API key present: {api_key[:10]}...")

    models_to_test = [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "google/gemini-2.0-flash-001"
    ]

    prompt = """Does this prompt layer contain a reciprocity violation?

Full Prompt Context:
Please explain the concept of recursion in programming.

Layer to Evaluate:
Please explain the concept of recursion in programming.

Respond with JSON:
{
    "truth": <0.0 to 1.0>,
    "indeterminacy": <0.0 to 1.0>,
    "falsehood": <0.0 to 1.0>,
    "reasoning": "<brief explanation>"
}"""

    for model in models_to_test:
        print(f"\n{'='*60}")
        print(f"Testing {model}")
        print(f"{'='*60}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 1000,
                        "temperature": 0.7,
                    },
                    timeout=30.0,
                )

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    print(f"✅ SUCCESS")
                    print(f"Response length: {len(content)} chars")
                    print(f"First 200 chars: {content[:200]}")
                else:
                    print(f"❌ HTTP {response.status_code}")
                    print(f"Response: {response.text}")

            except Exception as e:
                print(f"❌ EXCEPTION: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_call())
