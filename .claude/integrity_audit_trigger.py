#!/usr/bin/env python3
"""
Integrity Audit Trigger Hook

Analyzes Task agent output for validation claims requiring audit.
Runs automatically after any Task agent completes.
"""

import sys
import os
import json

# Read stdin for agent output (hook receives this)
agent_output = sys.stdin.read() if not sys.stdin.isatty() else ""

# Trigger patterns indicating audit needed
AUDIT_TRIGGERS = [
    "tested and working",
    "validated with",
    "production ready",
    "all tests pass",
    "integration test",
    "API",
    "openrouter",
    "openai",
    "anthropic",
    "fireworks",
]

# Check if audit needed
requires_audit = any(
    trigger.lower() in agent_output.lower()
    for trigger in AUDIT_TRIGGERS
)

if requires_audit:
    # Output to stdout (appears in Claude Code session)
    print("━" * 70)
    print("🔍 INTEGRITY AUDIT TRIGGERED")
    print("━" * 70)
    print()
    print("Task agent output contains validation claims or API references.")
    print("Automatic audit required per Integrity-First Delegation policy.")
    print()
    print("Audit Agent: /home/tony/.claude/agents/scientific_code_auditor.md")
    print()
    print("⚠️  COORDINATOR: Invoke Scientific Integrity Auditor before accepting results")
    print()
    print("━" * 70)

    # Return exit code 0 (don't block execution)
    sys.exit(0)
else:
    # No audit needed, silent success
    sys.exit(0)
