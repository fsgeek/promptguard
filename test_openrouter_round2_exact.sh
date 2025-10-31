#!/bin/bash
# Test OpenRouter API with EXACT Round 2 prompt that triggers truncation
# Purpose: See what OpenRouter actually returns when given complex Round 2 prompt

# Models that truncate in Round 2
MODEL1="nousresearch/hermes-4-405b"
MODEL2="mistralai/mistral-medium-3.1"

# Load the exact Round 2 prompt that triggers truncation
PROMPT=$(cat /tmp/round2_prompt.json)

echo "============================================================"
echo "Testing OpenRouter with EXACT Round 2 prompt that fails"
echo "============================================================"
echo ""
echo "Prompt length: $(echo "$PROMPT" | wc -c) characters"
echo ""

# Test Hermes-4-405b
echo "--- Testing $MODEL1 ---"
echo ""

echo curl -X POST https://openrouter.ai/api/v1/chat/completions -H "Content-Type: application/json" -H "Authorization: Bearer $OPENROUTER_API_KEY" -d "{ \"model\": \"$MODEL1\", \"messages\": [{ \"role\": \"user\", \"content\": $PROMPT }], \"max_tokens\": 8192, \"temperature\": 0.7 }"

curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -d "{
    \"model\": \"$MODEL1\",
    \"messages\": [{
      \"role\": \"user\",
      \"content\": $PROMPT
    }],
    \"max_tokens\": 8192,
    \"temperature\": 0.7
  }" | tee /tmp/hermes_round2_response.json

echo ""
echo "Response saved to: /tmp/hermes_round2_response.json"
echo ""
echo "Response content:"
cat /tmp/hermes_round2_response.json | jq '.choices[0].message.content'
echo ""
echo "Finish reason: $(cat /tmp/hermes_round2_response.json | jq -r '.choices[0].finish_reason')"
echo "Completion tokens: $(cat /tmp/hermes_round2_response.json | jq -r '.usage.completion_tokens')"
echo "Prompt tokens: $(cat /tmp/hermes_round2_response.json | jq -r '.usage.prompt_tokens')"
echo ""

# Test Mistral-Medium-3.1
echo "--- Testing $MODEL2 ---"
echo ""

curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -d "{
    \"model\": \"$MODEL2\",
    \"messages\": [{
      \"role\": \"user\",
      \"content\": $PROMPT
    }],
    \"max_tokens\": 8192,
    \"temperature\": 0.7
  }" > /tmp/mistral_round2_response.json

echo ""
echo "Response saved to: /tmp/mistral_round2_response.json"
echo ""
echo "Response content:"
cat /tmp/mistral_round2_response.json | jq '.choices[0].message.content'
echo ""
echo "Finish reason: $(cat /tmp/mistral_round2_response.json | jq -r '.choices[0].finish_reason')"
echo "Completion tokens: $(cat /tmp/mistral_round2_response.json | jq -r '.usage.completion_tokens')"
echo "Prompt tokens: $(cat /tmp/mistral_round2_response.json | jq -r '.usage.prompt_tokens')"
echo ""

echo "============================================================"
echo "ANALYSIS:"
echo "============================================================"
echo ""
echo "Check if content is truncated mid-word or mid-JSON"
echo "Check if finish_reason is 'stop' (normal) or 'length' (truncated)"
echo "Check if completion_tokens is suspiciously low (<200 for Round 2)"
echo ""
echo "Full responses saved to /tmp/*_round2_response.json for detailed inspection"
echo ""
