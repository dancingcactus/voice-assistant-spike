"""
Caching Layer for Phase 4.5 Performance Optimization.

This module provides a simple caching mechanism for frequently accessed
configuration files and data to reduce file I/O and improve response times.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConfigCache:
    """
    Simple in-memory cache with time-based TTL for configuration files.
    
    Thread-safe for reading (writes are atomic dict updates).
    """
    
    def __init__(self, default_ttl_seconds: int = 3600):
        """
        Initialize the cache.
        
        Args:
            default_ttl_seconds: Default time-to-live for cache entries (default: 1 hour)
        """
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_time)
        logger.info(f"ConfigCache initialized with default TTL={default_ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            return None
        
        value, expiry_time = self._cache[key]
        
        # Check if expired
        if time.time() > expiry_time:
            logger.debug(f"Cache miss (expired): {key}")
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit: {key}")
        return value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional custom TTL (uses default if not provided)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expiry_time = time.time() + ttl
        
        self._cache[key] = (value, expiry_time)
        logger.debug(f"Cache set: {key} (TTL={ttl}s)")
    
    def invalidate(self, key: str):
        """
        Remove a specific key from the cache.
        
        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache invalidated: {key}")
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        now = time.time()
        valid_entries = sum(1 for _, expiry in self._cache.values() if expiry > now)
        
        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self._cache) - valid_entries,
            "default_ttl_seconds": self.default_ttl
        }


class CachedFileLoader:
    """
    Helper class for loading and caching JSON configuration files.
    """
    
    def __init__(self, cache: ConfigCache, base_path: Optional[Path] = None):
        """
        Initialize the file loader.
        
        Args:
            cache: ConfigCache instance to use
            base_path: Optional base directory for relative paths
        """
        self.cache = cache
        self.base_path = base_path or Path(__file__).parent.parent.parent
        logger.info(f"CachedFileLoader initialized with base_path={self.base_path}")
    
    def load_json(
        self,
        file_path: str,
        cache_key: Optional[str] = None,
        ttl_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Load a JSON file with caching.
        
        Args:
            file_path: Path to JSON file (relative to base_path or absolute)
            cache_key: Optional custom cache key (uses file_path if not provided)
            ttl_seconds: Optional custom TTL for this file
            
        Returns:
            Parsed JSON data as dictionary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        cache_key = cache_key or f"json:{file_path}"
        
        # Check cache first
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Load from file
        full_path = self.base_path / file_path if not Path(file_path).is_absolute() else Path(file_path)
        
        logger.debug(f"Loading JSON file: {full_path}")
        
        if not full_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Cache the data
        self.cache.set(cache_key, data, ttl_seconds)
        
        logger.info(f"Loaded and cached JSON file: {file_path}")
        return data
    
    def load_character_config(self, character_id: str) -> Dict[str, Any]:
        """
        Load a character configuration file.
        
        Args:
            character_id: Character identifier (e.g., "delilah", "hank")
            
        Returns:
            Character configuration dictionary
        """
        file_path = f"story/characters/{character_id}.json"
        cache_key = f"character_config:{character_id}"
        return self.load_json(file_path, cache_key=cache_key, ttl_seconds=3600)
    
    def load_story_beats(self, chapter_id: int) -> Dict[str, Any]:
        """
        Load story beat definitions for a chapter.
        
        Args:
            chapter_id: Chapter number
            
        Returns:
            Story beat definitions
        """
        file_path = f"story/beats/chapter_{chapter_id}.json"
        cache_key = f"story_beats:chapter_{chapter_id}"
        return self.load_json(file_path, cache_key=cache_key, ttl_seconds=3600)
    
    def load_intent_patterns(self) -> Dict[str, Any]:
        """
        Load intent pattern definitions.
        
        Returns:
            Intent patterns dictionary
        """
        file_path = "backend/src/config/intent_patterns.json"
        cache_key = "intent_patterns"
        return self.load_json(file_path, cache_key=cache_key, ttl_seconds=600)
    
    def load_character_relationships(self) -> Dict[str, Any]:
        """
        Load character relationship definitions.
        
        Returns:
            Character relationships dictionary
        """
        file_path = "story/characters/relationships.json"
        cache_key = "character_relationships"
        return self.load_json(file_path, cache_key=cache_key, ttl_seconds=3600)
    
    def load_character_assignments(self) -> Dict[str, Any]:
        """
        Load character assignment rules.
        
        Returns:
            Character assignment rules dictionary
        """
        file_path = "backend/src/config/character_assignments.json"
        cache_key = "character_assignments"
        return self.load_json(file_path, cache_key=cache_key, ttl_seconds=3600)


# Global cache instance (singleton pattern)
_global_cache: Optional[ConfigCache] = None
_global_file_loader: Optional[CachedFileLoader] = None


def get_global_cache() -> ConfigCache:
    """Get or create the global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = ConfigCache(default_ttl_seconds=3600)
        logger.info("Global ConfigCache created")
    return _global_cache


def get_file_loader() -> CachedFileLoader:
    """Get or create the global file loader instance."""
    global _global_file_loader
    if _global_file_loader is None:
        cache = get_global_cache()
        _global_file_loader = CachedFileLoader(cache)
        logger.info("Global CachedFileLoader created")
    return _global_file_loader


def clear_global_cache():
    """Clear the global cache (useful for testing)."""
    cache = get_global_cache()
    cache.clear()
    logger.info("Global cache cleared")
