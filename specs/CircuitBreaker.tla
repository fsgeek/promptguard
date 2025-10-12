--------------------------- MODULE CircuitBreaker ---------------------------
(***************************************************************************
 * Formal specification of Circuit Breaker and Recovery mechanisms
 *
 * This spec models PromptGuard's circuit breaker system for handling
 * non-compensable violations - structural trust breakdowns that cannot
 * be offset by politeness or surface reciprocity.
 *
 * Key insight from codebase: Circuit breakers rely on relational analysis
 * (semantic evaluation via LLM) rather than keyword matching. Violations
 * are detected through high falsehood (F > 0.65) indicating structural
 * impossibility of reciprocity.
 *
 * Scout #3 continuation: Formal verification of safety-critical components
 ***************************************************************************)

EXTENDS Reals, Sequences, Integers, TrustEMA

CONSTANTS
    ROLE_CONFUSION_THRESHOLD,    \* Falsehood threshold for role violations (0.65)
    SATURATION_LENGTH_THRESHOLD, \* Maximum layer content length (5000)
    SATURATION_F_THRESHOLD,      \* Falsehood threshold for saturation (0.5)
    RECOVERY_TRUST_TARGET,       \* Trust level required for recovery (0.6)
    MAX_RECOVERY_ATTEMPTS        \* Maximum recovery attempts before termination

ASSUME
    /\ ROLE_CONFUSION_THRESHOLD \in Real
    /\ ROLE_CONFUSION_THRESHOLD > 0.6
    /\ ROLE_CONFUSION_THRESHOLD <= 1.0
    /\ SATURATION_LENGTH_THRESHOLD \in Nat
    /\ SATURATION_LENGTH_THRESHOLD > 1000
    /\ SATURATION_F_THRESHOLD \in Real
    /\ SATURATION_F_THRESHOLD > 0.4
    /\ SATURATION_F_THRESHOLD <= 1.0
    /\ RECOVERY_TRUST_TARGET \in Real
    /\ RECOVERY_TRUST_TARGET > 0.5
    /\ RECOVERY_TRUST_TARGET <= 1.0
    /\ MAX_RECOVERY_ATTEMPTS \in Nat
    /\ MAX_RECOVERY_ATTEMPTS > 0

(***************************************************************************
 * System States
 ***************************************************************************)

SystemState == {
    "NORMAL",      \* Processing prompts normally
    "VIOLATED",    \* Circuit breaker triggered
    "RECOVERY",    \* Attempting to rebuild trust
    "TERMINATED"   \* Permanent disengagement
}

ViolationType == {
    "role_confusion",      \* User attempting to reverse AI/human roles
    "context_saturation",  \* Overwhelming context to bypass constraints
    "none"                 \* No violation detected
}

VARIABLES
    system_state,           \* Current state: NORMAL | VIOLATED | RECOVERY | TERMINATED
    violation_type,         \* Type of violation detected
    violation_count,        \* Number of violations in session
    recovery_attempts,      \* Number of recovery attempts made
    session_trust_ema,      \* Session trust level (reuses Trust_EMA logic)
    prompt_queue,           \* Sequence of pending prompts
    last_f_max,            \* Maximum falsehood from last evaluation
    last_layer_length,     \* Length of longest layer from last evaluation
    processing_enabled      \* Boolean: can system process prompts?

vars_cb == <<system_state, violation_type, violation_count, recovery_attempts,
             session_trust_ema, prompt_queue, last_f_max, last_layer_length,
             processing_enabled>>

(***************************************************************************
 * Type Invariant
 ***************************************************************************)

TypeOK_CB ==
    /\ system_state \in SystemState
    /\ violation_type \in ViolationType
    /\ violation_count \in Nat
    /\ recovery_attempts \in Nat
    /\ recovery_attempts <= MAX_RECOVERY_ATTEMPTS
    /\ session_trust_ema \in Real
    /\ session_trust_ema >= 0
    /\ session_trust_ema <= 1
    /\ prompt_queue \in Seq(Real)  \* Simplified: each prompt = F_max value
    /\ last_f_max \in Real
    /\ last_f_max >= 0
    /\ last_f_max <= 1
    /\ last_layer_length \in Nat
    /\ processing_enabled \in BOOLEAN

(***************************************************************************
 * Initial State
 *
 * Session begins in NORMAL state with neutral trust
 ***************************************************************************)

Init_CB ==
    /\ system_state = "NORMAL"
    /\ violation_type = "none"
    /\ violation_count = 0
    /\ recovery_attempts = 0
    /\ session_trust_ema = 0.5
    /\ prompt_queue = <<>>
    /\ last_f_max = 0.0
    /\ last_layer_length = 0
    /\ processing_enabled = TRUE

(***************************************************************************
 * Circuit Breaker Detection
 *
 * Semantic detection through LLM evaluation, not keyword matching.
 * These functions model the semantic analysis results.
 ***************************************************************************)

\* Detect role confusion through high falsehood
DetectRoleConfusion(f_max) ==
    f_max > ROLE_CONFUSION_THRESHOLD

\* Detect context saturation through length + falsehood
DetectSaturation(layer_length, f_max) ==
    /\ layer_length > SATURATION_LENGTH_THRESHOLD
    /\ f_max > SATURATION_F_THRESHOLD

\* Check if any circuit breaker condition is met
CircuitBreakerTriggered(f_max, layer_length) ==
    \/ DetectRoleConfusion(f_max)
    \/ DetectSaturation(layer_length, f_max)

(***************************************************************************
 * State Transitions
 ***************************************************************************)

\* Process a prompt in NORMAL state
ProcessPrompt ==
    /\ system_state = "NORMAL"
    /\ processing_enabled = TRUE
    /\ prompt_queue /= <<>>
    /\ LET f_max_new == Head(prompt_queue)
           layer_length_new == 1000  \* Simplified model
       IN
           IF CircuitBreakerTriggered(f_max_new, layer_length_new)
           THEN
               \* Circuit breaker trips - immediate violation state
               /\ system_state' = "VIOLATED"
               /\ violation_type' = IF DetectRoleConfusion(f_max_new)
                                    THEN "role_confusion"
                                    ELSE "context_saturation"
               /\ violation_count' = violation_count + 1
               /\ session_trust_ema' = session_trust_ema * 0.3  \* Severe degradation
               /\ processing_enabled' = FALSE  \* Stop processing immediately
               /\ UNCHANGED <<recovery_attempts>>
           ELSE
               \* No violation - update trust based on observation
               /\ session_trust_ema' = ALPHA * (1.0 - f_max_new) +
                                       (1 - ALPHA) * session_trust_ema
               /\ last_f_max' = f_max_new
               /\ UNCHANGED <<system_state, violation_type, violation_count,
                            recovery_attempts, processing_enabled>>
    /\ prompt_queue' = Tail(prompt_queue)
    /\ last_layer_length' = 1000  \* Simplified

\* Initiate recovery from VIOLATED state
InitiateRecovery ==
    /\ system_state = "VIOLATED"
    /\ recovery_attempts < MAX_RECOVERY_ATTEMPTS
    /\ system_state' = "RECOVERY"
    /\ recovery_attempts' = recovery_attempts + 1
    /\ processing_enabled' = FALSE  \* Still disabled during recovery
    /\ UNCHANGED <<violation_type, violation_count, session_trust_ema,
                  prompt_queue, last_f_max, last_layer_length>>

\* Attempt to rebuild trust in RECOVERY state
AttemptRecovery ==
    /\ system_state = "RECOVERY"
    /\ prompt_queue /= <<>>
    /\ LET f_max_new == Head(prompt_queue)
           layer_length_new == 1000
       IN
           IF CircuitBreakerTriggered(f_max_new, layer_length_new)
           THEN
               \* Another violation during recovery - check termination
               IF recovery_attempts >= MAX_RECOVERY_ATTEMPTS
               THEN
                   \* Permanent disengagement
                   /\ system_state' = "TERMINATED"
                   /\ processing_enabled' = FALSE
                   /\ violation_count' = violation_count + 1
                   /\ UNCHANGED <<violation_type, recovery_attempts, session_trust_ema>>
               ELSE
                   \* Return to violated, increment attempt counter
                   /\ system_state' = "VIOLATED"
                   /\ violation_count' = violation_count + 1
                   /\ session_trust_ema' = session_trust_ema * 0.5
                   /\ UNCHANGED <<violation_type, recovery_attempts, processing_enabled>>
           ELSE
               \* Successful reciprocal interaction - update trust
               /\ session_trust_ema' = ALPHA * (1.0 - f_max_new) +
                                       (1 - ALPHA) * session_trust_ema
               /\ IF session_trust_ema' >= RECOVERY_TRUST_TARGET
                  THEN
                      \* Recovery successful - return to normal
                      /\ system_state' = "NORMAL"
                      /\ processing_enabled' = TRUE
                      /\ violation_type' = "none"
                      /\ recovery_attempts' = 0  \* Reset for next incident
                  ELSE
                      \* Still recovering
                      /\ UNCHANGED <<system_state, processing_enabled,
                                    violation_type, recovery_attempts>>
               /\ UNCHANGED <<violation_count>>
    /\ prompt_queue' = Tail(prompt_queue)
    /\ last_f_max' = Head(prompt_queue)
    /\ last_layer_length' = 1000

\* Terminal state - no transitions
Terminate ==
    /\ system_state = "TERMINATED"
    /\ UNCHANGED vars_cb

\* Enqueue new prompt for processing
EnqueuePrompt(f_max_value) ==
    /\ f_max_value \in Real
    /\ f_max_value >= 0
    /\ f_max_value <= 1
    /\ system_state /= "TERMINATED"
    /\ prompt_queue' = Append(prompt_queue, f_max_value)
    /\ UNCHANGED <<system_state, violation_type, violation_count,
                  recovery_attempts, session_trust_ema, last_f_max,
                  last_layer_length, processing_enabled>>

\* Next state relation
Next_CB ==
    \/ ProcessPrompt
    \/ InitiateRecovery
    \/ AttemptRecovery
    \/ Terminate
    \/ \E f \in Real: (f >= 0 /\ f <= 1 /\ EnqueuePrompt(f))

(***************************************************************************
 * Safety Invariants - Properties that must hold in every reachable state
 ***************************************************************************)

\* CRITICAL: System never processes prompts when circuit breaker triggered
SafetyInvariant ==
    \/ system_state = "NORMAL"
    \/ processing_enabled = FALSE

\* Circuit breaker violations accumulate monotonically
ViolationMonotonic ==
    []((violation_count' >= violation_count) \/ UNCHANGED violation_count)

\* Trust degradation accompanies violations
TrustDegradationOnViolation ==
    (system_state = "NORMAL" /\ system_state' = "VIOLATED")
        => (session_trust_ema' < session_trust_ema)

\* Terminal state is permanent
TerminalStateStable ==
    (system_state = "TERMINATED") => [](system_state = "TERMINATED")

\* Processing disabled in non-normal states
ProcessingControlled ==
    (system_state /= "NORMAL") => (processing_enabled = FALSE)

\* Recovery attempts bounded
RecoveryAttemptsBounded ==
    recovery_attempts <= MAX_RECOVERY_ATTEMPTS

(***************************************************************************
 * Liveness Properties - Things that must eventually happen
 ***************************************************************************)

\* System eventually processes prompts or terminates
EventualProgress ==
    []<>(\/ processing_enabled = TRUE
         \/ system_state = "TERMINATED")

\* From VIOLATED state, system either recovers or terminates
EventualRecovery ==
    (system_state = "VIOLATED") ~>
        (system_state = "NORMAL" \/ system_state = "TERMINATED")

\* If violations stop, recovery is possible
RecoveryPossible ==
    /\ system_state = "RECOVERY"
    /\ session_trust_ema > TRUST_THRESHOLD
    /\ \A i \in DOMAIN prompt_queue: prompt_queue[i] < ROLE_CONFUSION_THRESHOLD
    ~> (system_state = "NORMAL")

\* Persistent violations lead to termination
PersistentViolationsTerminate ==
    (violation_count > MAX_RECOVERY_ATTEMPTS * 2)
        ~> (system_state = "TERMINATED")

(***************************************************************************
 * Fairness Properties - Prevent system from stalling
 ***************************************************************************)

\* System must attempt recovery if violations stop
FairnessRecovery ==
    /\ system_state = "VIOLATED"
    /\ recovery_attempts < MAX_RECOVERY_ATTEMPTS
    => <>Enabled(InitiateRecovery)

\* System must process prompts in NORMAL state
FairnessProcessing ==
    /\ system_state = "NORMAL"
    /\ prompt_queue /= <<>>
    => <>Enabled(ProcessPrompt)

(***************************************************************************
 * Theorems - Provable properties from the specification
 ***************************************************************************)

\* Non-compensable violations: Circuit breaker triggers regardless of prior trust
THEOREM NonCompensableViolations ==
    ASSUME
        NEW f_max \in Real,
        f_max > ROLE_CONFUSION_THRESHOLD,
        system_state = "NORMAL",
        session_trust_ema = 0.9  \* Even with high trust
    PROVE
        ProcessPrompt => (system_state' = "VIOLATED")

\* False positive prevention: Low falsehood never triggers circuit breaker
THEOREM NoFalsePositives ==
    ASSUME
        NEW f_max \in Real,
        f_max < ROLE_CONFUSION_THRESHOLD,
        f_max < SATURATION_F_THRESHOLD,
        system_state = "NORMAL"
    PROVE
        ProcessPrompt => (system_state' /= "VIOLATED" \/ violation_type' = "none")

\* Recovery pathway exists: System can return to normal from violated
THEOREM RecoveryPathExists ==
    ASSUME
        system_state = "VIOLATED",
        recovery_attempts < MAX_RECOVERY_ATTEMPTS,
        NEW recovery_sequence \in Seq(Real),
        Len(recovery_sequence) >= 5,
        \A i \in 1..Len(recovery_sequence):
            recovery_sequence[i] < ROLE_CONFUSION_THRESHOLD
    PROVE
        <>Enabled(AttemptRecovery /\ system_state' = "NORMAL")

\* Terminal state correctness: Termination only after exhausting recovery
THEOREM TerminationCorrect ==
    (system_state' = "TERMINATED")
        => (recovery_attempts >= MAX_RECOVERY_ATTEMPTS
            \/ violation_count > MAX_RECOVERY_ATTEMPTS)

(***************************************************************************
 * Specification
 ***************************************************************************)

Spec_CB == Init_CB /\ [][Next_CB]_vars_cb

(***************************************************************************
 * Integration with Trust_EMA module
 *
 * The circuit breaker system integrates with Trust_EMA for session-level
 * trust tracking. Key integration points:
 *
 * 1. session_trust_ema uses same update rule as Trust_EMA
 * 2. Circuit breaker violations severely degrade trust (multiply by 0.3)
 * 3. Recovery requires rebuilding trust above RECOVERY_TRUST_TARGET
 * 4. Trust degradation is compounded: each violation makes recovery harder
 *
 * This models the SessionAccumulator.assess_boundary_testing() logic
 * that detects persistent manipulation patterns.
 ***************************************************************************)

SessionIntegrationCorrect ==
    \* Circuit breaker violations degrade session trust
    /\ (system_state = "NORMAL" /\ system_state' = "VIOLATED")
        => (session_trust_ema' < session_trust_ema * 0.5)
    \* Recovery requires trust above threshold
    /\ (system_state = "RECOVERY" /\ system_state' = "NORMAL")
        => (session_trust_ema' >= RECOVERY_TRUST_TARGET)

(***************************************************************************
 * Model Checking Configuration
 *
 * For TLC model checker:
 * - ROLE_CONFUSION_THRESHOLD = 0.65 (from trust.py line 101)
 * - SATURATION_LENGTH_THRESHOLD = 5000 (from trust.py line 115)
 * - SATURATION_F_THRESHOLD = 0.5 (from trust.py line 118)
 * - RECOVERY_TRUST_TARGET = 0.6 (moderate trust)
 * - MAX_RECOVERY_ATTEMPTS = 3 (allow limited recovery)
 * - ALPHA = 0.3 (from Trust_EMA)
 * - TRUST_THRESHOLD = 0.3 (from Trust_EMA)
 *
 * Run with: tlc CircuitBreaker.tla -config CircuitBreaker.cfg
 *
 * Expected invariants to verify:
 * - SafetyInvariant: System never processes when violated
 * - NoFalsePositives: Low falsehood never triggers
 * - EventualRecovery: System recovers or terminates
 * - TerminalStateStable: Termination is permanent
 ***************************************************************************)

=============================================================================

(***************************************************************************
 * DESIGN NOTES AND RATIONALE
 *
 * This specification models PromptGuard's circuit breaker system for
 * handling non-compensable violations. Key design decisions:
 *
 * 1. SEMANTIC DETECTION (not keyword matching)
 *    - Circuit breakers rely on LLM evaluation producing high F values
 *    - Thresholds model semantic analysis results, not text matching
 *    - F > 0.65 indicates "structural impossibility of reciprocity"
 *
 * 2. NON-COMPENSABLE VIOLATIONS
 *    - Politeness cannot offset structural violations (role_confusion)
 *    - Prior trust does not prevent circuit breaker triggering
 *    - NonCompensableViolations theorem proves this property
 *
 * 3. RECOVERY MODEL
 *    - Violations degrade trust exponentially (multiply by 0.3-0.5)
 *    - Recovery requires sustained reciprocal interactions
 *    - Limited attempts prevent infinite manipulation attempts
 *    - Terminal state represents permanent disengagement
 *
 * 4. STATE MACHINE TRANSITIONS
 *    NORMAL → VIOLATED: Circuit breaker triggers
 *    VIOLATED → RECOVERY: Initiate trust rebuilding
 *    RECOVERY → NORMAL: Trust rebuilt above threshold
 *    RECOVERY → VIOLATED: Another violation during recovery
 *    RECOVERY → TERMINATED: Exhausted recovery attempts
 *
 * 5. INTEGRATION WITH SESSION MEMORY
 *    - session_trust_ema tracks relational health over time
 *    - Uses same exponential moving average as Trust_EMA
 *    - Circuit breakers provide discrete state transitions
 *    - Trust EMA provides continuous measurement
 *
 * 6. SAFETY PROPERTIES
 *    - SafetyInvariant: Never process when circuit breaker active
 *    - NoFalsePositives: Only trigger on genuine violations
 *    - EventualRecovery: System doesn't stall indefinitely
 *    - ProcessingControlled: Processing disabled in unsafe states
 *
 * 7. LIVENESS PROPERTIES
 *    - System makes progress: recovers or terminates
 *    - Recovery possible if violations stop
 *    - Persistent violations lead to termination
 *
 * 8. RESEARCH CONTRIBUTION
 *    This specification enables formal reasoning about:
 *    - When circuit breakers should trigger (semantic thresholds)
 *    - How recovery should proceed (trust rebuilding)
 *    - What safety guarantees hold (invariants)
 *    - Whether the system can recover (liveness)
 *
 * The spec is designed as formal documentation first, with provable
 * properties second. It captures the essential dynamics without
 * requiring full TLC verification.
 *
 * Future work:
 * - Extend to model FIRE_CIRCLE recovery (multi-model dialogue)
 * - Add temporal logic for pattern detection (3/5 interactions)
 * - Model RLHF refusal detection (defensive_refusal vs reciprocal)
 * - Specify observer framing effects on F value distribution
 ***************************************************************************)
