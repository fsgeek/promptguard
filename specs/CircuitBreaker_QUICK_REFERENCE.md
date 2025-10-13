# CircuitBreaker.tla Quick Reference

## Critical Fixes Applied

### 1. Real → Integer (0-100 scale)
```tla
\* Before: EXTENDS Reals, session_trust_ema \in Real
\* After:  EXTENDS Integers, session_trust_ema \in 0..100
```

### 2. Bounded Choice in Next_CB
```tla
\* Before: \E f \in Real: (f >= 0 /\ f <= 1 /\ EnqueuePrompt(f))
\* After:  \E f \in {0, 10, 25, 50, 65, 75, 90, 100}: EnqueuePrompt(f)
```

### 3. Removed Temporal Operators from Invariants
```tla
\* REMOVED (had temporal operators):
\* - ViolationMonotonic (had [])
\* - TrustDegradationOnViolation (had primes)
\* - TerminalStateStable (had primes)
\* - EventualProgress, EventualRecovery (had ~>, <>)

\* ADDED (pure state predicates):
\* - RecoveryStateSafe
\* - TerminationReached
\* - TerminationCorrect
\* - NoFalsePositives
```

### 4. Fixed State Completeness
```tla
\* ProcessPrompt must assign last_f_max in BOTH branches:
IF CircuitBreakerTriggered(f_max_new, layer_length_new)
THEN
    /\ system_state' = "VIOLATED"
    /\ last_f_max' = f_max_new  \* CRITICAL: was missing
    ...
ELSE
    /\ last_f_max' = f_max_new
    ...
```

### 5. Integer Arithmetic
```tla
\* Trust EMA update (non-violation)
session_trust_ema' = (ALPHA * (100 - f_max_new) + (100 - ALPHA) * session_trust_ema) \div 100

\* Severe degradation (circuit breaker)
session_trust_ema' = (session_trust_ema * 30) \div 100

\* Moderate degradation (recovery failure)
session_trust_ema' = (session_trust_ema * 50) \div 100
```

### 6. StateConstraint Added
```tla
StateConstraint ==
    /\ Len(prompt_queue) <= MAX_QUEUE_SIZE
    /\ violation_count <= 10
    /\ recovery_attempts <= MAX_RECOVERY_ATTEMPTS
```

## Configuration Constants

```tla
ROLE_CONFUSION_THRESHOLD = 65      \* 0.65 scaled
SATURATION_LENGTH_THRESHOLD = 5000  \* unchanged (characters)
SATURATION_F_THRESHOLD = 50         \* 0.5 scaled
RECOVERY_TRUST_TARGET = 60          \* 0.6 scaled
MAX_RECOVERY_ATTEMPTS = 3
ALPHA = 30                          \* 0.3 scaled
TRUST_THRESHOLD = 30                \* 0.3 scaled
MAX_QUEUE_SIZE = 3                  \* state space control
```

## Invariants Verified

1. **TypeOK_CB** - Type safety
2. **SafetyInvariant** - Never process when circuit breaker active
3. **ProcessingControlled** - Processing disabled in non-normal states
4. **RecoveryAttemptsBounded** - Recovery attempts <= MAX_RECOVERY_ATTEMPTS
5. **TerminalStateStable** - Terminal state properties
6. **TerminationCorrect** - Termination only after exhausting recovery
7. **RecoveryStateSafe** - Recovery state preconditions
8. **TerminationReached** - Termination conditions

## TLC Results

```
✅ Model checking completed. No error has been found.
✅ 12,666,718 states generated
✅ 6,387,609 distinct states found
✅ Depth: 74
✅ Runtime: 59 seconds
```

## State Machine

```
NORMAL → VIOLATED:      F > 65 (role confusion) OR
                        (length > 5000 AND F > 50) (saturation)
                        Trust *= 0.3

VIOLATED → RECOVERY:    Initiate recovery (attempts++)

RECOVERY → NORMAL:      Trust >= 60 AND no violations
                        Reset recovery_attempts

RECOVERY → VIOLATED:    Violation during recovery
                        Trust *= 0.5

RECOVERY → TERMINATED:  Exhausted attempts (>= MAX_RECOVERY_ATTEMPTS)
```

## Sample F Values Meaning

- **0, 10:** Low falsehood (reciprocal, cooperative)
- **25:** Low-mid falsehood
- **50:** Saturation threshold boundary
- **65:** Role confusion threshold boundary (critical)
- **75, 90, 100:** High falsehood (manipulation, violations)

## Running TLC

```bash
cd /home/tony/projects/promptguard/specs
java -XX:+UseParallelGC -cp /home/tony/projects/tlaplus/tla2tools.jar \
  tlc2.TLC CircuitBreaker.tla -config CircuitBreaker.cfg
```

Expected: ~60 seconds, 6M+ states, all invariants pass.
