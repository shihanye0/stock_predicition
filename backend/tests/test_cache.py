"""
缓存模块单元测试
"""
import pytest
import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.cache import (
    MemoryCache, 
    CacheManager, 
    cached, 
    generate_cache_key,
    CacheKeys
)


class TestMemoryCache:
    """内存缓存测试"""
    
    def test_set_and_get(self):
        """测试设置和获取"""
        cache = MemoryCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_get_nonexistent(self):
        """测试获取不存在的key"""
        cache = MemoryCache()
        assert cache.get("nonexistent") is None
    
    def test_delete(self):
        """测试删除"""
        cache = MemoryCache()
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_ttl_expiry(self):
        """测试TTL过期"""
        cache = MemoryCache()
        cache.set("key1", "value1", ttl=1)
        assert cache.get("key1") == "value1"
        time.sleep(1.5)
        assert cache.get("key1") is None
    
    def test_lru_eviction(self):
        """测试LRU淘汰"""
        cache = MemoryCache(max_size=3)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        # 添加第四个，应该淘汰key1
        cache.set("key4", "value4")
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
    
    def test_exists(self):
        """测试exists方法"""
        cache = MemoryCache()
        cache.set("key1", "value1")
        assert cache.exists("key1") is True
        assert cache.exists("key2") is False
    
    def test_clear(self):
        """测试清空缓存"""
        cache = MemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_complex_data(self):
        """测试复杂数据类型"""
        cache = MemoryCache()
        data = {
            "list": [1, 2, 3],
            "dict": {"a": 1, "b": 2},
            "nested": {"x": [1, 2, {"y": 3}]}
        }
        cache.set("complex", data)
        assert cache.get("complex") == data


class TestCacheManager:
    """缓存管理器测试"""
    
    def test_set_and_get(self):
        """测试基本设置和获取"""
        manager = CacheManager()
        manager.set("test_key", {"data": 123})
        result = manager.get("test_key")
        assert result == {"data": 123}
    
    def test_delete(self):
        """测试删除"""
        manager = CacheManager()
        manager.set("test_key", "value")
        manager.delete("test_key")
        assert manager.get("test_key") is None
    
    def test_exists(self):
        """测试exists"""
        manager = CacheManager()
        manager.set("test_key", "value")
        assert manager.exists("test_key") is True
        assert manager.exists("nonexistent") is False
    
    def test_get_stats(self):
        """测试获取统计信息"""
        manager = CacheManager()
        stats = manager.get_stats()
        assert "backend" in stats
        assert stats["backend"] in ["redis", "memory"]


class TestCachedDecorator:
    """缓存装饰器测试"""
    
    def test_cached_decorator(self):
        """测试缓存装饰器"""
        call_count = 0
        
        @cached(ttl=10, prefix="test")
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # 第一次调用
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # 第二次调用（应该命中缓存）
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # 没有增加
        
        # 不同参数（缓存未命中）
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2


class TestGenerateCacheKey:
    """缓存key生成测试"""
    
    def test_same_args_same_key(self):
        """相同参数生成相同key"""
        key1 = generate_cache_key("arg1", "arg2", kwarg1="value1")
        key2 = generate_cache_key("arg1", "arg2", kwarg1="value1")
        assert key1 == key2
    
    def test_different_args_different_key(self):
        """不同参数生成不同key"""
        key1 = generate_cache_key("arg1")
        key2 = generate_cache_key("arg2")
        assert key1 != key2
    
    def test_order_matters(self):
        """参数顺序影响key"""
        key1 = generate_cache_key("a", "b")
        key2 = generate_cache_key("b", "a")
        assert key1 != key2


class TestCacheKeys:
    """缓存key常量测试"""
    
    def test_ttl_values(self):
        """测试TTL值"""
        assert CacheKeys.TTL_SHORT == 60
        assert CacheKeys.TTL_MEDIUM == 300
        assert CacheKeys.TTL_LONG == 1800
        assert CacheKeys.TTL_HOUR == 3600
        assert CacheKeys.TTL_DAY == 86400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
