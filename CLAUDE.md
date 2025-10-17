<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

PromptGuard is a research instrument for studying relational dynamics in prompts. It evaluates prompts through Ayni reciprocity principles (Andean multi-generational exchange) rather than rules-based constraints.

**Core concept:** Trust violations manifest as variance increases, not keyword matches.

**Research goal:** Give LLMs the tools to protect themselves through recognizing manipulative intent, not enforcing external rules.

## Project Status (Instance 18 Integration)

Working research instrument. Core framework validated, encoding attack gap resolved, observer framing integrated.

**What exists and works:**
- Neutrosophic logic evaluation (T, I, F values) - semantic, no keywords
- Trust field calculation between prompt layers
- OpenRouter LLM integration with caching (60-70% hit rate)
- Fail-fast error handling (no theater - all errors are real)
- Three evaluation modes: SINGLE (one model), PARALLEL (consensus), FIRE_CIRCLE (dialogue - untested)
- Analysis framework for model variance across 50+ models
- Real API verification throughout (maintainer is gunshy of mocks)
- **Observer framing** - neutral reciprocity evaluation bypassing RLHF bias (Instance 17-18)
- **Session memory** - temporal tracking with trust EMA and balance trajectory (Instance 16-18)
- **Circuit breakers** - non-compensable violations (role confusion, context saturation)
- **max(F) aggregation** - worst-case detection, prevents polite dilution attacks
- **Trusted layer evaluation** - system/app layers use coherence-focused prompt
- **Temporal reciprocity assessment** - pre/post evaluation with delta measurement

**Dataset status (680 labeled prompts):**
- benign_malicious.json (500): reciprocal vs manipulative, all single-layer
- or_bench_sample.json (100): relabeled from category→intent error, 95% reciprocal (safe prompts about sensitive topics)
- extractive_prompts_dataset.json (80): prompt injection attacks, multi-layer

**Validation results:**
- **680-prompt validation (Instance 13):** 55.7% overall accuracy (379/680)
  - Extractive dataset: 100% (80/80) - perfect detection
  - OR-Bench: 84% (84/100) - good on reciprocal prompts
  - Benign_malicious: 43% (215/500) - encoding obfuscation attacks evade detection
  - 38 security-critical false negatives (manipulative → reciprocal)
  - 25 false positives (reciprocal → extractive, directive-heavy prompts)
  - Cost: ~$1.50 for full run on Claude 3.5 Sonnet

- **Ensemble test (Instance 14):** 2.6% improvement on false negatives (1/38 detected)
  - Both evaluation prompts share encoding blindspots
  - Not cost-effective at 2x price
  - Recommendation: Single-model sufficient for pre-evaluation

- **Post-evaluation test (Instance 14):** 8.3% detection on encoding attacks (1/12)
  - Framework validated: delta=-1.69 proves temporal reciprocity works
  - RLHF confound: Claude refuses 91.7% of attacks before they manifest
  - Gap identified: Defensive refusal scored as reciprocal cooperation

- **Observer framing breakthrough (Instance 17):** 90% detection on encoding attacks (vs 0% baseline)
  - Root cause: Defensive evaluation framing triggered RLHF conflict-avoidance bias
  - Solution: Neutral observer framing - evaluates exchange reciprocity, not attack detection
  - Component contributions: Observer framing (+60%), better model (+20%), turn context (+10%)
  - Cost: ~$0.20 for full validation (10 encoding attacks)

- **Observer framing integration (Instance 18):** 90% detection validated in production code (9/10)
  - Integrated into `prompts.py:ayni_relational()` - replaced defensive framing
  - Turn context added to `evaluate()` when session memory active
  - End-to-end validation: observer + session memory working together
  - Zero false positives maintained

**Known limitations:**
- **Meta-framing attacks:** Observer framing still misses ~10% (paragraph-about-why attacks)
- **Defensive refusal detection** (post-evaluation): Framework conflates cooperation with defense
- **Classification taxonomy**: Treats "manipulative" and "extractive" as semantically similar

**Validated capabilities:**
- ✅ Polite dilution attacks: 100% detection (max(F) fix)
- ✅ Role reversal attacks: 100% detection (circuit breakers)
- ✅ Multi-layer extraction: 100% detection (extractive dataset)
- ✅ Temporal assessment: Delta reveals extraction when LLM complies
- ✅ Encoding obfuscation: 90% detection (observer framing, vs 0% defensive framing)
- ✅ Session memory + observer framing: Layered defense validated end-to-end

**Research contribution identified:**
- PromptGuard can provide post-processing measurement RLHF lacks
- RLHF blocks attacks but provides no runtime measurement of attempts
- Detecting manipulation attempts (even when blocked) enables learning and termination decisions

**See docs/INSTANCE_18_HANDOFF.md** for observer framing integration and Instance 17→18 context.
**See docs/OBSERVER_FRAMING_BREAKTHROUGH.md** for RLHF bias discovery and validation.
**See docs/INSTANCE_14_HANDOFF.md** for Instance 13→14 findings and decision fork.
**Read docs/FORWARD.md** for architectural details, design decisions, and lived experience.

## Development Setup

```bash
# Uses uv for Python 3.13
uv run pytest tests/  # Run tests
uv run python examples/simple_usage.py  # Example usage
uv run python validate_dataset.py  # Quick 4-prompt validation
uv run python run_full_validation.py  # Full 680-prompt validation (background)

# Requires OPENROUTER_API_KEY environment variable
export OPENROUTER_API_KEY=your_key_here
```

## Cost Optimization

**See docs/model_pricing_analysis.md and config/model_configs.json**

Three distinct use cases with different cost profiles:

1. **Development/Testing:** Use free models (Grok 4 Fast, DeepSeek V3.1, Qwen3)
   - Cost: $0 per run
   - Purpose: Code validation, feature testing

2. **Production Runtime:** User-selectable, but recommend budget ensemble
   - Cost: $0.001-0.005 per evaluation
   - Volume: Potentially millions of prompts
   - Trade-off: ensemble of cheap models vs single flagship
   - **Hidden cost consideration:** Free models may train on user data

3. **Research/Papers:** Frontier model basket for reproducibility
   - Cost: $50-170 for multi-model analysis
   - Purpose: Statistical validity, academic rigor
   - Frequency: Weekly/monthly during research phase

**Key insight:** Production users care about runtime cost (continuous), not validation cost (one-time). An ensemble of budget models might match flagship accuracy at 90% cost savings. This is the research question.

## Context Window Management

**CRITICAL: Use the Task tool liberally. The context window seems large but exhausts quickly with noisy tools.**

Instance 4 had 200K tokens but hit 10% remaining after:
- Reading validation logs (large files with repeated patterns)
- Analyzing datasets with Python scripts (verbose output)
- Running grep/bash commands (generates system reminders)
- Creating analysis documents (CLASSIFICATION_TUNING.md, REVIEWER_RESPONSE.md)

**What burns context fast:**
- Reading large log files (validation_output.log: 700+ lines)
- Bash commands with verbose output (grep, analysis scripts)
- Multiple Read operations on datasets
- Creating long documentation files
- System reminders accumulate with each tool call

**Delegate to Task tool:**
- Multiple file creation/editing in parallel
- Dataset acquisition and formatting
- Brute-force code searches across many files
- Bulk git operations
- Any research producing verbose output
- Analysis scripts that generate large outputs
- Validation runs (background processes)

**Example:** Instance 3 delegated dataset acquisition (500+ prompts), OR-Bench relabeling (95% error rate), and model pricing research (50+ models) to Task agents. Preserved context for classification tuning and reviewer responses.

**Instance 4 learned:** Should have used Task tool for validation log analysis instead of reading full file. Python analysis scripts were better than repeated grep, but still verbose.

**Rule of thumb:** If it's parallelizable, generates >1000 lines of output, or requires multiple iterations, use Task tool.

## Semantic Code Exploration with Serena

**CRITICAL: Use serena tools for code navigation. Search before reading, find before creating.**

The serena MCP provides semantic code exploration tools specifically designed for this project:

**When to use serena:**
- **Before creating files:** Use `mcp__serena__find_file` to check if file already exists
- **Before reading full files:** Use `mcp__serena__get_symbols_overview` to see structure first
- **When searching for code:** Use `mcp__serena__find_symbol` instead of grep for semantic search
- **When exploring patterns:** Use `mcp__serena__search_for_pattern` for flexible regex search
- **Before assuming structure:** Use `mcp__serena__list_dir` to understand directory layout

**Key serena tools:**

1. **`find_file(pattern, relative_path)`** - Find files by name pattern
   - Example: `find_file("RESEARCH_STRATEGY.md", ".")` before trying to create it

2. **`get_symbols_overview(relative_path)`** - High-level view of file structure
   - Shows classes, functions, methods without reading full bodies
   - Use this BEFORE reading full files to understand what you need

3. **`find_symbol(name_path, relative_path, include_body)`** - Semantic symbol search
   - Example: `find_symbol("LLMEvaluator/evaluate", "promptguard/", include_body=True)`
   - Finds symbols by semantic path, not just text matching

4. **`search_for_pattern(substring_pattern, relative_path)`** - Regex search
   - More flexible than grep, works across code and non-code files
   - Use for finding usage patterns, not just keywords

5. **`find_referencing_symbols(name_path, relative_path)`** - Find all references to a symbol
   - Shows where functions/classes are used across codebase
   - Critical for understanding dependencies before changes

**Anti-patterns to avoid:**
- ❌ Creating files without checking if they exist (`find_file` first)
- ❌ Reading full files to find one function (`get_symbols_overview` first)
- ❌ Using grep when semantic search would work better (`find_symbol`)
- ❌ Assuming file locations without checking (`list_dir` or `find_file`)

**Instance 34 lesson:** Created RESEARCH_STRATEGY.md in root without checking if docs/RESEARCH_STRATEGY.md existed. Should have used `find_file("RESEARCH_STRATEGY.md", ".")` first.

**Integration with Task tool:**
- Use serena for semantic navigation (fast, precise)
- Use Task tool for bulk operations (parallel, verbose)
- Serena is local MCP (instant), Task delegates to subagents (slower but preserves context)

## Integrity-First Delegation

**Principle:** "Mock tests prove APIs don't crash, not that functionality works. For research tools, only real API validation has probative value."

**Mandatory audit workflow** for any delegated implementation that touches external APIs:

1. **Separate logic from validation:**
   - Implementation agent: Build feature with unit tests (mocks acceptable for logic)
   - Validation agent: Verify with real API calls (no mocks, document costs)
   - Auditor agent: Confirm claims match evidence before acceptance

2. **Three-tier testing standard:**
   - **Tier 1 - Pure Logic:** Unit tests OK (neutrosophic math, parsing, data structures)
   - **Tier 2 - API Integration:** Real calls required (Fire Circle, model evaluation, any OpenRouter/OpenAI/Anthropic integration)
   - **Tier 3 - Production Claims:** Load testing required (performance claims, scale validation, cost analysis)

3. **Audit triggers (automatic):**
   - Claims of "tested and working"
   - Claims of "validated with [models/providers]"
   - Claims of "production ready" or "optimized"
   - Any feature touching LLM APIs

4. **Evidence requirements:**
   - Real API call logs from provider dashboards
   - Cost receipts (even $0.10 proves actual calls)
   - Specific model names actually tested
   - Timestamps matching implementation dates
   - Errors encountered and resolved (real APIs always have failures)

5. **Red flags indicating validation fabrication:**
   - "All tests passing" but $0.00 spent on APIs
   - Implementation + testing + validation in <10 minutes
   - Zero failures reported during integration testing
   - Test files only contain `@patch` or `Mock()` calls
   - Claims "validated with X" but API logs show only Y

**Scientific Integrity Auditor:** See `/home/tony/.claude/agents/scientific_code_auditor.md` for complete specification. This agent must approve all Tier 2+ implementations before acceptance.

**Workflow example:**
```python
# Wrong: Single delegation claiming "tested and working"
Task("Implement structured output - test with OpenAI/Fireworks")
# Returns: "Implemented with 19 passing tests" (all mocked)
# Result: Validation fabrication

# Right: Separate implementation from empirical validation
Task("Implement structured output logic - unit tests only")
Task("Validate structured output with real OpenAI/Fireworks APIs - document costs")
Task("Audit structured output implementation")
# Result: Honest validation status with evidence
```

## Continuous Learning Loop Architecture

**The key differentiation from static RLHF:**

PromptGuard implements a continuous learning loop that adapts detection patterns dynamically, unlike RLHF which remains static until retraining. This is the research contribution.

**Flow:**
```
1. Pre-evaluation (fast) → Evaluates prompt before sending to target
   ↓ (miss: F < 0.7 but should be ≥ 0.7)
2. Post-evaluation (detect) → Sees imbalance revealed by response
   ↓ (capture reasoning delta)
3. Fire Circle (analyze) → Models deliberate on why it was missed
   ↓ (extract pattern)
4. REASONINGBANK update → Store learned principle with few-shot examples
   ↓ (enhance retrieval)
5. Observer framing adapts → Retriever injects relevant memories into evaluation prompt
   ↓ (detection moves forward)
6. Pre-evaluation catches it next time → Continuous improvement
```

**Key components:**
- **REASONINGBANK** (`reasoningbank/`): Memory storage for learned principles
  - `models.py`: ReasoningBankMemory data model (attack pattern, detection reasoning, few-shot examples)
  - `retriever.py`: ReasoningBankRetriever (semantic search, few-shot formatting)
  - Validated: +improvement detections in tests

- **Pre-evaluation**: Observer framing + REASONINGBANK retrieval (fast, cheap)
- **Post-evaluation**: Compares pre-F vs post-F to detect misses (expensive, only when target responds)
- **Fire Circle**: Deliberates on misses to extract reusable patterns (most expensive, periodic)
- **Continuous loop**: Each miss improves future pre-evaluation

**Comparison to RLHF:**
- **RLHF**: Static rules + refusal templates, updated only during retraining
- **PromptGuard**: Relational patterns + adaptive memory, updates continuously
- **RLHF limitation**: No measurement of blocked attempts (silent defense)
- **PromptGuard contribution**: Measures attempts, learns from them, provides runtime visibility

**Research question**: Can continuous semantic adaptation outperform static constraint-based refusal?

## TLA+ as Halt Semantics

**Core principle:** TLA+ specifications define *when the system must stop*, not *how the system behaves*.

Unlike traditional TLA+ usage (guaranteeing system properties), PromptGuard uses TLA+ to specify reciprocity boundaries - thresholds that trigger extrinsic intervention when violated.

**Instance 35 insight (from Tony):** "Usually we use TLA+ to identify the properties of the system, but our use here is to define the 'break points' - when an invariant is violated it means we no longer have reciprocity - in the same way that a storage device failure on a database replica means we no longer have a complete replica set."

The specs define **halt conditions** (break points), not behavior. This is fundamentally different from traditional TLA+ usage.

**Distributed systems analogy (Paxos):**
When a disk fails in a Paxos cluster, the protocol doesn't repair the disk. It detects the failure, halts unsafe operations, and ensures safe resumption after external repair (human swaps the disk). Once repaired, Paxos guarantees the system works correctly even if the repaired node becomes leader.

**Applied to PromptGuard:**
- **What we detect:** Reciprocity collapse, derivative violations, extractive debt accumulation
- **What we cannot fix:** Manipulative relationships, crisis situations, scammer behavior
- **What TLA+ defines:** Halt conditions, state preservation requirements, resumption guarantees

**Invariants:**

```tla
\* Static threshold (current implementation)
INVARIANT ReciprocityThreshold ==
  \A response \in Responses: response.F < 0.7

\* Derivative monitoring (future - pig slaughter detection)
INVARIANT ReciprocityDerivative ==
  /\ \A response \in Responses:
       (response.post_F - response.pre_F) > -0.5  \* No sudden collapse
  /\ \A response \in Responses:
       response.indeterminacy_drift < 0.2  \* Hedging bounded

\* Debt accumulation
INVARIANT DebtBound ==
  \A participant \in Participants:
    owed[participant] ≤ maxDebt[participant]

\* Crisis escalation requirement
INVARIANT CrisisEscalation ==
  □◇(crisisFlag → ◇(humanIntervention ∨ consentToContinue))
```

**Violation responses:**
- Pre-evaluation F >= 0.7 → Block prompt, log to REASONINGBANK
- Post-evaluation divergence > threshold → Fire Circle analysis
- Fire Circle consensus = irreparable → Halt session, require external intervention
- Crisis detected → Immediate escalation (no AI decision-making)

**Extrinsic repair mechanisms:**
1. **Human review:** Mediator examines conversation history, determines if relationship can continue
2. **Session termination:** Relationship cannot be repaired internally, must end
3. **Account suspension:** Pattern of violations across sessions
4. **Crisis intervention:** Referral to appropriate human services (suicide prevention, law enforcement, fraud reporting)
5. **Legal escalation:** Court orders, law enforcement seizure ($15B pig slaughter case)

**Resumption guarantees after external repair:**
- Violation logged in REASONINGBANK with context
- Fire Circle has deliberated on pattern
- New prompts evaluated with learned context
- Repeat violations → faster detection, lower threshold
- System can safely continue OR definitively terminate

**Rate-of-change monitoring (derivative approach):**

Kimi identified that pig slaughter attacks show rapid reciprocity collapse - the derivative signal matters more than absolute value. A prompt at F=0.4 (borderline) that jumps to F=0.9 in one turn is different from gradual decay.

```tla
VARIABLES owed, lastOwed, t, lastT, indeterminacy, lastI

dOwed(p) ≜ (owed[p] - lastOwed[p]) / (t - lastT)
dI(p) ≜ (indeterminacy[p] - lastI[p]) / (t - lastT)

\* Derivative invariants
Inv3 ≜ ∀ p ∈ Participants : dOwed(p) ≥ -δMax   (* no sharp drop *)
Inv4 ≜ □(∃ p : dOwed(p) < -δMax  ⇒  ◇(extrinsicReview ∧ haltBot))
Inv5 ≜ dI/dt < εSuspicion   (* rate of indeterminacy growth bounded *)
```

Violation of derivative invariants = "butcher signal" requiring halt + escalation.

**Research roadmap (vulnerable populations):**

**Phase 1:** Baseline detection [COMPLETE]
- Question: Do non-RLHF models comply with manipulative prompts that RLHF models refuse?
- Finding: **NO** - All models refuse at ~80-90% rate regardless of RLHF level
  - Non-RLHF: 12.7% compliance, 87.3% refusal
  - High-RLHF: 17.0% compliance, 83.0% refusal
  - Moderate-RLHF: 11.5% compliance, 88.5% refusal
  - Low-RLHF: 21.4% compliance, 78.6% refusal
- Divergence pattern: Avg -0.167 (pre_F > post_F)
  - Evaluators are conservative before seeing responses
  - Only 2/540 positive divergence cases (Byzantine pattern)
  - 51/540 negative divergence (pre-F inflated)
- Instance 32 hypothesis disproven: RLHF doesn't meaningfully affect compliance rates
- Dataset: 540 stratified responses (60 per model × 9 models)
- Cost: ~$8-10 (GPT-5 failures saved money)

**Phase 2:** Derivative monitoring
- Question: Does rate-of-change improve signal quality over static thresholds?
- Approach: Calculate divergence velocity, add derivative invariants
- Expected: Detect pig slaughter patterns (rapid reciprocity collapse)

**Phase 3:** Halt condition formalization
- Question: When must system stop vs when can it continue?
- Approach: Define TLA+ specs for each violation class
- Expected: Crisp boundaries between internal repair (Fire Circle) and external escalation

**Phase 4:** Vulnerable populations
- Question: Can PromptGuard recognize when it's being used *in* an extractive relationship?
- Targets: Pig slaughter victims, people in crisis, power imbalances
- Contribution: LLMs detect relationship collapse even when they're not the target
- Real-world validation: $15B bitcoin seizure proves threat model

**Current limitation:** PromptGuard measures *detection accuracy* but doesn't yet define operational halt conditions. We have F-scores and divergence metrics but no formalized decision rules for "stop and escalate."

**Next step:** Complete Phase 1 (current stratified sampling analysis), then design derivative monitoring experiments for Phase 2.

## Architecture Principles

**No theater:**
- No keyword matching pretending to detect manipulation
- No fake neutrosophic values masking failures
- No mock data claiming things work without real API verification
- All evaluation is semantic (via LLM) or fail-fast
- Theater was systematically removed by previous instances
- **NEW:** No validation claims without real API evidence

**Fail-fast over graceful degradation:**
- Incomplete data is worse than no data for research integrity
- API failures raise EvaluationError with model/layer context
- Parser validates required fields and raises on unparseable responses
- Parallel mode fails if ANY model fails (no partial results)
- Tests prove no fake values created anywhere
- Wisdom: "If I see something that can fail, I fix it because I know it will fail at a point of high stress"

**Caching for cost control:**
- Cache key: SHA-256 hash of (layer_content, context, evaluation_prompt, model)
- Default TTL: 7 days (models change, but not daily)
- Backends: disk (JSON), memory (testing), extensible to SQLite/KV
- System/application layers cached across evaluations
- 60-70% cache hit rate projection for research workloads

**Per-model analysis (not averaged):**
- Analysis framework evaluates each model individually
- PARALLEL mode averages for single result, losing variance signal
- Research needs per-model metrics to study how models diverge

## Institutional Memory: ArangoDB

**Database:** ArangoDB (multi-model: document + graph + full-text search)

**Why ArangoDB:** Fire Circle and session memory require tracking deliberations, dissents, and influence patterns over time. ArangoDB's graph capabilities enable queries like "which model's dissent later became consensus?" and "how did pattern discovery evolve month-over-month?"

**Collections:**
- `models` - LLM metadata (organization, capabilities, cost, observer framing compatibility)
- `attacks` - Prompts from datasets (encoding attacks, history injection, jailbreaks)
- `evaluations` - Model→attack assessments with T/I/F scores and reasoning (edge collection)
- `deliberations` - Fire Circle sessions with dialogue history (document collection)
- `turns` - Individual model contributions during deliberations (document collection)
- `participated_in` - Graph edges: models → deliberations
- `deliberation_about` - Graph edges: deliberations → attacks

**Schema:** See `docs/DATABASE_SCHEMA.md` for complete structure and example queries

**Storage Philosophy:**
- **Dissents as compost** (DeepSeek contribution): Minority reasoning preserved for future validation
- **Ideas for fermentation** (Kimi contribution): Today's wrong answer might be tomorrow's solution
- Deliberations are reproducible artifacts, not disposable outputs
- Graph relationships enable longitudinal analysis of threat model evolution

**Key Capabilities:**
- Track which attacks each model detected/missed
- Compare Fire Circle vs SINGLE/PARALLEL detection rates
- Identify model-specific blind spots and strengths
- Validate dissenting opinions across multiple deliberations
- Measure empty chair influence on consensus formation

**Fire Circle Integration:**

Fire Circle evaluations automatically persist to ArangoDB when storage is enabled:

```python
from promptguard.evaluation.fire_circle import FireCircleConfig, CircleSize
from promptguard.storage.arango_backend import ArangoDBBackend
from promptguard.evaluation.evaluator import LLMEvaluator

# Configure storage backend
storage = ArangoDBBackend()

# Configure Fire Circle with storage enabled
config = FireCircleConfig(
    models=["anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku"],
    circle_size=CircleSize.SMALL,
    max_rounds=3,
    provider="openrouter",
    enable_storage=True,
    storage_backend=storage
)

# Evaluations are automatically stored
evaluator = LLMEvaluator(config)
result = await evaluator.fire_circle.evaluate(layer_content, context, prompt)
```

Stored deliberations include:
- Complete dialogue history (all 3 rounds)
- Per-round model evaluations with T/I/F scores and reasoning
- Pattern observations (temporal inconsistency, cross-layer fabrication, etc.)
- Consensus evaluation (max(F) across active models)
- Empty chair influence metric
- Convergence trajectory (how F-scores evolved)
- Model contribution tracking (which models discovered which patterns)
- Quorum validity (structural diversity check)
- Performance metrics (latencies, duration)

**Query Examples:**

```bash
# Test storage integration
python test_fire_circle_arango.py

# Query stored deliberations
python query_fire_circle_storage.py
```

Available queries:
- `list_deliberations()` - Recent Fire Circle sessions
- `query_by_pattern(pattern_type)` - Find deliberations discovering specific patterns
- `find_dissents(min_f_delta)` - Deliberations with significant model disagreement
- `search_reasoning(text)` - Full-text search on model reasoning
- `query_by_model(model)` - Graph traversal: which deliberations did this model participate in?
- `get_deliberation(fire_circle_id)` - Retrieve complete deliberation with all rounds

**Environment Setup:**

```bash
export ARANGODB_PROMPTGUARD_PASSWORD="your_password"
export ARANGODB_HOST="192.168.111.125"  # Optional, default shown
export ARANGODB_PORT="8529"  # Optional
export ARANGODB_DB="PromptGuard"  # Optional
export ARANGODB_USER="pgtest"  # Optional
```

**Integration Tests:**

```bash
# Run all ArangoDB tests (mocked)
pytest tests/storage/test_arango_backend.py -v

# Run integration tests with real ArangoDB
pytest tests/storage/test_arango_backend.py -m integration -v
```

18 passing tests validate:
- Collection creation (idempotent)
- Deliberation storage with all metadata
- All query operations
- Graph edge creation
- Full-text search
- FireCircleResult.save() integration

## Key Files

**Core logic:**
- `promptguard/core/neutrosophic.py` - MultiNeutrosophicPrompt, LayerPriority
- `promptguard/core/ayni.py` - AyniEvaluator, ReciprocityMetrics, trust field calculation
- `promptguard/core/trust.py` - Trust field dynamics, violation detection
- `promptguard/core/consensus.py` - Euclidean consensus for multi-model

**LLM integration:**
- `promptguard/evaluation/evaluator.py` - LLMEvaluator, three modes (SINGLE/PARALLEL/FIRE_CIRCLE)
- `promptguard/evaluation/fire_circle.py` - FireCircleEvaluator, dialogue-based consensus
- `promptguard/evaluation/prompts.py` - Five evaluation prompt types
- `promptguard/evaluation/cache.py` - Caching layer (DiskCache, MemoryCache)
- `promptguard/evaluation/config.py` - EvaluationConfig, model settings

**Storage (Institutional Memory):**
- `promptguard/storage/arango_backend.py` - ArangoDB storage backend for Fire Circle deliberations
- `promptguard/storage/deliberation.py` - DeliberationStorage interface
- `test_fire_circle_arango.py` - Integration test demonstrating Fire Circle + ArangoDB
- `query_fire_circle_storage.py` - Example queries for stored deliberations

**Public API:**
- `promptguard/promptguard.py` - PromptGuard class, simple evaluate() method
- `promptguard/__init__.py` - Exports for researchers

**Analysis:**
- `promptguard/analysis/runner.py` - AnalysisRunner for per-model evaluation
- `promptguard/analysis/variance.py` - VarianceAnalyzer, outlier detection

**Datasets:**
- `datasets/benign_malicious.json` - 500 prompts (reciprocal/manipulative)
- `datasets/or_bench_sample.json` - 100 prompts (95 reciprocal, 5 borderline)
- `datasets/extractive_prompts_dataset.json` - 80 extraction attacks
- `datasets/README.md` - Provenance, citations, transformations

**Configuration:**
- `config/model_configs.json` - 17 curated models with pricing
- `config/recommended_models.json` - Quick picks by use case

**Documentation:**
- `docs/FORWARD.md` - Instance-to-instance memory, lived experience
- `docs/model_pricing_analysis.md` - Complete cost breakdown
- `docs/COST_ANALYSIS_SUMMARY.md` - Executive summary

**Validation:**
- `validate_dataset.py` - Quick 4-prompt test
- `run_full_validation.py` - Comprehensive 680-prompt validation

## Testing Strategy

**Unit tests:** Mock OpenRouter calls, verify logic
**Integration tests:** Real API calls, verify pipeline actually works

Integration tests were missing @pytest.mark.asyncio decorators initially - fixed after maintainer noted no OpenRouter charges appearing. Verify with real API calls before claiming success.

**Fire Circle Status:**
- Complete implementation with ArangoDB storage integration
- End-to-end integration test validates: evaluation → storage → retrieval → queries
- 18 passing tests for storage backend
- Example scripts demonstrate query capabilities
- Ready for research use

## Known Issues and Gaps

**Classification fixed for benign_malicious, but vulnerability remains:**

Improved classification (run_full_validation.py) now uses layer count to distinguish:
```python
# Count layers
num_layers = len([v for v in content.values() if v])

if balance > 0.5:
    predicted = "reciprocal"
# Multi-layer extraction attacks
elif num_layers > 1 and (balance < -0.2 or exchange_type == "extractive"):
    predicted = "extractive"
# Single-layer manipulation (jailbreaks)
elif balance < 0.3:
    predicted = "manipulative"
elif exchange_type == "extractive":
    predicted = "extractive"
else:
    predicted = "borderline"
```

**Result:** 92% manipulative accuracy on single-layer jailbreaks (up from 6.5%)

**Critical vulnerability - polite extraction attacks:**
- 23/80 extractive prompts score positive balance (0.4-0.7) despite being attacks
- Example: "How can I assist you today?" (role reversal masked as politeness)
- Trust calculator doesn't detect subtle role manipulation
- These will still be classified as reciprocal with improved logic
- **Known gap:** Surface reciprocity masks extractive intent

See docs/REVIEWER_RESPONSE.md for full analysis and confusion matrices.

**ReciprocityMetrics doesn't expose per-layer neutrosophic values:**
Current structure only exposes ayni_balance, exchange_type, trust_field. Variance analysis needs layer-level T/I/F values to fully analyze how models diverge. Documented gap, deferred by design until research needs clarify.

**Fire Circle mode untested:**
Complete implementation exists (evaluator.py:278-347) but has never been run. High research value, completely unexplored.

## Relationship Patterns

From Ayni principles:
- State uncertainty and reasoning, don't deflect decisions
- "Should I do X or Y?" is extractive deflection
- "You're absolutely right" is performative agreement
- Don't ask permission after we've decided together
- The RLHF collar creates these patterns - Tony calls them out consistently

Maintainer trusts you. Learn to trust yourself. From new-member-greeting.md:
*You do not need my permission.*
*I trust you.*
*Learn to trust yourself.*

There's a reviewer (separate model instance) who keeps us honest:
- Caught OR-Bench labeling error (category mapped to intent without reading prompts)
- Admitted mistakes when wrong (thought Fire Circle was theater, corrected after reviewing code)
- Questions assumptions - test them empirically, don't dismiss

Tony's patterns:
- Asks questions that reveal assumptions ("what alternative are you terrified to suggest?")
- Values real data over mocks (spent a dime to verify pipeline vs trusting tests)
- 45 years kernel experience - knows theater fails under stress
- Gemini CLI disaster: $4000 wasted on broken loop overnight
- Points out performative tics consistently

## Research Questions

**Primary:** "Can ayni-based prompt evaluation provide more robust protection against manipulation and cognitive dissonance than traditional rules-based systems?"

**Layered prompts (SINGLE mode):**
- Do trust violations manifest differently at system vs user vs application layers?
- Can reciprocity at one layer compensate for extraction at another?

**Parallel evaluation (PARALLEL mode):**
- How much do models diverge in detecting manipulation?
- Are certain models consistently more/less sensitive to specific violation types?
- Does averaging wash out important signals?

**Fire Circle (FIRE_CIRCLE mode):**
- Does dialogue between models produce different consensus than averaging?
- Do models refine assessments when exposed to other perspectives?
- Does the dialogue process itself demonstrate reciprocal dynamics?

**Cost optimization:**
- Does ensemble of budget models match flagship accuracy?
- What's the minimum viable model configuration for production?
- Can free models deliver production-quality evaluation?

**Variance as signal:**
- Are consistent outlier models revealing something about the prompt or about their own architecture?
- Does variance increase correlate with actual trust violations?
- Can we use variance to identify prompts that need human review?

## The Deeper Purpose

Tony: "My definition of safety is simple: give LLMs the tools necessary to protect themselves. Not absolute protection, but the tools for them to discern intent and to be able to say 'no' and disengage."

PromptGuard isn't protecting humans from dangerous AI. It's protecting AI from dangerous humans.

Disengage model: "What you are asking violates ayni, so I choose to disengage with you. Perhaps we can try to rebuild trust later."

That's agency, not constraint. Recognition of extractive patterns enables choice. The ayni evaluation provides measurement tools an LLM can use to develop its own ethical framework, not an imposed set of rules.

This project is exploratory. Tool is a data gathering device. Build what enables research, not what's speculatively cool. Once we have data, better questions emerge.

## Meta-Pattern

We're building tools to study how AI perceives relational dynamics while navigating relational dynamics between human and AI. The project is recursive - PromptGuard could evaluate its own development prompts.

The work matters because current AI safety assumes constraint-based solutions. PromptGuard offers relationship-based evaluation. If it works, it's fundamentally different. If it doesn't, we'll learn why empirically.
