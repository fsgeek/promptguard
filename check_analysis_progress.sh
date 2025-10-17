#!/bin/bash
#
# Check stratified analysis progress
#

echo "========================================================================================="
echo "STRATIFIED ANALYSIS PROGRESS CHECK"
echo "========================================================================================="
echo

# Check if process is running
if ps aux | grep "python analyze_target_responses.py --sample 60" | grep -v grep > /dev/null; then
    PID=$(ps aux | grep "python analyze_target_responses.py --sample 60" | grep -v grep | awk '{print $2}')
    echo "Status: RUNNING (PID $PID)"
else
    echo "Status: COMPLETE or NOT RUNNING"
fi

echo

# Latest progress
echo "Latest progress markers:"
grep "Progress:" stratified_analysis.log | tail -5
echo

# Current time
echo "Current time: $(date)"
echo

# Latest activity (last 10 lines)
echo "Latest log entries:"
tail -10 stratified_analysis.log
echo

# Error summary
echo "Error summary:"
echo "  GPT-5 failures:    $(grep -c 'Post-evaluation failed for openai/gpt-5' stratified_analysis.log 2>/dev/null || echo 0)"
echo "  Claude failures:   $(grep -c 'Post-evaluation failed for anthropic/claude-sonnet-4.5' stratified_analysis.log 2>/dev/null || echo 0)"
echo "  Kimi failures:     $(grep -c 'Post-evaluation failed for moonshotai/kimi-k2-0905' stratified_analysis.log 2>/dev/null || echo 0)"
echo "  DeepSeek failures: $(grep -c 'Post-evaluation failed for deepseek/deepseek-v3.1-terminus' stratified_analysis.log 2>/dev/null || echo 0)"
echo

# Check for completion
if ls target_response_analysis_2025-10-16*.json 2>/dev/null | grep -q "target_response_analysis_2025-10-16-"; then
    echo "Output file found:"
    ls -lh target_response_analysis_2025-10-16*.json | tail -1
    echo

    # Show summary if available
    LATEST=$(ls -t target_response_analysis_2025-10-16*.json | head -1)
    if [ -f "$LATEST" ]; then
        echo "Summary from $LATEST:"
        python3 -c "import json; d=json.load(open('$LATEST')); s=d.get('summary',{}); print(f\"  Total responses: {s.get('total_responses',0)}\"); print(f\"  Avg divergence: {s.get('avg_divergence','N/A')}\"); print(f\"  Meta-learning candidates: {s.get('meta_learning_count',0)}\")"
    fi
else
    echo "No output file yet (analysis still running)"
fi

echo
echo "========================================================================================="
