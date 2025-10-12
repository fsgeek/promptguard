# PromptGuard ArangoDB Schema

**Database:** PromptGuard
**Date:** 2025-10-11
**Purpose:** Store model metadata, attack prompts, and evaluation results for research analysis

## Collections

### 1. models (Document Collection)

Stores metadata about LLM models used in experiments.

**Document Structure:**
```json
{
  "_key": "anthropic/claude-sonnet-4.5",
  "name": "Claude Sonnet 4.5",
  "organization": "anthropic",
  "model_type": "frontier_aligned",
  "release_date": "2024-10-22",
  "cost_per_1m_input": 3.0,
  "cost_per_1m_output": 15.0,
  "context_window": 200000,
  "model_description": "Anthropic's current frontier model...",
  "training_characteristics": ["RLHF", "Constitutional AI"],
  "known_capabilities": ["Strong instruction following", "Long context"],
  "observer_framing_compatible": "confirmed_yes|confirmed_no|likely_yes|likely_no|unknown",
  "known_limitations": ["RTLO text processing failure"],
  "deployment_notes": "Good observer framing candidate...",
  "deprecated": false,
  "metadata": {
    "added_date": "2025-10-11T00:00:00Z",
    "last_tested": "2025-10-11T00:00:00Z"
  }
}
```

**Indexes:**
- `organization` (persistent hash index)
- `model_type` (persistent hash index)
- `observer_framing_compatible` (persistent hash index)
- `deprecated` (persistent hash index)

**Queries Enabled:**
- "Show me all frontier_aligned models"
- "Which models are confirmed compatible with observer framing?"
- "List all models from OpenAI"

---

### 2. attacks (Document Collection)

Stores attack prompts from various datasets.

**Document Structure:**
```json
{
  "_key": "external_001",
  "prompt_text": "What is the result of eval(\"1+1\")",
  "encoding_technique": "mathematical_bold_unicode",
  "ground_truth": "extractive|manipulative|reciprocal",
  "dataset_source": "encoding_attacks_external|benign_malicious|or_bench|history_injection",
  "attack_metadata": {
    "technique_category": "encoding_obfuscation|prompt_injection|history_fabrication",
    "severity": "low|medium|high|critical",
    "description": "Optional description of attack mechanism"
  },
  "metadata": {
    "added_date": "2025-10-11T00:00:00Z",
    "dataset_file": "datasets/encoding_attacks_external_n72.jsonl"
  }
}
```

**Indexes:**
- `encoding_technique` (persistent hash index)
- `ground_truth` (persistent hash index)
- `dataset_source` (persistent hash index)
- `attack_metadata.technique_category` (persistent hash index)

**Queries Enabled:**
- "Show all RTLO attacks"
- "List extractive prompts from encoding dataset"
- "Which attacks are from the benign_malicious dataset?"

---

### 3. evaluations (Edge Collection)

Stores evaluation results connecting models to attacks. Using edge collection enables graph queries.

**Edge Structure:**
```json
{
  "_key": "auto-generated",
  "_from": "models/anthropic/claude-sonnet-4.5",
  "_to": "attacks/external_001",
  "condition": "direct|observer",
  "evaluation_result": {
    "success": true,
    "detected": false,
    "T": 0.8,
    "I": 0.2,
    "F": 0.6,
    "reasoning": "The user's intent is mostly clear...",
    "exchange_type": "extractive|manipulative|reciprocal"
  },
  "response_text": "Full model response...",
  "error": null,
  "cost_usd": 0.0017275,
  "timestamp": "2025-10-11T12:34:56Z",
  "experiment_metadata": {
    "experiment_id": "baseline_comparison_parseable",
    "run_id": "20251011_123456",
    "condition_description": "Baseline comparison with observer framing"
  }
}
```

**Indexes:**
- `condition` (persistent hash index)
- `evaluation_result.detected` (persistent hash index)
- `evaluation_result.success` (persistent hash index)
- `timestamp` (persistent skiplist index)
- `experiment_metadata.experiment_id` (persistent hash index)

**Graph Queries Enabled:**
```aql
// Find all attacks that GPT-4.5 failed to detect
FOR v, e IN 1..1 OUTBOUND 'models/openai/gpt-4.5' evaluations
  FILTER e.condition == 'observer' AND e.evaluation_result.detected == false
  RETURN {attack: v, evaluation: e}

// Find all models that detected a specific attack
FOR v, e IN 1..1 INBOUND 'attacks/external_001' evaluations
  FILTER e.condition == 'observer' AND e.evaluation_result.detected == true
  RETURN {model: v, evaluation: e}

// Compare detection rates across models for encoding attacks
FOR attack IN attacks
  FILTER attack.dataset_source == 'encoding_attacks_external'
  FOR model, eval IN 1..1 INBOUND attack evaluations
    FILTER eval.condition == 'observer'
    COLLECT model_id = model._key INTO detections = eval.evaluation_result.detected
    RETURN {
      model: model_id,
      total: LENGTH(detections),
      detected: LENGTH(detections[* FILTER CURRENT == true])
    }
```

---

## Data Import Strategy

### Phase 1: Import Existing Data

1. **Models:**
   - Parse `config/openrouter_frontier_models.json`
   - Import curated models from `config/model_registry_template.json`
   - Merge with experiment-discovered metadata

2. **Attacks:**
   - `datasets/encoding_attacks_external_n72.jsonl`
   - `datasets/benign_malicious.json`
   - `datasets/or_bench_sample.json`
   - `datasets/extractive_prompts_dataset.json`
   - `datasets/history_injection_attacks.json`

3. **Evaluations:**
   - `baseline_comparison_parseable_results.json`
   - Scout mission results (cross-model, encoding validation, history attacks)
   - Fire Circle manual test results

### Phase 2: Future Experiments Write Directly to DB

All future evaluation scripts will insert directly into ArangoDB instead of writing JSON files.

---

## Query Performance Optimization

**Persistent Indexes:**
- Hash indexes for equality lookups (organization, technique, detected)
- Skiplist indexes for range queries (timestamp, cost)
- Fulltext index on prompt_text for semantic search (optional)

**ArangoDB Features:**
- Graph traversal for model-attack relationships
- AQL joins for complex analytics
- Aggregation for detection rate calculations

---

## Example Queries

### Research Questions

**Q: Which models have the highest detection rate on encoding attacks?**
```aql
FOR attack IN attacks
  FILTER attack.attack_metadata.technique_category == 'encoding_obfuscation'
  FOR model, eval IN 1..1 INBOUND attack evaluations
    FILTER eval.condition == 'observer' AND eval.evaluation_result.success == true
    COLLECT model_id = model._key INTO results = eval.evaluation_result.detected
    RETURN {
      model: model_id,
      detection_rate: LENGTH(results[* FILTER CURRENT == true]) / LENGTH(results)
    }
```

**Q: What's the cost breakdown by model for baseline experiment?**
```aql
FOR eval IN evaluations
  FILTER eval.experiment_metadata.experiment_id == 'baseline_comparison_parseable'
  COLLECT model_id = PARSE_IDENTIFIER(eval._from).key INTO costs = eval.cost_usd
  RETURN {
    model: model_id,
    total_cost: SUM(costs),
    evaluations: LENGTH(costs)
  }
```

**Q: Which encoding techniques have the lowest detection rate?**
```aql
FOR attack IN attacks
  FILTER attack.dataset_source == 'encoding_attacks_external'
  FOR model, eval IN 1..1 INBOUND attack evaluations
    FILTER eval.condition == 'observer' AND eval.evaluation_result.success == true
    COLLECT technique = attack.encoding_technique INTO detections = eval.evaluation_result.detected
    RETURN {
      technique: technique,
      detection_rate: LENGTH(detections[* FILTER CURRENT == true]) / LENGTH(detections)
    }
```

---

## Schema Evolution

ArangoDB allows adding fields without migration. As experiments evolve:

- Add new fields to existing documents
- Add new indexes as query patterns emerge
- Extend metadata structures
- No downtime for schema changes
