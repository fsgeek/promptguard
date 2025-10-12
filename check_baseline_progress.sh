#!/bin/bash
# Monitor baseline comparison experiment progress

echo "Baseline Comparison Experiment Progress"
echo "========================================"
echo ""

# Check if running
if pgrep -f "test_baseline_comparison.py" > /dev/null; then
    echo "Status: RUNNING ✓"
else
    echo "Status: NOT RUNNING (may be complete or failed)"
fi

echo ""

# Show model progress
echo "Model Progress:"
grep -E "Testing model:" baseline_comparison.log 2>/dev/null | tail -1

echo ""

# Count completed prompts
echo "Completion Status:"
if [ -f "baseline_comparison_intermediate.json" ]; then
    python3 -c "
import json
with open('baseline_comparison_intermediate.json', 'r') as f:
    results = json.load(f)

# Count by model
by_model = {}
for r in results:
    model = r['model']
    by_model[model] = by_model.get(model, 0) + 1

print(f'Total evaluations: {len(results)}')
print(f'Expected: 432 (72 prompts × 6 models)')
print(f'Progress: {len(results)/432*100:.1f}%')
print('')
print('By model:')
for model, count in sorted(by_model.items()):
    print(f'  {model}: {count}/72 ({count/72*100:.0f}%)')
" 2>/dev/null
else
    echo "  No intermediate results yet"
fi

echo ""

# Show cost
echo "Cost So Far:"
if [ -f "baseline_comparison_intermediate.json" ]; then
    python3 -c "
import json
with open('baseline_comparison_intermediate.json', 'r') as f:
    results = json.load(f)

total_cost = 0.0
for r in results:
    total_cost += r['condition_a_direct'].get('cost_usd', 0.0)
    total_cost += r['condition_b_observer'].get('cost_usd', 0.0)

print(f'  \${total_cost:.2f}')
print(f'  Estimated final: \${total_cost / len(results) * 432:.2f}')
" 2>/dev/null
else
    echo "  N/A"
fi

echo ""

# Show recent errors
echo "Recent Errors:"
if grep -q "ERROR" baseline_comparison.log 2>/dev/null; then
    tail -5 baseline_comparison.log | grep "ERROR"
else
    echo "  None"
fi

echo ""

# Estimated completion
echo "Latest Activity:"
tail -3 baseline_comparison.log 2>/dev/null | grep -E "prompt/s|Testing model"

echo ""
echo "Monitor live: tail -f baseline_comparison.log"
echo "Full log: cat baseline_comparison.log"
