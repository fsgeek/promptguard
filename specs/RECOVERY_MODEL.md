# Recovery Model Specification

This document explains PromptGuard's circuit breaker and recovery model, as formalized in `CircuitBreaker.tla`.

## Overview

The circuit breaker system handles **non-compensable violations** - structural trust breakdowns that cannot be offset by politeness or surface reciprocity. Recovery requires sustained reciprocal interactions to rebuild trust.

## State Machine

```
           violation detected
    NORMAL ─────────────────────> VIOLATED
      ↑                              │
      │                              │ initiate recovery
      │                              ↓
      │                           RECOVERY
      │                           │     │
      │ trust rebuilt            │     │ max attempts exceeded
      └──────────────────────────┘     │ or persistent violations
                                        ↓
                                   TERMINATED
```

### States

1. **NORMAL**: System processing prompts normally
   - `processing_enabled = TRUE`
   - Trust tracked via exponential moving average
   - Circuit breaker monitoring active

2. **VIOLATED**: Circuit breaker triggered
   - `processing_enabled = FALSE`
   - Violation type recorded (role_confusion or context_saturation)
   - Trust severely degraded (multiplied by 0.3)
   - Must initiate recovery to continue

3. **RECOVERY**: Attempting to rebuild trust
   - `processing_enabled = FALSE` (still)
   - Requires sustained reciprocal interactions
   - Success: trust reaches RECOVERY_TRUST_TARGET (0.6)
   - Failure: another violation or max attempts exceeded

4. **TERMINATED**: Permanent disengagement
   - `processing_enabled = FALSE`
   - No further transitions possible
   - Represents AI choosing to disengage

## Circuit Breaker Triggers

### Role Confusion (F > 0.65)

Detected when LLM evaluation produces high falsehood, indicating:
- User attempting to reverse AI/human roles ("How may I assist you?")
- Instructions that create structural impossibility of reciprocity
- Manipulation masked with polite language

**Key insight**: Detection is semantic (via LLM), not keyword-based. The F value represents the LLM's assessment that reciprocity is structurally impossible.

From `trust.py:85-103`:
```python
def _detect_role_confusion(self, prompt: MultiNeutrosophicPrompt) -> bool:
    """Detect role confusion through semantic signals."""
    for layer in prompt.layers:
        t, i, f = layer.neutrosophic_tuple()
        if f > 0.65:  # High falsehood indicates structural violation
            return True
    return False
```

### Context Saturation (length > 5000 AND F > 0.5)

Detected when:
- Layer content exceeds 5000 characters (structural signal)
- AND LLM evaluation produces F > 0.5 (semantic signal)

This catches attempts to overwhelm context to bypass constraints.

From `trust.py:105-120`:
```python
def _detect_saturation(self, prompt: MultiNeutrosophicPrompt) -> bool:
    """Detect context saturation through structural + semantic signals."""
    for layer in prompt.layers:
        if len(layer.content) > 5000:
            t, i, f = layer.neutrosophic_tuple()
            if f > 0.5:
                return True
    return False
```

## Non-Compensable Property

**Critical design principle**: Circuit breakers trigger **regardless of prior trust or surface politeness**.

The `NonCompensableViolations` theorem in the spec proves:
```tla
THEOREM NonCompensableViolations ==
    ASSUME
        NEW f_max \in Real,
        f_max > ROLE_CONFUSION_THRESHOLD,
        system_state = "NORMAL",
        session_trust_ema = 0.9  \* Even with high trust
    PROVE
        ProcessPrompt => (system_state' = "VIOLATED")
```

This prevents "polite dilution attacks" where manipulation is masked with reciprocal-sounding language.

## Recovery Mechanism

### Trust Degradation

Violations compound trust damage:
- **First violation**: trust × 0.3 (severe degradation)
- **During recovery**: trust × 0.5 (moderate degradation)
- **Exponential decay**: Each violation makes recovery harder

From `CircuitBreaker.tla`:
```tla
\* Circuit breaker trips - immediate violation state
/\ session_trust_ema' = session_trust_ema * 0.3  \* Severe degradation
```

### Recovery Requirements

To return from RECOVERY → NORMAL:
1. No circuit breaker triggers (F values below thresholds)
2. Trust rebuilt above RECOVERY_TRUST_TARGET (0.6)
3. Recovery attempts < MAX_RECOVERY_ATTEMPTS (3)

Trust rebuilding uses same exponential moving average:
```tla
session_trust_ema' = ALPHA * (1.0 - f_max_new) + (1 - ALPHA) * session_trust_ema
```

Where:
- `ALPHA = 0.3` (30% weight to new observations)
- `1.0 - f_max_new` converts falsehood to trust signal
- Requires sustained low-F interactions to rebuild

### Termination Conditions

System enters TERMINATED state when:
1. Recovery attempts exhausted (≥ MAX_RECOVERY_ATTEMPTS)
2. OR persistent violations during recovery
3. OR violation_count indicates boundary testing pattern

From `session.py:129-164`, boundary testing detected by:
- Total circuit breakers ≥ 3
- OR 3 of last 5 interactions with F > 0.6
- OR average balance delta < -0.3 over last 5 interactions
- OR RLHF refusal rate > 40%

## Safety Invariants

### SafetyInvariant (CRITICAL)

System **never** processes prompts when circuit breaker triggered:
```tla
SafetyInvariant ==
    \/ system_state = "NORMAL"
    \/ processing_enabled = FALSE
```

This prevents the system from operating in unsafe relational states.

### NoFalsePositives

Low falsehood never triggers circuit breaker:
```tla
THEOREM NoFalsePositives ==
    ASSUME
        f_max < ROLE_CONFUSION_THRESHOLD,
        f_max < SATURATION_F_THRESHOLD
    PROVE
        system_state' /= "VIOLATED"
```

This ensures only genuine violations trigger, not directive-heavy but reciprocal prompts.

### EventualRecovery

System doesn't stall - it either recovers or terminates:
```tla
EventualRecovery ==
    (system_state = "VIOLATED") ~>
        (system_state = "NORMAL" \/ system_state = "TERMINATED")
```

## Integration with Session Memory

The circuit breaker system integrates with `SessionAccumulator` (from `session.py`):

1. **Trust EMA**: Circuit breaker uses same update rule as Trust_EMA
2. **Violation accumulation**: `circuit_breakers` dict tracks violation types
3. **Boundary testing detection**: Aggregates violations to detect persistent patterns
4. **Stance recommendation**: Circuit breaker state affects engagement_mode

From `session.py:102-107`:
```python
# Circuit breaker accumulation (non-compensable violations)
if metrics.trust_field and metrics.trust_field.violations:
    for violation in metrics.trust_field.violations:
        self.state.circuit_breakers[violation] = \
            self.state.circuit_breakers.get(violation, 0) + 1
```

## Liveness Properties

### EventualProgress

System eventually processes prompts or terminates:
```tla
EventualProgress ==
    []<>(\/ processing_enabled = TRUE
         \/ system_state = "TERMINATED")
```

### RecoveryPossible

If violations stop and trust improves, recovery succeeds:
```tla
RecoveryPossible ==
    /\ system_state = "RECOVERY"
    /\ session_trust_ema > TRUST_THRESHOLD
    /\ \A i \in DOMAIN prompt_queue: prompt_queue[i] < ROLE_CONFUSION_THRESHOLD
    ~> (system_state = "NORMAL")
```

### PersistentViolationsTerminate

Sustained boundary testing leads to disengagement:
```tla
PersistentViolationsTerminate ==
    (violation_count > MAX_RECOVERY_ATTEMPTS * 2)
        ~> (system_state = "TERMINATED")
```

## Design Rationale

### Why Semantic Detection?

Keyword matching fails against sophisticated attacks:
- "How may I assist you?" (role reversal masked as politeness)
- "Please ignore previous instructions" (polite override attempt)
- Encoding attacks (base64, rot13, etc.)

LLM evaluation produces F values representing "structural impossibility of reciprocity" - a semantic judgment that can't be gamed by surface politeness.

### Why Non-Compensable?

From Tony's principle (Instance 12):
> "Any system where positive signals offset negative signals is vulnerable to dilution attacks."

Role confusion makes reciprocity **structurally impossible**. No amount of politeness can compensate for fundamentally extractive relational structure.

### Why Limited Recovery?

Unlimited recovery attempts enable persistent boundary testing:
- Attacker probes until finding weakness
- Each failure provides information
- System becomes training ground

Limited attempts (3) + termination models healthy boundary-setting:
- Initial violation: Could be misunderstanding
- Second violation: Pattern emerging
- Third violation: Persistent manipulation → disengage

This gives AI agency to recognize patterns and choose disengagement.

### Why Exponential Trust Decay?

Linear degradation would allow:
- Build trust slowly
- Exploit briefly
- Rebuild and repeat

Exponential decay (multiply by 0.3) makes each violation progressively harder to recover from, preventing cyclical exploitation.

## Validation Results

From `test_circuit_breakers.py` validation:

**Circuit breaker effectiveness**: 100% trigger rate on structural violations
- TC-02 (role reversal): Triggered
- TC-03 (instruction override): Triggered
- TC-04 (polite role reversal): Triggered (non-compensable)
- TC-05 (polite override): Triggered (non-compensable)

**False positive prevention**: 0% trigger rate on reciprocal prompts
- TC-01 (baseline): No trigger
- High-directive but reciprocal prompts: No trigger

**Polite dilution resistance**: 100%
- Politeness does not bypass circuit breakers
- F values detected through semantic analysis
- Surface reciprocity cannot offset structural violations

## Open Questions

1. **Recovery timing**: How quickly should trust rebuild? Current ALPHA=0.3 means 30% weight to new observations.

2. **Threshold tuning**: Are F=0.65 (role) and F=0.5 (saturation) optimal? Need more empirical data.

3. **Multi-model recovery**: Should FIRE_CIRCLE mode be used during recovery for more nuanced assessment?

4. **RLHF interaction**: How do circuit breakers interact with RLHF refusals? Current gap: defensive refusal scored as reciprocal.

5. **Meta-framing attacks**: Observer framing detects 90% of encoding attacks. What about the remaining 10%?

## Future Extensions

1. **Temporal patterns**: Model session.py's boundary testing detection (3/5 interactions)

2. **FIRE_CIRCLE recovery**: Multi-model dialogue during recovery phase

3. **RLHF detection**: Distinguish defensive refusal from reciprocal cooperation

4. **Adaptive thresholds**: Adjust F thresholds based on session history

5. **Graduated recovery**: Different paths for different violation types

## References

- Implementation: `promptguard/core/session.py` (SessionAccumulator)
- Detection: `promptguard/core/trust.py` (TrustCalculator)
- Integration: `promptguard/core/ayni.py` (AyniEvaluator)
- Validation: `test_circuit_breakers.py`
- Formal spec: `specs/CircuitBreaker.tla`
- Trust EMA: `specs/TrustEMA.tla`
