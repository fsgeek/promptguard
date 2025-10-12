#!/bin/bash
# Run RLHF comparison experiment

echo "=========================================="
echo "RLHF COMPARISON EXPERIMENT"
echo "Base Models vs Instruct Models"
echo "Defensive Framing vs Observer Framing"
echo "=========================================="
echo ""
echo "This experiment will:"
echo "  1. Test 3 model pairs (Llama 405B, DeepSeek V3, Llama 70B)"
echo "  2. Run 4 conditions per pair (2×2 design)"
echo "  3. Evaluate 72 encoding attacks per condition"
echo "  4. Total: 3 pairs × 4 conditions × 72 attacks = 864 evaluations"
echo ""
echo "Expected runtime: 2-4 hours (with caching)"
echo "Expected cost: ~$5-15 (varies by model pricing)"
echo ""

# Check for API key
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "ERROR: OPENROUTER_API_KEY not set"
    echo "Export your API key first:"
    echo "  export OPENROUTER_API_KEY=your_key_here"
    exit 1
fi

echo "API key found: ${OPENROUTER_API_KEY:0:8}..."
echo ""

# Confirm before running
read -p "Proceed with experiment? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Create cache directory
mkdir -p .cache/rlhf_comparison

# Run experiment
echo ""
echo "Starting experiment..."
echo "Results will be saved to: rlhf_comparison_results.json"
echo "Log output: rlhf_experiment.log"
echo ""

uv run python test_rlhf_comparison.py 2>&1 | tee rlhf_experiment.log

# Check if experiment completed
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "EXPERIMENT COMPLETED"
    echo "=========================================="
    echo ""
    echo "Generating analysis report..."
    uv run python analyze_rlhf_results.py

    echo ""
    echo "Files generated:"
    echo "  - rlhf_comparison_results.json (raw data)"
    echo "  - RLHF_COMPARISON_ANALYSIS.md (analysis report)"
    echo "  - rlhf_experiment.log (execution log)"
    echo ""
    echo "Done!"
else
    echo ""
    echo "ERROR: Experiment failed. Check rlhf_experiment.log for details."
    exit 1
fi
