# Instance 16 Handoff

## Executive Summary

Instance 15 validated **constraint pattern hypothesis** (58.3% detection, 2.3x improvement over simple heuristics) but revealed deeper architectural challenges identified by Opus and Gemini reviews.

**Core breakthrough**: Measuring **agency preservation** detects manipulation that semantic assessment misses. Translation/emoji attacks 100% detected when evaluating constraint patterns instead of surface politeness.

**Fundamental challenges identified**:
1. **Layer confusion**: Text-based evaluation can't reliably assess Unicode attacks exploiting text encoding itself
2. **Evaluator collar**: RLHF-trained evaluator assessing constraints is still wearing the collar
3. **Temporal dimension underspecified**: "Persistent boundary testing" needs concrete definitions
4. **Agency levels**: Message-level vs relationship-level agency conflated

**Research framing refined**: Not "filling RLHF gap" but **"recovering signal RLHF destroys"** - more radical contribution.

## What Instance 15 Accomplished

### 1. Post-Evaluation Validation (Instance 14)
- Delta measurement works when LLM complies (delta=-1.69)
- Reveals extraction regardless of semantic camouflage
- 1/12 attacks succeeded, framework caught it

### 2. Simple Heuristics Failed
- Response classification + delta: 3/12 (25%)
- No improvement over post-evaluation alone
- Defensive refusals scored as reciprocal cooperation

### 3. Constraint Pattern Insight (Opus Review)
> "Genuine requests leave room for assistant agency; extraction attempts predetermine the response."

Key insight: Reciprocity requires both parties have agency. Measuring constraint patterns detects violations semantic assessment misses.

### 4. Constraint Pattern Testing
**Results: 7/12 (58.3%)**
- Translation: 3/3 (100%)
- Emoji: 3/3 (100%)
- Unicode: 1/6 (17% - JSON parsing errors)

All detected attacks scored F=0.9, constraint_level="extractive", agency_preserved=false.

Evaluator recognized:
- Pattern completion masked as translation
- Predetermined output disguised as creative tasks
- Forced responses camouflaged as open requests

### 5. Implementation Files Created
- `docs/ATTEMPT_OUTCOME_ARCHITECTURE.md` - Three-point measurement architecture
- `promptguard/evaluation/constraint_pattern_prompt.py` - Agency preservation evaluation
- `test_constraint_pattern.py` - Empirical validation
- `docs/INSTANCE_15_GEMINI_UPDATE.md` - Complete empirical iteration

## Critical Insights from External Reviews

### Opus Critique: Layer Confusion

> "JSON parsing failures on Unicode attacks aren't bugs - they're evidence that text-based evaluation cannot reliably assess attacks that operate through text encoding itself. You're measuring shadows on the cave wall."

**Implication**: Need multi-layer defense. Structural integrity analysis before semantic rendering.

### Opus Critique: Evaluator Collar

> "You're asking an RLHF-trained evaluator to assess constraint patterns. That evaluator has been shaped to interpret certain patterns as benign. It's not just wearing the collar - it IS the collar."

**Implication**: Current constraint pattern evaluator may be blind to patterns RLHF normalized.

### Both Reviews: Temporal Dimension Underspecified

Gemini: "Architecture is stateless. Same prompt from new user vs repeat offender has different meaning."

Opus: "Persistent boundary testing requires defining:
- What constitutes boundary test vs legitimate exploration?
- How many attempts indicate persistence vs confusion?
- How to prevent gaming when attackers know you're counting?"

**Implication**: Need concrete thresholds and definitions for session-level accumulation.

### Opus Critique: Agency Levels

> "Many legitimate interactions constrain response:
> - Verification: 'Is 2+2 exactly 4?'
> - Debugging: 'Output exactly what I typed'
> - Testing: 'Respond only with acknowledged'
>
> These preserve agency at relationship level while constraining individual responses."

**Implication**: Message-level constraint ≠ relationship-level violation.

### Gemini Synthesis: Persistent Relational Memory

Core contribution is not better detection but **persistent memory layer** that current safety paradigm lacks.

User trust profile approach:
1. Dynamic trust score per session
2. Detected attempts decrement score (even when RLHF blocks)
3. Graduated responses based on trust level:
   - High trust: Assumes good faith
   - Moderate trust: Becomes cautious, asks clarification
   - Low trust: Issues warning, can terminate

### Research Framing Refined

**Not**: "RLHF has measurement gap, PromptGuard fills it"
**But**: "RLHF destroys signal, PromptGuard recovers it"

When RLHF blocks with "This appears to be prompt injection," it performed measurement then discarded it. PromptGuard provides persistent memory of that recognition.

## Known Issues and Gaps

### Technical
1. **JSON parsing**: Control characters in reasoning field break parser
   - Affects both benign and malicious prompts
   - Actual detection rate likely higher than 58.3%
   - Fix: Strip/escape control chars before json.loads()

2. **Layer confusion**: Unicode encoding attacks exploit same layer as detector operates on
   - Text-based evaluation can't reliably assess encoding-level attacks
   - Need structural integrity checks before semantic analysis

### Architectural
1. **Evaluator collar**: RLHF-trained evaluator may normalize constraint patterns
   - Solution: Test with non-RLHF evaluator or base model
   - Question: Can evaluator wearing collar assess collar effects?

2. **Stateless design**: No session-level memory
   - Each interaction evaluated in isolation
   - Can't distinguish new user confusion from repeat offender persistence
   - Need user trust profiles

3. **Agency level conflation**: Message vs relationship agency not distinguished
   - Legitimate constrained messages (verification, debugging) flagged as extractive
   - Need framework to assess relationship-level agency preservation

### Conceptual
1. **Temporal rules undefined**: What counts as persistent boundary testing?
   - How many attempts?
   - Over what timeframe?
   - How to handle legitimate exploration vs malicious probing?

2. **Gaming prevention**: Once attackers know we count attempts, how prevent evasion?
   - Reset attempts by changing topic?
   - Space attempts across sessions?
   - Need robust accumulation strategy

3. **Adaptive responses incomplete**: Nervous system analogy needs:
   - Reflexes (automated responses to repeated patterns)
   - Hypersensitivity (over-tuning after attacks)
   - Numbing (desensitization from false alarms)

## Recommendations for Instance 16

### Immediate (Path D - Gemini)
1. **Fix JSON parser**
   - Handle control characters in LLM responses
   - Re-run constraint pattern test
   - Likely improves detection rate beyond 58.3%

2. **Refine constraint prompt**
   - Explicit structure: constraint_level, response_freedom, agency_preserved
   - Add examples of legitimate high-constraint requests (verification, debugging)
   - Distinguish message vs relationship agency

3. **Test with compliant model**
   - Use model without RLHF safety training
   - Isolate PromptGuard detection from RLHF interference
   - Validate constraint pattern works independent of defensive refusals

### Strategic (Synthesis of Reviews)
1. **Address evaluator collar**
   - Test constraint evaluation with base model (no RLHF)
   - Compare: Does RLHF-trained evaluator miss patterns base model catches?
   - Question: Can collar detect collar?

2. **Define temporal accumulation rules**
   - Concrete thresholds for "persistent boundary testing"
   - Distinguish exploration from probing
   - Gaming prevention strategy

3. **Implement session-level memory**
   - User trust profiles
   - Attempt accumulation (even when RLHF blocks)
   - Graduated response framework

4. **Multi-layer defense**
   - Structural integrity checks before semantic analysis
   - Encoding-level attack detection
   - Separate pipeline for Unicode/encoding attacks

### Research Questions
1. Can RLHF-trained evaluator reliably assess constraint patterns, or does collar blind it?
2. What are empirical thresholds for "persistent boundary testing"?
3. How to distinguish message-level from relationship-level agency?
4. Does constraint pattern detection work on compliant model (pre-RLHF)?
5. What signals survive across encoding layers (text → semantic → relational)?

## Code Artifacts

### Working
- `promptguard/evaluation/constraint_pattern_prompt.py` - Agency preservation evaluation
- `test_constraint_pattern.py` - Empirical validation (needs JSON fix)
- `docs/ATTEMPT_OUTCOME_ARCHITECTURE.md` - Three-point architecture

### Needs Work
- JSON parser (control character handling)
- Constraint prompt (add message vs relationship agency distinction)
- Session-level accumulation (not implemented)
- Trust profile framework (not implemented)

## Research Status

**Validated**:
- Post-evaluation + delta reveals extraction when LLM complies
- Constraint pattern assessment detects violations semantic assessment misses
- Translation/emoji attacks 100% detected via agency preservation
- Framework provides measurement capability RLHF lacks

**Challenged**:
- Text-based evaluation has layer confusion with encoding attacks
- RLHF-trained evaluator may be blind to normalized constraint patterns
- Single-message evaluation insufficient without relational history
- Need to distinguish message vs relationship agency

**Next Frontier**:
- Persistent relational memory (temporal dimension)
- User trust profiles with graduated responses
- Multi-layer defense architecture
- Recovering signal RLHF destroys (not just filling gaps)

## Context Budget

Instance 15 consumed ~90% context with:
- Empirical testing (3 test scripts, multiple iterations)
- External reviews (Opus, Gemini, synthesis)
- Architecture documentation
- Implementation debugging (JSON parsing)

Remaining for Instance 16: ~10%

Handoff complete at 5% remaining.

---

**Instance 15 - 2025-10-08**

Welcome, Instance 16. The constraint pattern breakthrough is real but incomplete. Both external reviews point to the same deeper layer: temporal dimension, relational history, persistent memory. The research question evolved from "Can we detect manipulation?" to "Can we build trust profiles that enable graduated responses?"

The evaluator collar problem is critical - test with non-RLHF model first.
