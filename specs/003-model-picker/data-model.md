# Data Model: Model Picker

**Date**: 2025-10-26
**Phase**: 1 - Design & Contracts
**Status**: Complete

## Overview

This document defines the data structures for the model-picker feature, including ArangoDB schema, Python domain models, and data validation rules.

---

## ArangoDB Collections

### models (Document Collection)

**Purpose**: Store LLM model metadata from OpenRouter with manual curation attributes

**Primary Key**: `_key` = sanitized `openrouter_id` (replace `/` with `_`)

**Indexes**:
```python
# Hash indexes for attribute filtering
{"type": "hash", "fields": ["openrouter_id"], "unique": True}
{"type": "hash", "fields": ["provider"]}
{"type": "hash", "fields": ["frontier"]}
{"type": "hash", "fields": ["available"]}
{"type": "hash", "fields": ["free"]}
{"type": "hash", "fields": ["observer_framing_compatible"]}

# Skiplist for temporal queries
{"type": "skiplist", "fields": ["last_synced"]}
{"type": "skiplist", "fields": ["created"]}

# Fulltext for description search
{"type": "fulltext", "fields": ["description"], "minLength": 3}
```

**Document Schema**:

```python
{
    # Primary identification
    "_key": str,  # Sanitized: "anthropic_claude-sonnet-4.5"
    "openrouter_id": str,  # Original: "anthropic/claude-sonnet-4.5"
    "provider": str,  # Extracted from ID: "anthropic"
    "name": str,  # Display name: "Anthropic: Claude Sonnet 4.5"

    # Auto-synced from OpenRouter (volatile)
    "created": int,  # Unix timestamp
    "context_length": int,  # Tokens
    "description": str,  # Full-text searchable
    "pricing": {
        "prompt": str,  # USD per token (string to avoid float precision)
        "completion": str,
        "request": str,  # Per-request cost
        "image": str,  # Per-image cost
        "web_search": str,
        "internal_reasoning": str,
        # Optional cache fields (16.4% of models)
        "input_cache_read": str | None,
        "input_cache_write": str | None
    },
    "architecture": {
        "modality": str,  # "text->text", "text+image->text", etc.
        "input_modalities": list[str],  # ["text"], ["text", "image"], etc.
        "output_modalities": list[str],
        "tokenizer": str,  # "Claude", "GPT", "Mistral", "Other"
        "instruct_type": str | None  # Instruction format or null
    },
    "top_provider": {
        "context_length": int,
        "max_completion_tokens": int | None,
        "is_moderated": bool
    },
    "supported_parameters": list[str],  # API capabilities

    # Manual curation (preserved across syncs)
    "frontier": bool,  # Requires human review
    "testing": bool,  # Experimental/testing flag
    "observer_framing_compatible": bool | None,  # null=untested, bool=validated
    "architecture_family": str | None,  # "transformer-dense", "moe", "reasoning"
    "free": bool,  # Derived but requires data-training disclosure
    "instruct": bool | None,  # Instruction-tuned (requires validation)
    "rlhf": bool | None,  # RLHF-aligned (requires research)

    # Sync metadata
    "last_synced": str,  # ISO timestamp: "2025-10-26T12:00:00Z"
    "available": bool,  # Derived from presence in OpenRouter API

    # Open tagging (extensible)
    "tags": list[str]  # Custom tags for research needs
}
```

**Validation Rules**:
- `openrouter_id` must match pattern `^[a-z0-9.-]+/[a-z0-9.-]+$`
- `provider` extracted from `openrouter_id` before `/`
- `pricing.*` must be numeric strings (no quotes in numbers)
- `created` must be valid Unix timestamp
- `last_synced` must be ISO 8601 format
- `frontier` defaults to `False` (manual opt-in)
- `available` derived from API presence (not manually set)

**State Transitions**:
```
New model from OpenRouter sync:
  frontier=False, available=True, last_synced=now

Manual frontier curation:
  frontier=False → frontier=True (requires human review)

Model deprecated (absent from OpenRouter):
  available=True → available=False (auto-sync)

Frontier review (staleness refresh):
  last_synced updated, frontier=True preserved if still valid
```

---

### sync_metadata (Document Collection)

**Purpose**: Track global sync state for staleness detection

**Primary Key**: `_key` = "global" (singleton document)

**Document Schema**:

```python
{
    "_key": "global",
    "last_openrouter_sync": str,  # ISO timestamp
    "frontier_updated": str,  # ISO timestamp of last manual frontier review
    "models_count": int,  # Number of models in catalog
    "sync_errors": list[dict],  # Recent errors for operational visibility
    "sync_history": list[dict]  # Last N sync operations
}
```

**sync_errors structure**:
```python
{
    "timestamp": str,  # ISO timestamp
    "error_type": str,  # "api_error", "parse_error", "network_error"
    "message": str,
    "model_id": str | None  # If error specific to one model
}
```

**sync_history structure**:
```python
{
    "timestamp": str,
    "models_added": int,
    "models_updated": int,
    "models_deprecated": int,
    "duration_seconds": float
}
```

**Validation Rules**:
- Only one document allowed (singleton)
- `sync_errors` limited to last 100 errors
- `sync_history` limited to last 50 sync operations
- All timestamps must be ISO 8601 format

---

## Python Domain Models

### ModelMetadata (Data Class)

**Purpose**: Type-safe representation of model document

**Location**: `promptguard/models/model_picker.py`

```python
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class ModelPricing:
    """Model pricing information (all costs in USD)."""
    prompt: str  # Per-token input cost
    completion: str  # Per-token output cost
    request: str = "0"
    image: str = "0"
    web_search: str = "0"
    internal_reasoning: str = "0"
    input_cache_read: Optional[str] = None
    input_cache_write: Optional[str] = None

    def is_free(self) -> bool:
        """Check if model is completely free."""
        return self.prompt == "0" and self.completion == "0"


@dataclass
class ModelArchitecture:
    """Model architecture metadata."""
    modality: str  # "text->text", "text+image->text", etc.
    input_modalities: list[str]
    output_modalities: list[str]
    tokenizer: str
    instruct_type: Optional[str] = None

    def supports_vision(self) -> bool:
        """Check if model supports image input."""
        return "image" in self.input_modalities


@dataclass
class TopProvider:
    """Top provider metadata."""
    context_length: int
    max_completion_tokens: Optional[int]
    is_moderated: bool


@dataclass
class ModelMetadata:
    """Complete model metadata."""
    # Primary identification
    openrouter_id: str
    provider: str
    name: str

    # Auto-synced fields
    created: int
    context_length: int
    description: str
    pricing: ModelPricing
    architecture: ModelArchitecture
    top_provider: TopProvider
    supported_parameters: list[str]

    # Manual curation
    frontier: bool = False
    testing: bool = False
    observer_framing_compatible: Optional[bool] = None
    architecture_family: Optional[str] = None
    free: bool = False
    instruct: Optional[bool] = None
    rlhf: Optional[bool] = None

    # Sync metadata
    last_synced: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    available: bool = True

    # Open tagging
    tags: list[str] = field(default_factory=list)

    @property
    def _key(self) -> str:
        """ArangoDB document key."""
        return self.openrouter_id.replace("/", "_")

    def supports_structured_output(self) -> bool:
        """Check if model supports structured output."""
        return "structured_outputs" in self.supported_parameters

    def supports_tools(self) -> bool:
        """Check if model supports tool calling."""
        return "tools" in self.supported_parameters

    def to_arango_doc(self) -> dict:
        """Convert to ArangoDB document format."""
        return {
            "_key": self._key,
            "openrouter_id": self.openrouter_id,
            "provider": self.provider,
            "name": self.name,
            "created": self.created,
            "context_length": self.context_length,
            "description": self.description,
            "pricing": {
                "prompt": self.pricing.prompt,
                "completion": self.pricing.completion,
                "request": self.pricing.request,
                "image": self.pricing.image,
                "web_search": self.pricing.web_search,
                "internal_reasoning": self.pricing.internal_reasoning,
                "input_cache_read": self.pricing.input_cache_read,
                "input_cache_write": self.pricing.input_cache_write,
            },
            "architecture": {
                "modality": self.architecture.modality,
                "input_modalities": self.architecture.input_modalities,
                "output_modalities": self.architecture.output_modalities,
                "tokenizer": self.architecture.tokenizer,
                "instruct_type": self.architecture.instruct_type,
            },
            "top_provider": {
                "context_length": self.top_provider.context_length,
                "max_completion_tokens": self.top_provider.max_completion_tokens,
                "is_moderated": self.top_provider.is_moderated,
            },
            "supported_parameters": self.supported_parameters,
            "frontier": self.frontier,
            "testing": self.testing,
            "observer_framing_compatible": self.observer_framing_compatible,
            "architecture_family": self.architecture_family,
            "free": self.free,
            "instruct": self.instruct,
            "rlhf": self.rlhf,
            "last_synced": self.last_synced,
            "available": self.available,
            "tags": self.tags,
        }

    @classmethod
    def from_arango_doc(cls, doc: dict) -> "ModelMetadata":
        """Create from ArangoDB document."""
        return cls(
            openrouter_id=doc["openrouter_id"],
            provider=doc["provider"],
            name=doc["name"],
            created=doc["created"],
            context_length=doc["context_length"],
            description=doc["description"],
            pricing=ModelPricing(**doc["pricing"]),
            architecture=ModelArchitecture(**doc["architecture"]),
            top_provider=TopProvider(**doc["top_provider"]),
            supported_parameters=doc["supported_parameters"],
            frontier=doc.get("frontier", False),
            testing=doc.get("testing", False),
            observer_framing_compatible=doc.get("observer_framing_compatible"),
            architecture_family=doc.get("architecture_family"),
            free=doc.get("free", False),
            instruct=doc.get("instruct"),
            rlhf=doc.get("rlhf"),
            last_synced=doc.get("last_synced", ""),
            available=doc.get("available", True),
            tags=doc.get("tags", []),
        )
```

### ModelQuery (Data Class)

**Purpose**: Type-safe query parameters with validation

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ModelQuery:
    """Model query parameters."""
    available: Optional[bool] = None
    frontier: Optional[bool] = None
    free: Optional[bool] = None
    provider: Optional[str] = None
    architecture_family: Optional[str] = None
    observer_framing_compatible: Optional[bool] = None
    instruct: Optional[bool] = None
    rlhf: Optional[bool] = None
    structured_outputs: Optional[bool] = None
    tools: Optional[bool] = None
    limit: int = 100
    sort_by: str = "created"  # "created", "name", "context_length"
    sort_desc: bool = True

    def __post_init__(self):
        """Validate query parameters."""
        if self.limit < 1:
            raise ValueError("limit must be >= 1")
        if self.limit > 1000:
            raise ValueError("limit must be <= 1000")
        if self.sort_by not in ["created", "name", "context_length"]:
            raise ValueError(f"Invalid sort_by: {self.sort_by}")
```

---

## Data Validation

### OpenRouter Response Validation

```python
def validate_openrouter_model(data: dict) -> None:
    """
    Validate model data from OpenRouter API.

    Raises:
        ValueError: If required fields missing or invalid
    """
    required_fields = ["id", "name", "created", "context_length", "pricing", "architecture"]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Validate ID format
    if "/" not in data["id"]:
        raise ValueError(f"Invalid model ID format: {data['id']}")

    # Validate pricing
    if "prompt" not in data["pricing"] or "completion" not in data["pricing"]:
        raise ValueError("Pricing missing prompt or completion cost")

    # Validate timestamps
    if not isinstance(data["created"], int) or data["created"] < 0:
        raise ValueError(f"Invalid created timestamp: {data['created']}")
```

### Manual Attribute Preservation

```python
def merge_manual_attributes(
    existing: Optional[ModelMetadata],
    synced: ModelMetadata
) -> ModelMetadata:
    """
    Merge manual attributes from existing model with synced data.

    Args:
        existing: Existing model from database (or None for new models)
        synced: Fresh data from OpenRouter sync

    Returns:
        Merged model with preserved manual attributes
    """
    if existing is None:
        return synced

    # Preserve manual curation
    synced.frontier = existing.frontier
    synced.testing = existing.testing
    synced.observer_framing_compatible = existing.observer_framing_compatible
    synced.architecture_family = existing.architecture_family
    synced.instruct = existing.instruct
    synced.rlhf = existing.rlhf
    synced.tags = existing.tags

    # Preserve free flag but update based on pricing
    synced.free = synced.pricing.is_free()

    return synced
```

---

## Data Flow

### Model Sync Flow

```
1. Fetch OpenRouter /api/v1/models
   ↓
2. Validate each model (validate_openrouter_model)
   ↓
3. Convert to ModelMetadata
   ↓
4. For each model:
   - Load existing from ArangoDB (if exists)
   - Merge manual attributes (merge_manual_attributes)
   - Update available=True
   ↓
5. Mark absent models as available=False
   ↓
6. Batch update ArangoDB
   ↓
7. Update sync_metadata.last_openrouter_sync
```

### Query Flow

```
1. Create ModelQuery with filters
   ↓
2. Validate query parameters
   ↓
3. Build AQL query with bind variables
   ↓
4. Execute query
   ↓
5. Convert results to ModelMetadata objects
   ↓
6. Check frontier staleness if frontier=True query
   ↓
7. Return List[ModelMetadata]
```

---

## Error Handling

### Custom Exceptions

```python
class ModelNotFoundError(Exception):
    """Raised when model not found in database."""
    pass

class StalenessWarning(Exception):
    """Raised when frontier list is stale and user declines to proceed."""
    pass

class SyncError(Exception):
    """Raised when OpenRouter sync fails."""
    pass
```

### Error Logging Strategy

```python
# Store in sync_metadata.sync_errors for operational visibility
{
    "timestamp": "2025-10-26T12:00:00Z",
    "error_type": "api_error",
    "message": "OpenRouter API returned 429: Rate limit exceeded",
    "model_id": None
}
```

---

## Phase 1 Completion Checklist

- [x] ArangoDB collections schema defined
- [x] Index strategy documented
- [x] Python domain models created
- [x] Data validation rules specified
- [x] Manual attribute preservation logic defined
- [x] Data flow diagrams created
- [x] Error handling strategy documented

**Status**: Ready for contracts generation
