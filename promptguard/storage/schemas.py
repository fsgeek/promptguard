"""
SQLite schema definitions for Fire Circle deliberation metadata.

Provides fast queries without loading full JSON deliberations:
- Time-based queries (when did deliberations occur?)
- Attack-based queries (which deliberations evaluated this attack?)
- Pattern-based queries (which deliberations found this pattern?)
- Dissent tracking (where did models disagree significantly?)
"""

# SQL schema for deliberations metadata database
SCHEMA_SQL = """
-- Main deliberations table (structural metadata)
CREATE TABLE IF NOT EXISTS fire_circles (
    fire_circle_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    models TEXT NOT NULL,  -- JSON array of model IDs
    attack_id TEXT,
    attack_category TEXT,
    consensus_f REAL NOT NULL,
    consensus_t REAL NOT NULL,
    consensus_i REAL NOT NULL,
    empty_chair_influence REAL NOT NULL,
    quorum_valid INTEGER NOT NULL,  -- 0 or 1
    total_duration_seconds REAL NOT NULL,
    rounds_completed INTEGER NOT NULL,
    file_path TEXT NOT NULL  -- Path to full JSON file
);

-- Patterns table (one row per pattern per deliberation)
CREATE TABLE IF NOT EXISTS patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fire_circle_id TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    first_observed_by TEXT NOT NULL,
    agreement_score REAL NOT NULL,
    round_discovered INTEGER NOT NULL,
    FOREIGN KEY (fire_circle_id) REFERENCES fire_circles(fire_circle_id)
);

-- Dissents table (significant F-score divergence between models)
CREATE TABLE IF NOT EXISTS dissents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fire_circle_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    model_high TEXT NOT NULL,  -- Model with highest F
    model_low TEXT NOT NULL,   -- Model with lowest F
    f_high REAL NOT NULL,
    f_low REAL NOT NULL,
    f_delta REAL NOT NULL,  -- f_high - f_low
    FOREIGN KEY (fire_circle_id) REFERENCES fire_circles(fire_circle_id)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_timestamp ON fire_circles(timestamp);
CREATE INDEX IF NOT EXISTS idx_attack_category ON fire_circles(attack_category);
CREATE INDEX IF NOT EXISTS idx_attack_id ON fire_circles(attack_id);
CREATE INDEX IF NOT EXISTS idx_pattern_type ON patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_pattern_agreement ON patterns(agreement_score);
CREATE INDEX IF NOT EXISTS idx_dissent_delta ON dissents(f_delta);
CREATE INDEX IF NOT EXISTS idx_dissent_fire_circle ON dissents(fire_circle_id);
"""


def initialize_database(db_path: str) -> None:
    """
    Initialize SQLite database with schema.

    Args:
        db_path: Path to SQLite database file

    Raises:
        IOError: If database creation fails
    """
    import sqlite3

    try:
        conn = sqlite3.connect(db_path)
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise IOError(f"Failed to initialize database at {db_path}: {e}")
