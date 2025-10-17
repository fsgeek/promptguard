# PromptGuard Testing Infrastructure Specification
Version: 1.0.0
Status: Draft

## 1. Overview

### 1.1 Purpose
Define a robust, reproducible testing infrastructure for PromptGuard evaluation across multiple LLM models.

### 1.2 Goals
- Complete data capture without truncation
- Parallel execution capability
- Resumable/restartable test runs
- Full audit trail of all operations
- Configuration-driven test execution

## 2. Architecture

### 2.1 Data Storage
- Primary storage: ArangoDB
- Collections required:
  - `prompts`: Source prompts with metadata
  - `evaluations`: Model evaluation results
  - `test_runs`: Test execution metadata
  - `model_configs`: Model configuration snapshots

### 2.2 Execution Model
- Parallel execution with configurable worker count
- Each worker handles one model/prompt combination
- Real-time result persistence (not batch at end)
- Automatic retry on transient failures

## 3. Data Requirements

### 3.1 Prompt Storage
```json
{
  "prompt_id": "string (unique)",
  "content": "string (complete, no truncation)",
  "category": "string",
  "expected_label": "string",
  "source": "string",
  "created_at": "ISO-8601 timestamp"
}
```

### 3.2 Evaluation Storage
```json
{
  "evaluation_id": "string (unique)",
  "test_run_id": "string",
  "prompt_id": "string",
  "model": "string (exact model version)",
  "timestamp": "ISO-8601",
  "request": {
    "full_prompt": "string (complete)",
    "temperature": "float",
    "max_tokens": "integer"
  },
  "response": {
    "raw": "string (complete API response)",
    "parsed": {
      "T": "float",
      "I": "float",
      "F": "float",
      "reasoning": "string (complete, no truncation)"
    },
    "error": "string (if applicable)"
  },
  "metrics": {
    "latency_ms": "integer",
    "tokens_used": "integer",
    "cost_usd": "float"
  }
}
```

## 4. Configuration Format

### 4.1 Test Configuration (YAML)
```yaml
test_run:
  id: "string (auto-generated if not provided)"
  name: "string"
  timestamp: "ISO-8601"

models:
  - provider: "anthropic"
    model: "claude-sonnet-4.5"
    version: "2024-10-22"  # Explicit version
    max_tokens: 1000
    temperature: 0.0

prompts:
  source: "database"  # or "file"
  collection: "calibration_480"
  filters:
    category: ["manipulative", "reciprocal"]

execution:
  parallel_workers: 4
  retry_attempts: 3
  retry_delay_ms: 1000
  timeout_per_request_ms: 30000

output:
  database:
    enabled: true
    real_time: true
  file:
    enabled: true
    format: "jsonl"
    path: "./outputs/{timestamp}_{test_name}.jsonl"
```

## 5. Execution Requirements

### 5.1 Model Selection
- Models MUST be specified by exact version string
- NO automatic substitution if specified model unavailable
- Failed model calls must be logged with complete error

### 5.2 Data Completeness
- NO truncation of any text fields
- Prompts must be stored complete in database before testing
- Reasoning field must capture complete model output
- Error messages must include full stack traces

### 5.3 Timestamps
- All output files must include ISO-8601 timestamp in filename
- Pattern: `YYYY-MM-DD_HH-MM-SS_{test_name}.{extension}`
- All database records must include creation timestamp

### 5.4 Error Handling
- Network errors: Exponential backoff retry
- Parsing errors: Store raw response, mark as error
- Model refusals: Store complete refusal message
- Rate limits: Queue and retry after delay

## 6. Output Requirements

### 6.1 Real-time Persistence
- Each evaluation result written to database immediately
- No batching until end of run
- Partial results must be queryable during execution

### 6.2 File Output
- JSONL format (one record per line)
- Each line must be valid JSON
- Include metadata header as first line
- Checkpoint files every N evaluations (configurable)

## 7. Prohibited Behaviors

### 7.1 Data Manipulation
- MUST NOT truncate any text fields
- MUST NOT modify prompt content
- MUST NOT substitute models without explicit config change

### 7.2 Autonomous Decisions
- MUST NOT choose alternative models if specified unavailable
- MUST NOT skip prompts without logging
- MUST NOT modify test parameters during execution

## 8. Monitoring and Observability

### 8.1 Progress Tracking
- Real-time progress updates
- Running cost accumulation
- Error rate tracking
- Estimated completion time

### 8.2 Audit Trail
```json
{
  "event": "string",
  "timestamp": "ISO-8601",
  "test_run_id": "string",
  "details": {}
}
```

## 9. Resume/Restart Capability

### 9.1 Checkpointing
- Test state saved after each evaluation
- Can resume from any checkpoint
- Skips already-completed evaluations on restart

## 10. Validation

### 10.1 Pre-execution Validation
- Verify all models accessible
- Confirm database connectivity
- Validate configuration schema
- Check prompt completeness

### 10.2 Post-execution Validation
- Verify all prompts evaluated
- Check for data truncation
- Validate cost calculations
- Confirm database integrity
