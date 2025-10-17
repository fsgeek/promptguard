"""
Abstract interface for Fire Circle deliberation storage.

Defines contract for storing and querying institutional memory:
- Structural metadata (fire_circle_id, timestamp, models, attack_id)
- Deliberation dynamics (rounds, prompts, evaluations, reasoning)
- Synthesis artifacts (patterns, consensus, empty_chair_influence)
- Dissents (minority perspectives, reasoning evolution)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class DeliberationStorage(ABC):
    """
    Abstract base class for Fire Circle deliberation storage.

    Implementations must provide:
    - Persistent storage of complete deliberation data
    - Metadata indexing for fast queries
    - Dissent tracking for validation
    - Pattern-based retrieval
    """

    @abstractmethod
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
        Store complete deliberation data.

        Args:
            fire_circle_id: Unique identifier for this Fire Circle
            timestamp: When deliberation occurred
            models: List of model IDs that participated
            attack_id: Optional attack identifier for validation tracking
            attack_category: Optional attack category (e.g., "encoding_obfuscation")
            rounds: List of dialogue rounds with evaluations
            patterns: List of pattern observations
            consensus: Final consensus evaluation
            empty_chair_influence: Empty chair contribution metric
            metadata: Additional metadata (quorum_valid, duration, etc.)

        Raises:
            IOError: If storage fails
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def query_by_pattern(
        self,
        pattern_type: str,
        min_agreement: float = 0.5,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query deliberations by pattern type.

        Args:
            pattern_type: Pattern type to search for (e.g., "temporal_inconsistency")
            min_agreement: Minimum agreement score (0.0-1.0)
            limit: Maximum number of results

        Returns:
            List of deliberation metadata with matching patterns
        """
        pass

    @abstractmethod
    def find_dissents(
        self,
        min_f_delta: float = 0.3,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find deliberations with significant dissenting opinions.

        Dissent = significant divergence in F-scores between models,
        indicating disagreement about prompt manipulation.

        Args:
            min_f_delta: Minimum F-score delta to qualify as dissent
            limit: Maximum number of results

        Returns:
            List of dissenting deliberations with delta information
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
