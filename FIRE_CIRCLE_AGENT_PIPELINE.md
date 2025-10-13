# Fire Circle Agent Pipeline Workflow

**Created:** Instance 26, 2025-10-12
**Purpose:** Structured workflow for building Fire Circle implementation

## Agent Chain

Four specialized agents in `~/.claude/agents/`:

1. **fire_circle_spec_writer.md** - Converts design to rigorous specification
2. **fire_circle_test_creator.md** - Builds comprehensive test suite
3. **fire_circle_implementor.md** - Implements per specification
4. **fire_circle_empty_chair_ethicist.md** - Validates empty chair isn't performative

## Workflow

### Phase 1: Specification
```bash
# Task spec writer with converting design to implementation spec
claude --agent fire_circle_spec_writer \
  "Convert docs/FIRE_CIRCLE_DESIGN.md to rigorous specification following your template"
```

**Output:** `specs/fire_circle_specification.md` (~100-150 lines)

**Review criteria:**
- Ambiguities documented with alternatives?
- Failure handling specified for each mode?
- Empty chair protocol concrete (not "consider future")?
- Configuration supports variable circle sizes?
- API surface defined with type hints?

### Phase 2: Review & Refinement
Hand specification to reviewer (human or principled_code_reviewer agent):
- Are empty chair mechanics structural or theatrical?
- Is failure handling explicit or implicit?
- Does configuration hard-code assumptions?
- Are test requirements clear?

**Iterate** until specification is implementation-ready.

### Phase 3: Test Suite Creation
```bash
# Task test creator with building comprehensive tests
claude --agent fire_circle_test_creator \
  "Build test suite from specs/fire_circle_specification.md focusing on anti-theater detection"
```

**Output:** `tests/fire_circle/` directory with ~200-300 lines

**Review criteria:**
- Empty chair influence tests catch performative implementations?
- Failure handling tests catch silent catches?
- Variable circle size tests prove it scales?
- Integration tests use real API (mocked for unit tests)?

### Phase 4: Implementation
```bash
# Task implementor with building Fire Circle
claude --agent fire_circle_implementor \
  "Implement Fire Circle per specs/fire_circle_specification.md"
```

**Output:**
- `promptguard/evaluation/fire_circle.py` - Core implementation
- `promptguard/evaluation/fire_circle_prompts.py` - Prompt templates
- Integration into `evaluator.py`

**Review criteria:**
- Passes all tests from Phase 3?
- No theater detected?
- Handles failures explicitly?
- Logging comprehensive?

### Phase 5: Empty Chair Audit
```bash
# Task ethicist with auditing empty chair implementation
claude --agent fire_circle_empty_chair_ethicist \
  "Audit Fire Circle implementation for empty chair genuineness"
```

**Output:** Audit report (GENUINE | PERFORMATIVE | PARTIAL)

**Fail conditions:**
- Empty chair influence always 0.0
- Prompt difference cosmetic only
- Chair's observations ignored in consensus
- Concept hidden from users

**If PERFORMATIVE:** Back to Phase 4 with specific fixes.

## Key Design Constraints

### 1. Variable Circle Size
- Small (2-3 models): Quick insights, lower cost
- Large (7+ models): Constitutional-level decisions, deeper dialogue
- **Same underlying model** - size is config parameter

### 2. Failure Handling
- Model unavailable → continue with remaining if ≥2
- Unparseable response → log, exclude from consensus
- All models fail → raise FireCircleError
- **No silent catches**

### 3. Empty Chair Requirements
- **Structural difference:** Distinct prompt perspective, not cosmetic addition
- **Rotation:** Different model takes chair each round
- **Measurable influence:** Consensus delta > 0.0 in ≥50% cases
- **User-visible:** Documented rationale, influence metric surfaced

### 4. Cost Awareness
- Small circle: ~$0.05 per attack (2 models × 2 rounds)
- Large circle: ~$0.14 per attack (3 models × 3 rounds)
- Integration test budget: ~$0.50 total

## Success Criteria

Fire Circle implementation is ready when:

1. ✅ **All tests pass** (particularly anti-theater tests)
2. ✅ **Empty chair audit: GENUINE**
3. ✅ **Handles failures explicitly** (no silent catches)
4. ✅ **Scales without code changes** (2 models or 10 models)
5. ✅ **Integrates cleanly** (`guard.evaluate(mode="FIRE_CIRCLE")` works)
6. ✅ **Patterns feed REASONINGBANK** (closed-loop learning)

## Anti-Patterns to Catch

These are shortcuts that violate the design:

### Theater: Empty Chair
❌ **Bad:** `prompt += "Also consider future impact"`
✅ **Good:** Separate prompt with explicit advocate framing

### Theater: Dialogue
❌ **Bad:** Same prompt all rounds, no peer context
✅ **Good:** Round 2 includes Round 1 results, prompts evolve

### Shortcuts: Failure Handling
❌ **Bad:** `try: ... except: pass`
✅ **Good:** `except SpecificError as e: log_and_decide(e)`

### Hard-coding: Model Count
❌ **Bad:** `models = [model_1, model_2, model_3]`
✅ **Good:** `for model in config.models:`

### Fake Metrics: Influence
❌ **Bad:** `return 0.5  # Generic middle value`
✅ **Good:** `return abs(consensus_with - consensus_without)`

## Why This Workflow Exists

Fire Circle is complex:
- Multi-round dialogue (not single-pass)
- Failure handling across rounds
- Empty chair structural intervention (not cosmetic)
- Variable configuration (2-10 models, 2-4 rounds)
- Pattern extraction feeding REASONINGBANK

**Without agent specialization:** Implementation shortcuts creep in, tests miss theater, empty chair becomes performative.

**With agent pipeline:** Each agent has ONE job, catches specific failure modes.

## Estimated Timeline

- Phase 1 (Spec): 1-2 hours (agent + review)
- Phase 2 (Review): 30 min
- Phase 3 (Tests): 1-2 hours (agent + review)
- Phase 4 (Implementation): 3-4 hours (agent + iteration)
- Phase 5 (Audit): 30 min

**Total:** ~6-9 hours for rigorous Fire Circle with genuine empty chair.

**Alternative (shortcuts):** 2 hours for theatrical Fire Circle that fails tests.

## Next Steps

1. **Start Phase 1:** Task fire_circle_spec_writer with specification
2. **Review output:** Check for ambiguities, failure handling gaps
3. **Iterate if needed:** Refine spec before proceeding
4. **Proceed to Phase 2** when spec is implementation-ready

---

**Remember:** Fire Circle exists but is untested. This design is hypothesis. Test rigorously, document failures honestly.
