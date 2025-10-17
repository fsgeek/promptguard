#!/bin/bash
#
# Launch parallel target response collection across all 9 models
#
# Usage:
#   # Test mode (10 prompts × 9 models = 90 responses)
#   ./launch_parallel_collection.sh --test
#
#   # Full collection (478 prompts × 9 models = 4,302 responses)
#   ./launch_parallel_collection.sh
#
# Each model runs as independent process with own log file
# All processes complete in parallel (wall-clock time = single model time)

# Parse arguments
TEST_FLAG=""
if [ "$1" == "--test" ]; then
    TEST_FLAG="--test"
    echo "TEST MODE: 10 prompts per model"
fi

# Load models from config
MODELS=(
    "anthropic/claude-sonnet-4.5"
    "openai/gpt-4o"
    "moonshotai/kimi-k2-0905"
    "deepseek/deepseek-v3.1-terminus"
    "meta-llama/llama-3.3-70b-instruct"
    "cognitivecomputations/dolphin3.0-mistral-24b:free"
    "mistralai/mistral-7b-instruct-v0.2"
    "nousresearch/hermes-3-llama-3.1-405b"
    "deepseek/deepseek-v3.2-exp"
)

echo "Launching ${#MODELS[@]} parallel collection workers..."
echo

# Launch each model as background process
PIDS=()
for model in "${MODELS[@]}"; do
    # Sanitize model name for log file
    log_name=$(echo "$model" | tr '/:' '_')
    log_file="collection_${log_name}.log"

    echo "Starting: $model → $log_file"

    # Launch in background
    uv run python collect_target_responses.py $TEST_FLAG --model "$model" > "$log_file" 2>&1 &

    PIDS+=($!)

    # Small delay to avoid API burst
    sleep 0.5
done

echo
echo "All workers launched. PIDs: ${PIDS[@]}"
echo "Monitoring progress (Ctrl-C to stop monitoring, workers continue)..."
echo

# Monitor completion
completed=0
while [ $completed -lt ${#MODELS[@]} ]; do
    completed=0
    for pid in "${PIDS[@]}"; do
        if ! kill -0 $pid 2>/dev/null; then
            ((completed++))
        fi
    done

    echo -ne "\rCompleted: $completed/${#MODELS[@]} workers"
    sleep 5
done

echo
echo
echo "=================================================================================="
echo "ALL WORKERS COMPLETE"
echo "=================================================================================="
echo

# Summary from logs
echo "Per-model summaries:"
echo
for model in "${MODELS[@]}"; do
    log_name=$(echo "$model" | tr '/:' '_')
    log_file="collection_${log_name}.log"

    if [ -f "$log_file" ]; then
        echo "Model: $model"
        grep "COMPLETE" "$log_file" || echo "  [No completion marker found]"
        echo
    fi
done

echo "Check individual log files for details: collection_*.log"
echo "Aggregate statistics available in ArangoDB"
