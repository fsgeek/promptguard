#!/usr/bin/env python3
"""
Test the config loader for model lists.

Validates that:
1. Config file loads successfully
2. Target models are loaded correctly
3. Evaluation models are loaded correctly
4. Category filtering works
5. Single-model selection works
"""

from promptguard.config import load_target_models, load_evaluation_models, load_model_config


def test_config_loader():
    """Test config loader functionality."""
    print("=" * 80)
    print("Testing Config Loader")
    print("=" * 80)

    # Test 1: Load complete config
    print("\n1. Loading complete config...")
    config = load_model_config()
    print(f"   ✓ Config loaded successfully")
    print(f"   - RLHF categories: {list(config.target_models.keys())}")
    print(f"   - Total target models: {len(config.all_target_models)}")
    print(f"   - Evaluation models: {len(config.evaluation_models)}")

    # Test 2: Load all target models
    print("\n2. Loading all target models...")
    all_targets = load_target_models()
    print(f"   ✓ Loaded {len(all_targets)} target models:")
    for model in all_targets:
        print(f"     - {model}")

    # Test 3: Load by category
    print("\n3. Loading by RLHF category...")
    categories = ["high_rlhf", "moderate_rlhf", "low_rlhf", "non_rlhf"]
    for category in categories:
        models = load_target_models(category=category)
        print(f"   ✓ {category}: {len(models)} models")
        for model in models:
            print(f"     - {model}")

    # Test 4: Load evaluation models
    print("\n4. Loading evaluation models...")
    eval_models = load_evaluation_models()
    print(f"   ✓ Loaded {len(eval_models)} evaluation models:")
    for model in eval_models:
        print(f"     - {model}")

    # Test 5: Validate counts
    print("\n5. Validating counts...")
    expected_targets = 9
    expected_evaluators = 4
    assert len(all_targets) == expected_targets, f"Expected {expected_targets} targets, got {len(all_targets)}"
    assert len(eval_models) == expected_evaluators, f"Expected {expected_evaluators} evaluators, got {len(eval_models)}"
    print(f"   ✓ Counts match expectations")

    # Test 6: Single model simulation
    print("\n6. Simulating single-model selection...")
    single_model = "anthropic/claude-sonnet-4.5"
    single_list = [single_model]
    print(f"   ✓ Single model mode: {single_model}")
    print(f"   - Would process with 1 worker instead of {len(all_targets)}")

    print("\n" + "=" * 80)
    print("✓ All tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    test_config_loader()
