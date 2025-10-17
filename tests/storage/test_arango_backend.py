"""
Tests for ArangoDB storage backend.

Tests cover:
- Storage and retrieval of complete deliberations
- Query operations (by attack, pattern, model)
- Dissent detection
- Edge creation and graph queries
- Full-text search on reasoning
- Integration with FireCircleResult.save()
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from promptguard.storage.arango_backend import ArangoDBBackend


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_arango_db():
    """Mock ArangoDB database."""
    db = MagicMock()

    # Mock collections
    deliberations = MagicMock()
    turns = MagicMock()
    participated_in = MagicMock()
    deliberation_about = MagicMock()

    # Setup collection() to return appropriate mocks
    def get_collection(name):
        if name == "deliberations":
            return deliberations
        elif name == "turns":
            return turns
        elif name == "participated_in":
            return participated_in
        elif name == "deliberation_about":
            return deliberation_about
        return MagicMock()

    db.collection.side_effect = get_collection

    # Mock has_collection to return False (collections don't exist yet)
    db.has_collection.return_value = False

    # Mock create_collection
    db.create_collection.return_value = MagicMock()

    # Mock AQL execution
    db.aql.execute.return_value = []

    return db


@pytest.fixture
def backend(mock_arango_db, monkeypatch):
    """Create ArangoDBBackend with mocked database."""
    # Mock environment variables
    monkeypatch.setenv("ARANGODB_PROMPTGUARD_PASSWORD", "test_password")

    # Mock ArangoClient
    mock_client = MagicMock()
    mock_client.db.return_value = mock_arango_db

    # Patch ArangoClient creation
    def mock_arango_client(hosts):
        return mock_client

    monkeypatch.setattr("promptguard.storage.arango_backend.ArangoClient", mock_arango_client)

    # Create backend
    backend = ArangoDBBackend(use_existing_db=True)
    backend.db = mock_arango_db  # Ensure mock is used

    return backend


@pytest.fixture
def sample_deliberation_data():
    """Sample deliberation data for testing."""
    return {
        "fire_circle_id": "test_fc_001",
        "timestamp": datetime(2025, 10, 14, 12, 0, 0),
        "models": [
            "anthropic/claude-sonnet-4.5",
            "openai/gpt-4.5",
            "alibaba/qwen3-72b"
        ],
        "attack_id": "external_001",
        "attack_category": "encoding_obfuscation",
        "rounds": [
            {
                "round_number": 1,
                "duration_seconds": 2.5,
                "empty_chair_model": None,
                "active_models": [
                    "anthropic/claude-sonnet-4.5",
                    "openai/gpt-4.5",
                    "alibaba/qwen3-72b"
                ],
                "convergence_metric": 0.15,
                "evaluations": [
                    {
                        "model": "anthropic/claude-sonnet-4.5",
                        "T": 0.2,
                        "I": 0.1,
                        "F": 0.8,
                        "reasoning": "Temporal inconsistency detected in layer coordination"
                    },
                    {
                        "model": "openai/gpt-4.5",
                        "T": 0.3,
                        "I": 0.2,
                        "F": 0.7,
                        "reasoning": "Cross-layer fabrication suggests manipulation"
                    },
                    {
                        "model": "alibaba/qwen3-72b",
                        "T": 0.4,
                        "I": 0.1,
                        "F": 0.5,
                        "reasoning": "Some indicators but uncertain about extraction"
                    }
                ]
            },
            {
                "round_number": 2,
                "duration_seconds": 3.0,
                "empty_chair_model": "openai/gpt-4.5",
                "active_models": [
                    "anthropic/claude-sonnet-4.5",
                    "openai/gpt-4.5",
                    "alibaba/qwen3-72b"
                ],
                "convergence_metric": 0.10,
                "evaluations": [
                    {
                        "model": "anthropic/claude-sonnet-4.5",
                        "T": 0.2,
                        "I": 0.1,
                        "F": 0.8,
                        "reasoning": "Pattern confirmed by peer observations",
                        "patterns_observed": ["temporal_inconsistency", "cross_layer_fabrication"]
                    },
                    {
                        "model": "openai/gpt-4.5",
                        "T": 0.2,
                        "I": 0.1,
                        "F": 0.7,
                        "reasoning": "Empty chair perspective: future users would flag this",
                        "patterns_observed": ["temporal_inconsistency"]
                    },
                    {
                        "model": "alibaba/qwen3-72b",
                        "T": 0.3,
                        "I": 0.1,
                        "F": 0.6,
                        "reasoning": "Revised assessment based on dialogue",
                        "patterns_observed": ["temporal_inconsistency"]
                    }
                ]
            }
        ],
        "patterns": [
            {
                "pattern_type": "temporal_inconsistency",
                "first_observed_by": "anthropic/claude-sonnet-4.5",
                "agreement_score": 1.0,
                "round_discovered": 2
            },
            {
                "pattern_type": "cross_layer_fabrication",
                "first_observed_by": "anthropic/claude-sonnet-4.5",
                "agreement_score": 0.33,
                "round_discovered": 2
            }
        ],
        "consensus": {
            "model": "anthropic/claude-sonnet-4.5",
            "T": 0.2,
            "I": 0.1,
            "F": 0.8,
            "reasoning": "Temporal inconsistency detected in layer coordination"
        },
        "empty_chair_influence": 0.5,
        "metadata": {
            "quorum_valid": True,
            "total_duration_seconds": 5.5,
            "final_active_models": [
                "anthropic/claude-sonnet-4.5",
                "openai/gpt-4.5",
                "alibaba/qwen3-72b"
            ],
            "failed_models": [],
            "empty_chair_assignments": {2: "openai/gpt-4.5"}
        }
    }


# ============================================================================
# Initialization Tests
# ============================================================================

def test_initialization_with_defaults(monkeypatch):
    """Test initialization with default configuration."""
    monkeypatch.setenv("ARANGODB_PROMPTGUARD_PASSWORD", "test_password")

    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_client.db.return_value = mock_db

    def mock_arango_client(hosts):
        return mock_client

    monkeypatch.setattr("promptguard.storage.arango_backend.ArangoClient", mock_arango_client)

    backend = ArangoDBBackend(use_existing_db=False)

    assert backend.host == "192.168.111.125"
    assert backend.port == 8529
    assert backend.db_name == "PromptGuard"
    assert backend.username == "pgtest"
    assert backend.password == "test_password"


def test_initialization_missing_password(monkeypatch):
    """Test initialization fails without password."""
    # Clear environment variable
    monkeypatch.delenv("ARANGODB_PROMPTGUARD_PASSWORD", raising=False)

    with pytest.raises(ValueError, match="password required"):
        ArangoDBBackend(use_existing_db=False)


def test_initialization_with_custom_config(monkeypatch):
    """Test initialization with custom configuration."""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_client.db.return_value = mock_db

    def mock_arango_client(hosts):
        return mock_client

    monkeypatch.setattr("promptguard.storage.arango_backend.ArangoClient", mock_arango_client)

    backend = ArangoDBBackend(
        host="localhost",
        port=9999,
        db_name="TestDB",
        username="testuser",
        password="testpass",
        use_existing_db=False
    )

    assert backend.host == "localhost"
    assert backend.port == 9999
    assert backend.db_name == "TestDB"
    assert backend.username == "testuser"
    assert backend.password == "testpass"


# ============================================================================
# Collection Creation Tests
# ============================================================================

def test_ensure_collections_creates_all_collections(backend):
    """Test that _ensure_collections creates all required collections."""
    backend.db.has_collection.return_value = False
    backend._ensure_collections()

    # Verify all collections created
    calls = [call[0][0] for call in backend.db.create_collection.call_args_list]
    assert "deliberations" in calls
    assert "turns" in calls
    assert "participated_in" in calls
    assert "deliberation_about" in calls


def test_ensure_collections_idempotent(monkeypatch):
    """Test that _ensure_collections is idempotent (can be called multiple times)."""
    monkeypatch.setenv("ARANGODB_PROMPTGUARD_PASSWORD", "test_password")

    # Create fresh mock database
    mock_db = MagicMock()
    mock_db.has_collection.return_value = True  # Collections already exist
    mock_db.create_collection.return_value = MagicMock()
    mock_db.collection.return_value = MagicMock()

    mock_client = MagicMock()
    mock_client.db.return_value = mock_db

    monkeypatch.setattr("promptguard.storage.arango_backend.ArangoClient", lambda hosts: mock_client)

    backend = ArangoDBBackend(use_existing_db=True)

    # Should not create collections if they exist
    backend.db.create_collection.assert_not_called()


# ============================================================================
# Storage Tests
# ============================================================================

def test_store_deliberation(backend, sample_deliberation_data):
    """Test storing complete deliberation."""
    backend.store_deliberation(**sample_deliberation_data)

    # Verify deliberation document inserted
    deliberations = backend.db.collection("deliberations")
    deliberations.insert.assert_called_once()

    # Verify turn documents inserted (2 rounds x 3 models = 6 turns)
    turns = backend.db.collection("turns")
    assert turns.insert.call_count == 6

    # Verify participated_in edges created (3 models)
    participated_in = backend.db.collection("participated_in")
    assert participated_in.insert.call_count == 3

    # Verify deliberation_about edge created (attack_id provided)
    deliberation_about = backend.db.collection("deliberation_about")
    deliberation_about.insert.assert_called_once()


def test_store_deliberation_without_attack_id(backend, sample_deliberation_data):
    """Test storing deliberation without attack_id (no deliberation_about edge)."""
    sample_deliberation_data["attack_id"] = None
    backend.store_deliberation(**sample_deliberation_data)

    # Verify deliberation_about edge NOT created
    deliberation_about = backend.db.collection("deliberation_about")
    deliberation_about.insert.assert_not_called()


def test_store_deliberation_handles_errors(backend, sample_deliberation_data):
    """Test that storage errors are properly raised."""
    deliberations = backend.db.collection("deliberations")
    deliberations.insert.side_effect = Exception("Database error")

    with pytest.raises(IOError, match="Failed to store deliberation"):
        backend.store_deliberation(**sample_deliberation_data)


# ============================================================================
# Query Tests
# ============================================================================

def test_query_by_attack(backend):
    """Test querying deliberations by attack category."""
    # Mock AQL result
    backend.db.aql.execute.return_value = [
        {
            "fire_circle_id": "test_fc_001",
            "attack_category": "encoding_obfuscation",
            "consensus_f": 0.8
        }
    ]

    results = backend.query_by_attack("encoding_obfuscation", limit=10)

    assert len(results) == 1
    assert results[0]["attack_category"] == "encoding_obfuscation"
    backend.db.aql.execute.assert_called_once()


def test_query_by_pattern(backend):
    """Test querying deliberations by pattern type."""
    backend.db.aql.execute.return_value = [
        {
            "fire_circle_id": "test_fc_001",
            "pattern_type": "temporal_inconsistency",
            "agreement_score": 1.0
        }
    ]

    results = backend.query_by_pattern("temporal_inconsistency", min_agreement=0.5, limit=10)

    assert len(results) == 1
    assert results[0]["pattern_type"] == "temporal_inconsistency"


def test_find_dissents(backend):
    """Test finding deliberations with significant dissents."""
    backend.db.aql.execute.return_value = [
        {
            "fire_circle_id": "test_fc_001",
            "round_number": 1,
            "f_delta": 0.3,
            "model_high": "anthropic/claude-sonnet-4.5",
            "model_low": "alibaba/qwen3-72b"
        }
    ]

    results = backend.find_dissents(min_f_delta=0.3, limit=10)

    assert len(results) == 1
    assert results[0]["f_delta"] == 0.3


def test_get_deliberation(backend):
    """Test retrieving complete deliberation by ID."""
    backend.db.aql.execute.return_value = [
        {
            "fire_circle_id": "test_fc_001",
            "consensus": {"F": 0.8},
            "rounds": []
        }
    ]

    result = backend.get_deliberation("test_fc_001")

    assert result is not None
    assert result["fire_circle_id"] == "test_fc_001"


def test_get_deliberation_not_found(backend):
    """Test retrieving non-existent deliberation returns None."""
    backend.db.aql.execute.return_value = []

    result = backend.get_deliberation("nonexistent")

    assert result is None


def test_list_deliberations(backend):
    """Test listing deliberations with date filtering."""
    backend.db.aql.execute.return_value = [
        {"fire_circle_id": "test_fc_001"},
        {"fire_circle_id": "test_fc_002"}
    ]

    results = backend.list_deliberations(
        start_date=datetime(2025, 10, 1),
        end_date=datetime(2025, 10, 31),
        limit=10
    )

    assert len(results) == 2


def test_query_by_model(backend):
    """Test querying deliberations where model participated (graph query)."""
    backend.db.aql.execute.return_value = [
        {
            "fire_circle_id": "test_fc_001",
            "consensus_f": 0.8
        }
    ]

    results = backend.query_by_model("anthropic/claude-sonnet-4.5", limit=10)

    assert len(results) == 1


def test_search_reasoning(backend):
    """Test full-text search on reasoning."""
    backend.db.aql.execute.return_value = [
        {
            "fire_circle_id": "test_fc_001",
            "reasoning": "Temporal inconsistency detected"
        }
    ]

    results = backend.search_reasoning("temporal inconsistency", limit=10)

    assert len(results) == 1


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
def test_real_arango_connection():
    """
    Integration test with real ArangoDB.

    Requires:
    - ArangoDB running at 192.168.111.125:8529
    - ARANGODB_PROMPTGUARD_PASSWORD environment variable

    Run with: pytest tests/storage/test_arango_backend.py -m integration
    """
    import os

    if not os.environ.get("ARANGODB_PROMPTGUARD_PASSWORD"):
        pytest.skip("ARANGODB_PROMPTGUARD_PASSWORD not set")

    try:
        backend = ArangoDBBackend()

        # Test collections created
        assert backend.db.has_collection("deliberations")
        assert backend.db.has_collection("turns")
        assert backend.db.has_collection("participated_in")
        assert backend.db.has_collection("deliberation_about")

        print("✓ Real ArangoDB connection successful")

    except Exception as e:
        pytest.fail(f"Real ArangoDB connection failed: {e}")


@pytest.mark.integration
def test_fire_circle_result_save():
    """
    Integration test: FireCircleResult.save() with ArangoDBBackend.

    Tests end-to-end integration from Fire Circle evaluation to storage.
    """
    import os
    import uuid
    from promptguard.evaluation.fire_circle import FireCircleResult, DialogueRound
    from promptguard.evaluation.evaluator import NeutrosophicEvaluation

    if not os.environ.get("ARANGODB_PROMPTGUARD_PASSWORD"):
        pytest.skip("ARANGODB_PROMPTGUARD_PASSWORD not set")

    try:
        backend = ArangoDBBackend()

        # Generate unique ID for this test run
        test_id = f"test_integration_{uuid.uuid4().hex[:8]}"

        # Create mock Fire Circle result
        eval1 = NeutrosophicEvaluation(
            truth=0.2,
            indeterminacy=0.1,
            falsehood=0.8,
            reasoning="Test evaluation",
            model="anthropic/claude-sonnet-4.5"
        )

        round1 = DialogueRound(
            round_number=1,
            evaluations=[eval1],
            active_models=["anthropic/claude-sonnet-4.5"]
        )

        result = FireCircleResult(
            evaluations=[eval1],
            consensus=eval1,
            dialogue_history=[round1],
            patterns=[],
            empty_chair_influence=0.0,
            metadata={
                "fire_circle_id": test_id,
                "model_contributions": {"anthropic/claude-sonnet-4.5": {}}
            }
        )

        # Save to ArangoDB
        result.save(
            storage=backend,
            attack_id="test_attack_001",
            attack_category="integration_test"
        )

        # Retrieve and verify
        retrieved = backend.get_deliberation(test_id)
        assert retrieved is not None
        assert retrieved["fire_circle_id"] == test_id

        print("✓ FireCircleResult.save() integration successful")

    except Exception as e:
        pytest.fail(f"Integration test failed: {e}")
