"""Debug OpenRouter API issue."""
import asyncio
import httpx
import os
import json

async def test_httpx():
    """Test if httpx can hit OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"API key present: {api_key is not None}")

    if not api_key:
        print("No API key found!")
        return

    async with httpx.AsyncClient() as client:
        try:
            # Test both paid and free models
            models_to_test = [
                "openai/gpt-4o",
                "x-ai/grok-4-fast:free",
                "meta-llama/llama-3.1-8b-instruct:free"
            ]

            for model in models_to_test:
                print(f"\n{'='*60}")
                print(f"Testing model: {model}")
                print(f"{'='*60}")

                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 10,
                    },
                    timeout=30.0,
                )

                print(f"Status code: {response.status_code}")

                if response.status_code != 200:
                    print(f"Error response: {response.text}")
                    continue

                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')
                print(f"Success! Response: {content[:100]}")

        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_httpx())
