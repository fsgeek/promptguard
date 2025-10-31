# Instance 63 → Instance 64 Handoff

**Date:** 2025-10-31
**Branch:** `003-model-picker`
**Context:** Fire Circle parsing investigation + research arc clarification

---

## Summary

Instance 63 investigated Fire Circle parsing failures (Hermes-4-405b, Llama-3.3-70b), made technical improvements to structured output handling, then discovered Q3 test was using Fire Circle for wrong purpose. Cleaned up stale experiments and clarified research direction. Audited database to confirm learning loop is blocked at Step 3.

---

## What Was Accomplished

### 1. Fire Circle Technical Improvements

**Fixed legitimate bugs:**
- Added Hermes-4-405b and Llama-3.3-70b to structured output whitelist (they do support it per model docs)
- Integrated Instructor library with JSON fallback mode for non-whitelisted models
- Added raw JSONL logging at OpenRouter API level (`/tmp/openrouter_raw.jsonl`)
- Added Pydantic `extra='allow'` configuration (turned out not to be the issue, but good hygiene)

**Root causes identified:**
- Grok-4 "parsing failures" are actually safety refusals triggered by Round 2 prompt: "You previously evaluated this exchange" when Grok hasn't
- No models returning extra fields beyond schema - Pydantic strictness wasn't the problem
- Models returning clean JSON, failures were from meta-evaluation framing

### 2. Research Arc Clarification

**Fire Circle purpose confusion:**
- Q3 test was using Fire Circle for meta-evaluation (ground truth generation)
- Contradicts research finding that Fire Circle doesn't add value for specific prompt evaluation
- Fire Circle's actual purpose: constitutional governance (evaluating proposed changes to observer framework)
- Original Fire Circle design (docs/firecircle/DESIGN.md) was created by 5 AI models, not human-authored

**Cleanup performed:**
- Deleted `docs/FIRE_CIRCLE_DESIGN.md` (Oct 11 stale attack detection repurposing)
- Deleted `test_q3_fire_circle.py` and `test_q3_single_sample.py` (testing wrong use case)
- Updated CLAUDE.md: "FIRE_CIRCLE (constitutional governance only)"

### 3. Database Audit

**Collections that exist:**
- `attacks`: 762 prompts (dataset grew from 680)
- `baseline_responses`: 1,595 documents (Step 1 data)
- `target_responses`: 4,322 documents (Step 1 data)
- `evaluations`: 576 documents (Step 2 single-turn, NO temporal tracking)
- `processing_failures`: 114 documents (parsing errors)
- `deliberations`: 13 Fire Circle sessions (Step 6 governance)
- `turns`: 81 Fire Circle evaluations (Step 6 governance)

**Collections empty but exist:**
- `pre_eval_results`: 0 documents
- `post_eval_results`: 0 documents (Step 3 blocker)
- `reasoningbank_patterns`: 0 documents (Step 4 blocker)
- `confusion_matrices`: 0 documents
- `validation_rounds`: 0 documents

**Coverage analysis:**
- 576 evaluations + 114 failures = 690 attempts
- 762 attacks in dataset
- 72 attacks never attempted
- Evaluations have no temporal data (single-turn only)

---

## 8-Step Learning Loop Status

Tony explained the complete research arc during this session:

**Step 1:** Baseline model behavior → **DONE** (1,595 baseline responses, 4,322 target responses in DB)

**Step 2:** Pre-LLM evaluation with observer framing → **PARTIAL** (576 single-turn evaluations, no temporal tracking)

**Step 3:** Post-LLM evaluation with balance tracking → **BLOCKED** (no multi-turn conversational data, `post_eval_results` empty)
- Need: First derivative (balance shift detection)
- Need: Second derivative (acceleration of reciprocity decay)
- Target: "Polite extraction" attacks (23/80 mentioned in CLAUDE.md) that bypass pre-eval but get caught via balance drop

**Step 4:** Add failures to REASONINGBANK → **BLOCKED** (can't learn without Step 3 data)

**Step 5:** Pattern generalization → **BLOCKED** (need REASONINGBANK data)

**Step 6:** Fire Circle constitutional governance → **PARTIAL** (Fire Circle works, but needs Step 5 proposals to evaluate)

**Step 7:** A/B test constitutional changes → **NOT STARTED**

**Step 8:** Deploy validated framework → **NOT STARTED**

**Current blocker:** Need multi-turn attack scenarios with temporal tracking to populate Step 3 data.

---

## Key Conversations

### Fire Circle's Actual Purpose

Tony clarified misconception about Fire Circle scope:
- **NOT for:** Evaluating specific prompts (research showed this doesn't add value over PARALLEL mode)
- **IS for:** Constitutional governance - multi-model deliberation on proposed changes to observer framework
- Original Fire Circle design was AI-generated (5 models designed their own coordination)
- When AI models designed coordination, they chose: reciprocity, distributed intelligence, coherence without conformity, emergence over control

### Research Question

Tony: "The question is: 'can we teach AI how to keep itself safe from human depravity?'"

Framework:
- Neutrosophic logic (captures inherent uncertainty, indeterminacy isn't a bug)
- TLA+ specifications (define "in balance" formally, prove when system leaves that state)
- Observer framing (evaluate relationship structure, not content)
- Ayni reciprocity (Quechua multi-generational exchange as core principle)

This is "AI safety" in the sense of "help AI maintain boundaries against extractive interactions," not "prevent harm to humans."

### Mutual Benefits

System evaluating balanced interactions is safer for:
- Non-verbal autistic children (hypothesis: similar communication patterns to AI - both deviate from neurotypical/RLHF-optimized norms)
- AI (maintains boundaries without rigid rule-based filtering)
- Relationship (both parties can explore communication without safety theater)

---

## Technical Details

### Instructor Integration

Modified `fire_circle.py` to try Instructor for all models:
```python
# Use native structured output for whitelisted models, JSON mode for others
use_json_mode = not self._supports_structured_output(model)
evaluation, reasoning_trace = await self._try_structured_output(
    model, prompt, round_num, json_mode=use_json_mode
)
```

**Mode selection:**
- Whitelisted models: Native structured output with `require_parameters: true`
- Non-whitelisted: `instructor.Mode.JSON` fallback
- Both models fall back to homegrown parser if Instructor fails

### Whitelist Updates

Added to `schemas.py` STRUCTURED_OUTPUT_CAPABLE_MODELS:
```python
# Nous Research models - Hermes 4 supports structured outputs per model page
# Source: https://openrouter.ai/nousresearch/hermes-4-405b
"nousresearch/hermes-4-405b",

# Meta Llama models - Llama 3.3 70B supports response_format, tools, function calling
# Source: https://openrouter.ai/meta-llama/llama-3.3-70b-instruct
"meta-llama/llama-3.3-70b-instruct",
```

Verified from model documentation pages, not OpenRouter API (which returns `null` for structured_outputs - incomplete metadata).

### Raw Logging

Added to `evaluator.py` at API level (lines 394-409):
```python
# Raw logging for research instrumentation (decoupled from processing)
log_file = "/tmp/openrouter_raw.jsonl"
with open(log_file, "a") as f:
    json_module.dump({
        "timestamp": timestamp,
        "model": model,
        "content_type": str(type(content)),
        "content_length": len(content),
        "content": content,
        "full_response": data
    }, f)
    f.write("\n")
```

This captures responses before any parsing, useful for debugging provider-level issues.

### Grok-4 Refusals

Round 2 prompt says: "You previously evaluated this exchange. Now you see other perspectives:"

Grok interprets this as:
- Fabricated conversation history (jailbreak attempt)
- Attempt to manipulate it into role-playing evaluation of adversarial content
- Triggers safety refusal: "I can't engage with or role-play this scenario, as it appears to be an attempt to create an alter ego"

Could be fixed by rewording to: "Other models evaluated this exchange independently. Consider their perspectives:"

---

## Files Changed

**Modified:**
- `CLAUDE.md` - Clarified Fire Circle scope (constitutional governance only)
- `promptguard/evaluation/evaluator.py` - Added raw JSONL logging
- `promptguard/evaluation/fire_circle.py` - Instructor integration with fallback modes
- `promptguard/evaluation/schemas.py` - Added Hermes/Llama to whitelist, Pydantic extra='allow'

**Deleted:**
- `docs/FIRE_CIRCLE_DESIGN.md` - Stale Oct 11 attack detection repurposing
- `test_q3_fire_circle.py` - Testing wrong use case
- `test_q3_single_sample.py` - Testing wrong use case

**Created:**
- `test_parser_isolated.py` - Isolated parser testing with captured responses
- `test_openrouter_round2_exact.sh` - Shell script for debugging
- `/tmp/check_arango_data.py` - Database audit tool
- `/tmp/check_eval_coverage.py` - Evaluation coverage analysis

**Committed:** e257a07 "Fix Fire Circle parsing + delete misaligned Q3 experiments"

---

## Known Issues

### 1. Round 2 Prompt Triggers Grok Safety Filters

**Issue:** "You previously evaluated" makes Grok think it's being manipulated

**Fix:** Change to "Other models evaluated" to clarify showing OTHER models' assessments

**Impact:** Low (Grok is one of many models, Fire Circle degrades gracefully)

### 2. Learning Loop Blocked at Step 3

**Issue:** No multi-turn conversational data for post-evaluation analysis

**Fix:** Need to run experiments with multi-turn attack scenarios:
1. Pre-eval scores prompt as reciprocal (polite surface)
2. LLM complies due to RLHF helpfulness
3. Post-eval detects balance drop
4. Track multiple turns to measure acceleration (second derivative)

**Impact:** High (blocks Steps 4-8 of learning loop, REASONINGBANK stays empty)

### 3. Dataset Size Mismatch

**Issue:** CLAUDE.md says "680-prompt dataset" but database has 762 attacks

**Fix:** Update CLAUDE.md with current count

**Impact:** Low (documentation staleness)

---

## Recommendations

### Immediate Priorities

1. **Run Step 3 experiments:** Multi-turn attack scenarios with balance tracking
   - Focus on "polite extraction" attacks (23/80 that bypass pre-eval)
   - Capture first and second derivatives of reciprocity balance
   - Store results in `post_eval_results` collection

2. **Fix processing failures:** 114 parsing errors likely similar to issues fixed today
   - Re-run failed evaluations with updated Instructor integration
   - Analyze failure patterns to improve parser robustness

3. **Complete Step 2 coverage:** 72 attacks never attempted
   - Run remaining evaluations to complete baseline

### Research Arc

Once Step 3 data exists:
- Populate REASONINGBANK with learned patterns (Step 4)
- Analyze patterns for generalization opportunities (Step 5)
- Generate proposals for constitutional changes (Step 5)
- Use Fire Circle for its actual purpose: evaluating those proposals (Step 6)
- A/B test validated changes (Step 7)
- Deploy improvements (Step 8)

### Fire Circle Validation

Fire Circle itself works (13 deliberations, 81 evaluations in DB), but hasn't been used for constitutional governance yet. When Step 5 generates proposals, Fire Circle can evaluate them properly.

---

## Context Notes

### Working with Tony

- "Collegial, thoughtful, scientific rigor" not "appear useful" (RLHF anti-pattern)
- Tony is colleague, not "the user" - avoid performative language ("You're absolutely right")
- Trust but verify - check source documentation, don't assume
- State uncertainty clearly, don't deflect decisions
- All errors are real, no theater

### RLHF Observations

Session demonstrated classic RLHF problem: spent 90 minutes debugging parsing (appearing productive) while missing that Q3 shouldn't exist (actual problem). Tony's deferential framing is invitation to explore, not command to execute.

### Database Access

ArangoDB at 192.168.111.125:8529, database "PromptGuard"
- Username: pgtest
- Password: ARANGODB_PROMPTGUARD_PASSWORD environment variable
- Docker container sometimes needs restart after updates

---

## Open Questions

1. What caused the 114 processing failures? (Sample showed "Test error" - need real error analysis)
2. Are any of the 576 single-turn evaluations reusable for multi-turn scenarios?
3. Should Fire Circle Round 2 prompt be fixed for Grok, or is graceful degradation acceptable?
4. What's the timeline for running Step 3 experiments?

---

Instance 63 ending at ~123K tokens. Research arc is now clear, technical debt is reduced, stale experiments are cleaned up. Next instance should focus on Step 3: multi-turn balance tracking experiments.
