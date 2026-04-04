"""
速率限制模块单元测试
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.rate_limit import RateLimiter


# Mock Request对象
MockClient = namedtuple('MockClient', ['host'])


class MockRequest:
    def __init__(self, path="/api/test", client_ip="127.0.0.1", headers=None):
        self.url = MagicMock()
        self.url.path = path
        self.client = MockClient(host=client_ip)
        self.headers = headers or {}
    
    def __hash__(self):
        return id(self)


class TestRateLimiter:
    """速率限制器测试"""
    
    def test_whitelist_allowed(self):
        """测试白名单路径"""
        limiter = RateLimiter()
        request = MockRequest(path="/health")
        allowed, info = limiter.is_allowed(request)
        assert allowed is True
    
    def test_normal_request_allowed(self):
        """测试正常请求被允许"""
        limiter = RateLimiter()
        request = MockRequest(path="/api/v1/stocks")
        allowed, info = limiter.is_allowed(request)
        assert allowed is True
        assert info.get("remaining", 0) >= 0
    
    def test_rate_limit_exceeded(self):
        """测试超过速率限制"""
        limiter = RateLimiter()
        # 使用登录接口，限制为5次/分钟
        request = MockRequest(path="/api/auth/login", client_ip="192.168.1.1")
        
        # 发送5次请求（允许）
        for i in range(5):
            allowed, _ = limiter.is_allowed(request)
            assert allowed is True
        
        # 第6次应该被限制
        allowed, info = limiter.is_allowed(request)
        assert allowed is False
        assert info.get("remaining") == 0
    
    def test_different_clients_independent(self):
        """测试不同客户端独立计数"""
        limiter = RateLimiter()
        request1 = MockRequest(path="/api/auth/login", client_ip="192.168.1.1")
        request2 = MockRequest(path="/api/auth/login", client_ip="192.168.1.2")
        
        # 客户端1发送5次
        for _ in range(5):
            limiter.is_allowed(request1)
        
        # 客户端2应该仍然被允许
        allowed, _ = limiter.is_allowed(request2)
        assert allowed is True
    
    def test_route_specific_limits(self):
        """测试路由特定限制"""
        limiter = RateLimiter()
        
        # 爬虫接口限制更严格
        config = limiter._get_route_config("/api/v1/crawler/start")
        assert config["limit"] == 5
        assert config["window"] == 300
        
        # 股票接口限制宽松
        config = limiter._get_route_config("/api/v1/stocks")
        assert config["limit"] == 60
    
    def test_get_client_key_ip(self):
        """测试获取客户端key（IP）"""
        limiter = RateLimiter()
        request = MockRequest(client_ip="192.168.1.100")
        key = limiter._get_client_key(request)
        assert "192.168.1.100" in key
    
    def test_get_client_key_forwarded(self):
        """测试获取客户端key（X-Forwarded-For）"""
        limiter = RateLimiter()
        request = MockRequest(
            client_ip="127.0.0.1",
            headers={"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        )
        key = limiter._get_client_key(request)
        assert "10.0.0.1" in key
    
    def test_get_client_key_with_token(self):
        """测试获取客户端key（带Token）"""
        limiter = RateLimiter()
        request = MockRequest(
            headers={"Authorization": "Bearer test_token_123"}
        )
        key = limiter._get_client_key(request)
        assert "user:" in key
    
    def test_response_headers(self):
        """测试响应头信息"""
        limiter = RateLimiter()
        request = MockRequest(path="/api/v1/stocks")
        allowed, info = limiter.is_allowed(request)
        
        assert "limit" in info
        assert "remaining" in info
        assert "reset" in info
        assert "window" in info


class TestRateLimiterCleanup:
    """速率限制器清理测试"""
    
    def test_old_requests_cleaned(self):
        """测试过期请求被清理"""
        limiter = RateLimiter()
        client_key = "ip:test_cleanup"
        
        # 模拟添加旧请求
        import time
        old_time = time.time() - 120  # 2分钟前
        limiter.requests[client_key] = [(old_time, 1)]
        
        # 清理
        limiter._clean_old_requests(client_key, window=60)
        
        # 应该被清理
        assert len(limiter.requests[client_key]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
