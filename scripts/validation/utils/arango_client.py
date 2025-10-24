"""
ArangoDB client wrapper with connection pooling and sink implementations.

Provides:
- Connection management with environment variable configuration
- Collection-specific sinks implementing Sink protocol
- Query utilities for checkpoint/resume
"""

import os
from typing import Any
from arango import ArangoClient
from arango.database import StandardDatabase


class ArangoConnection:
    """
    Manage ArangoDB connection with environment variable configuration.

    Environment variables:
    - ARANGODB_PROMPTGUARD_PASSWORD (required)
    - ARANGODB_HOST (default: 192.168.111.125)
    - ARANGODB_PORT (default: 8529)
    - ARANGODB_DB (default: PromptGuard)
    - ARANGODB_USER (default: pgtest)
    """

    def __init__(self):
        # Load configuration from environment
        self.host = os.getenv("ARANGODB_HOST", "192.168.111.125")
        self.port = os.getenv("ARANGODB_PORT", "8529")
        self.db_name = os.getenv("ARANGODB_DB", "PromptGuard")
        self.user = os.getenv("ARANGODB_USER", "pgtest")
        self.password = os.getenv("ARANGODB_PROMPTGUARD_PASSWORD")

        if not self.password:
            from ..common.errors import ConfigurationError
            raise ConfigurationError(
                "ARANGODB_PROMPTGUARD_PASSWORD environment variable required"
            )

        # Initialize client
        self.client = ArangoClient(hosts=f"http://{self.host}:{self.port}")
        self._db: StandardDatabase | None = None

    def get_database(self) -> StandardDatabase:
        """
        Get database connection, creating if needed.

        Returns:
            ArangoDB database instance

        Raises:
            ConfigurationError: If connection fails
        """
        if self._db is None:
            try:
                self._db = self.client.db(
                    self.db_name,
                    username=self.user,
                    password=self.password
                )
            except Exception as e:
                from ..common.errors import ConfigurationError
                raise ConfigurationError(
                    f"Cannot connect to ArangoDB at {self.host}:{self.port}: {e}"
                )

        return self._db


class ArangoSink:
    """
    Write items to ArangoDB collection (INSERT only per FR-035).

    Implements Sink protocol for pipeline integration.
    """

    def __init__(self, collection_name: str, connection: ArangoConnection | None = None):
        """
        Args:
            collection_name: Target collection (e.g., "baseline_responses")
            connection: Optional ArangoConnection (creates new if None)
        """
        self.collection_name = collection_name
        self.connection = connection or ArangoConnection()
        self.db = self.connection.get_database()

        # Verify collection exists
        if not self.db.has_collection(collection_name):
            from ..common.errors import ConfigurationError
            raise ConfigurationError(
                f"Collection '{collection_name}' does not exist. "
                f"Run scripts/validation/init_database.py first."
            )

        self.collection = self.db.collection(collection_name)

    def write(self, item: dict[str, Any]) -> None:
        """
        Insert item into collection (immutable INSERT only).

        Args:
            item: Dictionary matching collection schema

        Raises:
            StorageError: If insert fails
            ValidationError: If item invalid
        """
        try:
            self.collection.insert(item)
        except Exception as e:
            from ..common.errors import StorageError
            raise StorageError(
                f"Failed to insert into {self.collection_name}: {e}"
            )


class ArangoSource:
    """
    Query prompts from ArangoDB collection.

    Implements Source protocol for reading existing prompts.
    """

    def __init__(
        self,
        collection_name: str,
        experiment_id: str,
        connection: ArangoConnection | None = None
    ):
        """
        Args:
            collection_name: Source collection (e.g., "prompts")
            experiment_id: Filter by experiment_id
            connection: Optional ArangoConnection
        """
        self.collection_name = collection_name
        self.experiment_id = experiment_id
        self.connection = connection or ArangoConnection()
        self.db = self.connection.get_database()

    def read(self) -> list[dict[str, Any]]:
        """
        Query prompts by experiment_id.

        Returns:
            List of prompt dictionaries

        Raises:
            ConfigurationError: If query fails
        """
        query = f"""
        FOR p IN {self.collection_name}
        FILTER p.experiment_id == @exp_id
        RETURN p
        """

        try:
            cursor = self.db.aql.execute(
                query,
                bind_vars={"exp_id": self.experiment_id}
            )
            return list(cursor)
        except Exception as e:
            from ..common.errors import ConfigurationError
            raise ConfigurationError(f"Query failed: {e}")


def get_completed_prompt_ids(experiment_id: str, collection_name: str = "prompts") -> set[str]:
    """
    Get set of prompt_ids already processed for an experiment (checkpoint/resume).

    Args:
        experiment_id: Experiment identifier
        collection_name: Collection to query (default: "prompts")

    Returns:
        Set of prompt_id strings

    Raises:
        ConfigurationError: If query fails
    """
    connection = ArangoConnection()
    db = connection.get_database()

    query = f"""
    FOR p IN {collection_name}
    FILTER p.experiment_id == @exp_id
    RETURN p.prompt_id
    """

    try:
        cursor = db.aql.execute(query, bind_vars={"exp_id": experiment_id})
        return set(cursor)
    except Exception as e:
        from ..common.errors import ConfigurationError
        raise ConfigurationError(f"Checkpoint query failed: {e}")
