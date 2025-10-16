"""
Redis-based caching layer for genealogical computations.

Provides high-performance caching for expensive operations:
- Consanguinity calculations
- Relationship paths
- Sosa numbers
- Tree data
- Search results

Features:
- TTL-based cache expiration
- Cache invalidation strategies
- Distributed caching support
- Cache statistics and monitoring
"""

import hashlib
import json
import pickle
from functools import wraps
from typing import Any, Callable, Optional

try:
    import redis
    from redis import Redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = None


class CacheConfig:
    """Cache configuration."""

    # TTL values (in seconds)
    TTL_CONSANGUINITY = 3600  # 1 hour
    TTL_RELATIONSHIP = 1800  # 30 minutes
    TTL_SOSA = 7200  # 2 hours
    TTL_TREE = 1800  # 30 minutes
    TTL_SEARCH = 600  # 10 minutes
    TTL_STATISTICS = 900  # 15 minutes

    # Cache key prefixes
    PREFIX_CONSANGUINITY = "consang"
    PREFIX_RELATIONSHIP = "rel"
    PREFIX_SOSA = "sosa"
    PREFIX_TREE = "tree"
    PREFIX_SEARCH = "search"
    PREFIX_STATISTICS = "stats"


class RedisCache:
    """
    Redis-based cache implementation.
    
    Provides get/set/delete operations with automatic serialization.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = False,
    ):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (if required)
            decode_responses: Whether to decode responses as strings
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis is not installed. "
                "Install with: pip install redis"
            )

        self.client = Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=decode_responses,
        )

        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            value = self.client.get(key)

            if value is None:
                self.stats["misses"] += 1
                return None

            self.stats["hits"] += 1

            # Deserialize
            return pickle.loads(value)

        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful
        """
        try:
            # Serialize
            serialized = pickle.dumps(value)

            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)

            self.stats["sets"] += 1
            return True

        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        try:
            self.client.delete(key)
            self.stats["deletes"] += 1
            return True

        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "consang:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = self.client.keys(pattern)
            if keys:
                count = self.client.delete(*keys)
                self.stats["deletes"] += count
                return count
            return 0

        except Exception as e:
            print(f"Cache delete pattern error: {e}")
            return 0

    def clear_all(self) -> bool:
        """Clear all cache entries."""
        try:
            self.client.flushdb()
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            self.stats["hits"] / total_requests if total_requests > 0 else 0
        )

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"],
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }


class InMemoryCache:
    """
    Simple in-memory cache (fallback when Redis unavailable).
    
    Uses Python dict for storage. Not distributed.
    """

    def __init__(self):
        """Initialize in-memory cache."""
        self.cache = {}
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            self.stats["hits"] += 1
            return self.cache[key]

        self.stats["misses"] += 1
        return None

    def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache (TTL ignored in memory cache)."""
        self.cache[key] = value
        self.stats["sets"] += 1
        return True

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            self.stats["deletes"] += 1
            return True
        return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern."""
        # Simple pattern matching (supports * at end)
        pattern_base = pattern.rstrip("*")
        keys_to_delete = [k for k in self.cache if k.startswith(pattern_base)]

        count = 0
        for key in keys_to_delete:
            if self.delete(key):
                count += 1

        return count

    def clear_all(self) -> bool:
        """Clear all cache."""
        self.cache.clear()
        return True

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            self.stats["hits"] / total_requests if total_requests > 0 else 0
        )

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"],
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "size": len(self.cache),
        }


# Global cache instance
_cache_instance = None


def get_cache(
    use_redis: bool = True,
    redis_host: str = "localhost",
    redis_port: int = 6379,
):
    """
    Get cache instance (singleton).
    
    Args:
        use_redis: Whether to use Redis (fallback to in-memory)
        redis_host: Redis host
        redis_port: Redis port
        
    Returns:
        Cache instance
    """
    global _cache_instance

    if _cache_instance is None:
        if use_redis and REDIS_AVAILABLE:
            try:
                _cache_instance = RedisCache(host=redis_host, port=redis_port)
            except Exception as e:
                print(f"Redis connection failed: {e}")
                print("Falling back to in-memory cache")
                _cache_instance = InMemoryCache()
        else:
            _cache_instance = InMemoryCache()

    return _cache_instance


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Create unique key from arguments
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items()),
    }

    key_json = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.sha256(key_json.encode()).hexdigest()

    return key_hash


def cached(prefix: str, ttl: Optional[int] = None):
    """
    Decorator for caching function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        
    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_hash = cache_key(*args, **kwargs)
            full_key = f"{prefix}:{key_hash}"

            # Try to get from cache
            cache = get_cache()
            cached_value = cache.get(full_key)

            if cached_value is not None:
                return cached_value

            # Call function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(full_key, result, ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache(prefix: str, *args, **kwargs) -> None:
    """
    Invalidate specific cache entry.
    
    Args:
        prefix: Cache key prefix
        *args: Function arguments
        **kwargs: Function keyword arguments
    """
    cache = get_cache()
    key_hash = cache_key(*args, **kwargs)
    full_key = f"{prefix}:{key_hash}"
    cache.delete(full_key)


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate all cache entries matching pattern.
    
    Args:
        pattern: Cache key pattern (e.g., "consang:*")
        
    Returns:
        Number of entries invalidated
    """
    cache = get_cache()
    return cache.delete_pattern(pattern)


# Convenience decorators for specific use cases
def cache_consanguinity(ttl: int = CacheConfig.TTL_CONSANGUINITY):
    """Cache consanguinity calculations."""
    return cached(CacheConfig.PREFIX_CONSANGUINITY, ttl)


def cache_relationship(ttl: int = CacheConfig.TTL_RELATIONSHIP):
    """Cache relationship calculations."""
    return cached(CacheConfig.PREFIX_RELATIONSHIP, ttl)


def cache_sosa(ttl: int = CacheConfig.TTL_SOSA):
    """Cache Sosa number calculations."""
    return cached(CacheConfig.PREFIX_SOSA, ttl)


def cache_tree(ttl: int = CacheConfig.TTL_TREE):
    """Cache tree data."""
    return cached(CacheConfig.PREFIX_TREE, ttl)


def cache_search(ttl: int = CacheConfig.TTL_SEARCH):
    """Cache search results."""
    return cached(CacheConfig.PREFIX_SEARCH, ttl)


# Example usage:
# @cache_consanguinity()
# def calculate_consanguinity(person_id: int) -> float:
#     # Expensive calculation
#     return result
