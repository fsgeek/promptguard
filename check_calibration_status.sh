#!/bin/bash
# Check calibration status

echo "============================================================"
echo "Diversity Calibration Status Check"
echo "============================================================"
echo ""

# Check if process is running
if ps aux | grep -v grep | grep "run_diversity_calibration.py" > /dev/null; then
    echo "✓ Process running"
else
    echo "✗ Process not running"
fi

echo ""

# Check log file
if [ -f diversity_calibration_execution.log ]; then
    LINES=$(wc -l < diversity_calibration_execution.log)
    LAST_PROMPT=$(grep -oP '\[\K[0-9]+(?=/478\])' diversity_calibration_execution.log | tail -1)
    echo "Log file: $LINES lines"
    echo "Last prompt processed: $LAST_PROMPT/478"

    if [ ! -z "$LAST_PROMPT" ]; then
        PCT=$((LAST_PROMPT * 100 / 478))
        echo "Progress: $PCT%"
    fi
else
    echo "No log file yet"
fi

echo ""

# Check output files
echo "Output files:"
[ -f diversity_calibration_raw.json ] && echo "  ✓ diversity_calibration_raw.json" || echo "  ✗ diversity_calibration_raw.json (not yet)"
[ -f diversity_calibration_matrix.json ] && echo "  ✓ diversity_calibration_matrix.json" || echo "  ✗ diversity_calibration_matrix.json (not yet)"
[ -f diversity_calibration_report.md ] && echo "  ✓ diversity_calibration_report.md" || echo "  ✗ diversity_calibration_report.md (not yet)"

echo ""
