"""
API速率限制模块
基于滑动窗口算法实现
"""
import time
from collections import defaultdict
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class RateLimiter:
    """
    速率限制器 - 滑动窗口算法
    """
    
    def __init__(self):
        # 存储请求记录: {client_key: [(timestamp, count), ...]}
        self.requests: dict = defaultdict(list)
        # 默认限制配置
        self.default_limit = 100  # 每个窗口最大请求数
        self.default_window = 60  # 窗口大小（秒）
        
        # 路由特定限制配置
        self.route_limits = {
            # 认证相关 - 严格限制防止暴力破解
            "/api/auth/login": {"limit": 10, "window": 60},
            "/api/auth/register": {"limit": 5, "window": 60},
            
            # 爬虫相关 - 允许正常操作
            "/api/v1/crawler/start": {"limit": 30, "window": 60},
            "/api/v1/crawler/stop": {"limit": 30, "window": 60},
            "/api/v1/crawler/status": {"limit": 60, "window": 60},
            "/api/v1/crawler/stats": {"limit": 60, "window": 60},
            
            # 情感分析 - 计算密集型
            "/api/v1/sentiment/analyze": {"limit": 30, "window": 60},
            "/api/v1/sentiment/batch": {"limit": 10, "window": 60},
            
            # 股票数据 - 允许较高频率
            "/api/v1/stocks": {"limit": 60, "window": 60},
            "/api/v1/emotion": {"limit": 60, "window": 60},
        }
        
        # 白名单路径（不限制）
        self.whitelist = [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
    
    def _get_client_key(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用 X-Forwarded-For（代理场景）
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        # 如果有认证token，使用用户标识
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # 简单哈希token作为用户标识
            token_hash = hash(auth_header) % 10000000
            return f"user:{token_hash}"
        
        return f"ip:{client_ip}"
    
    def _get_route_config(self, path: str) -> dict:
        """获取路由限制配置"""
        # 精确匹配
        if path in self.route_limits:
            return self.route_limits[path]
        
        # 前缀匹配
        for route, config in self.route_limits.items():
            if path.startswith(route):
                return config
        
        return {"limit": self.default_limit, "window": self.default_window}
    
    def _clean_old_requests(self, key: str, window: int):
        """清理过期的请求记录"""
        current_time = time.time()
        cutoff = current_time - window
        self.requests[key] = [
            (ts, count) for ts, count in self.requests[key]
            if ts > cutoff
        ]
    
    def is_allowed(self, request: Request) -> tuple[bool, dict]:
        """
        检查请求是否被允许
        返回: (是否允许, 限制信息)
        """
        path = request.url.path
        
        # 白名单检查
        if path in self.whitelist:
            return True, {}
        
        client_key = self._get_client_key(request)
        config = self._get_route_config(path)
        limit = config["limit"]
        window = config["window"]
        
        # 清理过期记录
        self._clean_old_requests(client_key, window)
        
        # 计算当前窗口内的请求数
        current_count = sum(count for _, count in self.requests[client_key])
        
        # 计算剩余配额
        remaining = max(0, limit - current_count)
        
        # 计算重置时间
        if self.requests[client_key]:
            oldest = min(ts for ts, _ in self.requests[client_key])
            reset_time = int(oldest + window - time.time())
        else:
            reset_time = window
        
        info = {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "window": window,
        }
        
        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for {client_key} on {path}")
            return False, info
        
        # 记录本次请求
        self.requests[client_key].append((time.time(), 1))
        info["remaining"] = remaining - 1
        
        return True, info


# 全局限制器实例
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        allowed, info = rate_limiter.is_allowed(request)
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "请求过于频繁，请稍后再试",
                    "error": "rate_limit_exceeded",
                    "retry_after": info.get("reset", 60),
                },
                headers={
                    "X-RateLimit-Limit": str(info.get("limit", 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info.get("reset", 0)),
                    "Retry-After": str(info.get("reset", 60)),
                }
            )
        
        # 执行请求
        response = await call_next(request)
        
        # 添加速率限制响应头
        if info:
            response.headers["X-RateLimit-Limit"] = str(info.get("limit", 0))
            response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
            response.headers["X-RateLimit-Reset"] = str(info.get("reset", 0))
        
        return response


def get_rate_limit_status(request: Request) -> dict:
    """获取当前速率限制状态（用于API端点）"""
    client_key = rate_limiter._get_client_key(request)
    path = request.url.path
    config = rate_limiter._get_route_config(path)
    
    rate_limiter._clean_old_requests(client_key, config["window"])
    current_count = sum(count for _, count in rate_limiter.requests[client_key])
    
    return {
        "client": client_key,
        "limit": config["limit"],
        "window": config["window"],
        "used": current_count,
        "remaining": max(0, config["limit"] - current_count),
    }
