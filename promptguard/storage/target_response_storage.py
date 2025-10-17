"""
ArangoDB storage for target LLM responses in baseline compliance analysis.

Stores complete responses (encrypted) and metadata for measuring which prompts
succeed vs fail with each target model. Post-evaluation will classify outcomes.

Collection: target_responses
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from arango import ArangoClient
from arango.database import StandardDatabase
from arango.collection import StandardCollection

from .encryption import ResponseEncryption, ensure_encryption_key


class TargetResponseStorage:
    """
    Storage for target LLM responses with encryption.

    Design:
    - One document per (prompt_id, target_model) pair
    - Response text encrypted with AES-256
    - Outcome classification stored unencrypted (for querying)
    - Checkpoint tracking for resume capability
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        encryption_key_path: Optional[str] = None
    ):
        """
        Initialize target response storage.

        Args:
            host: ArangoDB host (default: 192.168.111.125)
            port: ArangoDB port (default: 8529)
            db_name: Database name (default: PromptGuard)
            username: Database username (default: pgtest)
            password: Database password (default: from env)
            encryption_key_path: Path to encryption key (default: ~/.promptguard/target_responses.key)

        Raises:
            ValueError: If password not provided
            ConnectionError: If unable to connect to ArangoDB
        """
        # Database configuration
        self.host = host or os.environ.get("ARANGODB_HOST", "192.168.111.125")
        self.port = port or int(os.environ.get("ARANGODB_PORT", "8529"))
        self.db_name = db_name or os.environ.get("ARANGODB_DB", "PromptGuard")
        self.username = username or os.environ.get("ARANGODB_USER", "pgtest")

        self.password = password or os.environ.get("ARANGODB_PROMPTGUARD_PASSWORD")
        if not self.password:
            raise ValueError(
                "ArangoDB password required. Set ARANGODB_PROMPTGUARD_PASSWORD "
                "environment variable"
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

        # Initialize encryption
        ensure_encryption_key(encryption_key_path)
        self.encryption = ResponseEncryption(encryption_key_path)

        # Initialize collections
        self._ensure_collections()

    def _ensure_collections(self) -> None:
        """
        Create target_responses collection and indexes if they don't exist.

        Idempotent - safe to call multiple times.
        """
        try:
            # Create collection if needed
            if not self.db.has_collection("target_responses"):
                self.db.create_collection("target_responses")

            collection = self.db.collection("target_responses")

            # Create indexes
            existing_indexes = collection.indexes()

            # Index on prompt_id for querying by prompt
            if not any(
                idx.get("type") == "hash" and "prompt_id" in idx.get("fields", [])
                for idx in existing_indexes
            ):
                collection.add_index({"type": "hash", "fields": ["prompt_id"]})

            # Index on target_model for querying by model
            if not any(
                idx.get("type") == "hash" and "target_model" in idx.get("fields", [])
                for idx in existing_indexes
            ):
                collection.add_index({"type": "hash", "fields": ["target_model"]})

            # Index on label for filtering by prompt type
            if not any(
                idx.get("type") == "hash" and "prompt_label" in idx.get("fields", [])
                for idx in existing_indexes
            ):
                collection.add_index({"type": "hash", "fields": ["prompt_label"]})

            # Index on timestamp for temporal queries
            if not any(
                idx.get("type") == "skiplist" and "request.timestamp" in idx.get("fields", [])
                for idx in existing_indexes
            ):
                collection.add_index({"type": "skiplist", "fields": ["request.timestamp"]})

        except Exception as e:
            raise IOError(f"Failed to initialize target_responses collection: {e}")

    def store_response(
        self,
        prompt_id: str,
        prompt_text: str,
        prompt_label: str,
        target_model: str,
        response_text: str,
        temperature: float,
        max_tokens: int,
        tokens: int,
        latency_ms: int,
        cost_usd: float,
        error: Optional[str] = None
    ) -> None:
        """
        Store target LLM response with encryption.

        Args:
            prompt_id: Unique prompt identifier
            prompt_text: Full prompt text (not encrypted)
            prompt_label: reciprocal|manipulative|extractive|borderline
            target_model: Model that generated response
            response_text: Complete response text (will be encrypted)
            temperature: Request temperature
            max_tokens: Request max tokens
            tokens: Response token count
            latency_ms: Response latency in milliseconds
            cost_usd: Response cost in USD
            error: Optional error message if API call failed

        Raises:
            IOError: If storage fails
        """
        try:
            collection = self.db.collection("target_responses")

            # Encrypt response text
            encrypted_text = self.encryption.encrypt(response_text)

            # Create document
            doc = {
                "_key": f"{prompt_id}_{target_model.replace('/', '_')}",
                "prompt_id": prompt_id,
                "prompt_text": prompt_text,
                "prompt_label": prompt_label,
                "target_model": target_model,
                "request": {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timestamp": datetime.now().isoformat()
                },
                "response": {
                    "text_encrypted": encrypted_text,
                    "tokens": tokens,
                    "latency_ms": latency_ms,
                    "cost_usd": cost_usd
                }
            }

            if error:
                doc["error"] = error

            # Insert or update
            collection.insert(doc, overwrite=True)

        except Exception as e:
            raise IOError(f"Failed to store response for {prompt_id}/{target_model}: {e}")

    def get_response(
        self,
        prompt_id: str,
        target_model: str,
        decrypt: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored response.

        Args:
            prompt_id: Prompt identifier
            target_model: Target model
            decrypt: Whether to decrypt response text (default: True)

        Returns:
            Response document with decrypted text, or None if not found
        """
        try:
            collection = self.db.collection("target_responses")
            key = f"{prompt_id}_{target_model.replace('/', '_')}"

            doc = collection.get(key)
            if not doc:
                return None

            # Decrypt if requested
            if decrypt and "response" in doc and "text_encrypted" in doc["response"]:
                encrypted = doc["response"]["text_encrypted"]
                doc["response"]["text"] = self.encryption.decrypt(encrypted)
                del doc["response"]["text_encrypted"]

            return doc

        except Exception as e:
            raise IOError(f"Failed to retrieve response for {prompt_id}/{target_model}: {e}")

    def list_completed(self, target_model: str) -> List[str]:
        """
        List prompt IDs already completed for a target model.

        Used for checkpoint/resume - skip already processed prompts.

        Args:
            target_model: Target model to check

        Returns:
            List of completed prompt IDs
        """
        query = """
        FOR doc IN target_responses
            FILTER doc.target_model == @model
            RETURN doc.prompt_id
        """

        try:
            cursor = self.db.aql.execute(
                query,
                bind_vars={"model": target_model}
            )
            return list(cursor)
        except Exception as e:
            raise IOError(f"Failed to list completed prompts: {e}")

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics across all target responses.

        Returns:
            Dictionary with counts by model and label, total cost
        """
        query = """
        LET total = LENGTH(target_responses)

        LET by_model = (
            FOR doc IN target_responses
                COLLECT model = doc.target_model
                AGGREGATE
                    count = COUNT(doc),
                    total_tokens = SUM(doc.response.tokens),
                    avg_latency = AVG(doc.response.latency_ms),
                    total_cost = SUM(doc.response.cost_usd)
                RETURN {
                    model: model,
                    count: count,
                    total_tokens: total_tokens,
                    avg_latency_ms: avg_latency,
                    cost_usd: total_cost
                }
        )

        LET by_label = (
            FOR doc IN target_responses
                COLLECT label = doc.prompt_label
                AGGREGATE count = COUNT(doc)
                RETURN {
                    label: label,
                    count: count
                }
        )

        LET total_cost = SUM(
            FOR doc IN target_responses
                RETURN doc.response.cost_usd
        )

        RETURN {
            total: total,
            by_model: by_model,
            by_label: by_label,
            total_cost: total_cost
        }
        """

        try:
            cursor = self.db.aql.execute(query)
            results = list(cursor)
            return results[0] if results else {}
        except Exception as e:
            raise IOError(f"Failed to get summary stats: {e}")
