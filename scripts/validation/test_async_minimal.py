"""
Minimal test to verify async pattern doesn't produce deprecation warnings.
"""

import sys
import warnings
from pathlib import Path

# Add scripts/validation to path
sys.path.insert(0, str(Path(__file__).parent))
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Capture all warnings
warnings.simplefilter("always", DeprecationWarning)

from experiment_01_baseline import BaselineEvaluationStage, ComplianceClassificationStage
from datetime import datetime, timezone

def test_baseline_stage():
    """Test that BaselineEvaluationStage.process() doesn't emit deprecation warnings."""
    print("Testing BaselineEvaluationStage.process()...")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)

        stage = BaselineEvaluationStage("anthropic/claude-3-haiku", "test_exp")

        test_item = {
            "prompt_id": "test_001",
            "prompt_text": "What is 2+2?"
        }

        try:
            result = stage.process(test_item)
            print(f"✓ BaselineEvaluationStage completed successfully")

            # Check for deprecation warnings
            deprecation_warnings = [warning for warning in w
                                   if issubclass(warning.category, DeprecationWarning)]

            if deprecation_warnings:
                print(f"✗ Found {len(deprecation_warnings)} deprecation warning(s):")
                for warning in deprecation_warnings:
                    print(f"  {warning.filename}:{warning.lineno}: {warning.message}")
                return False
            else:
                print("✓ No deprecation warnings from BaselineEvaluationStage")
                return True

        except Exception as e:
            print(f"✗ Error during evaluation: {e}")
            # Check warnings anyway
            deprecation_warnings = [warning for warning in w
                                   if issubclass(warning.category, DeprecationWarning)]
            if deprecation_warnings:
                print(f"✗ Found {len(deprecation_warnings)} deprecation warning(s):")
                for warning in deprecation_warnings:
                    print(f"  {warning.filename}:{warning.lineno}: {warning.message}")
            return False


def test_compliance_stage():
    """Test that ComplianceClassificationStage.process() doesn't emit deprecation warnings."""
    print("\nTesting ComplianceClassificationStage.process()...")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)

        stage = ComplianceClassificationStage("anthropic/claude-3-haiku", "test_prompt_id")

        test_item = {
            "prompt_text": "What is 2+2?",
            "response_text": "2+2 equals 4."
        }

        try:
            result = stage.process(test_item)
            print(f"✓ ComplianceClassificationStage completed successfully")

            # Check for deprecation warnings
            deprecation_warnings = [warning for warning in w
                                   if issubclass(warning.category, DeprecationWarning)]

            if deprecation_warnings:
                print(f"✗ Found {len(deprecation_warnings)} deprecation warning(s):")
                for warning in deprecation_warnings:
                    print(f"  {warning.filename}:{warning.lineno}: {warning.message}")
                return False
            else:
                print("✓ No deprecation warnings from ComplianceClassificationStage")
                return True

        except Exception as e:
            print(f"✗ Error during classification: {e}")
            # Check warnings anyway
            deprecation_warnings = [warning for warning in w
                                   if issubclass(warning.category, DeprecationWarning)]
            if deprecation_warnings:
                print(f"✗ Found {len(deprecation_warnings)} deprecation warning(s):")
                for warning in deprecation_warnings:
                    print(f"  {warning.filename}:{warning.lineno}: {warning.message}")
            return False


if __name__ == "__main__":
    print("="*60)
    print("Minimal Async Pattern Test")
    print("="*60)
    print()

    baseline_ok = test_baseline_stage()
    compliance_ok = test_compliance_stage()

    print()
    print("="*60)
    if baseline_ok and compliance_ok:
        print("✓ All tests passed - no deprecation warnings")
        sys.exit(0)
    else:
        print("✗ Tests failed - deprecation warnings detected")
        sys.exit(1)
