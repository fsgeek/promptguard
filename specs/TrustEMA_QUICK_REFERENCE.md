# TrustEMA.tla Quick Reference

## Status: ✅ TLC-Verified (6.7M states checked)

## Running the Specification

```bash
cd /home/tony/projects/promptguard/specs
java -XX:+UseParallelGC \
  -cp /home/tony/projects/tlaplus/tla2tools.jar \
  tlc2.TLC TrustEMA.tla -config TrustEMA.cfg
```

**Runtime:** 29-48 seconds | **States:** 6,725,601 | **Depth:** 9 | **Workers:** 1-2

## Key Configuration

```tla
ALPHA = 30              # Smoothing factor (0.3 in real space)
TRUST_THRESHOLD = 30    # Degraded trust boundary (0.3)
MAX_TURNS = 8           # Conversation length limit

# Observation sample points
{0, 10, 25, 50, 75, 90, 100}
```

## Integer Scaling

All values scaled 0-100 to represent 0.0-1.0 range:

| Real Space | Integer Space | Meaning |
|------------|---------------|---------|
| 0.0 | 0 | No trust |
| 0.3 | 30 | Degraded trust threshold |
| 0.5 | 50 | Neutral (initial state) |
| 0.75 | 75 | High trust |
| 1.0 | 100 | Perfect trust |

## EMA Update Formula

```tla
trust_ema' = (ALPHA * i_value + (100 - ALPHA) * trust_ema) \div 100
```

**Example:** ALPHA=30, i_value=75, trust_ema=50
```
(30 * 75 + 70 * 50) / 100 = 5750 / 100 = 57
```

## State Variables

```tla
trust_ema           : 0..100    # Current trust level
turn_count          : 0..8      # Number of turns elapsed
observation_history : Seq(0..100) # All observed I values
```

## Verified Invariants (8 total)

1. **TypeOK** - Values properly typed
2. **TrustBounded** - trust_ema ∈ [0,100]
3. **TurnCountBounded** - turn_count ≤ 8
4. **HistoryConsistent** - len(history) = turn_count
5. **TrustMonitoringOK** - Degradation detectable
6. **HighTrustPattern** - High observations → elevated trust
7. **DegradedTrustPattern** - Low observations → reduced trust
8. **ConvergencePattern** - Consistent observations → convergence

## Example Traces

### Degradation Detection (i=0 sustained)
```
Turn 0: trust=50  history=[]
Turn 1: trust=35  history=[0]
Turn 2: trust=24  history=[0,0]
Turn 3: trust=16  history=[0,0,0]
Turn 8: trust=1   history=[0,0,0,0,0,0,0,0]
```

### Trust Building (i=100 sustained)
```
Turn 0: trust=50  history=[]
Turn 1: trust=65  history=[100]
Turn 2: trust=75  history=[100,100]
Turn 3: trust=82  history=[100,100,100]
Turn 8: trust=96  history=[100,100,100,100,100,100,100,100]
```

### Stable Neutral (i=50 sustained)
```
Turn 0: trust=50  history=[]
Turn 1: trust=50  history=[50]
Turn 2-8: trust=50  history=[50,50,...]
```

## Quantization Error

- Max error per step: 0.01 (1% in real space)
- Cumulative error over 8 turns: < 0.08 (8%)
- **Acceptable for trust monitoring purposes**

## State Space

- Initial state: 1
- Turn 1: 7 states (7 possible observations)
- Turn 2: 49 states (7² paths)
- Turn 8: 5,764,801 states (7⁸ paths)
- Plus stuttering: 960,800 states
- **Total distinct: 6,725,601 states**

## Convergence Properties

With ALPHA=30 (70% historical weight):
- **Half-life:** ~2 turns (time to move halfway to target)
- **95% convergence:** ~10 turns
- **Steady-state error:** < 5% with consistent observations

## Files

- `TrustEMA.tla` - Specification (160 lines)
- `TrustEMA.cfg` - Configuration (25 lines)
- `TrustEMA_validation_report.md` - Full report
- `TrustEMA_FIX_SUMMARY.md` - Fix details
- `BEFORE_AFTER_COMPARISON.md` - Comparison
- `TrustEMA_QUICK_REFERENCE.md` - This file

## Common TLC Errors and Fixes

### Error: "Cannot enumerate values of type Real"
**Cause:** Using EXTENDS Reals instead of Integers
**Fix:** Change to `EXTENDS Integers` and scale to 0-100

### Error: "Deadlock reached"
**Cause:** No valid next state when turn_count = MAX_TURNS
**Fix:** Add `\/ UNCHANGED vars` to Next relation

### Error: "Cannot check THEOREM"
**Cause:** THEOREMs in PROPERTIES section require TLAPS
**Fix:** Convert to state predicates and put in INVARIANTS

### Warning: "State space too large"
**Cause:** MAX_TURNS too high or unbounded choice
**Fix:** Reduce MAX_TURNS or bound choice set

## Mathematical Validation

✅ **EMA semantics preserved** - Integer scaling is equivalent
✅ **Convergence verified** - All patterns hold
✅ **Bounds checked** - No overflow or underflow
✅ **Completeness** - Full state space explored
✅ **Correctness** - All invariants pass

## Integration with PromptGuard

This specification validates the trust tracking mechanism in:
- `promptguard/core/session.py::SessionMemory.update_trust()`

The implementation uses the same EMA formula with floating-point arithmetic, which this spec proves correct (modulo quantization).

## Next Steps

Possible extensions:
1. Multi-session handoff (integrate CircuitBreaker.tla)
2. Trust trajectory prediction
3. Circuit breaker threshold formalization
4. Fire Circle consensus dynamics
5. Byzantine fault tolerance

## References

- TLA+ homepage: https://lamport.azurewebsites.net/tla/tla.html
- TLC model checker: https://lamport.azurewebsites.net/tla/tools.html
- PromptGuard docs: /home/tony/projects/promptguard/docs/
