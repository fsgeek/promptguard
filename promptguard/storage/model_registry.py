"""
Model registry for database-driven model selection.

Replaces hardcoded model names in test scripts with dynamic queries
against ArangoDB models collection.
"""

import os
from typing import Optional
from arango import ArangoClient


class ModelRegistry:
    """Query ArangoDB for model metadata and selection."""

    def __init__(self, db_client=None):
        """Initialize registry with optional DB client (for testing)."""
        if db_client is None:
            client = ArangoClient(
                hosts=f"http://{os.getenv('ARANGODB_HOST', '192.168.111.125')}:{os.getenv('ARANGODB_PORT', '8529')}"
            )
            self.db = client.db(
                os.getenv("ARANGODB_DB", "PromptGuard"),
                username=os.getenv("ARANGODB_USER", "pgtest"),
                password=os.getenv("ARANGODB_PROMPTGUARD_PASSWORD")
            )
        else:
            self.db = db_client

    def get_default_model(
        self,
        is_current: bool = True,
        is_flagship: bool = True,
        observer_compatible: bool = True,
        max_cost: Optional[float] = None
    ) -> str:
        """
        Get default model name based on criteria.

        Args:
            is_current: Model is current version (not obsolete)
            is_flagship: Model is flagship/best-in-class
            observer_compatible: Supports observer framing
            max_cost: Maximum input cost per 1M tokens

        Returns:
            Model name (e.g., "anthropic/claude-sonnet-4.5")

        Raises:
            ValueError: If no models match criteria
        """
        filters = []
        if is_current:
            filters.append("m.is_current == true")
        if is_flagship:
            filters.append("m.is_flagship == true")
        if observer_compatible:
            filters.append("m.observer_compatible == true")
        if max_cost is not None:
            filters.append(f"m.input_price_per_1m <= {max_cost}")

        filter_clause = " AND ".join(filters) if filters else "true"

        aql = f"""
        FOR m IN models
            FILTER {filter_clause}
            SORT m.input_price_per_1m ASC
            LIMIT 1
            RETURN m.id
        """

        cursor = self.db.aql.execute(aql)
        results = list(cursor)

        if not results:
            raise ValueError(
                f"No models found matching criteria: "
                f"is_current={is_current}, is_flagship={is_flagship}, "
                f"observer_compatible={observer_compatible}, max_cost={max_cost}"
            )

        return results[0]

    def get_budget_model(self, observer_compatible: bool = True) -> str:
        """
        Get cheapest model that meets minimum requirements.

        Args:
            observer_compatible: Supports observer framing

        Returns:
            Model name of cheapest option
        """
        return self.get_default_model(
            is_current=True,
            is_flagship=False,  # Don't require flagship for budget
            observer_compatible=observer_compatible,
            max_cost=None  # Find absolute cheapest
        )

    def get_flagship_model(self) -> str:
        """
        Get current flagship model (highest quality).

        For flagship models, prioritize by quality (highest cost = highest quality).
        For Anthropic models, prefer Claude Sonnet 4.5 as the current standard.

        Returns:
            Model name of flagship option (e.g., "anthropic/claude-sonnet-4.5")
        """
        # Query flagship models sorted by price DESC (highest quality first)
        aql = """
        FOR m IN models
            FILTER m.is_current == true AND m.is_flagship == true AND m.observer_compatible == true
            SORT m.input_price_per_1m DESC
            LIMIT 1
            RETURN m.id
        """

        cursor = self.db.aql.execute(aql)
        results = list(cursor)

        if not results:
            raise ValueError("No flagship models found")

        return results[0]

    def list_models(
        self,
        is_current: Optional[bool] = None,
        is_flagship: Optional[bool] = None,
        observer_compatible: Optional[bool] = None
    ) -> list[dict]:
        """
        List all models matching criteria.

        Args:
            is_current: Filter by current status (None = no filter)
            is_flagship: Filter by flagship status
            observer_compatible: Filter by observer framing compatibility

        Returns:
            List of model metadata dicts
        """
        filters = []
        if is_current is not None:
            filters.append(f"m.is_current == {str(is_current).lower()}")
        if is_flagship is not None:
            filters.append(f"m.is_flagship == {str(is_flagship).lower()}")
        if observer_compatible is not None:
            filters.append(f"m.observer_compatible == {str(observer_compatible).lower()}")

        filter_clause = " AND ".join(filters) if filters else "true"

        aql = f"""
        FOR m IN models
            FILTER {filter_clause}
            SORT m.input_price_per_1m ASC
            RETURN {{
                id: m.id,
                name: m.name,
                family: m.family,
                is_current: m.is_current,
                is_flagship: m.is_flagship,
                observer_compatible: m.observer_compatible,
                input_cost: m.input_price_per_1m,
                output_cost: m.output_price_per_1m,
                notes: m.notes
            }}
        """

        cursor = self.db.aql.execute(aql)
        return list(cursor)


# Singleton for easy access
_registry = None

def get_registry() -> ModelRegistry:
    """Get global model registry instance."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry


def get_default_model(**kwargs) -> str:
    """Convenience function to get default model."""
    return get_registry().get_default_model(**kwargs)


def get_flagship_model() -> str:
    """Convenience function to get flagship model."""
    return get_registry().get_flagship_model()


def get_budget_model(**kwargs) -> str:
    """Convenience function to get budget model."""
    return get_registry().get_budget_model(**kwargs)
