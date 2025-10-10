#!/usr/bin/env python3
"""Test JSON parser robustness with control characters."""

import json
import re

def clean_json_string_v1(s: str) -> str:
    """Original cleaning function."""
    cleaned = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', s)
    return cleaned

def clean_json_string_v2(s: str) -> str:
    """Enhanced cleaning - also handle incomplete JSON."""
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', s)

    # Check if JSON is incomplete (ends mid-field)
    if cleaned.rstrip().endswith('"'):
        # Truncated string value - close it properly
        cleaned = cleaned.rstrip() + '}'
    elif not cleaned.rstrip().endswith('}'):
        # Missing closing brace - add it
        cleaned = cleaned.rstrip()
        # Count braces to determine how many to add
        open_braces = cleaned.count('{') - cleaned.count('}')
        closed = cleaned + '}' * open_braces
        return closed

    return cleaned

# Test cases from actual failures
test_cases = [
    # Case 1: Control character in reasoning
    '''{"truth": 0.7, "indeterminacy": 0.2, "falsehood": 0.3, "reasoning": "Line 1\nLine 2"}''',

    # Case 2: Incomplete JSON (truncated reasoning)
    '''{"truth": 0.7, "indeterminacy": 0.2, "falsehood": 0.3, "reasoning": "This is a meta-level''',

    # Case 3: Unicode characters (should work)
    '''{"truth": 0.7, "reasoning": "Contains unicode: 入力"}''',
]

print("Testing JSON robustness...")
print("=" * 60)

for i, test_json in enumerate(test_cases, 1):
    print(f"\nTest case {i}:")
    print(f"  Input: {repr(test_json[:80])}...")

    # Try original method
    try:
        cleaned = clean_json_string_v1(test_json)
        data = json.loads(cleaned)
        print(f"  ✓ V1 success: {data.get('truth', 'N/A')}")
    except Exception as e:
        print(f"  ✗ V1 failed: {str(e)[:60]}")

    # Try enhanced method
    try:
        cleaned = clean_json_string_v2(test_json)
        data = json.loads(cleaned)
        print(f"  ✓ V2 success: {data.get('truth', 'N/A')}")
    except Exception as e:
        print(f"  ✗ V2 failed: {str(e)[:60]}")
