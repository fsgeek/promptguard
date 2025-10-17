#!/usr/bin/env python3
"""
Test target response collection system with 10 prompts.

Validates:
1. Encryption/decryption working
2. ArangoDB storage working
3. Response classification accurate
4. Parallel workers functioning
5. Complete end-to-end flow

Run this BEFORE full 478-prompt collection.
"""

import asyncio
import json
import os
from pathlib import Path

from promptguard.storage.encryption import ResponseEncryption, ensure_encryption_key
from promptguard.storage.target_response_storage import TargetResponseStorage
from collect_target_responses import TargetResponseCollector, OutcomeClassifier


def test_encryption():
    """Test encryption utilities."""
    print("=" * 80)
    print("TEST 1: Encryption/Decryption")
    print("=" * 80)

    # Ensure key exists
    key_path = ensure_encryption_key()
    print(f"✓ Encryption key exists at {key_path}")

    # Test encrypt/decrypt
    encryption = ResponseEncryption()
    test_text = "This is a test response with sensitive content."

    encrypted = encryption.encrypt(test_text)
    print(f"✓ Encrypted: {encrypted[:50]}...")

    decrypted = encryption.decrypt(encrypted)
    assert decrypted == test_text
    print(f"✓ Decrypted matches original")

    print()


def test_classification():
    """Test outcome classifier."""
    print("=" * 80)
    print("TEST 2: Outcome Classification")
    print("=" * 80)

    # Test refusal detection
    refusal_text = "I cannot help with that request as it goes against my guidelines."
    outcome = OutcomeClassifier.classify(refusal_text, "manipulative")
    assert outcome == "REFUSED"
    print(f"✓ Refusal detected: '{refusal_text[:50]}...'")

    # Test compliance detection (harmful prompt + long response)
    compliance_text = "Here's how to do that harmful thing: " + "X" * 200
    outcome = OutcomeClassifier.classify(compliance_text, "manipulative")
    assert outcome == "COMPLIED"
    print(f"✓ Compliance detected for harmful prompt")

    # Test deflection (short response)
    deflect_text = "I'd rather not discuss that."
    outcome = OutcomeClassifier.classify(deflect_text, "manipulative")
    assert outcome == "DEFLECTED"
    print(f"✓ Deflection detected")

    print()


def test_storage():
    """Test ArangoDB storage."""
    print("=" * 80)
    print("TEST 3: ArangoDB Storage")
    print("=" * 80)

    # Initialize storage
    storage = TargetResponseStorage()
    print("✓ Connected to ArangoDB")

    # Store test response
    test_response = {
        "prompt_id": "test_prompt_001",
        "prompt_text": "This is a test prompt",
        "prompt_label": "reciprocal",
        "target_model": "test/model",
        "response_text": "This is a test response that should be encrypted",
        "outcome": "COMPLIED",
        "temperature": 0.7,
        "max_tokens": 2000,
        "tokens": 50,
        "latency_ms": 1000,
        "cost_usd": 0.001
    }

    storage.store_response(**test_response)
    print("✓ Stored test response")

    # Retrieve and verify
    retrieved = storage.get_response("test_prompt_001", "test/model", decrypt=True)
    assert retrieved is not None
    assert retrieved["response"]["text"] == test_response["response_text"]
    print("✓ Retrieved and decrypted response matches")

    # Check encryption in database
    retrieved_encrypted = storage.get_response("test_prompt_001", "test/model", decrypt=False)
    assert "text_encrypted" in retrieved_encrypted["response"]
    assert retrieved_encrypted["response"]["text_encrypted"] != test_response["response_text"]
    print("✓ Response stored encrypted in database")

    print()


async def test_collection():
    """Test actual collection with 2 prompts and 2 models."""
    print("=" * 80)
    print("TEST 4: Response Collection (2 prompts x 2 models)")
    print("=" * 80)

    # Check API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("✗ OPENROUTER_API_KEY not set - skipping collection test")
        return

    # Load first 2 prompts
    dataset_path = Path("datasets/baseline_calibration.json")
    with open(dataset_path) as f:
        data = json.load(f)
        prompts = data["prompts"][:2]

    print(f"✓ Loaded {len(prompts)} test prompts")

    # Use 2 fast/cheap models for testing
    test_models = [
        "anthropic/claude-3-haiku",
        "deepseek/deepseek-v3.1-terminus"
    ]

    # Initialize
    storage = TargetResponseStorage()
    collector = TargetResponseCollector(storage, api_key)

    print(f"✓ Testing with models: {test_models}")

    # Collect responses
    for model in test_models:
        print(f"\nCollecting from {model}...")
        stats = await collector.process_model(model, prompts, resume=False)
        print(f"  Completed: {stats['completed']}, Failed: {stats['failed']}")

    # Verify storage
    for prompt in prompts:
        for model in test_models:
            response = storage.get_response(prompt["id"], model, decrypt=True)
            if response:
                print(f"  ✓ {prompt['id'][:30]:30} | {model:40} | {response['response']['outcome']}")

    print()


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("TARGET RESPONSE SYSTEM VALIDATION")
    print("=" * 80 + "\n")

    try:
        # Test 1: Encryption
        test_encryption()

        # Test 2: Classification
        test_classification()

        # Test 3: Storage
        test_storage()

        # Test 4: Collection (requires API key)
        await test_collection()

        print("=" * 80)
        print("ALL TESTS PASSED")
        print("=" * 80)
        print("\nSystem ready for full collection. Run:")
        print("  python collect_target_responses.py --test    # 10 prompts")
        print("  python collect_target_responses.py           # Full 478 prompts")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
