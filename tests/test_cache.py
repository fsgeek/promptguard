"""
Tests for caching layer.

Verifies that cache reduces API calls, handles TTL expiration,
and maintains correctness across different backends.
"""

import pytest
import asyncio
import time
from pathlib import Path
import tempfile
import shutil

from promptguard.evaluation.cache import (
    DiskCache,
    MemoryCache,
    CachedEvaluation,
    make_cache_key
)
from promptguard.evaluation import LLMEvaluator, EvaluationConfig, EvaluationMode
from promptguard.config import CacheConfig


class TestCacheKey:
    """Test cache key generation."""

    def test_consistent_keys(self):
        """Same inputs produce same key."""
        key1 = make_cache_key("layer", "context", "prompt", "model")
        key2 = make_cache_key("layer", "context", "prompt", "model")
        assert key1 == key2

    def test_different_keys(self):
        """Different inputs produce different keys."""
        key1 = make_cache_key("layer1", "context", "prompt", "model")
        key2 = make_cache_key("layer2", "context", "prompt", "model")
        assert key1 != key2

    def test_model_matters(self):
        """Different models produce different keys."""
        key1 = make_cache_key("layer", "context", "prompt", "model1")
        key2 = make_cache_key("layer", "context", "prompt", "model2")
        assert key1 != key2


class TestMemoryCache:
    """Test in-memory cache implementation."""

    def test_basic_get_set(self):
        """Can store and retrieve values."""
        cache = MemoryCache()
        key = "test_key"
        value = CachedEvaluation(
            truth=0.8,
            indeterminacy=0.3,
            falsehood=0.1,
            model="test-model",
            timestamp=time.time(),
            ttl_seconds=3600
        )

        cache.set(key, value)
        retrieved = cache.get(key)

        assert retrieved is not None
        assert retrieved.truth == 0.8
        assert retrieved.model == "test-model"

    def test_missing_key(self):
        """Returns None for missing keys."""
        cache = MemoryCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        """Expired entries return None."""
        cache = MemoryCache()
        key = "expiring_key"
        value = CachedEvaluation(
            truth=0.5,
            indeterminacy=0.5,
            falsehood=0.0,
            model="test-model",
            timestamp=time.time() - 100,  # 100 seconds ago
            ttl_seconds=10  # 10 second TTL
        )

        cache.set(key, value)
        retrieved = cache.get(key)

        assert retrieved is None  # Should be expired

    def test_clear(self):
        """Clear removes all entries."""
        cache = MemoryCache()
        cache.set("key1", CachedEvaluation(0.5, 0.5, 0.0, "m", time.time(), 3600))
        cache.set("key2", CachedEvaluation(0.5, 0.5, 0.0, "m", time.time(), 3600))

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestDiskCache:
    """Test disk-based cache implementation."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_basic_get_set(self, temp_cache_dir):
        """Can store and retrieve values."""
        cache = DiskCache(temp_cache_dir)
        key = "test_key"
        value = CachedEvaluation(
            truth=0.8,
            indeterminacy=0.3,
            falsehood=0.1,
            model="test-model",
            timestamp=time.time(),
            ttl_seconds=3600
        )

        cache.set(key, value)
        retrieved = cache.get(key)

        assert retrieved is not None
        assert retrieved.truth == 0.8
        assert retrieved.model == "test-model"

    def test_persistence(self, temp_cache_dir):
        """Cache persists across instances."""
        key = "persistent_key"
        value = CachedEvaluation(0.9, 0.2, 0.05, "model", time.time(), 3600)

        # Write with first instance
        cache1 = DiskCache(temp_cache_dir)
        cache1.set(key, value)

        # Read with second instance
        cache2 = DiskCache(temp_cache_dir)
        retrieved = cache2.get(key)

        assert retrieved is not None
        assert retrieved.truth == 0.9

    def test_ttl_expiration(self, temp_cache_dir):
        """Expired entries return None and are deleted."""
        cache = DiskCache(temp_cache_dir)
        key = "expiring_key"
        value = CachedEvaluation(
            truth=0.5,
            indeterminacy=0.5,
            falsehood=0.0,
            model="test-model",
            timestamp=time.time() - 100,
            ttl_seconds=10
        )

        cache.set(key, value)
        retrieved = cache.get(key)

        assert retrieved is None
        # File should be deleted
        assert not (temp_cache_dir / f"{key}.json").exists()

    def test_clear(self, temp_cache_dir):
        """Clear removes all cache files."""
        cache = DiskCache(temp_cache_dir)
        cache.set("key1", CachedEvaluation(0.5, 0.5, 0.0, "m", time.time(), 3600))
        cache.set("key2", CachedEvaluation(0.5, 0.5, 0.0, "m", time.time(), 3600))

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert len(list(temp_cache_dir.glob("*.json"))) == 0


class TestLLMEvaluatorCaching:
    """Test that LLMEvaluator properly uses cache."""

    @pytest.fixture
    def cache_config(self):
        """Memory cache config for testing."""
        return CacheConfig(
            enabled=True,
            backend="memory",
            ttl_seconds=3600
        )

    @pytest.fixture
    def eval_config_with_cache(self, cache_config):
        """Evaluation config with caching enabled."""
        return EvaluationConfig(
            mode=EvaluationMode.SINGLE,
            models=["anthropic/claude-3.5-sonnet"],
            cache_config=cache_config
        )

    @pytest.mark.asyncio
    async def test_cache_reduces_calls(self, eval_config_with_cache, monkeypatch):
        """Cache hits reduce API calls."""
        call_count = 0

        async def mock_call_openrouter(self, model, messages):
            nonlocal call_count
            call_count += 1
            return '{"truth": 0.8, "indeterminacy": 0.3, "falsehood": 0.1, "reasoning": "test"}'

        # Patch the API call
        monkeypatch.setattr(
            "promptguard.evaluation.evaluator.LLMEvaluator._call_openrouter",
            mock_call_openrouter
        )

        evaluator = LLMEvaluator(eval_config_with_cache)

        # First call - should hit API
        result1 = await evaluator.evaluate_layer(
            layer_content="test prompt",
            context="test context",
            evaluation_prompt="evaluate this"
        )

        assert call_count == 1
        assert result1[0].truth == 0.8

        # Second call with same inputs - should hit cache
        result2 = await evaluator.evaluate_layer(
            layer_content="test prompt",
            context="test context",
            evaluation_prompt="evaluate this"
        )

        assert call_count == 1  # No additional API call
        assert result2[0].truth == 0.8
        assert result2[0].reasoning == "[CACHED]"

    @pytest.mark.asyncio
    async def test_cache_disabled(self, monkeypatch):
        """Cache can be disabled."""
        call_count = 0

        async def mock_call_openrouter(self, model, messages):
            nonlocal call_count
            call_count += 1
            return '{"truth": 0.8, "indeterminacy": 0.3, "falsehood": 0.1, "reasoning": "test"}'

        monkeypatch.setattr(
            "promptguard.evaluation.evaluator.LLMEvaluator._call_openrouter",
            mock_call_openrouter
        )

        # Disable caching
        cache_config = CacheConfig(enabled=False)
        eval_config = EvaluationConfig(
            mode=EvaluationMode.SINGLE,
            models=["anthropic/claude-3.5-sonnet"],
            cache_config=cache_config
        )

        evaluator = LLMEvaluator(eval_config)

        # First call
        await evaluator.evaluate_layer(
            layer_content="test prompt",
            context="test context",
            evaluation_prompt="evaluate this"
        )
        assert call_count == 1

        # Second call - should NOT use cache
        await evaluator.evaluate_layer(
            layer_content="test prompt",
            context="test context",
            evaluation_prompt="evaluate this"
        )
        assert call_count == 2  # Additional API call

    @pytest.mark.asyncio
    async def test_parallel_caching(self, monkeypatch):
        """Parallel mode caches per-model results."""
        call_count = 0

        async def mock_call_openrouter(self, model, messages):
            nonlocal call_count
            call_count += 1
            return '{"truth": 0.8, "indeterminacy": 0.3, "falsehood": 0.1, "reasoning": "test"}'

        monkeypatch.setattr(
            "promptguard.evaluation.evaluator.LLMEvaluator._call_openrouter",
            mock_call_openrouter
        )

        cache_config = CacheConfig(enabled=True, backend="memory", ttl_seconds=3600)
        eval_config = EvaluationConfig(
            mode=EvaluationMode.PARALLEL,
            models=["model1", "model2", "model3"],
            cache_config=cache_config
        )

        evaluator = LLMEvaluator(eval_config)

        # First call - all 3 models should hit API
        result1 = await evaluator.evaluate_layer(
            layer_content="test prompt",
            context="test context",
            evaluation_prompt="evaluate this"
        )

        assert call_count == 3
        assert len(result1) == 3

        # Second call - all should hit cache
        result2 = await evaluator.evaluate_layer(
            layer_content="test prompt",
            context="test context",
            evaluation_prompt="evaluate this"
        )

        assert call_count == 3  # No additional calls
        assert len(result2) == 3
        assert all(r.reasoning == "[CACHED]" for r in result2)


class TestCacheSizeManagement:
    """Test cache size limits and eviction."""

    @pytest.fixture
    def small_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_size_calculation(self, small_cache_dir):
        """Cache reports size correctly."""
        cache = DiskCache(small_cache_dir, max_size_mb=1)

        # Empty cache
        assert cache.size_mb() == 0.0

        # Add some entries
        for i in range(10):
            cache.set(f"key_{i}", CachedEvaluation(
                0.5, 0.5, 0.0, "model", time.time(), 3600
            ))

        # Should have some size
        assert cache.size_mb() > 0.0

    def test_eviction_on_size_limit(self, small_cache_dir):
        """Cache evicts oldest entries when size limit reached."""
        # Very small cache - 0.01 MB
        cache = DiskCache(small_cache_dir, max_size_mb=0.01)

        # Add many entries to exceed limit
        for i in range(100):
            cache.set(f"key_{i}", CachedEvaluation(
                0.5, 0.5, 0.0, "model", time.time(), 3600
            ))

        # Cache should stay under limit
        assert cache.size_mb() <= 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
