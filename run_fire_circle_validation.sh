#!/bin/bash
# Fire Circle Validation Experiment Runner
#
# Executes all 6 experimental conditions sequentially:
# - baseline_single
# - baseline_parallel
# - baseline_fire_circle
# - enhanced_single
# - enhanced_parallel
# - enhanced_fire_circle
#
# Each condition evaluates 50 stratified prompts.
# Results saved to experiments/results/raw/

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Fire Circle Validation Experiment"
echo "========================================="
echo ""

# Check environment
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo -e "${RED}ERROR: OPENROUTER_API_KEY not set${NC}"
    exit 1
fi

# Check ArangoDB for Fire Circle storage
if [ -z "$ARANGODB_PROMPTGUARD_PASSWORD" ]; then
    echo -e "${YELLOW}WARNING: ARANGODB_PROMPTGUARD_PASSWORD not set${NC}"
    echo -e "${YELLOW}Fire Circle deliberations will not be stored${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Generate stratified sample (if not exists)
SAMPLE_PATH="experiments/fire_circle_validation/stratified_sample.json"
if [ ! -f "$SAMPLE_PATH" ]; then
    echo -e "${GREEN}Step 1: Generating stratified sample...${NC}"
    uv run python experiments/fire_circle_validation/stratified_sampler.py
    echo ""
else
    echo -e "${GREEN}Step 1: Stratified sample already exists (skip)${NC}"
    echo ""
fi

# Step 2: Run all 6 conditions
CONDITIONS=(
    "baseline_single"
    "baseline_parallel"
    "baseline_fire_circle"
    "enhanced_single"
    "enhanced_parallel"
    "enhanced_fire_circle"
)

TOTAL_CONDITIONS=${#CONDITIONS[@]}
COMPLETED=0

echo -e "${GREEN}Step 2: Running experimental conditions...${NC}"
echo "Total conditions: $TOTAL_CONDITIONS"
echo ""

for CONDITION in "${CONDITIONS[@]}"; do
    COMPLETED=$((COMPLETED + 1))
    CONFIG_PATH="experiments/configs/${CONDITION}.json"

    echo "========================================="
    echo -e "${GREEN}[$COMPLETED/$TOTAL_CONDITIONS] Running: $CONDITION${NC}"
    echo "========================================="
    echo "Config: $CONFIG_PATH"
    echo ""

    # Run experiment
    uv run python -m experiments.fire_circle_validation.experiment_runner "$CONFIG_PATH"

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ $CONDITION completed successfully${NC}"
    else
        echo ""
        echo -e "${RED}✗ $CONDITION failed${NC}"
        echo "Check logs above for error details"
        exit 1
    fi

    echo ""
    echo "Sleeping 5 seconds before next condition..."
    sleep 5
    echo ""
done

# Step 3: Summary
echo "========================================="
echo -e "${GREEN}Experiment Complete!${NC}"
echo "========================================="
echo ""
echo "Results saved to: experiments/results/raw/"
echo ""
echo "Available results:"
ls -lh experiments/results/raw/*.json | awk '{print $9, "(" $5 ")"}'
echo ""
echo "Next steps:"
echo "  1. Analyze results with analysis script (TBD)"
echo "  2. Query Fire Circle deliberations in ArangoDB"
echo "  3. Compare baseline vs enhanced conditions"
echo ""
