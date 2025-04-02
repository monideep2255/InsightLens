import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from diskcache import Cache
from cachetools import LRUCache, TTLCache

logger = logging.getLogger(__name__)

# Configure cache directory
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# Disk cache for document content and responses (persistent)
disk_cache = Cache(CACHE_DIR)

# In-memory cache for frequently accessed items (non-persistent)
# TTL of 1 hour for API responses
memory_cache = TTLCache(maxsize=100, ttl=3600)

def generate_content_hash(content):
    """
    Generate a hash for document content to use as a cache key
    """
    # Use only the first 50KB of the document for the hash to improve performance
    # while still being unique enough for most documents
    sample = content[:50000]
    return hashlib.md5(sample.encode('utf-8')).hexdigest()

def get_cached_ai_response(content, prompt_template, model_type):
    """
    Check if we have a cached response for this content and prompt
    
    Args:
        content (str): The document content
        prompt_template (str): The prompt template used
        model_type (str): The AI model type (e.g., "huggingface", "openai")
        
    Returns:
        dict or None: The cached insights if available, None otherwise
    """
    try:
        # Generate a cache key
        content_hash = generate_content_hash(content)
        # Include prompt template and model type in the key for version control
        prompt_hash = hashlib.md5(prompt_template.encode('utf-8')).hexdigest()[:8]
        cache_key = f"ai_response:{model_type}:{content_hash}:{prompt_hash}"
        
        # First check in-memory cache (faster)
        if cache_key in memory_cache:
            logger.info(f"Found in memory cache: {cache_key}")
            return memory_cache[cache_key]
        
        # Then check disk cache
        if cache_key in disk_cache:
            result = disk_cache[cache_key]
            logger.info(f"Found in disk cache: {cache_key}")
            # Also store in memory cache for faster access next time
            memory_cache[cache_key] = result
            return result
            
        return None
    except Exception as e:
        logger.error(f"Error checking cache: {str(e)}")
        return None

def save_ai_response(content, prompt_template, model_type, insights):
    """
    Save an AI response to the cache
    
    Args:
        content (str): The document content
        prompt_template (str): The prompt template used
        model_type (str): The AI model type (e.g., "huggingface", "openai")
        insights (dict): The generated insights
    """
    try:
        # Generate a cache key
        content_hash = generate_content_hash(content)
        prompt_hash = hashlib.md5(prompt_template.encode('utf-8')).hexdigest()[:8]
        cache_key = f"ai_response:{model_type}:{content_hash}:{prompt_hash}"
        
        # Store in both caches
        disk_cache[cache_key] = insights
        memory_cache[cache_key] = insights
        
        logger.info(f"Cached AI response: {cache_key}")
        return True
    except Exception as e:
        logger.error(f"Error saving to cache: {str(e)}")
        return False

def clear_old_cache_entries(max_age_days=7):
    """
    Clear cache entries older than specified days
    
    Args:
        max_age_days (int): Maximum age of cache entries in days
    """
    try:
        count = 0
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        for key in list(disk_cache.iterkeys()):
            # Check the access time of the cache entry
            stats = disk_cache.stats(key)
            if stats and stats.get('access_time') and datetime.fromtimestamp(stats['access_time']) < cutoff_time:
                disk_cache.pop(key, None)
                count += 1
        
        logger.info(f"Cleared {count} old cache entries")
        return count
    except Exception as e:
        logger.error(f"Error clearing old cache entries: {str(e)}")
        return 0

def get_cache_stats():
    """
    Get statistics about the cache
    
    Returns:
        dict: Cache statistics
    """
    try:
        size = len(disk_cache)
        total_size = sum(disk_cache.volume() for _ in range(1))  # Get disk volume
        memory_size = len(memory_cache)
        
        return {
            "disk_entries": size,
            "disk_size_mb": total_size / (1024 * 1024),
            "memory_entries": memory_size
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {
            "disk_entries": 0,
            "disk_size_mb": 0,
            "memory_entries": 0,
            "error": str(e)
        }