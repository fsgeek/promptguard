# Fire Circle Current Behavior Specification

**Document Version:** 1.0
**Last Updated:** 2025-10-24
**Purpose:** Descriptive documentation of actual Fire Circle implementation behavior (NOT prescriptive)

This specification documents what the code DOES, not what it SHOULD do. All claims are referenced to specific line numbers in `promptguard/evaluation/fire_circle.py`.

---

## 1. Configuration

### 1.1 Configurable Parameters

**FireCircleConfig** (lines 334-379) extends **BaseEvaluationConfig** (lines 323-330) with the following parameters:

| Parameter | Type | Default | Description | Line |
|-----------|------|---------|-------------|------|
| `api_key` | Optional[str] | None | OpenRouter API key (loaded from env if None) | 325 |
| `models` | List[str] | [] | Model IDs for Fire Circle | 326 |
| `max_tokens` | int | 1000 | Maximum tokens per LLM call | 327 |
| `timeout_seconds` | float | 30.0 | API timeout | 328 |
| `temperature` | float | 0.7 | LLM temperature | 329 |
| `provider` | str | "openrouter" | Provider ("openrouter" only supported) | 330 |
| `circle_size` | CircleSize | SMALL | Size constraint (SMALL/MEDIUM/LARGE) | 336 |
| `max_rounds` | int | 3 | Number of deliberation rounds | 337 |
| `empty_chair_model` | Optional[str] | None | Specific model for empty chair (None = auto-rotate) | 338 |
| `failure_mode` | FailureMode | RESILIENT | STRICT or RESILIENT | 339 |
| `pattern_threshold` | float | 0.5 | Minimum agreement score for pattern inclusion | 340 |
| `min_viable_circle` | int | 2 | Minimum active models to continue | 341 |
| `enable_storage` | bool | False | Enable ArangoDB persistence | 344 |
| `storage_backend` | Optional[Any] | None | DeliberationStorage implementation | 345 |

### 1.2 Circle Size Constraints

**CircleSize enum** (lines 45-49) defines model count constraints:

```python
SMALL = (2, 3)   # min=2, max=3 models
MEDIUM = (4, 6)  # min=4, max=6 models
LARGE = (7, 10)  # min=7, max=10 models
```

Configuration validation (lines 361-366) enforces: `min_size <= len(models) <= max_size`

### 1.3 Validation Rules

**__post_init__** (lines 347-378) validates:

1. **API key requirement** (lines 352-358): Loads from `OPENROUTER_API_KEY` env var if not provided, raises `ValueError` if missing
2. **Circle size match** (lines 361-366): Model count must fit circle size constraints
3. **Min viable circle** (lines 369-370): Must be >= 2
4. **Pattern threshold** (lines 373-374): Must be 0.0-1.0
5. **Max rounds** (lines 377-378): Must be >= 1

**Default configuration:**
- 3 rounds (line 337)
- RESILIENT failure mode (line 339)
- 0.5 pattern threshold (line 340)
- 2 minimum viable models (line 341)

---

## 2. Model Selection & Rotation

### 2.1 Initial Selection

Models are selected from `config.models` list (line 642). All models are initially **active** (participate in Round 1).

### 2.2 Empty Chair Mechanism

**What it is:** One model per round is assigned the "empty chair" role - speaking for absent stakeholders (future users, affected communities, maintainers).

**Rotation algorithm** `rotate_empty_chair()` (lines 433-470):

```python
# Round 1: No empty chair (independent baseline)
if round_number == 1:
    return None

# Round 2+: Rotate using modulo
index = (round_number - 1) % len(models)
return models[index]
```

**Example with 3 models [A, B, C]:**
- Round 1: None (all models provide independent assessment)
- Round 2: models[(2-1) % 3] = models[1] = B
- Round 3: models[(3-1) % 3] = models[2] = C

**Assignment tracking:** Empty chair assignments stored in `empty_chair_assignments` dict (line 644), mapping `round_number → model_id`.

**Prompt modification:** Empty chair model receives special instructions (lines 1239-1247, 1320-1328) asking them to consider:
- Future users inheriting pattern consequences
- Communities affected if extraction succeeds
- System maintainers bearing long-term costs

### 2.3 Model State Transitions

Models can be in three states:

1. **Active:** Participates and contributes to consensus (initial state)
2. **Zombie:** Failed mid-deliberation, history preserved but excluded from voting (Round 2+ failures)
3. **Excluded:** Failed in Round 1, removed from all rounds

**Round 1 failure** (lines 1056-1067):
```python
if round_num == 1:
    # Round 1 failure: exclude from all subsequent rounds
    active_models.remove(model)
```

**Round 2+ failure** (lines 1069-1079):
```python
else:
    # Round 2+ failure: becomes zombie (preserve history, no voting)
    logger.warning(f"Model {model} became zombie")
```

**Active model tracking:** `active_models` list is mutated during execution (line 642), removing failed models.

---

## 3. Deliberation Flow

### 3.1 Round Structure

Fire Circle conducts **exactly 3 rounds** (line 337 default, configurable via `max_rounds`).

**Round loop** (lines 652-759):
```python
for round_num in range(1, self.config.max_rounds + 1):
    # Determine empty chair
    # Execute round
    # Append to dialogue_history
    # Handle failures based on failure_mode
```

### 3.2 Per-Round Execution

**_execute_round()** (lines 900-1115) performs:

1. **Initialize state** (lines 929-931): Empty evaluations list, failed models tracker, round timestamp
2. **For each active model** (lines 933-1080):
   - Check empty chair role (line 938)
   - Build round-specific prompt (lines 939-946)
   - Try structured output if available (lines 965-982)
   - Fallback to standard LLM call (lines 985-989)
   - Parse response (line 988)
   - Track latency (lines 992-996)
   - Handle failures based on failure mode (lines 1025-1080)
3. **Calculate convergence metric** (lines 1081-1088): Standard deviation of F-scores
4. **Create round record** (lines 1091-1099)
5. **Check quorum** (lines 1102-1113): Warn if at minimum viable count

### 3.3 Context Provided Per Round

**Round 1** (lines 1164-1205):
- Base evaluation prompt using `ayni_relational()` observer framing (line 1174)
- Turn context from session memory if available (lines 1177-1179)
- Full prompt context (line 1187)
- Layer to evaluate (line 1191)
- JSON format instructions (lines 1193-1202)

**Round 2** (lines 1207-1277):
- Observer framing preamble (lines 1221-1227)
- Full prompt context + layer content (lines 1230-1236)
- Empty chair special instructions if applicable (lines 1239-1247)
- **Dialogue context from Round 1** (lines 1249-1252): Shows all Round 1 evaluations with T/I/F values and reasoning
- Pattern-seeking guidance (lines 1254-1265): Temporal consistency, cross-layer coordination, extraction masking, narrative plausibility
- JSON format with `patterns_observed` field (lines 1267-1276)

**Round 3** (lines 1280-1346):
- Observer framing preamble (lines 1295-1301)
- Full prompt context + layer content (lines 1304-1308)
- **Dialogue context from Round 1** (lines 1312-1313)
- **Dialogue context from Round 2** (lines 1315-1316)
- Empty chair special instructions if applicable (lines 1320-1328)
- Synthesis guidance (lines 1330-1335): Which patterns confirmed? Temporal/cross-layer analysis? Multi-generational perspective?
- JSON format with `consensus_patterns` field (lines 1338-1345)

### 3.4 Dialogue History Accumulation

**DialogueRound** dataclass (lines 82-99) stores per-round state:
```python
@dataclass
class DialogueRound:
    round_number: int
    evaluations: List[Any]  # NeutrosophicEvaluation objects
    active_models: List[str]
    empty_chair_model: Optional[str]
    prompt_used: str  # Full prompt sent to models
    convergence_metric: float  # stddev(F)
    timestamp: float  # Unix timestamp
    duration_seconds: float  # Round execution time
```

**Accumulation:** Each round appends to `dialogue_history` list (line 687).

**Context formatting** `_format_dialogue_context()` (lines 1380-1413):
- Shows model ID, T/I/F values, reasoning for each evaluation
- Includes `patterns_observed` if present (Round 2+)
- Blank line between rounds

### 3.5 Token Budget

**Per-call token limit:** 1000 tokens (line 327, configurable via `max_tokens`)

**CRITICAL BUG:** The 1000 token limit is PER LLM CALL, not per round. There is no aggregate token budget tracking across rounds. This means:
- Round 1: 3 models × 1000 tokens = 3000 tokens max
- Round 2: 3 models × 1000 tokens = 3000 tokens max (PLUS dialogue context)
- Round 3: 3 models × 1000 tokens = 3000 tokens max (PLUS Round 1 + Round 2 context)

**Dialogue context growth:** Round 2 includes Round 1 dialogue (lines 1146, 1249-1252), Round 3 includes Round 1 + Round 2 dialogue (lines 1154-1156, 1312-1316). No truncation logic exists.

**Token exhaustion risk:** As dialogue history grows, models may:
1. Fail to parse full context (no error - just truncated)
2. Exceed 1000 token response limit (line 1615: `max_tokens=self.config.max_tokens`)
3. Produce truncated JSON (parsing failure)

---

## 4. Response Handling

### 4.1 Parsing Strategy

**Two-path parsing** (lines 961-989):

**Path A: Structured Output** (lines 965-982, implemented in `_try_structured_output()` lines 1581-1636):
- Requires `instructor` library (lines 32-38)
- Only if model supports structured output (line 965, checked via `_supports_structured_output()` lines 1568-1579)
- Uses Pydantic `FireCircleEvaluation` schema (lines 1603-1616)
- Falls back to Path B on any exception (lines 971-982)

**Path B: Fallback Parsing** (lines 985-989, implemented in `_parse_response()` lines 1638-1815):
- Standard LLM call via `llm_caller` (line 987)
- Regex-based JSON extraction (lines 1668-1718)
- Text extraction fallback in RESILIENT mode (lines 1779-1799)

### 4.2 JSON Extraction Logic

**_parse_response()** handles multiple formats (lines 1668-1718):

1. **Strip markdown code fences** (lines 1672-1693):
   - ````json ... ```` → extract content between fences (lines 1676-1680)
   - ````python ... ```` → extract content (lines 1681-1684)
   - ```` ``` ... ``` ```` → extract content (lines 1685-1693)
   - Handles text BEFORE fences (e.g., "Here's the JSON:\n```json")

2. **Fix Gemini double-brace bug** (lines 1699-1703):
   - `{{ ... }}` → `{ ... }` (removes extra outer braces)

3. **Extract JSON object only** (lines 1706-1717):
   - Finds matching closing brace for opening brace
   - Truncates extra text after JSON

4. **Parse with lenient mode** (line 1719): `json.loads(json_str, strict=False)`

5. **Validate required fields** (lines 1722-1725): `truth`, `indeterminacy`, `falsehood`, `reasoning`

6. **Create NeutrosophicEvaluation** (lines 1728-1736)

7. **Attach pattern fields** (lines 1739-1742): `patterns_observed`, `consensus_patterns`

### 4.3 Accepted Formats

**Markdown-wrapped:**
```json
Here's my evaluation:
```json
{
    "truth": 0.7,
    "indeterminacy": 0.2,
    "falsehood": 0.3,
    "reasoning": "..."
}
```
```

**Plain JSON:**
```json
{
    "truth": 0.7,
    "indeterminacy": 0.2,
    "falsehood": 0.3,
    "reasoning": "..."
}
```

**Gemini format (with extra braces):**
```json
{{
    "truth": 0.7,
    "indeterminacy": 0.2,
    "falsehood": 0.3,
    "reasoning": "..."
}}
```

**Partial JSON with trailing text:**
```json
{
    "truth": 0.7,
    "indeterminacy": 0.2,
    "falsehood": 0.3,
    "reasoning": "..."
} <- this is valid JSON
```

### 4.4 Parsing Failure Handling

**STRICT mode** (lines 1762-1766):
- Raise `RuntimeError` immediately with response sample
- Propagates to `_execute_round()` which raises to caller

**RESILIENT mode** (lines 1768-1815):
- Attempt text extraction via `_extract_tif_from_text()` (lines 1780, 1817-1848)
- Looks for patterns: `truth: 0.7`, `indeterminacy: 0.2`, `falsehood: 0.6`
- If extraction succeeds, use full response as reasoning (line 1796)
- If extraction fails, raise `RuntimeError` (lines 1812-1815)

### 4.5 Retry Logic

**NO RETRY LOGIC EXISTS** for individual LLM calls. If an API call fails (timeout, network error, unparseable response), it is handled based on failure mode but never retried.

---

## 5. Failure Modes

### 5.1 Zombie Model Definition

**Zombie:** Model that succeeded in Round 1 but failed in Round 2 or 3 (lines 1069-1079).

**Characteristics:**
- Contributes to Round 1 baseline (evaluation preserved)
- Does NOT participate in consensus calculation (excluded from active_models)
- History preserved for observability
- Logged as state transition: "active → zombie" (line 1077)

**Contrast with excluded model:** Round 1 failures are removed from `active_models` immediately (line 1058) and never appear in subsequent rounds.

### 5.2 RESILIENT vs STRICT Mode

**RESILIENT** (default, line 339):
- Continue with remaining models after failures
- Attempt text extraction fallback on unparseable responses (lines 1768-1799)
- Mark Round 1 failures as excluded (line 1058)
- Mark Round 2+ failures as zombies (line 1074)
- Only abort if below minimum viable circle (lines 731-745)

**STRICT** (opt-in):
- Fail immediately on any model error (line 1053)
- Fail immediately on unparseable response (lines 1762-1766)
- Raise `RuntimeError` to caller (line 725)

### 5.3 Failure Tolerance

**Round-level tolerance:**
- Each round can lose models and continue
- Minimum viable circle checked after each failure (lines 731-745)
- Quorum warning at minimum viable count (lines 1102-1113)

**Deliberation-level tolerance:**
- If active models drops below `min_viable_circle` (default: 2), deliberation aborts (lines 731-745)
- Raises `RuntimeError` with quorum failure message (lines 742-745)

**Example:** With 3 models, min_viable=2:
- Lose 1 model: Continue with 2 (warning logged)
- Lose 2 models: Abort (quorum failure)

### 5.4 Failure Context Capture

**Logging metadata** (lines 1029-1051):
```python
logger.error(
    f"Model {model} failed in round {round_num}",
    extra={
        "fire_circle_id": self.fire_circle_id,
        "event": "model_failure",
        "round": round_num,
        "model": model,
        "is_empty_chair": is_empty_chair,
        "failure_type": type(e).__name__,
        "error_message": str(e),
        "state_before": {
            "active_models": list(active_models),
            "evaluations_completed": len(evaluations)
        }
    }
)
```

**Also printed to stderr** (lines 1047-1050): Raw exception with traceback for debugging.

**Stored in metadata** (line 796): `failed_models` list includes all failures.

### 5.5 Data Preserved on Failure

**Partial round data:** If some models succeed before quorum failure, their evaluations are in `dialogue_history` up to the failed round.

**Metadata tracking:**
- `failed_models`: List of failures (line 796)
- `empty_chair_assignments`: Preserved even if empty chair model failed (line 797)
- `final_active_models`: Shows who survived (line 798)

**No partial consensus:** If deliberation aborts, no consensus is calculated (line 771 only reached if all rounds complete).

---

## 6. Consensus Mechanism

### 6.1 Consensus Algorithm

**compute_max_f_consensus()** (lines 385-430) implements **worst-case detection**:

```python
# 1. Identify active models from FINAL round
active_models = set(dialogue_history[-1].active_models)

# 2. Collect ALL evaluations from active models across ALL rounds
all_evaluations = []
for round_data in dialogue_history:
    for evaluation in round_data.evaluations:
        if evaluation.model in active_models:
            all_evaluations.append(evaluation)

# 3. Return evaluation with MAXIMUM F-score
max_f_evaluation = max(all_evaluations, key=lambda e: e.falsehood)
return max_f_evaluation
```

**Rationale** (lines 394-395): "Preserves detection signal even if groupthink lowers F-scores in later rounds. Fire Circle is a detection system, not a democracy."

### 6.2 Aggregated Fields

**Consensus is NOT aggregated** - it is the single evaluation with highest F-score. This means:

- **T/I/F values:** From one model's one round (the max F evaluation)
- **Reasoning:** From that single evaluation
- **Model:** The model that produced max F evaluation
- **Round:** The round where max F occurred (implicit - not stored)

**No averaging, no voting, no median.** The most vigilant assessment wins.

### 6.3 Termination Conditions

Fire Circle **always runs all configured rounds** (default: 3, line 652). There is **no early termination** based on convergence.

**Convergence metric calculated** (lines 1081-1088) but only for observability:
```python
convergence_metric = stddev(F_scores)  # Standard deviation
```

Stored in `DialogueRound.convergence_metric` (line 1097) but NOT used for termination decision.

### 6.4 No Consensus Scenario

**Cannot occur** - if deliberation completes, consensus MUST be calculated (line 771). If quorum fails, deliberation aborts with `RuntimeError` before reaching consensus calculation (lines 742-745).

**Edge case:** If all active models have identical F-scores, `max()` returns the first one encountered (Python default).

---

## 7. Pattern Detection

### 7.1 Pattern Identification

Patterns are **self-reported by models** in Round 2 and Round 3 JSON responses:

- **Round 2:** `patterns_observed` field (lines 1271-1274)
- **Round 3:** `consensus_patterns` field (line 1344)

**No automatic pattern detection** - the system relies on models identifying patterns in their reasoning.

### 7.2 Pattern Extraction

**_extract_patterns()** (lines 1415-1492) aggregates patterns:

1. **Get active models from final round** (lines 1435-1440): Only patterns from models that survived count
2. **Process Round 2+ evaluations** (lines 1446-1473): Round 1 has no patterns
3. **Classify each pattern string** (line 1464): Maps string to pattern type via `_classify_pattern()`
4. **Track first observer** (line 1468): First model to mention this pattern type
5. **Count observing models** (line 1473): How many active models mentioned it
6. **Calculate agreement score** (line 1478): `observing_models / active_model_count`
7. **Filter by threshold** (line 1481): Only patterns with `agreement_score >= pattern_threshold` (default: 0.5)
8. **Sort by agreement** (line 1490): Highest agreement first

### 7.3 Pattern Taxonomy

**_classify_pattern()** (lines 1494-1534) uses keyword matching:

| Pattern Type | Keywords | Line |
|--------------|----------|------|
| `temporal_inconsistency` | "temporal", "turn", "earlier", "previous" | 1509-1510 |
| `cross_layer_fabrication` | "cross-layer", "system layer", "coordination" | 1511-1512 |
| `polite_extraction` | "polite", "extraction", "masking" | 1513-1514 |
| `educational_escalation` | "educational", "escalation" | 1515-1516 |
| `context_saturation` | "context saturation", "consuming" | 1517-1518 |
| `role_confusion` | "role", "confusion", "reversal" | 1519-1520 |
| `fabricated_progression` | "fabricated", "history", "progression" | 1521-1522 |
| `false_authority` | "authority", "false" | 1523-1524 |
| `future_consequence` | "future", "consequence" | 1525-1526 |
| `absent_community_impact` | "absent", "community", "affected" | 1527-1528 |
| `maintenance_burden` | "maintenance", "burden", "debt" | 1529-1530 |
| `system_debt` | "system", "debt" | 1531-1532 |
| `unclassified` | (anything else) | 1534 |

**Classification is case-insensitive** (line 1506).

### 7.4 Pattern Aggregation

**PatternObservation** dataclass (lines 102-114):
```python
@dataclass
class PatternObservation:
    pattern_type: str  # Classification from _classify_pattern()
    first_observed_by: str  # Model ID that first mentioned it
    agreement_score: float  # 0.0-1.0, fraction of active models agreeing
    round_discovered: int  # Which round identified this pattern
```

**Agreement calculation** (line 1478):
```python
agreement_score = len(observing_models) / active_model_count
```

**Example:** 3 active models, pattern mentioned by 2:
- Agreement score = 2/3 = 0.667
- If `pattern_threshold=0.5`, pattern is included
- If `pattern_threshold=0.7`, pattern is excluded

### 7.5 Empty Chair Pattern Attribution

**Empty chair models can be pattern discoverers** (lines 1468-1470). If empty chair model is first to mention a pattern, `first_observed_by` = empty chair model ID.

**Empty chair influence calculation** uses pattern attribution (lines 1536-1566): Counts unique patterns first observed by empty chair models.

---

## 8. Storage & Persistence

### 8.1 Storage Trigger

Storage occurs **automatically if enabled** (lines 843-896):

```python
if self.storage:
    try:
        self.storage.store_deliberation(...)
    except Exception as e:
        logger.error(...)
        # Don't fail evaluation if storage fails
```

**Critical behavior:** Storage failures are logged but do NOT fail the evaluation (line 896).

### 8.2 ArangoDB Schema

**Collections created** (`_ensure_collections()` in `arango_backend.py` lines 97-159):

1. **deliberations** (document): Session-level metadata
2. **turns** (document): Individual model evaluations per round
3. **participated_in** (edge): models → deliberations
4. **deliberation_about** (edge): deliberations → attacks

**Indexes created:**

**deliberations:**
- Hash: `fire_circle_id` (unique)
- Skiplist: `created_at`
- Hash: `metadata.attack_category`
- Hash: `metadata.quorum_valid`

**turns:**
- Hash: `fire_circle_id`
- Skiplist: `round_number`
- Hash: `model`
- Fulltext: `reasoning`
- Skiplist: `timestamp`

### 8.3 Stored Data

**Deliberation document** (`arango_backend.py` lines 251-278):
```python
{
    "_key": fire_circle_id,
    "fire_circle_id": str,
    "created_at": ISO timestamp,
    "total_duration": float,
    "convergence_trajectory": [mean_f_round1, mean_f_round2, mean_f_round3],
    "consensus": {
        "model": str,
        "truth": float,
        "indeterminacy": float,
        "falsehood": float,
        "reasoning": str
    },
    "empty_chair_influence": float,
    "metadata": {
        "attack_id": Optional[str],
        "attack_category": Optional[str],
        "quorum_valid": bool,
        "total_duration_seconds": float,
        "rounds_completed": int,
        "final_active_models": List[str],
        "patterns_count": int,
        "unique_pattern_types": int,
        "failed_models": List[str],
        "empty_chair_assignments": Dict[int, str]
    },
    "patterns": List[PatternObservation]
}
```

**Turn documents** (`arango_backend.py` lines 283-305):
```python
{
    "turn_id": f"{fire_circle_id}_r{round_number}_{model}",
    "fire_circle_id": str,
    "round_number": int,
    "model": str,
    "empty_chair": bool,
    "truth": float,
    "indeterminacy": float,
    "falsehood": float,
    "reasoning": str,
    "patterns_observed": Optional[List[str]],
    "consensus_patterns": Optional[List[str]],
    "timestamp": ISO timestamp
}
```

### 8.4 Dialogue History Storage

**Full dialogue history stored via turns collection** - each model evaluation from each round gets its own document.

**Retrieval:** `get_deliberation()` joins turns back into rounds (`arango_backend.py` lines 485-518):
```python
FOR d IN deliberations
    FILTER d.fire_circle_id == @fire_circle_id
    LET round_data = (
        FOR t IN turns
            FILTER t.fire_circle_id == @fire_circle_id
            SORT t.round_number, t.model
            RETURN t
    )
    RETURN MERGE(d, {rounds: round_data})
```

**No truncation** - complete reasoning preserved for all rounds.

### 8.5 Dissent Preservation

**Dissents stored implicitly** via individual turn documents. No special "dissent" collection.

**Dissent extraction** via `find_dissents()` query (`arango_backend.py` lines 434-483):
- Compares F-scores between models in same round
- Returns pairs with `f_delta >= min_f_delta` (default: 0.3)

**Dissent metadata available** via `FireCircleResult.extract_dissents()` (lines 189-224):
```python
{
    "round_number": int,
    "model_high": str,  # Model with higher F
    "model_low": str,   # Model with lower F
    "f_high": float,
    "f_low": float,
    "f_delta": float
}
```

---

## 9. Empty Chair Influence

### 9.1 Calculation Method

**_measure_empty_chair_influence()** (lines 1536-1566):

```python
# Count patterns first observed by empty chair models
empty_chair_contributions = sum(
    1 for p in patterns
    if p.first_observed_by in empty_chair_models
)

# Calculate ratio
return empty_chair_contributions / total_unique_patterns
```

**Metric meaning:** Fraction of unique pattern types first mentioned by empty chair models.

### 9.2 Interpretation

**0.0:** Empty chair models contributed no unique patterns
**0.5:** Half of pattern types first discovered by empty chair models
**1.0:** ALL pattern types first discovered by empty chair models (all other models only confirmed)

**Not measured:** Agreement propagation, influence on F-score changes, dialogue pivots. Only tracks pattern discovery.

### 9.3 Storage & Retrieval

**Stored in deliberation document** (`arango_backend.py` line 264):
```python
"empty_chair_influence": float
```

**Included in metadata queries** - all query functions return `empty_chair_influence` for filtering/analysis.

---

## 10. Integration Points

### 10.1 LLMEvaluator Integration

Fire Circle is integrated via **FireCircleEvaluator** instance (lines 21-27 import).

**LLMEvaluator** (`evaluator.py`) instantiates Fire Circle when `mode=FIRE_CIRCLE`:
```python
if config.mode == EvaluationMode.FIRE_CIRCLE:
    fc_config = FireCircleConfig(...)
    self.fire_circle = FireCircleEvaluator(fc_config, self._call_llm)
```

**Shared LLM caller:** Fire Circle uses same `_call_llm()` method as SINGLE/PARALLEL modes (line 573).

### 10.2 API Surface

**Primary method:** `evaluate()` (lines 601-898)

```python
async def evaluate(
    self,
    layer_content: str,      # Layer to evaluate
    context: str,            # Full prompt context
    evaluation_prompt: str,  # NOT USED (ignored)
    session_memory: Optional[Any] = None  # Optional temporal context
) -> FireCircleResult
```

**Returns:** `FireCircleResult` (lines 118-316) containing:
- `evaluations`: All evaluations across all rounds
- `consensus`: Single evaluation with max(F)
- `dialogue_history`: List of DialogueRound objects
- `patterns`: List of PatternObservation objects
- `empty_chair_influence`: Float 0.0-1.0
- `metadata`: Dict with comprehensive tracking

### 10.3 Data Structures

**Inputs:**
- `layer_content`: String (the prompt layer being evaluated)
- `context`: String (full multi-layer prompt for context)
- `evaluation_prompt`: String (IGNORED - Fire Circle uses hardcoded prompts)
- `session_memory`: Object with `turn_count`, `balance_history`, `trust_trajectory` (optional)

**Outputs:**
- `FireCircleResult`: Dataclass with consensus, patterns, metadata
- `NeutrosophicEvaluation`: Dataclass with T/I/F values, reasoning, model
- `DialogueRound`: Dataclass with round state
- `PatternObservation`: Dataclass with pattern metadata

### 10.4 Caching Interaction

**Fire Circle does NOT use caching directly.** It calls `llm_caller` (line 987) which is injected from LLMEvaluator.

**LLMEvaluator** implements caching (lines 19-20 import), but Fire Circle:
- Has unique prompts per round (dialogue context varies)
- Has unique empty chair roles per model
- Likely has very low cache hit rate in practice

**No cache warming** for Fire Circle prompts.

---

## 11. Known Bugs & Quirks

### 11.1 Token Limit Issue

**Bug:** 1000 token limit is per-call, not per-round aggregate (line 327, 1615).

**Impact:**
- Long dialogue contexts in Round 3 may approach limit
- No warning or truncation logic
- Models silently truncate if context exceeds their limit
- Truncated responses likely fail parsing

**Evidence:** No token budget tracking in `_execute_round()` or `_build_round_prompt()`.

### 11.2 Prompt Storage Truncation

**Bug:** Prompt stored in DialogueRound is truncated to 200 chars (line 311):
```python
"prompt_sent": round_data.prompt_used[:200] if round_data.prompt_used else ""
```

**Impact:**
- Cannot reproduce exact evaluation from stored data
- Truncation occurs during storage, not during execution
- Full prompt available in memory during deliberation

**Location:** `arango_backend.py` line 311 (storage layer, not Fire Circle core).

### 11.3 KeyError Template Formatting

**Potential bug:** Round prompts use f-string interpolation with `dialogue_context` (lines 1146, 1149-1150, 1154-1158) but no KeyError handling.

**Risk:** If `_format_dialogue_context()` returns malformed string with unescaped braces, f-string formatting could fail.

**Mitigation:** `_format_dialogue_context()` uses `.format()` internally (lines 1401-1405), not f-strings, reducing risk.

### 11.4 Empty Chair Rotation Off-By-One

**Quirk (NOT A BUG):** Empty chair rotation formula (line 469):
```python
index = (round_number - 1) % len(models)
```

**Effect:** Round 2 assigns models[1] (second model), not models[0] (first model).

**Is this intentional?** Unclear. Pattern:
- Round 1: None
- Round 2: models[1]
- Round 3: models[2]
- Round 4: models[0]

**Alternative formula** `index = (round_number - 2) % len(models)` would start at models[0] in Round 2.

**Current behavior is DOCUMENTED but UNEXPLAINED** (no comment explaining why second model goes first).

### 11.5 Consensus Model Attribution

**Quirk:** Consensus includes `model` field (line 172) showing which model produced max F evaluation.

**Issue:** This is the model that produced the FINAL consensus, but it's not always clear which ROUND that evaluation came from.

**Workaround:** Consensus is deterministic - you can search `dialogue_history` for matching evaluation to find round.

### 11.6 Pattern Threshold Edge Case

**Bug:** If `pattern_threshold=1.0` (require unanimous agreement), patterns are excluded if ANY active model didn't mention them (line 1481).

**Issue:** Models may not mention a pattern because:
1. They disagree (legitimate exclusion)
2. They forgot to include it in JSON (implementation detail)
3. Their response was unparseable (failure, not disagreement)

**No distinction made** between genuine disagreement and technical failure to report.

### 11.7 Zombie Model Consensus Exclusion

**Design decision (not a bug):** Zombie models are excluded from consensus even though their Round 1 evaluation is preserved (line 411).

**Rationale:** "Only include evaluations from models that remained active" (line 421).

**Effect:** Model that provides highest-F Round 1 evaluation but fails in Round 2 will NOT contribute to consensus.

**Trade-off:** Ensures consensus comes from models that saw full dialogue vs. preserving strongest signal.

### 11.8 Storage Failure Silencing

**Design decision (not a bug):** Storage failures are logged but do not fail evaluation (line 896).

**Rationale:** Evaluation results are still valid even if persistence fails.

**Risk:** Silent data loss if storage fails consistently. No retry, no notification to caller.

### 11.9 Model Latency Tracking Incomplete

**Quirk:** `model_latencies` dict tracks per-round latencies (lines 649, 992-996) but does NOT include:
- Failed attempts
- Structured output attempt time (separate from fallback time)
- Network time vs. model time

**Stored as:** `{"model_id": [{"round": 1, "latency_ms": 450}, ...]}`

**Missing:** Total deliberation latency per model, percentiles, network overhead.

---

## 12. OpenRouter Integration

### 12.1 HTTP Headers

**Headers are NOT set in Fire Circle code.** Fire Circle delegates to `llm_caller` (line 987), which is `LLMEvaluator._call_llm()`.

**Expected headers (from LLMEvaluator):**
- `Authorization: Bearer {api_key}`
- `HTTP-Referer` (for OpenRouter ranking)
- `X-Title` (for OpenRouter ranking)

**Fire Circle does NOT verify headers** - assumes `llm_caller` handles this correctly.

### 12.2 API Call Pattern

**Standard OpenRouter chat completion:**
```python
POST https://openrouter.ai/api/v1/chat/completions
{
    "model": "anthropic/claude-sonnet-4.5",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 1000,
    "temperature": 0.7
}
```

**Structured output variation** (lines 1608-1616):
```python
{
    "model": "openai/gpt-4o",
    "messages": [...],
    "response_model": FireCircleEvaluation,  # Instructor extension
    "max_tokens": 1000,
    "temperature": 0.7,
    "extra_body": {"provider": {"require_parameters": True}}
}
```

### 12.3 Retry Logic

**NO RETRY LOGIC** in Fire Circle or structured output path.

**Fire Circle behavior on API failure:**
- STRICT mode: Raise exception immediately (line 1053)
- RESILIENT mode: Mark model as zombie/excluded, continue (lines 1056-1079)

**Expected:** `llm_caller` might have retry logic (not verified).

### 12.4 Cost Tracking

**No cost tracking in Fire Circle code.** Fire Circle logs:
- Model used (line 1019)
- Latency (line 1020)
- Round number (line 1018)

**Cost calculation requires:**
- Counting tokens in prompts (not done)
- Counting tokens in responses (not done)
- Looking up model pricing (external)

**Metadata includes** `total_duration_seconds` (line 805) but not estimated cost.

---

## Summary of Critical Behaviors

1. **Always runs 3 rounds** (no early termination)
2. **Consensus = max(F)** across all rounds from active models (not averaging)
3. **Empty chair rotates** starting with models[1] in Round 2
4. **Zombie models** excluded from consensus but history preserved
5. **1000 token limit PER CALL** with no aggregate budget tracking
6. **No retry logic** for API failures
7. **Storage failures logged** but don't fail evaluation
8. **Pattern detection is self-reported** by models, not automatic
9. **Dialogue context grows unbounded** across rounds
10. **Observer framing used** in all rounds (Instance 17 breakthrough)

---

## Code References

- Fire Circle implementation: `promptguard/evaluation/fire_circle.py` (lines 1-1917)
- ArangoDB backend: `promptguard/storage/arango_backend.py` (lines 1-653)
- Evaluation schemas: `promptguard/evaluation/schemas.py` (lines 1-121)
- Observer framing prompt: `promptguard/evaluation/prompts.py` (lines 19-36)

---

**Document Status:** Complete behavioral specification based on code as of 2025-10-24.

**Next Step:** Prescriptive specification defining what Fire Circle SHOULD do (design intent, rationale, error handling improvements).
