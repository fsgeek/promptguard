"""
API Contract: ModelPicker

This module defines the public API contract for the model-picker feature.
All implementations must conform to this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


# Domain models (from data-model.md)
@dataclass
class ModelMetadata:
    """Model metadata returned by queries."""
    openrouter_id: str
    provider: str
    name: str
    created: int
    context_length: int
    description: str
    # ... (full definition in data-model.md)


@dataclass
class ModelQuery:
    """Query parameters for model selection."""
    available: Optional[bool] = None
    frontier: Optional[bool] = None
    free: Optional[bool] = None
    provider: Optional[str] = None
    architecture_family: Optional[str] = None
    observer_framing_compatible: Optional[bool] = None
    structured_outputs: Optional[bool] = None
    limit: int = 100
    sort_by: str = "created"
    sort_desc: bool = True


# Exceptions
class ModelNotFoundError(Exception):
    """Raised when model not found in database."""
    pass


class StalenessWarning(Exception):
    """Raised when frontier list is stale and user declines to proceed."""
    pass


class SyncError(Exception):
    """Raised when OpenRouter sync fails."""
    pass


# Main API Contract
class IModelPicker(ABC):
    """
    Model picker interface for database-driven model selection.

    This interface replaces hardcoded model lists with dynamic queries
    that survive model deprecation.
    """

    @abstractmethod
    def query(
        self,
        *,
        available: Optional[bool] = None,
        frontier: Optional[bool] = None,
        free: Optional[bool] = None,
        provider: Optional[str] = None,
        architecture_family: Optional[str] = None,
        observer_framing_compatible: Optional[bool] = None,
        structured_outputs: Optional[bool] = None,
        limit: int = 100,
        sort_by: str = "created",
        sort_desc: bool = True,
        interactive: bool = True
    ) -> List[ModelMetadata]:
        """
        Query models by attributes.

        Args:
            available: Filter by availability (True=available, False=deprecated, None=all)
            frontier: Filter by frontier designation
            free: Filter by free models (pricing.prompt == "0" AND pricing.completion == "0")
            provider: Filter by provider (e.g., "anthropic", "openai")
            architecture_family: Filter by architecture family (e.g., "transformer-dense", "moe")
            observer_framing_compatible: Filter by observer framing compatibility
            structured_outputs: Filter by structured output support
            limit: Maximum number of results
            sort_by: Sort field ("created", "name", "context_length")
            sort_desc: Sort descending (True) or ascending (False)
            interactive: If True, prompt user for staleness acknowledgment

        Returns:
            List of models matching query, sorted by sort_by

        Raises:
            StalenessWarning: If frontier query and list >30 days old and user declines
            ValueError: If invalid query parameters
            IOError: If database query fails

        Example:
            # Get available frontier models for Fire Circle
            models = picker.query(available=True, frontier=True, limit=5)

            # Get free models for cost optimization
            models = picker.query(available=True, free=True)

            # Get observer-compatible models
            models = picker.query(
                available=True,
                observer_framing_compatible=True,
                limit=2
            )
        """
        pass

    @abstractmethod
    def get_by_id(self, openrouter_id: str) -> ModelMetadata:
        """
        Get specific model by OpenRouter ID.

        Args:
            openrouter_id: Model ID (e.g., "anthropic/claude-sonnet-4.5")

        Returns:
            Model metadata

        Raises:
            ModelNotFoundError: If model not found
            IOError: If database query fails

        Example:
            model = picker.get_by_id("anthropic/claude-sonnet-4.5")
        """
        pass

    @abstractmethod
    def sync_from_openrouter(self, api_key: str) -> dict:
        """
        Sync model catalog from OpenRouter API.

        This operation:
        1. Fetches all models from OpenRouter /api/v1/models
        2. Updates existing models (preserves manual attributes)
        3. Adds new models (frontier=False by default)
        4. Marks absent models as available=False
        5. Updates sync_metadata.last_openrouter_sync

        Args:
            api_key: OpenRouter API key

        Returns:
            Sync statistics:
            {
                "models_added": int,
                "models_updated": int,
                "models_deprecated": int,
                "duration_seconds": float,
                "errors": List[dict]
            }

        Raises:
            SyncError: If OpenRouter API call fails
            IOError: If database update fails

        Example:
            stats = picker.sync_from_openrouter(os.environ["OPENROUTER_API_KEY"])
            print(f"Added: {stats['models_added']}, Updated: {stats['models_updated']}")
        """
        pass

    @abstractmethod
    def get_sync_metadata(self) -> dict:
        """
        Get global sync metadata.

        Returns:
            Sync metadata:
            {
                "last_openrouter_sync": str (ISO timestamp),
                "frontier_updated": str (ISO timestamp),
                "models_count": int,
                "sync_errors": List[dict],
                "sync_history": List[dict]
            }

        Raises:
            IOError: If database query fails

        Example:
            metadata = picker.get_sync_metadata()
            last_sync = datetime.fromisoformat(metadata["last_openrouter_sync"])
            print(f"Last sync: {last_sync}")
        """
        pass

    @abstractmethod
    def needs_sync(self, ttl_hours: int = 24) -> bool:
        """
        Check if sync is needed based on TTL.

        Args:
            ttl_hours: Time-to-live for sync freshness

        Returns:
            True if last sync older than TTL or never synced

        Raises:
            IOError: If database query fails

        Example:
            if picker.needs_sync(ttl_hours=24):
                picker.sync_from_openrouter(api_key)
        """
        pass


class IModelAdmin(ABC):
    """
    Model administration interface for manual curation.

    This interface provides tools for:
    - Frontier designation management
    - Observer framing validation
    - Manual attribute updates
    """

    @abstractmethod
    def mark_frontier(self, openrouter_id: str, frontier: bool) -> None:
        """
        Mark model as frontier (or not).

        Updates frontier field and frontier_updated timestamp in sync_metadata.

        Args:
            openrouter_id: Model ID
            frontier: True to mark as frontier, False to unmark

        Raises:
            ModelNotFoundError: If model not found
            IOError: If database update fails

        Example:
            admin.mark_frontier("anthropic/claude-sonnet-4.5", frontier=True)
        """
        pass

    @abstractmethod
    def batch_mark_frontier(self, model_ids: List[str], frontier: bool) -> None:
        """
        Mark multiple models as frontier in single transaction.

        Updates frontier field for all models and frontier_updated timestamp.

        Args:
            model_ids: List of model IDs
            frontier: True to mark as frontier, False to unmark

        Raises:
            ModelNotFoundError: If any model not found
            IOError: If database update fails

        Example:
            admin.batch_mark_frontier([
                "anthropic/claude-opus-4.1",
                "openai/gpt-5-codex",
                "google/gemini-2.5-pro"
            ], frontier=True)
        """
        pass

    @abstractmethod
    def update_attributes(
        self,
        openrouter_id: str,
        *,
        observer_framing_compatible: Optional[bool] = None,
        architecture_family: Optional[str] = None,
        instruct: Optional[bool] = None,
        rlhf: Optional[bool] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """
        Update manual attributes for model.

        Args:
            openrouter_id: Model ID
            observer_framing_compatible: Observer framing compatibility
            architecture_family: Architecture family classification
            instruct: Instruction-tuned flag
            rlhf: RLHF-aligned flag
            tags: Custom tags (replaces existing tags)

        Raises:
            ModelNotFoundError: If model not found
            IOError: If database update fails

        Example:
            admin.update_attributes(
                "anthropic/claude-sonnet-4.5",
                observer_framing_compatible=True,
                architecture_family="transformer-dense",
                rlhf=True,
                tags=["production", "validated"]
            )
        """
        pass

    @abstractmethod
    def test_model_availability(self, openrouter_id: str, api_key: str) -> dict:
        """
        Test model availability via OpenRouter API.

        Args:
            openrouter_id: Model ID
            api_key: OpenRouter API key

        Returns:
            Test results:
            {
                "available": bool,
                "status_code": int,
                "error": str | None
            }

        Example:
            result = admin.test_model_availability(
                "anthropic/claude-sonnet-4.5",
                os.environ["OPENROUTER_API_KEY"]
            )
            if result["available"]:
                print("Model is available")
        """
        pass


# Contract validation tests (to be implemented in tests/unit/test_model_picker_contract.py)
class ContractTests:
    """
    Tests that validate implementations conform to API contract.

    These tests should be run against any implementation of IModelPicker or IModelAdmin.
    """

    @staticmethod
    def test_query_returns_list():
        """Verify query() returns List[ModelMetadata]."""
        pass

    @staticmethod
    def test_query_respects_limit():
        """Verify query() respects limit parameter."""
        pass

    @staticmethod
    def test_query_staleness_warning():
        """Verify query(frontier=True) raises StalenessWarning when appropriate."""
        pass

    @staticmethod
    def test_sync_preserves_manual_attributes():
        """Verify sync_from_openrouter() preserves frontier, observer_framing_compatible, etc."""
        pass

    @staticmethod
    def test_get_by_id_not_found():
        """Verify get_by_id() raises ModelNotFoundError for nonexistent models."""
        pass
