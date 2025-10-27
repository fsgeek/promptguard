"""
Database-driven LLM model selection.

Solves deprecated model problem by storing metadata in ArangoDB and enabling
attribute-based queries (e.g., "available frontier models").
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

from ..storage.arango_backend import ArangoDBBackend


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
    input_modalities: List[str]
    output_modalities: List[str]
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
    supported_parameters: List[str]

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
    tags: List[str] = field(default_factory=list)

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
        """Create ModelMetadata from ArangoDB document."""
        pricing_data = doc["pricing"]
        architecture_data = doc["architecture"]
        top_provider_data = doc["top_provider"]

        return cls(
            openrouter_id=doc["openrouter_id"],
            provider=doc["provider"],
            name=doc["name"],
            created=doc["created"],
            context_length=doc["context_length"],
            description=doc["description"],
            pricing=ModelPricing(**pricing_data),
            architecture=ModelArchitecture(**architecture_data),
            top_provider=TopProvider(**top_provider_data),
            supported_parameters=doc["supported_parameters"],
            frontier=doc.get("frontier", False),
            testing=doc.get("testing", False),
            observer_framing_compatible=doc.get("observer_framing_compatible"),
            architecture_family=doc.get("architecture_family"),
            free=doc.get("free", False),
            instruct=doc.get("instruct"),
            rlhf=doc.get("rlhf"),
            last_synced=doc.get("last_synced", datetime.utcnow().isoformat()),
            available=doc.get("available", True),
            tags=doc.get("tags", []),
        )


@dataclass
class ModelQuery:
    """Query parameters for filtering models."""
    available: Optional[bool] = None
    frontier: Optional[bool] = None
    free: Optional[bool] = None
    provider: Optional[str] = None
    observer_framing_compatible: Optional[bool] = None
    structured_outputs: Optional[bool] = None
    limit: int = 100
    sort_by: str = "created"
    sort_desc: bool = True


class ModelNotFoundError(Exception):
    """Model not found in database."""
    pass


class ModelPicker:
    """
    Database-driven model selection interface.

    Queries ArangoDB for available models based on attributes,
    replacing hardcoded model lists.
    """

    def __init__(self, backend: Optional[ArangoDBBackend] = None):
        """
        Initialize model picker.

        Args:
            backend: Optional ArangoDB backend (creates new if not provided)
        """
        self.backend = backend or ArangoDBBackend()

    def query(
        self,
        *,
        available: Optional[bool] = None,
        frontier: Optional[bool] = None,
        free: Optional[bool] = None,
        provider: Optional[str] = None,
        observer_framing_compatible: Optional[bool] = None,
        structured_outputs: Optional[bool] = None,
        limit: int = 100,
        sort_by: str = "created",
        sort_desc: bool = True
    ) -> List[ModelMetadata]:
        """
        Query models by attributes.

        Args:
            available: Filter by availability (True/False/None=all)
            frontier: Filter by frontier designation
            free: Filter by cost (True=free, False=paid, None=all)
            provider: Filter by provider (e.g., "anthropic")
            observer_framing_compatible: Filter by observer framing validation
            structured_outputs: Filter by structured output support
            limit: Maximum results to return
            sort_by: Field to sort by ("created", "context_length", etc.)
            sort_desc: Sort descending (newest first) if True

        Returns:
            List of matching models

        Example:
            >>> picker = ModelPicker()
            >>> models = picker.query(available=True, frontier=True, limit=2)
            >>> [m.openrouter_id for m in models]
            ['anthropic/claude-sonnet-4.5', 'google/gemini-2.5-pro']
        """
        # Build AQL filter clauses
        filters = []
        bind_vars = {"limit": limit}

        if available is not None:
            filters.append("m.available == @available")
            bind_vars["available"] = available

        if frontier is not None:
            filters.append("m.frontier == @frontier")
            bind_vars["frontier"] = frontier

        if free is not None:
            filters.append("m.free == @free")
            bind_vars["free"] = free

        if provider is not None:
            filters.append("m.provider == @provider")
            bind_vars["provider"] = provider

        if observer_framing_compatible is not None:
            filters.append("m.observer_framing_compatible == @observer_compatible")
            bind_vars["observer_compatible"] = observer_framing_compatible

        if structured_outputs is not None:
            if structured_outputs:
                filters.append('"structured_outputs" IN m.supported_parameters')
            else:
                filters.append('"structured_outputs" NOT IN m.supported_parameters')

        filter_clause = " AND ".join(filters) if filters else "true"

        # Build sort clause
        sort_direction = "DESC" if sort_desc else "ASC"
        sort_clause = f"m.{sort_by} {sort_direction}"

        # Execute query
        query = f"""
        FOR m IN models
            FILTER {filter_clause}
            SORT {sort_clause}
            LIMIT @limit
            RETURN m
        """

        try:
            cursor = self.backend.db.aql.execute(query, bind_vars=bind_vars)
            results = list(cursor)
            return [ModelMetadata.from_arango_doc(doc) for doc in results]
        except Exception as e:
            raise IOError(f"Model query failed: {e}")

    def get_by_id(self, openrouter_id: str) -> ModelMetadata:
        """
        Retrieve model by OpenRouter ID.

        Args:
            openrouter_id: Model ID (e.g., "anthropic/claude-sonnet-4.5")

        Returns:
            Model metadata

        Raises:
            ModelNotFoundError: If model not found
        """
        query = """
        FOR m IN models
            FILTER m.openrouter_id == @openrouter_id
            RETURN m
        """

        try:
            cursor = self.backend.db.aql.execute(
                query,
                bind_vars={"openrouter_id": openrouter_id}
            )
            results = list(cursor)

            if not results:
                raise ModelNotFoundError(f"Model not found: {openrouter_id}")

            return ModelMetadata.from_arango_doc(results[0])
        except Exception as e:
            if isinstance(e, ModelNotFoundError):
                raise
            raise IOError(f"Get model by ID failed: {e}")
