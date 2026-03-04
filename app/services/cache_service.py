"""
Cache Service
Implements intelligent caching for query results
"""
from typing import Optional, Dict, Any
from cachetools import LRUCache
import hashlib
import json

from app.config import get_settings


class CacheService:
    """Query result caching with LRU eviction"""
    
    def __init__(self):
        self.settings = get_settings()
        self.cache = LRUCache(maxsize=self.settings.cache_size)
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_cache_key(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k: int = 5
    ) -> str:
        """
        Generate cache key for query
        
        Args:
            query: Query text
            document_id: Optional document filter
            top_k: Number of results
            
        Returns:
            Cache key hash
        """
        cache_data = {
            "query": query.lower().strip(),
            "document_id": document_id,
            "top_k": top_k
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached result
        
        Args:
            query: Query text
            document_id: Optional document filter
            top_k: Number of results
            
        Returns:
            Cached result or None
        """
        cache_key = self._generate_cache_key(query, document_id, top_k)
        result = self.cache.get(cache_key)
        
        if result is not None:
            self.hit_count += 1
            return result
        else:
            self.miss_count += 1
            return None
    
    def set(
        self,
        query: str,
        result: Dict[str, Any],
        document_id: Optional[str] = None,
        top_k: int = 5
    ):
        """
        Cache query result
        
        Args:
            query: Query text
            result: Result to cache
            document_id: Optional document filter
            top_k: Number of results
        """
        cache_key = self._generate_cache_key(query, document_id, top_k)
        self.cache[cache_key] = result
    
    def invalidate_document(self, document_id: str):
        """
        Invalidate cache entries for a document
        
        Args:
            document_id: Document ID
        """
        # Find and remove cache entries containing this document
        keys_to_remove = []
        for key in self.cache.keys():
            # This is a simple implementation; more sophisticated tracking could be added
            cached_value = self.cache[key]
            if isinstance(cached_value, dict) and cached_value.get('document_id') == document_id:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.cache.maxsize,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": round(hit_rate, 3)
        }


# Singleton instance
_cache_service = None

def get_cache_service() -> CacheService:
    """Get cache service singleton"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
