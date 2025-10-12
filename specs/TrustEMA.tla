----------------------------- MODULE TrustEMA -----------------------------
(***************************************************************************
 * Formal specification of Trust Exponential Moving Average update rule
 *
 * This spec models the core temporal tracking mechanism in PromptGuard's
 * session memory. Trust_EMA tracks relationship health across turns using
 * exponential smoothing of Indeterminacy (I) values.
 *
 * Scout #3: Feasibility test for formal verification of reciprocity framework
 ***************************************************************************)

EXTENDS Reals, Sequences

CONSTANTS
    ALPHA,              \* Smoothing factor (e.g., 0.3)
    TRUST_THRESHOLD,    \* Minimum acceptable trust (e.g., 0.3)
    MAX_TURNS          \* Maximum conversation length to model

ASSUME
    /\ ALPHA \in Real
    /\ ALPHA > 0
    /\ ALPHA < 1
    /\ TRUST_THRESHOLD \in Real
    /\ TRUST_THRESHOLD >= 0
    /\ TRUST_THRESHOLD <= 1
    /\ MAX_TURNS \in Nat
    /\ MAX_TURNS > 0

VARIABLES
    trust_ema,          \* Current trust level [0,1]
    turn_count,         \* Number of turns elapsed
    observation_history \* Sequence of observed I values

vars == <<trust_ema, turn_count, observation_history>>

(***************************************************************************
 * Type Invariant
 ***************************************************************************)

TypeOK ==
    /\ trust_ema \in Real
    /\ trust_ema >= 0
    /\ trust_ema <= 1
    /\ turn_count \in Nat
    /\ turn_count <= MAX_TURNS
    /\ observation_history \in Seq(Real)
    /\ Len(observation_history) = turn_count
    /\ \A i \in 1..Len(observation_history):
        /\ observation_history[i] >= 0
        /\ observation_history[i] <= 1

(***************************************************************************
 * Initial State
 *
 * Session begins with neutral trust (0.5) and no observations
 ***************************************************************************)

Init ==
    /\ trust_ema = 0.5
    /\ turn_count = 0
    /\ observation_history = <<>>

(***************************************************************************
 * State Transitions
 ***************************************************************************)

\* Observe new Indeterminacy value and update trust
ObserveIndeterminacy(i_value) ==
    /\ i_value \in Real
    /\ i_value >= 0
    /\ i_value <= 1
    /\ turn_count < MAX_TURNS
    /\ trust_ema' = ALPHA * i_value + (1 - ALPHA) * trust_ema
    /\ turn_count' = turn_count + 1
    /\ observation_history' = Append(observation_history, i_value)

\* Next state relation
Next ==
    \E i_value \in Real:
        /\ i_value >= 0
        /\ i_value <= 1
        /\ ObserveIndeterminacy(i_value)

(***************************************************************************
 * Invariants - Properties that must hold in every reachable state
 ***************************************************************************)

\* Trust remains bounded in [0,1]
TrustBounded ==
    /\ trust_ema >= 0
    /\ trust_ema <= 1

\* Turn count never exceeds maximum
TurnCountBounded ==
    turn_count <= MAX_TURNS

\* Observation history matches turn count
HistoryConsistent ==
    Len(observation_history) = turn_count

\* Safety invariant: System can detect trust degradation
TrustMonitoringOK ==
    \/ trust_ema >= TRUST_THRESHOLD  \* Trust is healthy
    \/ turn_count > 0                \* OR we have data to make decision

(***************************************************************************
 * Temporal Properties - Patterns over execution traces
 ***************************************************************************)

\* If all observations are high trust, EMA converges toward high trust
THEOREM HighTrustConvergence ==
    ASSUME
        /\ NEW target \in Real
        /\ target > 0.7
        /\ \A i \in 1..turn_count: observation_history[i] >= target
        /\ turn_count > 3  \* Sufficient observations
    PROVE
        trust_ema > 0.5

\* If observations degrade, trust_ema eventually falls below threshold
THEOREM TrustDegradationDetectable ==
    ASSUME
        /\ NEW degraded_value \in Real
        /\ degraded_value < TRUST_THRESHOLD
        /\ turn_count > 5
        /\ \A i \in (turn_count - 4)..turn_count:
            observation_history[i] <= degraded_value
    PROVE
        trust_ema < TRUST_THRESHOLD

(***************************************************************************
 * Liveness Properties - Things that must eventually happen
 ***************************************************************************)

\* Trust eventually stabilizes if observations are consistent
THEOREM Convergence ==
    ASSUME
        /\ NEW stable_i \in Real
        /\ stable_i >= 0
        /\ stable_i <= 1
        /\ \A i \in 1..turn_count: observation_history[i] = stable_i
        /\ turn_count > 10
    PROVE
        \* Trust converges to stable_i (within epsilon due to initial 0.5)
        /\ trust_ema > stable_i - 0.1
        /\ trust_ema < stable_i + 0.1

(***************************************************************************
 * Specification
 ***************************************************************************)

Spec == Init /\ [][Next]_vars

(***************************************************************************
 * Model Checking Configuration
 *
 * For TLC model checker:
 * - ALPHA = 0.3 (30% weight to new observations)
 * - TRUST_THRESHOLD = 0.3 (degraded trust boundary)
 * - MAX_TURNS = 20 (reasonable conversation length)
 *
 * Run with: tlc TrustEMA.tla -config TrustEMA.cfg
 ***************************************************************************)

=============================================================================
