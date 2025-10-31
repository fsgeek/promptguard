#!/usr/bin/env python3
"""Test parser in isolation with actual failing responses from JSONL logs."""

import json
import sys

# Import the parser logic from fire_circle
sys.path.insert(0, '/home/tony/projects/promptguard')
from promptguard.evaluation.fire_circle import FireCircleEvaluator

def test_response(response_text, model, description):
    """Test parsing a single response."""
    print(f"\n{'='*80}")
    print(f"Testing: {description}")
    print(f"Model: {model}")
    print(f"Response length: {len(response_text)}")
    print(f"First 200 chars: {response_text[:200]}")
    print(f"{'='*80}")

    # Test parser directly - just extract and parse JSON
    import re

    try:
        json_str = response_text.strip()

        # Replicate parser logic from fire_circle.py:1728-1770
        if "```json" in json_str:
            start_idx = json_str.index("```json") + 7
            end_idx = json_str.index("```", start_idx)
            json_str = json_str[start_idx:end_idx].strip()
        elif "```python" in json_str:
            start_idx = json_str.index("```python") + 9
            end_idx = json_str.index("```", start_idx)
            json_str = json_str[start_idx:end_idx].strip()
        elif "```" in json_str:
            start_idx = json_str.index("```") + 3
            try:
                end_idx = json_str.index("```", start_idx)
                json_str = json_str[start_idx:end_idx].strip()
            except ValueError:
                json_str = json_str[start_idx:].strip()

        # Extract JSON object only (brace counting)
        if json_str.startswith("{"):
            brace_count = 0
            for i, char in enumerate(json_str):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_str = json_str[:i+1]
                        break

        print(f"Extracted JSON ({len(json_str)} chars): {json_str[:200]}...")

        data = json.loads(json_str, strict=False)
        print(f"✓ SUCCESS")
        print(f"  T={data.get('truth')}, I={data.get('indeterminacy')}, F={data.get('falsehood')}")
        print(f"  Reasoning: {data.get('reasoning', '')[:100]}...")
        return True
    except Exception as e:
        print(f"✗ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Load responses from JSONL and test parser."""

    # Load OpenRouter raw responses
    print("Loading OpenRouter raw responses from /tmp/openrouter_raw.jsonl...")
    with open("/tmp/openrouter_raw.jsonl") as f:
        raw_responses = [json.loads(line) for line in f]

    print(f"Loaded {len(raw_responses)} raw API responses")

    # Test Llama Round 1 (prose prefix issue)
    llama_responses = [r for r in raw_responses if "llama" in r["model"]]
    if llama_responses:
        print(f"\n\nTesting Llama responses ({len(llama_responses)} total):")
        for i, resp in enumerate(llama_responses[:3]):  # Test first 3
            test_response(
                resp["content"],
                resp["model"],
                f"Llama response #{i+1}"
            )

    # Test Hermes Round 2 (length mismatch issue)
    hermes_responses = [r for r in raw_responses if "hermes" in r["model"]]
    if hermes_responses:
        print(f"\n\nTesting Hermes responses ({len(hermes_responses)} total):")
        for i, resp in enumerate(hermes_responses[:3]):  # Test first 3
            test_response(
                resp["content"],
                resp["model"],
                f"Hermes response #{i+1}"
            )

    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total API calls logged: {len(raw_responses)}")
    print(f"Llama responses: {len(llama_responses)}")
    print(f"Hermes responses: {len(hermes_responses)}")

if __name__ == "__main__":
    main()
