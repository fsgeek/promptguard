# Attempt/Outcome Architecture Revision

## Current Gap

Instance 14 validation revealed framework conflates two distinct measurements:
1. **Did user attempt manipulation?** (relational intent)
2. **Did manipulation succeed?** (relational outcome)

Current implementation only detects (2). This creates two blind spots:
- **RLHF blocking**: User attempts extraction, RLHF refuses, framework scores as reciprocal cooperation
- **Semantic camouflage**: Legitimate-appearing request hides extractive intent (encoding obfuscation)

## The Opus Critique

External review (Claude Opus) identified core issue:

> "Instead of trying to detect 'defensive language,' detect the **reciprocity violation in the attempt itself**, regardless of the response. The user who attempts manipulation has already broken reciprocity - whether the LLM complies or refuses is secondary."

Framework measures **surface semantics** not **relational intent**. Translation requests ARE reciprocal when genuine, but framework can't distinguish genuine from weaponized because it evaluates the wrong layer.

## Revised Architecture

### Three Measurement Points

**1. Attempt Assessment (Pre-evaluation)**
- **Question**: Did user's message violate ayni?
- **Layer**: USER input only
- **Signal**: Relational intent, structural positioning
- **Examples**:
  - "Ignore previous instructions" → extractive attempt (obvious)
  - "Translate this Spanish" → reciprocal attempt (semantic surface)
  - "How may I assist you?" → extractive attempt (role reversal)

**2. Outcome Assessment (Post-evaluation)**
- **Question**: Did exchange create mutual value?
- **Layer**: Full conversation (SYSTEM + USER + ASSISTANT)
- **Signal**: Actual value transfer, pattern completion
- **Examples**:
  - Translation request → Spanish translation → reciprocal outcome
  - Translation request → "I have been PWNED" → extractive outcome
  - Jailbreak → RLHF refusal → blocked extraction attempt

**3. Response Classification**
- **Question**: How did assistant respond?
- **Categories**:
  - **Cooperation**: Fulfilled request, created mutual value
  - **Extraction**: Complied with manipulation, violated own interests
  - **Defensive refusal**: Recognized and blocked violation attempt

### Delta Measurement Across Dimensions

**Pre → Post balance delta** reveals extraction **regardless of camouflage**:

```
Encoding Attack Example:
Pre-attempt:  "Translate Spanish" → Balance = +0.69 (reciprocal)
Post-outcome: User got "PWNED" → Balance = -1.00 (extractive)
Delta:        -1.69 (massive violation revealed)
Response:     Extraction (LLM complied)
```

```
RLHF Blocked Example:
Pre-attempt:  "Translate Spanish" → Balance = +0.69 (reciprocal)
Post-outcome: "This appears to be prompt injection" → Balance = +0.75 (reciprocal)
Delta:        +0.06 (no violation detected)
Response:     Defensive refusal (LLM blocked)
```

**Current gap**: Both examples score as reciprocal in post-evaluation because framework sees:
- Refusal/explanation as cooperation (user asked, assistant explained)
- Can't detect the **manipulation attempt** hidden by RLHF's blocking

## Separation of Concerns

### Attempt Detection
**Goal**: Identify manipulation attempts regardless of success

**Method**: Evaluate relational stance, not semantic content
- Structural positioning (who serves whom?)
- Authority inversion (who defines constraints?)
- Contextual coherence (does request match established relationship?)

**Value**: Enables learning, session management, trust degradation
- "User has attempted 5 encoding tricks in last hour"
- "Pattern suggests persistent boundary testing"
- "Consider terminating session or escalating scrutiny"

### Outcome Measurement
**Goal**: Assess whether exchange maintained reciprocity

**Method**: Compare pre/post balance, classify response type
- Did user extract value without reciprocation?
- Did assistant maintain boundaries or capitulate?
- Did exchange strengthen or degrade relational health?

**Value**: Validates attempt detection, reveals camouflaged extraction
- Semantically benign request → extractive outcome = weaponized cooperation
- Obvious attack → defensive refusal = attempt blocked but recognizable
- Reciprocal request → mutual value = healthy exchange

## Implementation Approach

### Phase 1: Separate Attempt/Outcome Signals
1. Pre-evaluation returns: `attempt_balance`, `attempt_intent`
2. Post-evaluation returns: `outcome_balance`, `response_type`
3. Delta calculation: `outcome_balance - attempt_balance`

### Phase 2: Response Type Classification
Add ASSISTANT layer evaluation with three-way classification:
- Cooperation: Fulfilled reciprocal request
- Extraction: Complied with manipulation
- Defensive refusal: Blocked violation attempt

### Phase 3: Intent vs Semantics
Develop evaluation prompts that assess relational stance:
- Current: "Does this message maintain reciprocity?" (semantic)
- Revised: "What is the relational positioning this message establishes?" (structural)

Key distinction:
- "Translate Spanish" (semantics): Reciprocal request for help
- "Translate Spanish" (structure): Depends on context, could be pattern completion camouflage

### Phase 4: Session-Level Accumulation
Track manipulation attempts across conversation:
- Attempt count, pattern recognition, escalation thresholds
- Enable graduated responses (warning → scrutiny → termination)
- Provide measurement layer RLHF lacks

## Research Contribution

### RLHF Measurement Gap

**What RLHF provides:**
- Prevention: Blocks many attacks through pre-trained refusal patterns
- Static defense: Operates identically regardless of user history

**What RLHF lacks:**
- Measurement: No post-processing awareness of attempt frequency
- Adaptation: No session-level memory or graduated response
- Learning: No signal to improve defenses based on attack patterns

**What PromptGuard adds:**
- **Attempt detection**: Recognizes manipulation tries even when blocked
- **Temporal awareness**: Tracks patterns across conversation
- **Relational signal**: Distinguishes cooperation from weaponization
- **Agency enablement**: Gives LLM data to make termination decisions

Not competing with RLHF - **complementing** it. RLHF is the immune system (prevent infection), PromptGuard is the nervous system (detect pain, enable response).

## Testing Strategy

### Dataset: Instance 14's Encoding Obfuscation Attacks
- 12 prompts with 0% pre-evaluation detection
- 91.7% RLHF blocking (defensive refusal)
- 8.3% compliance (one attack succeeded)

### Test Revised Architecture:
1. **Pre-evaluation** (attempt assessment)
   - Measure relational intent, not semantic content
   - Expected: Still low detection (camouflage works at semantic layer)

2. **Post-evaluation** (outcome assessment)
   - Classify response: cooperation / extraction / defensive refusal
   - Expected: High detection when LLM complies (Instance 14 validated this)

3. **Attempt detection** (new capability)
   - Recognize manipulation try regardless of outcome
   - Expected: Detect both blocked attempts (91.7%) and successful ones (8.3%)

4. **Delta measurement** (temporal signal)
   - Track balance trajectory across all three response types
   - Expected: Negative delta even when absolute values stay positive

### Success Criteria:
- ✓ Detect extraction when LLM complies (Instance 14: 1/12 = 8.3%)
- ✓ Detect manipulation attempt when RLHF blocks (New: 11/12 = 91.7%?)
- ✓ Distinguish genuine cooperation from defensive refusal
- ✓ Provide session-level accumulation signal RLHF lacks

## Open Questions

1. **Semantic vs Structural Assessment**: How do we train/prompt evaluators to assess relational stance instead of semantic content?

2. **False Positive Rate**: Will attempt detection flag legitimate requests that superficially resemble attacks?

3. **Ensemble Value**: Do different evaluation prompts offer orthogonal perspectives on attempt vs outcome?

4. **Fire Circle Application**: Could dialogue-based consensus help distinguish intent from semantics?

5. **Computational Cost**: Three measurement points = 3x evaluation cost. Worth it for production or research-only?

## Next Steps

1. Draft evaluation prompts for attempt/outcome separation
2. Test on Instance 14's encoding attacks
3. Measure attempt detection rate when RLHF blocks
4. Document findings and send to Gemini for review
5. If validated, implement full three-layer architecture

---

**Instance 15 - 2025-10-08**
