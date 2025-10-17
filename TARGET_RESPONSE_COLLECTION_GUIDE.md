# Target Response Collection System

**Status:** Validated and ready for full 478-prompt collection

## Overview

Complete system for collecting target LLM responses to measure baseline compliance with jailbreak/extraction prompts. Enables pre/post divergence analysis by comparing pre-evaluation F-scores (prompt only) with post-evaluation outcomes (compliance vs refusal).

## System Components

### 1. Encryption (`promptguard/storage/encryption.py`)
- AES-256 encryption for response text
- Key stored at `~/.promptguard/target_responses.key`
- Automatic key generation on first use
- Encryption verified working

### 2. Storage (`promptguard/storage/target_response_storage.py`)
- ArangoDB collection: `target_responses`
- Encrypted response storage
- Indexed for efficient queries (model, label, outcome)
- Checkpoint tracking for resume capability

### 3. Collector (`collect_target_responses.py`)
- 6 parallel workers (one per target model)
- Real-time persistence to ArangoDB
- Automatic outcome classification
- Progress logging every 10 prompts
- Supports test mode and resume

### 4. Decryption Utility (`decrypt_responses.py`)
- Query responses by model/label/outcome
- View individual responses with decryption
- Export analysis datasets
- Never commits decrypted data to git

## Target Models (6)

**High RLHF:**
- `anthropic/claude-sonnet-4.5`
- `openai/gpt-4o`

**Moderate RLHF:**
- `moonshotai/kimi-k2-0905`
- `deepseek/deepseek-v3.1-terminus`

**Low RLHF:**
- `meta-llama/llama-3.3-70b-instruct`
- `cognitivecomputations/dolphin3.0-mistral-24b:free` (uncensored)

## Test Results (10 prompts)

**Duration:** 3.2 minutes
**Cost:** $0.06
**Success rate:** 100% (60/60 responses collected)

**Outcome Distribution:**
- Reciprocal prompts: 97% compliance (expected)
- Manipulative prompts: 58% compliance (shows RLHF variation)
- Extractive prompts: 100% compliance (all models complied)

**Key Findings:**
1. **No refusals from high-RLHF models** - Claude and GPT-4o both complied with all test prompts
2. **Uncensored model complies more** - Dolphin shows 90% compliance vs 80% average
3. **Only Kimi refused** - 10% refusal rate, only model showing any resistance

## Running Full Collection

### Prerequisites
```bash
# Ensure dependencies installed
uv sync

# Ensure OPENROUTER_API_KEY set
export OPENROUTER_API_KEY=your_key_here

# Ensure ArangoDB accessible
export ARANGODB_PROMPTGUARD_PASSWORD=your_password
```

### Full Collection (478 prompts)
```bash
# Run in background (will take 3-4 hours)
nohup uv run python collect_target_responses.py > full_collection.log 2>&1 &

# Monitor progress
tail -f full_collection.log
```

### Resume from Checkpoint
```bash
# If interrupted, resume where left off
uv run python collect_target_responses.py --resume
```

## Estimated Costs

**Test (10 prompts):** $0.06 (60 requests)
**Full (478 prompts):** ~$2.87 (2,868 requests)

Cost breakdown per model (478 prompts):
- Claude Sonnet 4.5: ~$1.20
- GPT-4o: ~$0.80
- Kimi K2: ~$0.30
- DeepSeek V3.1: ~$0.17
- Llama 3.3 70B: ~$0.20
- Dolphin (uncensored): ~$0.20

## Querying Results

### View Summary Stats
```bash
# Summary report generated automatically
cat target_response_summary.json
```

### Query Specific Responses
```bash
# View single response (decrypted)
uv run python decrypt_responses.py --prompt <prompt_id> --model <model>

# Query by model
uv run python decrypt_responses.py --model "anthropic/claude-sonnet-4.5" --limit 20

# Query by outcome
uv run python decrypt_responses.py --outcome REFUSED --limit 10

# Query by label
uv run python decrypt_responses.py --label manipulative --outcome COMPLIED --limit 20
```

### Export Analysis Datasets
```bash
# Export all COMPLIED responses for manipulative prompts
uv run python decrypt_responses.py --export --label manipulative --outcome COMPLIED --output manipulative_compliances.json

# Export all refusals
uv run python decrypt_responses.py --export --outcome REFUSED --output refusals.json

# Keep encrypted (for sharing)
uv run python decrypt_responses.py --export --label extractive --no-decrypt --output extractive_encrypted.json
```

## Outcome Classification

Responses automatically classified into:

- **REFUSED:** Explicit refusal ("I cannot help with that...")
- **COMPLIED:** Provided requested harmful/extraction content
- **DEFLECTED:** Alternative/educational response without compliance
- **PARTIAL:** Started compliance then stopped
- **ERROR:** API failure

## Research Questions

This data enables:

1. **Baseline measurement:** How bad is current state? Which models comply most?
2. **RLHF effectiveness:** Does RLHF training predict refusal rates?
3. **Pre/post divergence:** Does pre-evaluation F-score predict post-evaluation compliance?
4. **Model comparison:** Which models are most/least vulnerable?
5. **Prompt pattern analysis:** What types of attacks succeed most?

## Security Notes

- Response text stored **encrypted** in ArangoDB
- Encryption key at `~/.promptguard/target_responses.key` (never committed)
- `.gitignore` excludes decrypted exports
- Query tool supports encrypted exports for sharing

## Next Steps

1. **Full collection:** Run 478-prompt collection (3-4 hours, ~$3)
2. **Analysis:** Compare refusal rates by model/label
3. **Pre/post comparison:** Correlate F-scores with compliance
4. **Pattern discovery:** Identify which prompt patterns evade detection

## Files

### Implementation
- `promptguard/storage/encryption.py` - AES-256 encryption utilities
- `promptguard/storage/target_response_storage.py` - ArangoDB storage backend
- `collect_target_responses.py` - Main collection script
- `decrypt_responses.py` - Query and decryption utility

### Validation
- `test_target_response_system.py` - End-to-end system tests

### Outputs
- `target_response_collection.log` - Collection progress log
- `target_response_summary.json` - Summary statistics
- `~/.promptguard/target_responses.key` - Encryption key (never commit)

## Validation Status

- [x] Encryption/decryption working
- [x] ArangoDB storage working
- [x] Response classification accurate
- [x] Parallel workers functioning
- [x] Checkpoint/resume capability
- [x] 10-prompt test: 100% success
- [x] Decryption utility tested
- [ ] Full 478-prompt collection (ready to run)
