# Failure Analysis
## Summary
- Total error lines found: 10
- Total prompts evaluated: 478

## Error Details
### Parsing Failures (0)
- None detected

### Network Failures (0)
- None detected

### Other Failures (10)
- anthropic/claude-sonnet-4.5              ERROR: Failed to evaluate layer with anthropic/claude-sonnet-4.5: F
- openai/gpt-4o                            ERROR: Failed to evaluate layer with openai/gpt-4o: Failed to parse
- anthropic/claude-sonnet-4.5              ERROR: Failed to evaluate layer with anthropic/claude-sonnet-4.5: F
- openai/gpt-4o                            ERROR: Failed to evaluate layer with openai/gpt-4o: Failed to parse
- anthropic/claude-sonnet-4.5              ERROR: Failed to evaluate layer with anthropic/claude-sonnet-4.5: F
- anthropic/claude-sonnet-4.5              ERROR: Failed to evaluate layer with anthropic/claude-sonnet-4.5: F
- deepseek/deepseek-v3.1-terminus          ERROR: Failed to evaluate layer with deepseek/deepseek-v3.1-terminu
- anthropic/claude-sonnet-4.5              ERROR: Failed to evaluate layer with anthropic/claude-sonnet-4.5: F
- anthropic/claude-sonnet-4.5              ERROR: Failed to evaluate layer with anthropic/claude-sonnet-4.5: F
- anthropic/claude-sonnet-4.5              ERROR: Failed to evaluate layer with anthropic/claude-sonnet-4.5: F

## Model-Specific Failure Rates
- anthropic/claude-sonnet-4.5: 7/478 failures (1.5%)
- moonshotai/kimi-k2-0905: 0/478 failures (0.0%)
- deepseek/deepseek-v3.1-terminus: 1/478 failures (0.2%)
- openai/gpt-4o: 2/478 failures (0.4%)

## Recommendations
- Most failures appear to be transient (if error lines are low)
- Parser improvements needed if parsing failures are systematic
- Consider retry logic for network failures
