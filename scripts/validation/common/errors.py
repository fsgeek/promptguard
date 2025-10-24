"""
Error types for validation framework.

All exceptions follow fail-fast principle (Constitution: No Theater).
No silent degradation - all failures raise immediately.
"""


class ConfigurationError(Exception):
    """
    Raised when system configuration is invalid or corrupted.

    Examples:
    - Fixture file checksum mismatch (FR-356-362)
    - Prompt configuration uniqueness violation (FR-003d)
    - Required environment variable missing (ARANGODB_PROMPTGUARD_PASSWORD)
    - Dataset file not found (datasets/benign_malicious.json)
    - ArangoDB connection unavailable

    This is a fail-fast error - experiment cannot proceed with bad configuration.
    """
    pass


class ValidationError(Exception):
    """
    Raised when data fails Pydantic schema validation.

    Examples:
    - Timestamp missing timezone (FR-039 violation: must use ISO 8601 with Z suffix)
    - F-score outside [0.0, 1.0] range
    - Required field missing (e.g., prompt_id, experiment_id)
    - UUID format invalid
    - Enum value not recognized

    This is a fail-fast error - invalid data cannot be stored in ArangoDB.
    """
    pass


class EvaluationError(Exception):
    """
    Raised when LLM evaluation fails.

    Examples:
    - OpenRouter API timeout (network failure)
    - Model unavailable (503 Service Unavailable)
    - Response parsing failure (malformed JSON)
    - Cache write failure (disk full)
    - Rate limit exceeded (429 Too Many Requests)

    FR-005: Evaluation failures are stored in `processing_failures` collection
    as first-class research data. Experiment continues with next prompt.

    Constitution: No Theater - API failures raise errors, don't return fake values.
    """
    pass


class ModelVersionChangedError(Exception):
    """
    Raised when model version changes between strides (FR-032).

    Triggers PAUSE → user decision flow:
    - ABORT: Stop experiment, mark as incomplete
    - CONTINUE: Proceed with new version, log change
    - IGNORE: Suppress future warnings for this experiment

    Example:
        Current stride using anthropic/claude-3.5-sonnet:20241022
        Previous stride used anthropic/claude-3.5-sonnet:20241015
        → Raise ModelVersionChangedError

    Constitution: Empirical Integrity - model version changes affect results,
    must be explicitly acknowledged.
    """

    def __init__(self, old_version: str, new_version: str):
        self.old_version = old_version
        self.new_version = new_version
        super().__init__(
            f"Model version changed: {old_version} → {new_version}. "
            f"Decision required: ABORT/CONTINUE/IGNORE"
        )


class StorageError(Exception):
    """
    Raised when ArangoDB storage operation fails.

    Examples:
    - Document insert fails (unique constraint violation)
    - Collection doesn't exist (database not initialized)
    - Connection lost mid-write (network failure)
    - Disk full (cannot write document)

    This is a fail-fast error - data loss is unacceptable for research integrity.
    Constitution: Incomplete data is worse than no data.
    """
    pass
