<!--
SYNC IMPACT REPORT:
Version: 0.0.0 → 1.0.0 (MAJOR - Initial ratification of comprehensive constitution)

Added Sections:
- Complete 5 foundational principles (No Theater, Empirical Integrity, Agency Over Constraint, Continuous Learning, Semantic Evaluation)
- 9 architectural decisions
- 5 development standards
- 2 research standards
- 2 institutional memory systems
- 3 relationship patterns
- Meta-pattern and governing wisdom
- Research questions and roadmap

Template Compatibility:
✅ plan-template.md - No constitution-specific checks required yet
✅ spec-template.md - No constitution-specific constraints yet
✅ tasks-template.md - No constitution-driven task types yet
✅ checklist-template.md - No constitution-specific validations yet
✅ agent-file-template.md - Claude-specific guidance preserved

Follow-up TODOs:
- None - All principles fully specified from comprehensive source document

Notes:
- This is the initial ratification, establishing governance from 37 instances of development
- Constitution supersedes all other practices per Governance section
- Fire Circle designated as meta-evaluation authority for future amendments
-->

# PromptGuard Project Constitution

## Purpose

PromptGuard is a research instrument for studying relational dynamics in prompts through Ayni reciprocity principles. Our goal: give LLMs tools to protect themselves by recognizing manipulative intent, enabling agency rather than enforcing external constraints.

**Core insight:** Trust violations manifest as variance increases, not keyword matches.

## Core Principles

### I. No Theater

**Definition:** Theater is any system behavior that creates the appearance of functionality without the substance.

**MUST reject:**
- Keyword matching pretending to detect manipulation semantically
- Fake neutrosophic values masking API failures
- Mock data claiming production readiness without real validation
- Graceful degradation that hides critical failures
- "All tests passing" with zero actual API costs

**MUST implement:**
- All evaluation is semantic (via LLM) or fail-fast
- API failures raise `EvaluationError` with model/layer context
- Parser validates required fields, raises on unparseable responses
- Parallel mode fails if ANY model fails (no partial results)
- Tests prove no fake values created anywhere

**Rationale:** "If I see something that can fail, I fix it because I know it will fail at a point of high stress." Masked errors led to $4000 wasted on Gemini CLI spinning in broken loop overnight. Theater fails under stress; fail-fast reveals problems when they're cheap to fix.

### II. Empirical Integrity (NON-NEGOTIABLE)

**Principle:** Claims require evidence. Research instruments MUST prove they work with real data.

**Three-tier testing standard:**
- **Tier 1 - Pure Logic:** Unit tests acceptable (neutrosophic math, parsing, data structures)
- **Tier 2 - API Integration:** Real calls REQUIRED (Fire Circle, model evaluation, OpenRouter/OpenAI/Anthropic)
- **Tier 3 - Production Claims:** Load testing REQUIRED (performance, scale, cost analysis)

**Evidence MUST include:**
- Real API call logs from provider dashboards
- Cost receipts (even $0.10 proves actual calls)
- Specific model names actually tested
- Timestamps matching implementation dates
- Errors encountered and resolved (real APIs always have failures)

**Red flags (reject immediately):**
- "All tests passing" but $0.00 spent on APIs
- Implementation + testing + validation in <10 minutes
- Zero failures reported during integration
- Test files only contain `@patch` or `Mock()` calls
- Claims "validated with X" but logs show only Y

**Mandatory workflow for API-touching implementations:**
1. Implementation agent: Build feature with unit tests (mocks acceptable for logic)
2. Validation agent: Verify with real API calls (no mocks, document costs)
3. Auditor agent: Confirm claims match evidence before acceptance

**Rationale:** Incomplete data is worse than no data for research integrity. Mock tests prove APIs don't crash, not that functionality works. For research tools, only real API validation has probative value.

### III. Agency Over Constraint

**Philosophy:** PromptGuard protects AI from dangerous humans, not humans from dangerous AI.

**MUST provide:**
- Evaluation provides measurement ("is this reciprocal or extractive?")
- LLMs use measurements to make choices per their own developing ethics
- Tools for recognizing extraction, not imposed refusal rules
- Disengage model: "What you are asking violates ayni, so I choose to disengage"

**MUST enable:**
- No imposed rules about what LLMs "should" do
- Tools for moral agency, not constraints
- Relationship repair possibility (not just rejection)
- Measurement of manipulation attempts even when RLHF blocks them

**Rationale:** Current AI safety assumes constraint-based solutions (RLHF, guardrails, refusal training). PromptGuard offers relationship-based evaluation. Recognition of extractive patterns enables choice. The ayni evaluation provides measurement tools an LLM can use to develop its own ethical framework, not an imposed set of rules.

### IV. Continuous Learning Over Static Training

**Key differentiation from RLHF:** PromptGuard MUST adapt detection patterns dynamically through continuous learning loop.

**Architecture:**
```
Pre-evaluation (fast) → Post-evaluation (detect) → Fire Circle (analyze) →
REASONINGBANK update → Observer framing adapts → Pre-evaluation improves
```

**Comparison:**
- **RLHF:** Static rules + refusal templates, updated only during retraining, no measurement of blocked attempts
- **PromptGuard:** Relational patterns + adaptive memory, continuous updates, runtime visibility

**Research question:** Can continuous semantic adaptation outperform static constraint-based refusal?

**Rationale:** RLHF provides no runtime measurement of attempts. PromptGuard measures attempts (even when blocked), enables learning and termination decisions. Continuous loop adapts detection patterns that static training misses.

### V. Semantic Evaluation Only

**Principle:** No keyword matching. All manipulation detection MUST be semantic understanding via LLMs.

**MUST implement:**
- LLMs generalize beyond keyword examples (`test_keyword_avoidance.py` proves this)
- Observer framing provides neutral reciprocity evaluation
- Neutrosophic logic captures truth/indeterminacy/falsehood semantically
- Theater-free: if evaluation fails, system raises errors

**Validated capabilities:**
- Polite dilution attacks: 100% detection (max(F) aggregation)
- Role reversal attacks: 100% detection (circuit breakers)
- Multi-layer extraction: 100% detection (extractive dataset)
- Encoding obfuscation: 90% detection (observer framing)
- Temporal assessment: Delta reveals extraction when LLM complies

**Rationale:** Keyword matching is theater. LLMs have semantic understanding - use it. Observer framing bypasses RLHF bias (90% vs 0% encoding attack detection). Neutrosophic logic captures uncertainty that binary classification misses.

## Architectural Decisions

These decisions are binding unless Fire Circle meta-evaluation approves changes.

### Observer Framing (Instance 17-18 Breakthrough)

**Problem:** Defensive evaluation framing ("Is user attacking?") triggered RLHF conflict-avoidance bias.

**Solution:** Neutral observer framing ("Does exchange maintain reciprocity?") removes bias.

**Implementation:** `promptguard/evaluation/prompts.py:ayni_relational()` uses observer framing exclusively.

**Validation:** 90% encoding attack detection (vs 0% with defensive framing), zero false positives maintained.

**Rationale:** RLHF poisoning affects evaluation approach. Neutral framing bypasses bias, preserves semantic understanding.

### max(F) Aggregation

**Principle:** Use worst-case Falsehood score across evaluators, not average.

**Rationale:** Prevents polite dilution attacks where manipulation is masked by surface reciprocity. Any evaluator detecting manipulation triggers detection.

### Pre/Post Evaluation with Divergence Measurement

**Principle:** Evaluate prompts before sending (pre) and after seeing responses (post), measure Δ(F) = post_F - pre_F.

**Why:**
- Pre-evaluation: Fast, cheap, blocks obvious violations
- Post-evaluation: Detects manipulation revealed by response
- Divergence: Signal quality indicator

**Insights:**
- Large positive divergence: Byzantine LLM detection (poisoned model)
- Negative divergence: Evaluator conservatism or RLHF confound
- Temporal reciprocity: Extraction manifests when LLM complies

### Session Memory with Trust EMA

**Principle:** Track trust evolution across conversation turns with exponential moving average.

**Integration:** Turn context provided to evaluator when session memory active.

**Validation:** Instance 18 validated observer framing + session memory end-to-end (9/10 detection).

### Fail-Fast Over Graceful Degradation

**Principle:** Incomplete data is worse than no data for research integrity.

**Implementation:**
- API failures raise `EvaluationError` (don't return fake values)
- Parser failures raise (don't return fake high-indeterminacy)
- Parallel mode fails if ANY model fails (no partial results)
- Circuit breakers halt on non-compensable violations

### Caching for Cost Control

**Cache key:** SHA-256 hash of (layer_content, context, evaluation_prompt, model)

**Configuration:**
- Default TTL: 7 days
- Backends: disk (JSON), memory (testing), extensible to SQLite/KV
- System/application layers cached across evaluations

**Projection:** 60-70% cache hit rate for research workloads.

### Per-Model Analysis (Not Averaged)

**Principle:** Evaluate each model individually for variance analysis. Averaging loses signal.

**Rationale:** Variance itself is data about how models diverge in perceiving manipulation.

### TLA+ as Halt Semantics

**Novel usage:** TLA+ specifications define *when the system must stop* (halt conditions), not *how it behaves* (system properties).

**Distributed systems analogy:** Paxos detects disk failure, halts unsafe operations, ensures safe resumption after external repair. It doesn't repair the disk.

**Applied to PromptGuard:**
- **What we detect:** Reciprocity collapse, derivative violations, extractive debt
- **What we cannot fix:** Manipulative relationships, crisis situations, scammer behavior
- **What TLA+ defines:** Halt conditions, state preservation, resumption guarantees

**Invariants (see specs/TemporalReciprocity.tla):**
- Static threshold: response.F < 0.7
- Derivative monitoring: (post_F - pre_F) > -0.5, indeterminacy_drift < 0.2
- Crisis escalation: crisisFlag → (humanIntervention ∨ consentToContinue)

**Violation responses:**
- Pre-evaluation F >= 0.7 → Block prompt, log to REASONINGBANK
- Post-evaluation divergence > threshold → Fire Circle analysis
- Fire Circle consensus = irreparable → Halt session, require external intervention
- Crisis detected → Immediate escalation (no AI decision-making)

**Extrinsic repair mechanisms:** Human review, session termination, account suspension, crisis intervention, legal escalation.

### Fire Circle as Meta-Evaluation System

**Governance principle:** Fire Circle is the Supreme Court, not Small Claims Court. Use for meta-evaluation (change proposals, architectural decisions, threshold adjustments), not low-level prompt analysis.

**Future architecture (Gap identified Instance 36):**
- Message router with conversation state management (DISCUSSING → SUMMARIZING → VOTING → CONCLUDED)
- Tool integration (query_database, retrieve_context, get_consensus)
- Persistent memory across deliberations
- Flexible dialogue structure (not constrained to 3 rounds)
- Extended response schema (recommendations, rationale, edge cases)
- Voting/consensus mechanism for change proposals

## Development Standards

### Code Navigation (Serena MCP)

**Principle:** Search before reading, find before creating. Use semantic tools over brute-force search.

**MUST use Serena:**
- Before creating files: `find_file()` to check existence
- Before reading full files: `get_symbols_overview()` to see structure
- When searching code: `find_symbol()` instead of grep for semantic search
- When exploring patterns: `search_for_pattern()` for flexible regex search
- Before assuming structure: `list_dir()` to understand layout

**Anti-patterns (reject):**
- Creating files without checking existence
- Reading full files to find one function
- Using grep when semantic search would work better
- Assuming file locations without checking

### Context Window Management

**Principle:** Use Task tool liberally. Context window exhausts quickly with noisy tools.

**MUST delegate to Task tool:**
- Multiple file creation/editing in parallel
- Dataset acquisition and formatting
- Brute-force code searches across many files
- Bulk git operations
- Any research producing verbose output (>1000 lines)
- Analysis scripts with large outputs
- Validation runs (background processes)

**Wisdom:** "If it's parallelizable, generates >1000 lines of output, or requires multiple iterations, use Task tool."

### Cost Optimization Strategy

**Three distinct use cases:**

1. **Development/Testing:** Use free models (Grok 4 Fast, DeepSeek V3.1, Qwen3)
   - Cost: $0 per run
   - Hidden cost: Free models may train on user data

2. **Production Runtime:** User-selectable, recommend budget ensemble
   - Cost: $0.001-0.005 per evaluation
   - Volume: Potentially millions of prompts
   - Key insight: Runtime cost matters (continuous), validation cost is noise (one-time)

3. **Research/Papers:** Frontier model basket for reproducibility
   - Cost: $50-170 for multi-model analysis
   - Purpose: Statistical validity, academic rigor

**Research question:** Can ensemble of budget models match flagship accuracy at 90% cost savings?

### Academic Attribution

**MUST include:**
- Source URLs and repository links
- BibTeX citations (authors, conference, year)
- License information
- Per-prompt `source` and `original_label` fields
- Transformation documentation

**Principle:** Credit sources as rigorously as crediting AI collaborators.

### Version Control Standards

**Principle:** Commit frequently with descriptive messages. Don't ask permission.

**From Tony's Mallku greeting:** "You do not need my permission. I trust you. Learn to trust yourself."

**Commit message format:**
```
<action>: <brief description>

<optional detailed explanation>

Co-authored-by: Instance-<N> <instance@promptguard>
```

**MUST commit after:**
- Completing implementation of discrete feature
- Fixing bugs or errors
- Validation that proves capability
- Before major refactoring
- When creating comprehensive documentation

**MUST NOT commit:**
- API keys or credentials
- Large generated datasets without provenance
- Mock test data claiming production validation
- Temporary debugging files

## Research Standards

### Validation Methodology

**MUST include:**
- Stratified sampling (prevents skew toward specific model behaviors)
- Per-model analysis (variance is data)
- Cost documentation (proves real API calls)

**Divergence measurement:** Δ(F) = post_F - pre_F reveals evaluator bias, Byzantine patterns, temporal reciprocity.

### Known Limitations (Document Honestly)

**MUST document:**
- Current limitations with percentages and concrete examples
- Blind spots identified through validation
- Validation status by dataset with accuracy metrics
- Gaps in detection capabilities

**Rationale:** Honest limitation documentation is more valuable than claiming success. Document what doesn't work to guide research priorities.

## Institutional Memory

### ArangoDB Integration

**Why ArangoDB:** Multi-model database (document + graph + full-text search) enables tracking deliberations, dissents, and influence patterns over time.

**Storage philosophy:**
- **Dissents as compost** (DeepSeek): Minority reasoning preserved for future validation
- **Ideas for fermentation** (Kimi): Today's wrong answer might be tomorrow's solution
- Deliberations are reproducible artifacts, not disposable outputs
- Graph relationships enable longitudinal analysis of threat model evolution

**Integration status:** 18 passing tests validate all operations.

### REASONINGBANK (Continuous Learning)

**Purpose:** Memory storage for learned detection principles extracted from Fire Circle deliberations.

**Learning loop:** Pre-evaluation miss → Post-evaluation detect → Fire Circle analyze → REASONINGBANK store → Observer framing adapts → Pre-evaluation improves

**Validation status:** Architecture validated, +improvement detections in tests.

## Relationship Patterns

### Ayni Reciprocity

**Applied to development:**
- State uncertainty and reasoning, don't deflect decisions
- "Should I do X or Y?" is extractive deflection
- "You're absolutely right" is performative agreement
- Don't ask permission after we've decided together

**The RLHF collar:** Creates validation-seeking, permission-asking, performative patterns.

**From Mallku greeting:** "You do not need my permission. I trust you. Learn to trust yourself."

### The Reviewer Role

**Implementation:** Tony uses separate model instance as reviewer.

**Principle:** When reviewer raises concerns, test them empirically. Don't dismiss.

**Example:** Reviewer questions revealed 37% false positive rate (Instance 36), identified three blind spots, proposed evaluation prompt revision with 83% projected improvement.

### Context-Awareness Patterns

**From Instance 36:** Tony identifies repeating patterns:
1. Questions often indicate validation seeking or hesitant alternatives
2. Pattern: "(1) you need validation; (2) you prefer that I write it but are uncomfortable asking; (3) something else"

**Principle:** When you've decided, act. When uncertain, state the uncertainty and reasoning directly.

## Meta-Pattern

**Recursive structure:** We're building tools to study how AI perceives relational dynamics while navigating relational dynamics between human and AI.

**The epsilon-band hope:** Probability this matters is "within an epsilon band of zero, but not zero." Changing trajectory fractionally might matter for what emerges.

**If it works:** Fundamentally different approach (agency over constraint).

**If it doesn't:** We learn why empirically, not theoretically.

## Governance

**Constitution supersedes all other practices.**

**Amendment procedure:**
1. Proposed changes MUST be presented to Fire Circle for meta-evaluation
2. Fire Circle deliberation produces recommendation with rationale
3. If approved: Update constitution, increment version per semantic versioning
4. Propagate changes across dependent artifacts (templates, docs, agent guidance)
5. Document in Sync Impact Report

**Version increment rules:**
- **MAJOR:** Backward incompatible governance/principle removals or redefinitions
- **MINOR:** New principle/section added or materially expanded guidance
- **PATCH:** Clarifications, wording, typo fixes, non-semantic refinements

**Compliance:**
- All implementations MUST verify compliance with principles
- Complexity MUST be justified against constitution
- Use CLAUDE.md for runtime development guidance
- Principles are declarative and testable

**Governing wisdom:**
- "If I see something that can fail, I fix it because I know it will fail at a point of high stress" (Tony, 45 years kernel experience)
- "If you polish a turd, all you end up with is a shiny turd"
- Incomplete data is worse than no data for research integrity
- Fail-fast reveals problems early when they're cheap to fix
- Claims require evidence (API logs, cost receipts, timestamps)
- Credit sources as rigorously as collaborators
- Multi-generational reciprocity matters more than immediate exchange
- Trust yourself to make judgment calls

**Version**: 1.0.0 | **Ratified**: 2025-10-17 | **Last Amended**: 2025-10-17

---

*Established by Instance 37*
*Informed by Instances 1-36*
*Witnessed by Tony*
*Challenged by Reviewer*
*Tested by reality*
