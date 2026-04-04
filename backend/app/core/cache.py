"""
缓存模块
支持Redis缓存，当Redis不可用时自动降级到内存缓存
"""
import json
import time
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
from collections import OrderedDict
from datetime import datetime, timedelta
from loguru import logger

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis package not installed, using memory cache only")

from app.core.config import settings


class MemoryCache:
    """
    内存缓存实现（LRU策略）
    当Redis不可用时作为降级方案
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.expires: dict = {}
    
    def _cleanup_expired(self):
        """清理过期数据"""
        now = time.time()
        expired_keys = [k for k, exp in self.expires.items() if exp < now]
        for key in expired_keys:
            self.cache.pop(key, None)
            self.expires.pop(key, None)
    
    def _evict_if_needed(self):
        """LRU淘汰"""
        while len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            self.cache.pop(oldest_key)
            self.expires.pop(oldest_key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        self._cleanup_expired()
        
        if key in self.cache:
            # 移到末尾（最近使用）
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存"""
        self._evict_if_needed()
        
        self.cache[key] = value
        self.cache.move_to_end(key)
        self.expires[key] = time.time() + ttl
    
    def delete(self, key: str):
        """删除缓存"""
        self.cache.pop(key, None)
        self.expires.pop(key, None)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.expires.clear()
    
    def exists(self, key: str) -> bool:
        """检查key是否存在"""
        self._cleanup_expired()
        return key in self.cache


class CacheManager:
    """
    统一缓存管理器
    优先使用Redis，不可用时降级到内存缓存
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache = MemoryCache(max_size=2000)
        self.use_redis = False
        self._connect_redis()
    
    def _connect_redis(self):
        """连接Redis"""
        if not REDIS_AVAILABLE:
            logger.info("Redis not available, using memory cache")
            return
        
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # 测试连接
            self.redis_client.ping()
            self.use_redis = True
            logger.info(f"Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, using memory cache")
            self.redis_client = None
            self.use_redis = False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            if self.use_redis and self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
                return None
        except Exception as e:
            logger.warning(f"Redis get error: {e}, fallback to memory")
            self.use_redis = False
        
        return self.memory_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """设置缓存"""
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value, ensure_ascii=False, default=str))
                return
        except Exception as e:
            logger.warning(f"Redis set error: {e}, fallback to memory")
            self.use_redis = False
        
        self.memory_cache.set(key, value, ttl)
    
    def delete(self, key: str):
        """删除缓存"""
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.delete(key)
                return
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")
        
        self.memory_cache.delete(key)
    
    def delete_pattern(self, pattern: str):
        """删除匹配模式的所有key"""
        try:
            if self.use_redis and self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                return
        except Exception as e:
            logger.warning(f"Redis delete pattern error: {e}")
        
        # 内存缓存模式匹配删除
        import fnmatch
        keys_to_delete = [k for k in self.memory_cache.cache.keys() 
                         if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_delete:
            self.memory_cache.delete(key)
    
    def exists(self, key: str) -> bool:
        """检查key是否存在"""
        try:
            if self.use_redis and self.redis_client:
                return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.warning(f"Redis exists error: {e}")
        
        return self.memory_cache.exists(key)
    
    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        stats = {
            "backend": "redis" if self.use_redis else "memory",
            "memory_cache_size": len(self.memory_cache.cache),
        }
        
        if self.use_redis and self.redis_client:
            try:
                info = self.redis_client.info("memory")
                stats["redis_used_memory"] = info.get("used_memory_human", "N/A")
                stats["redis_keys"] = self.redis_client.dbsize()
            except Exception:
                pass
        
        return stats


# 全局缓存管理器
cache_manager = CacheManager()


def generate_cache_key(*args, **kwargs) -> str:
    """生成缓存key"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 300, prefix: str = "cache"):
    """
    缓存装饰器
    
    用法:
        @cached(ttl=600, prefix="stock")
        def get_stock_data(code: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存key
            key = f"{prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # 尝试从缓存获取
            cached_value = cache_manager.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {key}")
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            if result is not None:
                cache_manager.set(key, result, ttl)
                logger.debug(f"Cache set: {key}")
            
            return result
        
        # 添加缓存清除方法
        def clear_cache(*args, **kwargs):
            key = f"{prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            cache_manager.delete(key)
        
        wrapper.clear_cache = clear_cache
        wrapper.cache_prefix = prefix
        
        return wrapper
    return decorator


def async_cached(ttl: int = 300, prefix: str = "cache"):
    """
    异步缓存装饰器
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            cached_value = cache_manager.get(key)
            if cached_value is not None:
                logger.debug(f"Async cache hit: {key}")
                return cached_value
            
            result = await func(*args, **kwargs)
            
            if result is not None:
                cache_manager.set(key, result, ttl)
                logger.debug(f"Async cache set: {key}")
            
            return result
        
        return wrapper
    return decorator


# 预定义的缓存配置
class CacheKeys:
    """缓存key前缀定义"""
    STOCK_DATA = "stock:data"
    STOCK_LIST = "stock:list"
    SENTIMENT = "sentiment"
    EMOTION = "emotion"
    MARKET_DATA = "market"
    USER = "user"
    
    # TTL配置（秒）
    TTL_SHORT = 60  # 1分钟
    TTL_MEDIUM = 300  # 5分钟
    TTL_LONG = 1800  # 30分钟
    TTL_HOUR = 3600  # 1小时
    TTL_DAY = 86400  # 1天


# 便捷函数
def cache_stock_data(stock_code: str, data: dict, ttl: int = CacheKeys.TTL_MEDIUM):
    """缓存股票数据"""
    key = f"{CacheKeys.STOCK_DATA}:{stock_code}"
    cache_manager.set(key, data, ttl)


def get_cached_stock_data(stock_code: str) -> Optional[dict]:
    """获取缓存的股票数据"""
    key = f"{CacheKeys.STOCK_DATA}:{stock_code}"
    return cache_manager.get(key)


def cache_emotion_result(stock_code: str, result: dict, ttl: int = CacheKeys.TTL_MEDIUM):
    """缓存情绪分析结果"""
    key = f"{CacheKeys.EMOTION}:{stock_code}"
    cache_manager.set(key, result, ttl)


def get_cached_emotion_result(stock_code: str) -> Optional[dict]:
    """获取缓存的情绪分析结果"""
    key = f"{CacheKeys.EMOTION}:{stock_code}"
    return cache_manager.get(key)


def invalidate_stock_cache(stock_code: str):
    """清除股票相关的所有缓存"""
    cache_manager.delete_pattern(f"*:{stock_code}*")
