#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///

"""
Integrity Audit Trigger Hook for SubagentStop

Analyzes Task agent output for validation claims requiring scientific audit.
Automatically triggers when SubagentStop event contains API-related claims.
"""

import json
import sys


# Trigger patterns indicating audit needed
AUDIT_TRIGGERS = [
    "tested and working",
    "validated with",
    "production ready",
    "all tests pass",
    "integration test",
    "comprehensive testing",
    "empirically validated",
]

API_PATTERNS = [
    "api",
    "openrouter",
    "openai",
    "anthropic",
    "fireworks",
    "google",
]


def main():
    try:
        # Read JSON input from stdin (hook receives this automatically)
        input_data = json.load(sys.stdin)

        # Convert entire input to string for pattern matching
        # This includes all fields in the SubagentStop event
        input_str = json.dumps(input_data).lower()

        # Check if audit needed
        has_validation_claim = any(
            trigger.lower() in input_str
            for trigger in AUDIT_TRIGGERS
        )

        has_api_reference = any(
            pattern.lower() in input_str
            for pattern in API_PATTERNS
        )

        requires_audit = has_validation_claim or has_api_reference

        if requires_audit:
            # Output banner (appears in Claude Code session)
            print("━" * 70, file=sys.stderr)
            print("🔍 INTEGRITY AUDIT TRIGGERED", file=sys.stderr)
            print("━" * 70, file=sys.stderr)
            print(file=sys.stderr)
            print("Subagent output contains validation claims or API references.", file=sys.stderr)
            print("Automatic audit required per Integrity-First Delegation policy.", file=sys.stderr)
            print(file=sys.stderr)
            print("Audit Agent: /home/tony/.claude/agents/scientific_code_auditor.md", file=sys.stderr)
            print(file=sys.stderr)
            print("⚠️  COORDINATOR: Invoke Scientific Integrity Auditor before accepting", file=sys.stderr)
            print(file=sys.stderr)

            if has_validation_claim:
                print("Validation claims detected:", file=sys.stderr)
                for trigger in AUDIT_TRIGGERS:
                    if trigger.lower() in input_str:
                        print(f"  • {trigger}", file=sys.stderr)
                print(file=sys.stderr)

            if has_api_reference:
                print("API references detected:", file=sys.stderr)
                for pattern in API_PATTERNS:
                    if pattern.lower() in input_str:
                        print(f"  • {pattern}", file=sys.stderr)
                print(file=sys.stderr)

            print("━" * 70, file=sys.stderr)

        # Exit 0 (don't block execution)
        sys.exit(0)

    except json.JSONDecodeError:
        # Fail silently on JSON errors
        sys.exit(0)
    except Exception:
        # Fail silently on any other errors
        sys.exit(0)


if __name__ == "__main__":
    main()
