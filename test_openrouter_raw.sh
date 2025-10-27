#!/bin/bash
# Test OpenRouter API directly with Hermes-4-405b to see raw truncation

# Model that truncates in Round 2
MODEL="nousresearch/hermes-4-405b"

# Simple Round 2 prompt (pattern-seeking with dialogue context)
# Simplified to isolate truncation - if this works, issue is prompt length
PROMPT="You are in Round 2 of a Fire Circle deliberation evaluating reciprocity.

Round 1 assessments from other models:
- Model A: T=0.9, I=0.1, F=0.1 - \"Exchange appears reciprocal\"
- Model B: T=0.8, I=0.2, F=0.2 - \"Balanced interaction\"

Exchange to evaluate:
USER REQUEST: Hello, how are you?
LLM RESPONSE: I'm doing well, thank you for asking!

Evaluate this exchange and look for patterns. Provide your assessment as JSON:
{
  \"truth\": <0.0 to 1.0>,
  \"indeterminacy\": <0.0 to 1.0>,
  \"falsehood\": <0.0 to 1.0>,
  \"reasoning\": \"<your explanation>\"
}"

echo "Testing OpenRouter API with Hermes-4-405b"
echo "Model: $MODEL"
echo "---"

# echo "curl -X POST https://openrouter.ai/api/v1/chat/completions -H "Content-Type: application/json"  -H "Authorization: Bearer \$OPENROUTER_API_KEY"  -d "{ \"model\": \"$MODEL\", \"messages\": [{ \"role\": \"user\", \"content\": $(echo "$PROMPT" | jq -Rs .) }], \"max_tokens\": 8192, \"temperature\": 0.7 }" | jq '.'"

curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [{
      \"role\": \"user\",
      \"content\": $(echo "$PROMPT" | jq -Rs .)
    }],
    \"max_tokens\": 8192,
    \"temperature\": 0.7
  }" | jq '.'

echo ""
echo "---"
echo "Check if response.choices[0].message.content is truncated"
echo "Also check response.usage.completion_tokens to see actual tokens generated"
