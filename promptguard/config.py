"""
Configuration management for PromptGuard.

Handles cache settings, API configuration, and runtime overrides.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import os


@dataclass
class CacheConfig:
    """Configuration for evaluation result caching."""

    enabled: bool = True
    backend: str = "disk"  # "disk", "sqlite", "memory"
    location: Optional[Path] = None  # None = auto-detect
    ttl_seconds: int = 604800  # 7 days default
    max_size_mb: int = 100  # Disk usage limit

    def __post_init__(self):
        """Auto-detect cache location if not specified."""
        if self.location is None:
            # Prefer project-local .promptguard/cache if exists
            project_cache = Path.cwd() / ".promptguard" / "cache"

            # Otherwise use user home directory
            home_cache = Path.home() / ".promptguard" / "cache"

            # Use project cache if .promptguard directory exists
            if (Path.cwd() / ".promptguard").exists():
                self.location = project_cache
            else:
                self.location = home_cache

        # Ensure location is Path object
        if isinstance(self.location, str):
            self.location = Path(self.location)

    def override(self, **kwargs) -> "CacheConfig":
        """
        Create new config with overridden values.

        Usage:
            config = CacheConfig()
            test_config = config.override(ttl_seconds=60, backend="memory")
        """
        overrides = {
            "enabled": kwargs.get("enabled", self.enabled),
            "backend": kwargs.get("backend", self.backend),
            "location": kwargs.get("location", self.location),
            "ttl_seconds": kwargs.get("ttl_seconds", self.ttl_seconds),
            "max_size_mb": kwargs.get("max_size_mb", self.max_size_mb),
        }
        return CacheConfig(**overrides)
