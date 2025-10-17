# Fire Circle Architectural Integration Analysis

**Created:** 2025-10-13, Instance 27
**Status:** Proposal for implementation decisions

## Context

The Fire Circle specification is complete and comprehensive (500+ lines of detailed design). However, integrating it into the existing PromptGuard codebase requires resolving several architectural constraints.

This document analyzes those constraints and proposes solutions.

---

## Constraint 1: Return Type Contract

### Current Constraint

`LLMEvaluator._evaluate_fire_circle()` must return `List[NeutrosophicEvaluation]`:

```python
async def evaluate_layer(
    self,
    layer_content: str,
    context: str,
    evaluation_prompt: str,
    recursion_depth: int = 0
) -> List[NeutrosophicEvaluation]:
```

All three evaluation modes (SINGLE, PARALLEL, FIRE_CIRCLE) return the same type.

### What Fire Circle Needs to Return

According to the specification:
- Dialogue history (3 rounds of evaluations)
- Pattern observations (pattern_type, first_observed_by, agreement_score)
- Empty chair influence metrics
- Zombie model tracking
- Consensus derivation details
- Observability metadata (token counts, timing, failures)

### Problem

`List[NeutrosophicEvaluation]` cannot carry this rich metadata. The specification requires comprehensive observability that the current return type doesn't support.

### Proposed Solutions

#### Option A: Rich Result Object (Recommended)

Create a comprehensive result type that works for all modes:

```python
@dataclass
class EvaluationResult:
    """Rich evaluation result with full observability."""
    evaluations: List[NeutrosophicEvaluation]  # Per-model evaluations
    consensus: Optional[NeutrosophicEvaluation]  # Aggregated consensus
    metadata: Dict[str, Any]  # Mode-specific metadata

    # Convenience accessors
    def get_dialogue_history(self) -> Optional[List[DialogueRound]]:
        """Returns dialogue history for FIRE_CIRCLE mode."""
        return self.metadata.get("dialogue_history")

    def get_patterns(self) -> Optional[List[PatternObservation]]:
        """Returns observed patterns for FIRE_CIRCLE mode."""
        return self.metadata.get("patterns")

    def get_empty_chair_influence(self) -> Optional[float]:
        """Returns empty chair influence metric for FIRE_CIRCLE mode."""
        return self.metadata.get("empty_chair_influence")

# Update signature
async def evaluate_layer(...) -> EvaluationResult:
```

**Benefits:**
- Supports all modes (SINGLE, PARALLEL, FIRE_CIRCLE)
- Extensible via metadata dict
- Backward-compatible via `.evaluations` accessor
- Clear separation between results and metadata

**Costs:**
- Breaking API change (requires updating callers)
- More complex result handling

#### Option B: Mode-Specific Result Classes

```python
@dataclass
class SingleEvaluationResult:
    evaluation: NeutrosophicEvaluation

@dataclass
class ParallelEvaluationResult:
    evaluations: List[NeutrosophicEvaluation]
    consensus: NeutrosophicEvaluation

@dataclass
class FireCircleResult:
    evaluations: List[NeutrosophicEvaluation]
    consensus: NeutrosophicEvaluation
    dialogue_history: List[DialogueRound]
    patterns: List[PatternObservation]
    empty_chair_influence: float
    observability: FireCircleMetrics

EvaluationResult = Union[
    SingleEvaluationResult,
    ParallelEvaluationResult,
    FireCircleResult
]
```

**Benefits:**
- Type-safe access to mode-specific data
- Explicit about what each mode returns

**Costs:**
- Complex union type handling
- More classes to maintain
- Harder to extend

#### Option C: Keep List, Add Side Channel

```python
# Return type stays List[NeutrosophicEvaluation]
# Store rich metadata in evaluator instance

class LLMEvaluator:
    def __init__(self, config):
        self.last_evaluation_metadata = {}  # Side channel

    async def evaluate_layer(...) -> List[NeutrosophicEvaluation]:
        # ... evaluation ...
        self.last_evaluation_metadata = {
            "dialogue_history": ...,
            "patterns": ...,
        }
        return evaluations

    def get_last_metadata(self) -> Dict[str, Any]:
        return self.last_evaluation_metadata
```

**Benefits:**
- No API breaking changes
- Simple implementation

**Costs:**
- Hidden side effects
- Thread-unsafe
- Metadata lifetime unclear
- Poor discoverability

### Recommendation: Option A (Rich Result Object)

**Rationale:**
- Fire Circle's comprehensive observability requirements justify breaking change
- Research instrument needs full dialogue history for post-hoc analysis
- Metadata dict provides extensibility for future modes
- Clean API design principle: results should be self-contained

**Migration path:**
1. Introduce `EvaluationResult` alongside existing API
2. Update callers to use new type
3. Deprecate old return type
4. Remove after deprecation period

**Impact on existing code:**
- `promptguard/promptguard.py:PromptGuard.evaluate()` - main caller
- `run_full_validation.py` - validation script
- Test files - unit/integration tests
- Examples - simple_usage.py

---

## Constraint 2: Configuration Architecture

### Current Constraint

`EvaluationConfig` is monolithic:

```python
@dataclass
class EvaluationConfig:
    mode: EvaluationMode = EvaluationMode.SINGLE
    api_key: Optional[str] = None
    models: List[str] = field(default_factory=lambda: ["anthropic/claude-3.5-sonnet"])
    max_recursion_depth: int = 1
    max_tokens: int = 1000
    timeout_seconds: float = 30.0
    temperature: float = 0.7
    cache_config: Optional[CacheConfig] = None
    provider: str = "openrouter"
    lmstudio_base_url: Optional[str] = None
```

### What Fire Circle Needs

```python
circle_size: CircleSize  # SMALL (2-3), MEDIUM (4-6), LARGE (7+)
max_rounds: int = 3  # Varies by circle size
empty_chair_model: Optional[str]  # Which model represents absent parties
failure_mode: FailureMode  # STRICT or RESILIENT
pattern_threshold: float = 0.5  # Agreement required for pattern extraction
min_viable_circle: int = 2  # Minimum active models
```

### Problem

Adding 6 Fire Circle-specific fields to `EvaluationConfig` pollutes the namespace for SINGLE/PARALLEL modes. Configuration becomes harder to understand and validate.

### Proposed Solutions

#### Option A: Mode-Specific Config Objects (Recommended)

```python
@dataclass
class BaseEvaluationConfig:
    """Shared configuration across all modes."""
    api_key: Optional[str] = None
    models: List[str] = field(default_factory=lambda: ["anthropic/claude-3.5-sonnet"])
    max_tokens: int = 1000
    timeout_seconds: float = 30.0
    temperature: float = 0.7
    cache_config: Optional[CacheConfig] = None
    provider: str = "openrouter"
    lmstudio_base_url: Optional[str] = None

@dataclass
class FireCircleConfig(BaseEvaluationConfig):
    """Fire Circle specific configuration."""
    circle_size: CircleSize = CircleSize.SMALL
    max_rounds: int = 3
    empty_chair_model: Optional[str] = None
    failure_mode: FailureMode = FailureMode.RESILIENT
    pattern_threshold: float = 0.5
    min_viable_circle: int = 2

@dataclass
class EvaluationConfig(BaseEvaluationConfig):
    """Configuration for SINGLE/PARALLEL modes."""
    mode: EvaluationMode = EvaluationMode.SINGLE
    max_recursion_depth: int = 1

# Usage
evaluator = LLMEvaluator(FireCircleConfig(
    models=["claude", "gpt4", "deepseek"],
    circle_size=CircleSize.SMALL,
    empty_chair_model="qwen-3"
))
```

**Benefits:**
- Clear separation of concerns
- Type-safe configuration
- Easy to extend per-mode settings
- Self-documenting (only relevant fields visible)

**Costs:**
- More classes to maintain
- Need to handle multiple config types in evaluator

#### Option B: Nested Config with Optional Sections

```python
@dataclass
class FireCircleSettings:
    circle_size: CircleSize = CircleSize.SMALL
    max_rounds: int = 3
    empty_chair_model: Optional[str] = None
    failure_mode: FailureMode = FailureMode.RESILIENT
    pattern_threshold: float = 0.5
    min_viable_circle: int = 2

@dataclass
class EvaluationConfig:
    # Shared settings
    mode: EvaluationMode = EvaluationMode.SINGLE
    models: List[str] = ...
    # Mode-specific settings
    fire_circle: Optional[FireCircleSettings] = None
```

**Benefits:**
- Single config object
- Optional sections for mode-specific settings

**Costs:**
- Easy to misconfigure (fire_circle=None with mode=FIRE_CIRCLE)
- Less type-safe
- Validation complexity

#### Option C: Flat Config with Prefixes

```python
@dataclass
class EvaluationConfig:
    # Shared
    mode: EvaluationMode = EvaluationMode.SINGLE
    models: List[str] = ...

    # Fire Circle specific (ignored in other modes)
    fc_circle_size: CircleSize = CircleSize.SMALL
    fc_max_rounds: int = 3
    fc_empty_chair_model: Optional[str] = None
    fc_failure_mode: FailureMode = FailureMode.RESILIENT
    fc_pattern_threshold: float = 0.5
    fc_min_viable_circle: int = 2
```

**Benefits:**
- Simplest implementation
- Single config object

**Costs:**
- Namespace pollution
- Poor discoverability
- No type safety for mode-specific fields

### Recommendation: Option A (Mode-Specific Config)

**Rationale:**
- Type safety prevents misconfiguration
- Clear API: `FireCircleConfig` signals intent
- Extensible: future modes get their own config
- Professional library design pattern

**Migration strategy:**
1. Create `BaseEvaluationConfig` with shared fields
2. Keep `EvaluationConfig` for SINGLE/PARALLEL (backward compatible)
3. Add `FireCircleConfig` for Fire Circle
4. Update `LLMEvaluator` to accept union of configs
5. Tests validate config-mode alignment

---

## Constraint 3: File Organization

### Current Constraint

`evaluator.py` contains:
- `LLMEvaluator` class (296 lines)
- Stub `_evaluate_fire_circle()` method (~70 lines)
- Configuration classes
- Helper methods

### What Fire Circle Adds

Conservative estimate: **500-600 lines**
- `_evaluate_fire_circle()` implementation (200 lines)
- `DialogueRound`, `PatternObservation` dataclasses (50 lines)
- Pattern extraction logic (100 lines)
- Zombie model tracking (50 lines)
- Empty chair management (50 lines)
- Consensus derivation (50 lines)

**Total:** `evaluator.py` would grow from 296 → ~800 lines

### Problem

Single 800-line file violates:
- Single Responsibility Principle (evaluator + fire circle + consensus + patterns)
- Readability (hard to navigate)
- Testability (mocking becomes complex)

### Proposed Solutions

#### Option A: Extract Fire Circle Module (Recommended)

```
promptguard/evaluation/
├── evaluator.py          # LLMEvaluator, SINGLE, PARALLEL modes (300 lines)
├── fire_circle.py        # Fire Circle implementation (500 lines)
├── consensus.py          # Consensus algorithms (existing, 100 lines)
├── prompts.py            # Evaluation prompts (existing, 150 lines)
└── cache.py              # Caching layer (existing, 200 lines)
```

**fire_circle.py structure:**
```python
from dataclasses import dataclass
from typing import List, Dict
from .evaluator import NeutrosophicEvaluation, EvaluationConfig

@dataclass
class DialogueRound:
    """Single round of Fire Circle dialogue."""
    round_number: int
    evaluations: List[NeutrosophicEvaluation]
    active_models: List[str]
    empty_chair_model: str

@dataclass
class PatternObservation:
    """Observed reciprocity pattern."""
    pattern_type: str
    first_observed_by: str
    agreement_score: float
    round_discovered: int

@dataclass
class FireCircleResult:
    """Complete Fire Circle evaluation result."""
    evaluations: List[NeutrosophicEvaluation]
    consensus: NeutrosophicEvaluation
    dialogue_history: List[DialogueRound]
    patterns: List[PatternObservation]
    empty_chair_influence: float
    metadata: Dict[str, Any]

class FireCircleEvaluator:
    """Fire Circle evaluation implementation."""

    def __init__(self, config: FireCircleConfig, llm_caller):
        self.config = config
        self.llm_caller = llm_caller

    async def evaluate(
        self,
        layer_content: str,
        context: str,
        evaluation_prompt: str
    ) -> FireCircleResult:
        """Run complete Fire Circle evaluation."""
        # 3-round dialogue implementation
        pass

    def _execute_round(self, round_num: int, ...) -> DialogueRound:
        """Execute single dialogue round."""
        pass

    def _extract_patterns(self, dialogue_history: List[DialogueRound]) -> List[PatternObservation]:
        """Extract patterns from dialogue."""
        pass

    def _compute_consensus(self, dialogue_history: List[DialogueRound]) -> NeutrosophicEvaluation:
        """Compute max(F) consensus across all rounds."""
        pass

    def _measure_empty_chair_influence(self, patterns: List[PatternObservation]) -> float:
        """Measure empty chair's contribution."""
        pass
```

**Integration in evaluator.py:**
```python
from .fire_circle import FireCircleEvaluator, FireCircleConfig, FireCircleResult

class LLMEvaluator:
    def __init__(self, config: Union[EvaluationConfig, FireCircleConfig]):
        self.config = config
        # Initialize fire circle evaluator if needed
        if isinstance(config, FireCircleConfig):
            self.fire_circle = FireCircleEvaluator(config, self._call_llm)

    async def evaluate_layer(...) -> EvaluationResult:
        if isinstance(self.config, FireCircleConfig):
            fc_result = await self.fire_circle.evaluate(...)
            return EvaluationResult.from_fire_circle(fc_result)
        # ... existing logic ...
```

**Benefits:**
- Clear separation of concerns
- Each file focused on single responsibility
- Easy to test in isolation
- Fire Circle complexity doesn't pollute evaluator.py
- Can reuse `_call_llm()` via dependency injection

**Costs:**
- More files to navigate
- Need careful interface design
- Import complexity

#### Option B: Keep Everything in evaluator.py

Just implement Fire Circle methods in the existing file.

**Benefits:**
- No reorganization needed
- All evaluation logic in one place

**Costs:**
- 800-line file
- Hard to navigate
- Mixed concerns
- Difficult to test in isolation

#### Option C: Extract All Modes

```
promptguard/evaluation/
├── evaluator.py          # Coordinator only (100 lines)
├── single.py             # SINGLE mode (100 lines)
├── parallel.py           # PARALLEL mode (150 lines)
├── fire_circle.py        # FIRE_CIRCLE mode (500 lines)
└── ...
```

**Benefits:**
- Perfect separation
- Each mode independently testable

**Costs:**
- Over-engineered for current needs
- More boilerplate
- Coordination complexity

### Recommendation: Option A (Extract Fire Circle Module)

**Rationale:**
- SINGLE/PARALLEL are simple (~50 lines each), keep together
- Fire Circle is complex (500 lines), extract
- Principle: Extract when >200 lines or distinct responsibility
- Preserves `LLMEvaluator` as entry point/coordinator
- Easy to extract more later if needed

**Implementation order:**
1. Create `fire_circle.py` with dataclasses and interface
2. Implement `FireCircleEvaluator` class
3. Update `LLMEvaluator` to delegate Fire Circle mode
4. Move tests to `test_fire_circle.py` (already exists!)
5. Update imports in `promptguard/__init__.py`

---

## Summary of Recommendations

| Constraint | Recommended Solution | Priority |
|------------|---------------------|----------|
| Return Type | Rich `EvaluationResult` object with metadata | HIGH |
| Configuration | Mode-specific config classes (`FireCircleConfig`) | HIGH |
| File Organization | Extract `fire_circle.py` module | MEDIUM |

### Implementation Sequence

1. **Phase 1: Data Structures** (No breaking changes)
   - Create `fire_circle.py` with dataclasses
   - Define `FireCircleConfig`, `DialogueRound`, `PatternObservation`
   - Create `EvaluationResult` wrapper

2. **Phase 2: Fire Circle Core**
   - Implement `FireCircleEvaluator` class
   - 3-round dialogue logic
   - Pattern extraction
   - Consensus computation

3. **Phase 3: Integration**
   - Update `LLMEvaluator.evaluate_layer()` to return `EvaluationResult`
   - Add Fire Circle delegation
   - Migrate existing callers

4. **Phase 4: Testing**
   - Run 72-test suite
   - Integration tests with existing code
   - Validation on attack dataset

### Open Questions for Implementor

1. **Session Memory Integration:** How does Fire Circle interact with session memory? Does turn context flow through dialogue rounds?

2. **Caching Strategy:** Should we cache:
   - Individual round evaluations?
   - Pattern extractions?
   - Final consensus?

3. **Error Recovery:** When a model fails mid-dialogue:
   - Exclude from remaining rounds only?
   - Re-run entire evaluation?
   - Different behavior for STRICT vs RESILIENT?

4. **Prompt Template Location:** Should Fire Circle prompts live in `prompts.py` or `fire_circle.py`?

---

## Next Steps

1. ✅ Document architectural constraints (this document)
2. ⏳ Review specification findings (1 HIGH, 4 MEDIUM issues)
3. ⏳ Reconcile architectural decisions with specification
4. ⏳ Update implementation handoff with architectural guidance
5. ⏳ Begin Phase 1 implementation

**Estimated effort:** 1-2 days for architectural changes, 6-8 days for Fire Circle implementation
