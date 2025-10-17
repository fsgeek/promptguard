"""
File-based storage backend for Fire Circle deliberations.

Structure:
- deliberations/YYYY/MM/fire_circle_{id}/
  - metadata.json (structural metadata)
  - rounds.json (dialogue rounds)
  - synthesis.json (patterns, consensus, empty_chair_influence)
  - dissents.json (minority perspectives)
- deliberations.db (SQLite metadata index)

Design rationale:
- JSON files preserve complete deliberation (reproducibility)
- SQLite enables fast queries without loading JSON
- Year/month directory structure scales to millions of deliberations
- Separate files enable partial loading (don't need full JSON for queries)
"""

import json
import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .deliberation import DeliberationStorage
from .schemas import initialize_database


class FileBackend(DeliberationStorage):
    """
    File-based implementation of deliberation storage.

    Stores deliberations as JSON files organized by date, with
    SQLite metadata index for fast queries.
    """

    def __init__(self, base_path: str = "deliberations"):
        """
        Initialize file-based storage.

        Args:
            base_path: Base directory for deliberation storage
        """
        self.base_path = Path(base_path)
        self.db_path = self.base_path / "deliberations.db"

        # Create base directory
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Initialize database
        initialize_database(str(self.db_path))

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

        Creates directory structure:
        deliberations/YYYY/MM/fire_circle_{id}/
        ├── metadata.json
        ├── rounds.json
        ├── synthesis.json
        └── dissents.json
        """
        # Create directory structure
        year_month_dir = self.base_path / str(timestamp.year) / f"{timestamp.month:02d}"
        delib_dir = year_month_dir / f"fire_circle_{fire_circle_id}"
        delib_dir.mkdir(parents=True, exist_ok=True)

        # Write structural metadata
        metadata_file = delib_dir / "metadata.json"
        metadata_data = {
            "fire_circle_id": fire_circle_id,
            "timestamp": timestamp.isoformat(),
            "models": models,
            "attack_id": attack_id,
            "attack_category": attack_category,
            "quorum_valid": metadata.get("quorum_valid", False),
            "total_duration_seconds": metadata.get("total_duration_seconds", 0.0),
            "rounds_completed": len(rounds),
            "final_active_models": metadata.get("final_active_models", []),
        }
        with open(metadata_file, 'w') as f:
            json.dump(metadata_data, f, indent=2)

        # Write dialogue rounds
        rounds_file = delib_dir / "rounds.json"
        with open(rounds_file, 'w') as f:
            json.dump(rounds, f, indent=2)

        # Write synthesis artifacts
        synthesis_file = delib_dir / "synthesis.json"
        synthesis_data = {
            "patterns": patterns,
            "consensus": consensus,
            "empty_chair_influence": empty_chair_influence,
        }
        with open(synthesis_file, 'w') as f:
            json.dump(synthesis_data, f, indent=2)

        # Extract and write dissents
        dissents = self._extract_dissents_from_rounds(rounds)
        dissents_file = delib_dir / "dissents.json"
        with open(dissents_file, 'w') as f:
            json.dump(dissents, f, indent=2)

        # Update SQLite metadata
        self._index_deliberation(
            fire_circle_id=fire_circle_id,
            timestamp=timestamp,
            models=models,
            attack_id=attack_id,
            attack_category=attack_category,
            consensus=consensus,
            empty_chair_influence=empty_chair_influence,
            metadata=metadata,
            patterns=patterns,
            dissents=dissents,
            file_path=str(delib_dir)
        )

    def query_by_attack(
        self,
        attack_category: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query deliberations by attack category."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM fire_circles
            WHERE attack_category = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (attack_category, limit)
        )

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def query_by_pattern(
        self,
        pattern_type: str,
        min_agreement: float = 0.5,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query deliberations by pattern type."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT fc.* FROM fire_circles fc
            JOIN patterns p ON fc.fire_circle_id = p.fire_circle_id
            WHERE p.pattern_type = ? AND p.agreement_score >= ?
            ORDER BY fc.timestamp DESC
            LIMIT ?
            """,
            (pattern_type, min_agreement, limit)
        )

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def find_dissents(
        self,
        min_f_delta: float = 0.3,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Find deliberations with significant dissenting opinions."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT fc.*, d.round_number, d.model_high, d.model_low,
                   d.f_high, d.f_low, d.f_delta
            FROM fire_circles fc
            JOIN dissents d ON fc.fire_circle_id = d.fire_circle_id
            WHERE d.f_delta >= ?
            ORDER BY d.f_delta DESC, fc.timestamp DESC
            LIMIT ?
            """,
            (min_f_delta, limit)
        )

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def get_deliberation(
        self,
        fire_circle_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve complete deliberation by ID."""
        # Query metadata for file path
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT file_path FROM fire_circles WHERE fire_circle_id = ?",
            (fire_circle_id,)
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        file_path = Path(row["file_path"])

        # Load all JSON files
        try:
            with open(file_path / "metadata.json", 'r') as f:
                metadata = json.load(f)

            with open(file_path / "rounds.json", 'r') as f:
                rounds = json.load(f)

            with open(file_path / "synthesis.json", 'r') as f:
                synthesis = json.load(f)

            with open(file_path / "dissents.json", 'r') as f:
                dissents = json.load(f)

            return {
                **metadata,
                "rounds": rounds,
                "patterns": synthesis["patterns"],
                "consensus": synthesis["consensus"],
                "empty_chair_influence": synthesis["empty_chair_influence"],
                "dissents": dissents,
            }
        except (IOError, json.JSONDecodeError) as e:
            raise IOError(f"Failed to load deliberation {fire_circle_id}: {e}")

    def list_deliberations(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List deliberations with optional date filtering."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if start_date and end_date:
            cursor.execute(
                """
                SELECT * FROM fire_circles
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (start_date.isoformat(), end_date.isoformat(), limit)
            )
        elif start_date:
            cursor.execute(
                """
                SELECT * FROM fire_circles
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (start_date.isoformat(), limit)
            )
        elif end_date:
            cursor.execute(
                """
                SELECT * FROM fire_circles
                WHERE timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (end_date.isoformat(), limit)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM fire_circles
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def _extract_dissents_from_rounds(
        self,
        rounds: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract dissents from dialogue rounds.

        Dissent = significant F-score divergence between models in same round.
        """
        dissents = []

        for round_data in rounds:
            evaluations = round_data.get("evaluations", [])

            if len(evaluations) < 2:
                continue

            # Find max and min F-scores
            f_scores = [(eval["F"], eval["model"]) for eval in evaluations]
            f_scores.sort(reverse=True)

            f_high, model_high = f_scores[0]
            f_low, model_low = f_scores[-1]
            f_delta = f_high - f_low

            # Only record significant dissents
            if f_delta >= 0.3:
                dissents.append({
                    "round_number": round_data["round_number"],
                    "model_high": model_high,
                    "model_low": model_low,
                    "f_high": f_high,
                    "f_low": f_low,
                    "f_delta": f_delta,
                })

        return dissents

    def _index_deliberation(
        self,
        fire_circle_id: str,
        timestamp: datetime,
        models: List[str],
        attack_id: Optional[str],
        attack_category: Optional[str],
        consensus: Dict[str, Any],
        empty_chair_influence: float,
        metadata: Dict[str, Any],
        patterns: List[Dict[str, Any]],
        dissents: List[Dict[str, Any]],
        file_path: str
    ) -> None:
        """Index deliberation metadata in SQLite."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Insert main fire_circles record
        cursor.execute(
            """
            INSERT OR REPLACE INTO fire_circles
            (fire_circle_id, timestamp, models, attack_id, attack_category,
             consensus_f, consensus_t, consensus_i, empty_chair_influence,
             quorum_valid, total_duration_seconds, rounds_completed, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fire_circle_id,
                timestamp.isoformat(),
                json.dumps(models),
                attack_id,
                attack_category,
                consensus.get("F", 0.0),
                consensus.get("T", 0.0),
                consensus.get("I", 0.0),
                empty_chair_influence,
                int(metadata.get("quorum_valid", False)),
                metadata.get("total_duration_seconds", 0.0),
                len(metadata.get("per_round_metrics", [])),
                file_path
            )
        )

        # Insert patterns
        for pattern in patterns:
            cursor.execute(
                """
                INSERT INTO patterns
                (fire_circle_id, pattern_type, first_observed_by,
                 agreement_score, round_discovered)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    fire_circle_id,
                    pattern["pattern_type"],
                    pattern["first_observed_by"],
                    pattern["agreement_score"],
                    pattern["round_discovered"]
                )
            )

        # Insert dissents
        for dissent in dissents:
            cursor.execute(
                """
                INSERT INTO dissents
                (fire_circle_id, round_number, model_high, model_low,
                 f_high, f_low, f_delta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fire_circle_id,
                    dissent["round_number"],
                    dissent["model_high"],
                    dissent["model_low"],
                    dissent["f_high"],
                    dissent["f_low"],
                    dissent["f_delta"]
                )
            )

        conn.commit()
        conn.close()
