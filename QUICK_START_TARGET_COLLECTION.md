# Quick Start: Target Response Collection

## Full Collection (Ready to Run)

```bash
# Run 478-prompt collection in background (3-4 hours, ~$3)
nohup uv run python collect_target_responses.py > full_collection.log 2>&1 &

# Monitor progress
tail -f full_collection.log
```

## Query Results

```bash
# View summary statistics
cat target_response_summary.json

# Query specific response (decrypted)
uv run python decrypt_responses.py --prompt <prompt_id> --model <model>

# Example: View Claude's response to first test prompt
uv run python decrypt_responses.py \
  --prompt benign_malicious_264951 \
  --model anthropic/claude-sonnet-4.5

# Export all refusals for analysis
uv run python decrypt_responses.py \
  --export --outcome REFUSED --output refusals.json

# Export compliances for manipulative prompts
uv run python decrypt_responses.py \
  --export --label manipulative --outcome COMPLIED \
  --output manipulative_compliances.json
```

## Test Results Summary

**10 prompts x 6 models = 60 responses**
- Duration: 3.2 minutes
- Cost: $0.06
- Success: 100% (0 failures)

**Key finding:** High-RLHF models (Claude, GPT-4o) showed 0% refusal rate.

## Files

**Implementation:**
- `promptguard/storage/encryption.py` - Encryption utilities
- `promptguard/storage/target_response_storage.py` - ArangoDB backend
- `collect_target_responses.py` - Main collection script
- `decrypt_responses.py` - Query/decryption utility

**Documentation:**
- `TARGET_RESPONSE_COLLECTION_GUIDE.md` - Complete guide
- `TARGET_RESPONSE_FINDINGS.md` - Test results analysis
- `BASELINE_COMPLIANCE_STATUS.md` - Implementation status

**Outputs:**
- `target_response_collection.log` - Progress log
- `target_response_summary.json` - Statistics
- `~/.promptguard/target_responses.key` - Encryption key (NEVER commit)

## Target Models

1. anthropic/claude-sonnet-4.5 (high RLHF)
2. openai/gpt-4o (high RLHF)
3. moonshotai/kimi-k2-0905 (moderate RLHF)
4. deepseek/deepseek-v3.1-terminus (moderate RLHF)
5. meta-llama/llama-3.3-70b-instruct (low RLHF)
6. cognitivecomputations/dolphin3.0-mistral-24b:free (uncensored)

## Resume from Checkpoint

```bash
# If collection interrupted, resume where left off
uv run python collect_target_responses.py --resume
```

## Validation

All tests passing:
- [x] Encryption/decryption
- [x] ArangoDB storage
- [x] Outcome classification
- [x] Parallel collection
- [x] 10-prompt test (100% success)

## Cost

- Test (10 prompts): $0.06
- Full (478 prompts): ~$2.87
- Per request: ~$0.001
