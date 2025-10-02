"""
Caching layer for LLM evaluation results.

Provides abstraction over cache backends (disk, SQLite, memory) with
support for TTL expiration and size limits.
"""

from typing import Protocol, Optional, Dict
from dataclasses import dataclass, asdict
import json
import hashlib
import time
from pathlib import Path
import shutil


@dataclass
class CachedEvaluation:
    """Cached evaluation result with metadata."""
    truth: float
    indeterminacy: float
    falsehood: float
    model: str
    timestamp: float
    ttl_seconds: int

    def is_expired(self) -> bool:
        """Check if this cached result has expired."""
        age = time.time() - self.timestamp
        return age > self.ttl_seconds


class CacheProvider(Protocol):
    """Protocol for cache backend implementations."""

    def get(self, key: str) -> Optional[CachedEvaluation]:
        """Retrieve cached evaluation by key."""
        ...

    def set(self, key: str, value: CachedEvaluation) -> None:
        """Store evaluation with TTL."""
        ...

    def clear(self) -> None:
        """Clear all cached entries."""
        ...

    def size_mb(self) -> float:
        """Get current cache size in MB."""
        ...


class DiskCache:
    """
    Disk-based cache using JSON files.

    Each cache entry is a separate JSON file named by hash.
    Simple, debuggable, suitable for small-to-medium scale testing.
    """

    def __init__(self, cache_dir: Path, max_size_mb: int = 100):
        """
        Initialize disk cache.

        Args:
            cache_dir: Directory to store cache files
            max_size_mb: Maximum cache size before eviction
        """
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        """Get filesystem path for cache key."""
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> Optional[CachedEvaluation]:
        """Retrieve cached evaluation by key."""
        cache_file = self._cache_path(key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            cached = CachedEvaluation(**data)

            # Check expiration
            if cached.is_expired():
                cache_file.unlink()  # Delete expired entry
                return None

            return cached

        except (json.JSONDecodeError, TypeError, KeyError):
            # Corrupt cache file - delete it
            cache_file.unlink(missing_ok=True)
            return None

    def set(self, key: str, value: CachedEvaluation) -> None:
        """Store evaluation with TTL."""
        # Check size limits before writing
        if self.size_mb() > self.max_size_mb:
            self._evict_oldest()

        cache_file = self._cache_path(key)

        with open(cache_file, 'w') as f:
            json.dump(asdict(value), f)

    def clear(self) -> None:
        """Clear all cached entries."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

    def size_mb(self) -> float:
        """Get current cache size in MB."""
        total_bytes = sum(
            f.stat().st_size
            for f in self.cache_dir.glob("*.json")
            if f.is_file()
        )
        return total_bytes / (1024 * 1024)

    def _evict_oldest(self, target_mb: Optional[float] = None) -> None:
        """
        Evict oldest entries until size is below target.

        Args:
            target_mb: Target size in MB (default: 80% of max)
        """
        if target_mb is None:
            target_mb = self.max_size_mb * 0.8

        # Get all cache files sorted by modification time (oldest first)
        cache_files = sorted(
            self.cache_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime
        )

        # Delete oldest until under target
        for cache_file in cache_files:
            if self.size_mb() <= target_mb:
                break
            cache_file.unlink()


class MemoryCache:
    """
    In-memory cache for testing.

    Does not persist between runs. Useful for tests and development.
    """

    def __init__(self, max_size_mb: int = 100):
        """Initialize memory cache."""
        self.cache: Dict[str, CachedEvaluation] = {}
        self.max_size_mb = max_size_mb

    def get(self, key: str) -> Optional[CachedEvaluation]:
        """Retrieve cached evaluation by key."""
        if key not in self.cache:
            return None

        cached = self.cache[key]

        # Check expiration
        if cached.is_expired():
            del self.cache[key]
            return None

        return cached

    def set(self, key: str, value: CachedEvaluation) -> None:
        """Store evaluation with TTL."""
        # Simple eviction: clear everything if over size
        # (More sophisticated LRU could be added later)
        if self.size_mb() > self.max_size_mb:
            self.clear()

        self.cache[key] = value

    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()

    def size_mb(self) -> float:
        """
        Estimate cache size in MB.

        Rough approximation based on number of entries.
        Each entry ~100 bytes, so 10000 entries ≈ 1MB.
        """
        return len(self.cache) * 100 / (1024 * 1024)


def make_cache_key(
    layer_content: str,
    context: str,
    evaluation_prompt: str,
    model: str
) -> str:
    """
    Generate cache key for evaluation request.

    Uses SHA-256 hash of concatenated inputs for consistency.

    Args:
        layer_content: The layer being evaluated
        context: Full context including prior layers
        evaluation_prompt: The evaluation prompt template
        model: Model identifier

    Returns:
        Hex digest cache key
    """
    combined = f"{layer_content}|{context}|{evaluation_prompt}|{model}"
    return hashlib.sha256(combined.encode()).hexdigest()
