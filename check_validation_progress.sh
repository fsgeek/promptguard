#!/bin/bash
# Check validation progress

echo "=== Validation Progress Check ==="
echo "Time: $(date)"
echo ""

# Check if process is running
if pgrep -f run_quantitative_validation.py > /dev/null; then
    echo "✓ Validation script is RUNNING"
else
    echo "✗ Validation script is NOT RUNNING"
fi
echo ""

# Show last 20 lines of log
echo "=== Last 20 Log Lines ==="
tail -20 quantitative_validation.log 2>/dev/null || echo "Log file not yet created"
echo ""

# Check output files
echo "=== Output Files ==="
if [ -f validation_results_task1.jsonl ]; then
    count=$(wc -l < validation_results_task1.jsonl)
    echo "✓ validation_results_task1.jsonl: $count records"
else
    echo "✗ validation_results_task1.jsonl: Not created yet"
fi

if [ -f validation_metrics_task1.json ]; then
    echo "✓ validation_metrics_task1.json: Created"
else
    echo "✗ validation_metrics_task1.json: Not created yet"
fi

if [ -f validation_summary_task1.md ]; then
    echo "✓ validation_summary_task1.md: Created"
else
    echo "✗ validation_summary_task1.md: Not created yet"
fi
echo ""
