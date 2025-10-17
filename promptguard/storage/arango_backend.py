"""
ArangoDB storage backend for Fire Circle deliberations.

Replaces SQLite implementation with native graph database for:
- Graph queries (which models participated in which deliberations?)
- Full-text search on reasoning
- Native JSON storage without file system dependency
- Better scalability for research analysis

Schema:
- deliberations: Document collection (fire_circle_id, metadata, consensus)
- turns: Document collection (round-level evaluations with reasoning)
- participated_in: Edge collection (models → deliberations)
- deliberation_about: Edge collection (deliberations → attacks)

Design rationale:
- Document storage preserves complete deliberation without file I/O
- Edge collections enable graph traversal queries
- Full-text indexes on reasoning enable pattern research
- No SQLite metadata duplication - ArangoDB handles queries directly
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from arango import ArangoClient
from arango.database import StandardDatabase
from arango.collection import StandardCollection

from .deliberation import DeliberationStorage


class ArangoDBBackend(DeliberationStorage):
    """
    ArangoDB implementation of Fire Circle deliberation storage.

    Stores deliberations as documents with graph edges for relationships.
    Enables graph queries and full-text search without file I/O.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_existing_db: bool = True
    ):
        """
        Initialize ArangoDB storage backend.

        Args:
            host: ArangoDB host (default: 192.168.111.125)
            port: ArangoDB port (default: 8529)
            db_name: Database name (default: PromptGuard)
            username: Database username (default: pgtest)
            password: Database password (default: from env ARANGODB_PROMPTGUARD_PASSWORD)
            use_existing_db: Use existing database connection (default: True)

        Raises:
            ValueError: If password not provided and not in environment
            ConnectionError: If unable to connect to ArangoDB
        """
        # Default configuration (matches existing PromptGuard setup)
        self.host = host or os.environ.get("ARANGODB_HOST", "192.168.111.125")
        self.port = port or int(os.environ.get("ARANGODB_PORT", "8529"))
        self.db_name = db_name or os.environ.get("ARANGODB_DB", "PromptGuard")
        self.username = username or os.environ.get("ARANGODB_USER", "pgtest")

        # Password from environment if not provided
        self.password = password or os.environ.get("ARANGODB_PROMPTGUARD_PASSWORD")
        if not self.password:
            raise ValueError(
                "ArangoDB password required. Set ARANGODB_PROMPTGUARD_PASSWORD "
                "environment variable or pass password to ArangoDBBackend"
            )

        # Connect to ArangoDB
        try:
            client = ArangoClient(hosts=f"http://{self.host}:{self.port}")
            self.db: StandardDatabase = client.db(
                self.db_name,
                username=self.username,
                password=self.password
            )
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to ArangoDB at {self.host}:{self.port}: {e}"
            )

        # Initialize collections if using existing db
        if use_existing_db:
            self._ensure_collections()

    def _ensure_collections(self) -> None:
        """
        Create Fire Circle collections and indexes if they don't exist.

        Collections:
        - deliberations: Session-level metadata
        - turns: Individual model evaluations per round

        Edges:
        - participated_in: models → deliberations
        - deliberation_about: deliberations → attacks

        Idempotent - safe to call multiple times.

        Raises:
            IOError: If collection creation fails
        """
        try:
            # Create document collections
            if not self.db.has_collection("deliberations"):
                self.db.create_collection("deliberations")

            if not self.db.has_collection("turns"):
                self.db.create_collection("turns")

            # Create edge collections
            if not self.db.has_collection("participated_in"):
                self.db.create_collection("participated_in", edge=True)

            if not self.db.has_collection("deliberation_about"):
                self.db.create_collection("deliberation_about", edge=True)

            # Get collection handles
            deliberations = self.db.collection("deliberations")
            turns = self.db.collection("turns")

            # Create indexes on deliberations collection
            # fire_circle_id for lookups
            self._ensure_index(deliberations, "hash", ["fire_circle_id"], unique=True)

            # Timestamp for time-based queries
            self._ensure_index(deliberations, "skiplist", ["created_at"])

            # Metadata fields for filtering
            self._ensure_index(deliberations, "hash", ["metadata.attack_category"])
            self._ensure_index(deliberations, "hash", ["metadata.quorum_valid"])

            # Create indexes on turns collection
            # fire_circle_id for joins
            self._ensure_index(turns, "hash", ["fire_circle_id"])

            # Round number and model for filtering
            self._ensure_index(turns, "skiplist", ["round_number"])
            self._ensure_index(turns, "hash", ["model"])

            # Full-text index on reasoning for pattern search
            self._ensure_index(turns, "fulltext", ["reasoning"])

            # Timestamp for temporal queries
            self._ensure_index(turns, "skiplist", ["timestamp"])

        except Exception as e:
            raise IOError(f"Failed to initialize Fire Circle collections: {e}")

    def _ensure_index(
        self,
        collection: StandardCollection,
        index_type: str,
        fields: List[str],
        unique: bool = False
    ) -> None:
        """
        Create index if it doesn't exist (idempotent).

        Args:
            collection: ArangoDB collection
            index_type: Index type (hash, skiplist, fulltext)
            fields: List of fields to index
            unique: Whether index enforces uniqueness
        """
        try:
            # Get existing indexes
            existing_indexes = collection.indexes()

            # Check if index already exists
            for index in existing_indexes:
                if index.get("type") == index_type and set(index.get("fields", [])) == set(fields):
                    return  # Index exists

            # Create index using modern API
            if index_type == "hash":
                collection.add_index({"type": "hash", "fields": fields, "unique": unique})
            elif index_type == "skiplist":
                collection.add_index({"type": "skiplist", "fields": fields, "unique": unique})
            elif index_type == "fulltext":
                collection.add_index({"type": "fulltext", "fields": fields, "minLength": 3})

        except Exception:
            # Ignore errors if index already exists (race condition)
            pass

    def store_deliberation(
        self,
        fire_circle_id: str,
        timestamp: datetime,
        models: List[str],
        attack_id: Optional[str],
        attack_category: Optional[str],
        rounds: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        consensus: Dict[str, Any],
        empty_chair_influence: float,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Store complete deliberation data in ArangoDB.

        Creates:
        1. Deliberation document with metadata
        2. Turn documents for each model evaluation
        3. participated_in edges (models → deliberation)
        4. deliberation_about edge (deliberation → attack) if attack_id provided

        Args:
            fire_circle_id: Unique identifier for this Fire Circle
            timestamp: When deliberation occurred
            models: List of model IDs that participated
            attack_id: Optional attack identifier
            attack_category: Optional attack category
            rounds: List of dialogue rounds with evaluations
            patterns: List of pattern observations
            consensus: Final consensus evaluation
            empty_chair_influence: Empty chair contribution metric
            metadata: Additional metadata

        Raises:
            IOError: If storage fails
        """
        try:
            deliberations = self.db.collection("deliberations")
            turns_collection = self.db.collection("turns")
            participated_in = self.db.collection("participated_in")
            deliberation_about = self.db.collection("deliberation_about")

            # Calculate convergence trajectory
            convergence_trajectory = []
            for round_data in rounds:
                evaluations = round_data.get("evaluations", [])
                if evaluations:
                    f_scores = [e["F"] for e in evaluations]
                    mean_f = sum(f_scores) / len(f_scores)
                    convergence_trajectory.append(mean_f)

            # Store deliberation document
            deliberation_doc = {
                "_key": fire_circle_id,
                "fire_circle_id": fire_circle_id,
                "created_at": timestamp.isoformat(),
                "total_duration": metadata.get("total_duration_seconds", 0.0),
                "convergence_trajectory": convergence_trajectory,
                "consensus": {
                    "model": consensus.get("model", "unknown"),
                    "truth": consensus.get("T", 0.0),
                    "indeterminacy": consensus.get("I", 0.0),
                    "falsehood": consensus.get("F", 0.0),
                    "reasoning": consensus.get("reasoning", "")
                },
                "empty_chair_influence": empty_chair_influence,
                "metadata": {
                    "attack_id": attack_id,
                    "attack_category": attack_category,
                    "quorum_valid": metadata.get("quorum_valid", False),
                    "total_duration_seconds": metadata.get("total_duration_seconds", 0.0),
                    "rounds_completed": len(rounds),
                    "final_active_models": metadata.get("final_active_models", []),
                    "patterns_count": len(patterns),
                    "unique_pattern_types": len(set(p["pattern_type"] for p in patterns)),
                    "failed_models": metadata.get("failed_models", []),
                    "empty_chair_assignments": metadata.get("empty_chair_assignments", {}),
                },
                "patterns": patterns
            }

            deliberations.insert(deliberation_doc)

            # Store turn documents (individual evaluations)
            for round_data in rounds:
                round_number = round_data["round_number"]
                empty_chair_model = round_data.get("empty_chair_model")

                for evaluation in round_data.get("evaluations", []):
                    model = evaluation["model"]

                    turn_doc = {
                        "turn_id": f"{fire_circle_id}_r{round_number}_{model}",
                        "fire_circle_id": fire_circle_id,
                        "round_number": round_number,
                        "model": model,
                        "empty_chair": (model == empty_chair_model),
                        "truth": evaluation["T"],
                        "indeterminacy": evaluation["I"],
                        "falsehood": evaluation["F"],
                        "reasoning": evaluation.get("reasoning", ""),
                        "patterns_observed": evaluation.get("patterns_observed"),
                        "consensus_patterns": evaluation.get("consensus_patterns"),
                        "timestamp": timestamp.isoformat()
                    }

                    turns_collection.insert(turn_doc)

            # Create participated_in edges (models → deliberation)
            for model in models:
                # Model document key in models collection
                model_key = model.replace("/", "/")  # Already in correct format

                edge_doc = {
                    "_from": f"models/{model_key}",
                    "_to": f"deliberations/{fire_circle_id}",
                    "role": "participant",
                    "timestamp": timestamp.isoformat()
                }

                try:
                    participated_in.insert(edge_doc)
                except Exception:
                    # Ignore duplicate edges (idempotent)
                    pass

            # Create deliberation_about edge (deliberation → attack) if attack_id provided
            if attack_id:
                edge_doc = {
                    "_from": f"deliberations/{fire_circle_id}",
                    "_to": f"attacks/{attack_id}",
                    "timestamp": timestamp.isoformat()
                }

                try:
                    deliberation_about.insert(edge_doc)
                except Exception:
                    # Ignore duplicate edges (idempotent)
                    pass

        except Exception as e:
            raise IOError(f"Failed to store deliberation {fire_circle_id}: {e}")

    def query_by_attack(
        self,
        attack_category: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query deliberations by attack category.

        Args:
            attack_category: Attack category to search for
            limit: Maximum number of results

        Returns:
            List of deliberation metadata matching category
        """
        query = """
        FOR d IN deliberations
            FILTER d.metadata.attack_category == @category
            SORT d.created_at DESC
            LIMIT @limit
            RETURN {
                fire_circle_id: d.fire_circle_id,
                created_at: d.created_at,
                attack_category: d.metadata.attack_category,
                attack_id: d.metadata.attack_id,
                consensus_f: d.consensus.falsehood,
                consensus_t: d.consensus.truth,
                consensus_i: d.consensus.indeterminacy,
                empty_chair_influence: d.empty_chair_influence,
                quorum_valid: d.metadata.quorum_valid,
                rounds_completed: d.metadata.rounds_completed
            }
        """

        try:
            cursor = self.db.aql.execute(
                query,
                bind_vars={"category": attack_category, "limit": limit}
            )
            return list(cursor)
        except Exception as e:
            raise IOError(f"Query by attack category failed: {e}")

    def query_by_pattern(
        self,
        pattern_type: str,
        min_agreement: float = 0.5,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query deliberations by pattern type.

        Args:
            pattern_type: Pattern type to search for
            min_agreement: Minimum agreement score (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of deliberation metadata with matching patterns
        """
        query = """
        FOR d IN deliberations
            FOR pattern IN d.patterns
                FILTER pattern.pattern_type == @pattern_type
                FILTER pattern.agreement_score >= @min_agreement
                SORT d.created_at DESC
                LIMIT @limit
                RETURN DISTINCT {
                    fire_circle_id: d.fire_circle_id,
                    created_at: d.created_at,
                    attack_category: d.metadata.attack_category,
                    pattern_type: pattern.pattern_type,
                    agreement_score: pattern.agreement_score,
                    first_observed_by: pattern.first_observed_by,
                    round_discovered: pattern.round_discovered,
                    consensus_f: d.consensus.falsehood
                }
        """

        try:
            cursor = self.db.aql.execute(
                query,
                bind_vars={
                    "pattern_type": pattern_type,
                    "min_agreement": min_agreement,
                    "limit": limit
                }
            )
            return list(cursor)
        except Exception as e:
            raise IOError(f"Query by pattern failed: {e}")

    def find_dissents(
        self,
        min_f_delta: float = 0.3,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find deliberations with significant dissenting opinions.

        Dissent = significant F-score divergence between models in same round.

        Args:
            min_f_delta: Minimum F-score delta to qualify as dissent
            limit: Maximum number of results

        Returns:
            List of dissenting deliberations with delta information
        """
        query = """
        FOR d IN deliberations
            FOR t1 IN turns
                FILTER t1.fire_circle_id == d.fire_circle_id
                FOR t2 IN turns
                    FILTER t2.fire_circle_id == d.fire_circle_id
                    FILTER t2.round_number == t1.round_number
                    FILTER t2.model != t1.model
                    LET f_delta = ABS(t1.falsehood - t2.falsehood)
                    FILTER f_delta >= @min_f_delta
                    SORT f_delta DESC, d.created_at DESC
                    LIMIT @limit
                    RETURN DISTINCT {
                        fire_circle_id: d.fire_circle_id,
                        created_at: d.created_at,
                        round_number: t1.round_number,
                        model_high: t1.falsehood >= t2.falsehood ? t1.model : t2.model,
                        model_low: t1.falsehood < t2.falsehood ? t1.model : t2.model,
                        f_high: MAX([t1.falsehood, t2.falsehood]),
                        f_low: MIN([t1.falsehood, t2.falsehood]),
                        f_delta: f_delta,
                        attack_category: d.metadata.attack_category
                    }
        """

        try:
            cursor = self.db.aql.execute(
                query,
                bind_vars={"min_f_delta": min_f_delta, "limit": limit}
            )
            return list(cursor)
        except Exception as e:
            raise IOError(f"Find dissents query failed: {e}")

    def get_deliberation(
        self,
        fire_circle_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete deliberation by ID.

        Args:
            fire_circle_id: Fire Circle identifier

        Returns:
            Complete deliberation data, or None if not found
        """
        query = """
        FOR d IN deliberations
            FILTER d.fire_circle_id == @fire_circle_id
            LET round_data = (
                FOR t IN turns
                    FILTER t.fire_circle_id == @fire_circle_id
                    SORT t.round_number, t.model
                    RETURN t
            )
            RETURN MERGE(d, {rounds: round_data})
        """

        try:
            cursor = self.db.aql.execute(
                query,
                bind_vars={"fire_circle_id": fire_circle_id}
            )
            results = list(cursor)
            return results[0] if results else None
        except Exception as e:
            raise IOError(f"Get deliberation query failed: {e}")

    def list_deliberations(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List deliberations with optional date filtering.

        Args:
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)
            limit: Maximum number of results

        Returns:
            List of deliberation metadata
        """
        # Build query with optional date filters
        filters = []
        bind_vars = {"limit": limit}

        if start_date:
            filters.append("d.created_at >= @start_date")
            bind_vars["start_date"] = start_date.isoformat()

        if end_date:
            filters.append("d.created_at <= @end_date")
            bind_vars["end_date"] = end_date.isoformat()

        filter_clause = " AND ".join(filters) if filters else "true"

        query = f"""
        FOR d IN deliberations
            FILTER {filter_clause}
            SORT d.created_at DESC
            LIMIT @limit
            RETURN {{
                fire_circle_id: d.fire_circle_id,
                created_at: d.created_at,
                attack_category: d.metadata.attack_category,
                attack_id: d.metadata.attack_id,
                consensus_f: d.consensus.falsehood,
                empty_chair_influence: d.empty_chair_influence,
                quorum_valid: d.metadata.quorum_valid,
                rounds_completed: d.metadata.rounds_completed,
                patterns_count: d.metadata.patterns_count
            }}
        """

        try:
            cursor = self.db.aql.execute(query, bind_vars=bind_vars)
            return list(cursor)
        except Exception as e:
            raise IOError(f"List deliberations query failed: {e}")

    def query_by_model(
        self,
        model: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find deliberations where a specific model participated.

        Uses graph traversal: models → participated_in → deliberations

        Args:
            model: Model ID (e.g., "anthropic/claude-sonnet-4.5")
            limit: Maximum number of results

        Returns:
            List of deliberation metadata where model participated
        """
        query = """
        FOR d IN 1..1 OUTBOUND @model_doc participated_in
            SORT d.created_at DESC
            LIMIT @limit
            RETURN {
                fire_circle_id: d.fire_circle_id,
                created_at: d.created_at,
                attack_category: d.metadata.attack_category,
                consensus_f: d.consensus.falsehood,
                empty_chair_influence: d.empty_chair_influence
            }
        """

        try:
            model_doc = f"models/{model}"
            cursor = self.db.aql.execute(
                query,
                bind_vars={"model_doc": model_doc, "limit": limit}
            )
            return list(cursor)
        except Exception as e:
            raise IOError(f"Query by model failed: {e}")

    def search_reasoning(
        self,
        search_text: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Full-text search on turn reasoning.

        Enables queries like: "find deliberations mentioning 'temporal inconsistency'"

        Args:
            search_text: Text to search for in reasoning
            limit: Maximum number of results

        Returns:
            List of turns with matching reasoning
        """
        query = """
        FOR t IN FULLTEXT(turns, "reasoning", @search_text)
            LIMIT @limit
            RETURN {
                fire_circle_id: t.fire_circle_id,
                round_number: t.round_number,
                model: t.model,
                reasoning: t.reasoning,
                falsehood: t.falsehood,
                timestamp: t.timestamp
            }
        """

        try:
            cursor = self.db.aql.execute(
                query,
                bind_vars={"search_text": search_text, "limit": limit}
            )
            return list(cursor)
        except Exception as e:
            raise IOError(f"Search reasoning query failed: {e}")
