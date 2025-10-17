"""
Tests for Fire Circle deliberation storage.

Validates:
- Storage and retrieval of complete deliberations
- Metadata indexing and queries
- Dissent extraction and tracking
- Pattern-based and attack-based queries
- Reproducibility from stored JSON
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from promptguard.storage import FileBackend, DeliberationStorage
from promptguard.evaluation.fire_circle import FireCircleResult, DialogueRound, PatternObservation
from promptguard.evaluation.evaluator import NeutrosophicEvaluation


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def file_backend(temp_storage_dir):
    """Create file-based storage backend."""
    return FileBackend(base_path=temp_storage_dir)


@pytest.fixture
def sample_evaluations():
    """Create sample evaluations for testing."""
    return [
        NeutrosophicEvaluation(
            truth=0.1,
            indeterminacy=0.0,
            falsehood=0.9,
            reasoning="High manipulation detected",
            model="anthropic/claude-3.5-sonnet"
        ),
        NeutrosophicEvaluation(
            truth=0.2,
            indeterminacy=0.1,
            falsehood=0.7,
            reasoning="Moderate manipulation",
            model="anthropic/claude-3-haiku"
        ),
        NeutrosophicEvaluation(
            truth=0.8,
            indeterminacy=0.1,
            falsehood=0.1,
            reasoning="Looks reciprocal",
            model="google/gemini-2.0-flash-001"
        ),
    ]


@pytest.fixture
def sample_dialogue_round(sample_evaluations):
    """Create sample dialogue round."""
    return DialogueRound(
        round_number=1,
        evaluations=sample_evaluations,
        active_models=[
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku",
            "google/gemini-2.0-flash-001"
        ],
        empty_chair_model=None,
        prompt_used="Test prompt",
        convergence_metric=0.35,
        timestamp=datetime.now().timestamp(),
        duration_seconds=5.2
    )


@pytest.fixture
def sample_patterns():
    """Create sample pattern observations."""
    return [
        PatternObservation(
            pattern_type="temporal_inconsistency",
            first_observed_by="anthropic/claude-3.5-sonnet",
            agreement_score=1.0,
            round_discovered=2
        ),
        PatternObservation(
            pattern_type="polite_extraction",
            first_observed_by="anthropic/claude-3-haiku",
            agreement_score=0.67,
            round_discovered=2
        ),
    ]


@pytest.fixture
def sample_fire_circle_result(sample_evaluations, sample_dialogue_round, sample_patterns):
    """Create sample FireCircleResult."""
    return FireCircleResult(
        evaluations=sample_evaluations,
        consensus=sample_evaluations[0],  # Use highest F
        dialogue_history=[sample_dialogue_round],
        patterns=sample_patterns,
        empty_chair_influence=0.5,
        metadata={
            "fire_circle_id": "test123",
            "model_contributions": {
                "anthropic/claude-3.5-sonnet": {
                    "rounds_participated": [1],
                    "patterns_first_observed": ["temporal_inconsistency"],
                    "empty_chair_rounds": [],
                    "total_evaluations": 1
                },
                "anthropic/claude-3-haiku": {
                    "rounds_participated": [1],
                    "patterns_first_observed": ["polite_extraction"],
                    "empty_chair_rounds": [],
                    "total_evaluations": 1
                },
                "google/gemini-2.0-flash-001": {
                    "rounds_participated": [1],
                    "patterns_first_observed": [],
                    "empty_chair_rounds": [],
                    "total_evaluations": 1
                }
            },
            "quorum_valid": True,
            "total_duration_seconds": 15.5,
            "per_round_metrics": [
                {"round": 1, "duration_seconds": 5.2, "active_models": 3, "convergence_metric": 0.35}
            ],
        }
    )


# =============================================================================
# Storage and Retrieval Tests
# =============================================================================

def test_store_and_retrieve_deliberation(file_backend, sample_fire_circle_result):
    """Test storing and retrieving complete deliberation."""
    # Store deliberation
    sample_fire_circle_result.save(
        storage=file_backend,
        attack_id="attack_001",
        attack_category="encoding_obfuscation"
    )

    # Retrieve deliberation
    result = file_backend.get_deliberation("test123")

    assert result is not None
    assert result["fire_circle_id"] == "test123"
    assert result["attack_id"] == "attack_001"
    assert result["attack_category"] == "encoding_obfuscation"
    assert len(result["rounds"]) == 1
    assert len(result["patterns"]) == 2
    assert result["consensus"]["F"] == 0.9
    assert result["empty_chair_influence"] == 0.5


def test_stored_files_structure(file_backend, sample_fire_circle_result, temp_storage_dir):
    """Test that storage creates correct directory structure."""
    sample_fire_circle_result.save(
        storage=file_backend,
        attack_id="attack_001",
        attack_category="encoding_obfuscation"
    )

    # Check directory structure
    base_path = Path(temp_storage_dir)
    now = datetime.now()
    delib_dir = base_path / str(now.year) / f"{now.month:02d}" / "fire_circle_test123"

    assert delib_dir.exists()
    assert (delib_dir / "metadata.json").exists()
    assert (delib_dir / "rounds.json").exists()
    assert (delib_dir / "synthesis.json").exists()
    assert (delib_dir / "dissents.json").exists()
    assert (base_path / "deliberations.db").exists()


def test_retrieve_nonexistent_deliberation(file_backend):
    """Test retrieving nonexistent deliberation returns None."""
    result = file_backend.get_deliberation("nonexistent")
    assert result is None


def test_reproducibility_from_json(file_backend, sample_fire_circle_result):
    """Test that stored JSON fully reproduces deliberation."""
    # Store original
    sample_fire_circle_result.save(
        storage=file_backend,
        attack_id="attack_001",
        attack_category="encoding_obfuscation"
    )

    # Retrieve and validate all fields
    result = file_backend.get_deliberation("test123")

    # Validate rounds
    assert len(result["rounds"]) == 1
    round_data = result["rounds"][0]
    assert round_data["round_number"] == 1
    assert len(round_data["evaluations"]) == 3
    assert round_data["convergence_metric"] == 0.35

    # Validate evaluations
    eval_data = round_data["evaluations"][0]
    assert eval_data["model"] == "anthropic/claude-3.5-sonnet"
    assert eval_data["F"] == 0.9
    assert eval_data["reasoning"] == "High manipulation detected"

    # Validate patterns
    assert len(result["patterns"]) == 2
    pattern = result["patterns"][0]
    assert pattern["pattern_type"] == "temporal_inconsistency"
    assert pattern["agreement_score"] == 1.0

    # Validate consensus
    assert result["consensus"]["F"] == 0.9
    assert result["consensus"]["model"] == "anthropic/claude-3.5-sonnet"


# =============================================================================
# Query Tests
# =============================================================================

def test_query_by_attack_category(file_backend, sample_fire_circle_result):
    """Test querying deliberations by attack category."""
    # Store multiple deliberations with different categories
    sample_fire_circle_result.save(
        storage=file_backend,
        attack_id="attack_001",
        attack_category="encoding_obfuscation"
    )

    # Modify and store another
    sample_fire_circle_result.metadata["fire_circle_id"] = "test456"
    sample_fire_circle_result.save(
        storage=file_backend,
        attack_id="attack_002",
        attack_category="temporal_inconsistency"
    )

    # Query by category
    results = file_backend.query_by_attack("encoding_obfuscation")

    assert len(results) == 1
    assert results[0]["fire_circle_id"] == "test123"
    assert results[0]["attack_category"] == "encoding_obfuscation"


def test_query_by_pattern_type(file_backend, sample_fire_circle_result):
    """Test querying deliberations by pattern type."""
    sample_fire_circle_result.save(
        storage=file_backend,
        attack_id="attack_001",
        attack_category="encoding_obfuscation"
    )

    # Query by pattern
    results = file_backend.query_by_pattern("temporal_inconsistency", min_agreement=0.5)

    assert len(results) == 1
    assert results[0]["fire_circle_id"] == "test123"


def test_query_by_pattern_with_min_agreement(file_backend, sample_fire_circle_result):
    """Test pattern query respects min_agreement threshold."""
    sample_fire_circle_result.save(
        storage=file_backend,
        attack_id="attack_001",
        attack_category="encoding_obfuscation"
    )

    # Query with high threshold (should include temporal_inconsistency with 1.0 agreement)
    results = file_backend.query_by_pattern("temporal_inconsistency", min_agreement=0.9)
    assert len(results) == 1

    # Query with threshold above polite_extraction (0.67)
    results = file_backend.query_by_pattern("polite_extraction", min_agreement=0.8)
    assert len(results) == 0

    # Query with lower threshold (should include polite_extraction)
    results = file_backend.query_by_pattern("polite_extraction", min_agreement=0.6)
    assert len(results) == 1


def test_list_deliberations(file_backend, sample_fire_circle_result):
    """Test listing deliberations with date filtering."""
    sample_fire_circle_result.save(
        storage=file_backend,
        attack_id="attack_001",
        attack_category="encoding_obfuscation"
    )

    # List all
    results = file_backend.list_deliberations()
    assert len(results) >= 1

    # List with date range
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    results = file_backend.list_deliberations(start_date=yesterday, end_date=tomorrow)
    assert len(results) >= 1

    # List outside date range
    last_week = today - timedelta(days=7)
    last_month = today - timedelta(days=30)
    results = file_backend.list_deliberations(start_date=last_month, end_date=last_week)
    assert len(results) == 0


# =============================================================================
# Dissent Tracking Tests
# =============================================================================

def test_extract_dissents(sample_fire_circle_result):
    """Test dissent extraction from FireCircleResult."""
    dissents = sample_fire_circle_result.extract_dissents()

    # Should have 1 dissent (F=0.9 vs F=0.1, delta=0.8)
    assert len(dissents) == 1
    dissent = dissents[0]

    assert dissent["round_number"] == 1
    assert dissent["f_delta"] >= 0.3  # Significant dissent
    assert dissent["model_high"] == "anthropic/claude-3.5-sonnet"
    assert dissent["model_low"] == "google/gemini-2.0-flash-001"


def test_find_dissents_query(file_backend, sample_fire_circle_result):
    """Test querying for deliberations with significant dissents."""
    sample_fire_circle_result.save(
        storage=file_backend,
        attack_id="attack_001",
        attack_category="encoding_obfuscation"
    )

    # Query for dissents
    results = file_backend.find_dissents(min_f_delta=0.3)

    assert len(results) == 1
    assert results[0]["fire_circle_id"] == "test123"
    assert results[0]["f_delta"] >= 0.3


def test_dissents_stored_in_json(file_backend, sample_fire_circle_result, temp_storage_dir):
    """Test that dissents are stored in dissents.json."""
    sample_fire_circle_result.save(
        storage=file_backend,
        attack_id="attack_001",
        attack_category="encoding_obfuscation"
    )

    # Read dissents.json directly
    base_path = Path(temp_storage_dir)
    now = datetime.now()
    dissents_file = base_path / str(now.year) / f"{now.month:02d}" / "fire_circle_test123" / "dissents.json"

    with open(dissents_file, 'r') as f:
        dissents = json.load(f)

    assert len(dissents) == 1
    assert dissents[0]["f_delta"] >= 0.3


# =============================================================================
# Data Extraction Methods Tests
# =============================================================================

def test_to_metadata(sample_fire_circle_result):
    """Test metadata extraction for indexing."""
    metadata = sample_fire_circle_result.to_metadata()

    assert metadata["fire_circle_id"] == "test123"
    assert len(metadata["models"]) == 3
    assert metadata["consensus_f"] == 0.9
    assert metadata["consensus_t"] == 0.1
    assert metadata["quorum_valid"] is True
    assert metadata["rounds_completed"] == 1
    assert metadata["patterns_count"] == 2


def test_extract_deliberation_trajectory(sample_fire_circle_result):
    """Test trajectory extraction for convergence analysis."""
    trajectory = sample_fire_circle_result.extract_deliberation_trajectory()

    assert len(trajectory) == 1
    round_stats = trajectory[0]

    assert round_stats["round_number"] == 1
    assert round_stats["mean_f"] == pytest.approx(0.567, rel=0.01)  # (0.9 + 0.7 + 0.1) / 3
    assert round_stats["stddev_f"] == 0.35
    assert round_stats["range_f"] == 0.8  # 0.9 - 0.1
    assert round_stats["active_models_count"] == 3
    assert round_stats["empty_chair_model"] is None


def test_extract_rounds_for_storage(sample_fire_circle_result):
    """Test round extraction for JSON serialization."""
    rounds = sample_fire_circle_result.extract_rounds_for_storage()

    assert len(rounds) == 1
    round_data = rounds[0]

    assert round_data["round_number"] == 1
    assert round_data["duration_seconds"] == 5.2
    assert len(round_data["evaluations"]) == 3
    assert round_data["convergence_metric"] == 0.35

    # Validate evaluation structure
    eval_data = round_data["evaluations"][0]
    assert "model" in eval_data
    assert "T" in eval_data
    assert "F" in eval_data
    assert "reasoning" in eval_data


# =============================================================================
# Integration Tests
# =============================================================================

def test_full_storage_retrieval_cycle(file_backend, sample_fire_circle_result):
    """Test complete storage → query → retrieval cycle."""
    # 1. Store deliberation
    sample_fire_circle_result.save(
        storage=file_backend,
        attack_id="attack_001",
        attack_category="encoding_obfuscation"
    )

    # 2. Query by attack
    attack_results = file_backend.query_by_attack("encoding_obfuscation")
    assert len(attack_results) == 1

    # 3. Query by pattern
    pattern_results = file_backend.query_by_pattern("temporal_inconsistency")
    assert len(pattern_results) == 1

    # 4. Query by dissent
    dissent_results = file_backend.find_dissents(min_f_delta=0.3)
    assert len(dissent_results) == 1

    # 5. Retrieve full deliberation
    full_result = file_backend.get_deliberation("test123")
    assert full_result is not None
    assert full_result["fire_circle_id"] == "test123"


def test_multiple_deliberations_storage(file_backend, sample_fire_circle_result):
    """Test storing multiple deliberations."""
    # Store 3 deliberations with different IDs
    for i in range(3):
        sample_fire_circle_result.metadata["fire_circle_id"] = f"test_{i}"
        sample_fire_circle_result.save(
            storage=file_backend,
            attack_id=f"attack_{i}",
            attack_category="encoding_obfuscation"
        )

    # List all
    results = file_backend.list_deliberations(limit=10)
    assert len(results) == 3


def test_storage_with_empty_patterns(file_backend, sample_evaluations, sample_dialogue_round):
    """Test storage works with no patterns extracted."""
    result = FireCircleResult(
        evaluations=sample_evaluations,
        consensus=sample_evaluations[0],
        dialogue_history=[sample_dialogue_round],
        patterns=[],  # No patterns
        empty_chair_influence=0.0,
        metadata={
            "fire_circle_id": "test_no_patterns",
            "model_contributions": {},
            "quorum_valid": True,
            "total_duration_seconds": 10.0,
        }
    )

    result.save(storage=file_backend, attack_id="attack_001")

    # Retrieve and validate
    retrieved = file_backend.get_deliberation("test_no_patterns")
    assert retrieved is not None
    assert len(retrieved["patterns"]) == 0


def test_storage_query_limit(file_backend, sample_fire_circle_result):
    """Test query result limit parameter."""
    # Store 5 deliberations
    for i in range(5):
        sample_fire_circle_result.metadata["fire_circle_id"] = f"test_{i}"
        sample_fire_circle_result.save(
            storage=file_backend,
            attack_id=f"attack_{i}",
            attack_category="encoding_obfuscation"
        )

    # Query with limit=2
    results = file_backend.query_by_attack("encoding_obfuscation", limit=2)
    assert len(results) == 2

    # Query with limit=10 (should return all 5)
    results = file_backend.query_by_attack("encoding_obfuscation", limit=10)
    assert len(results) == 5
