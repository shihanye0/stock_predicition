"""
Prometheus监控指标模块
"""
import time
from typing import Callable
from functools import wraps
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


# =====================================================
# 应用信息
# =====================================================
APP_INFO = Info("stock_sentiment_app", "Application information")
APP_INFO.info({
    "version": "1.0.0",
    "name": "stock_sentiment_system",
})


# =====================================================
# HTTP请求指标
# =====================================================
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["method", "endpoint"]
)


# =====================================================
# 业务指标
# =====================================================
SENTIMENT_ANALYSIS_TOTAL = Counter(
    "sentiment_analysis_total",
    "Total number of sentiment analyses",
    ["label"]
)

SENTIMENT_ANALYSIS_DURATION = Histogram(
    "sentiment_analysis_duration_seconds",
    "Sentiment analysis duration in seconds",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
)

CRAWLER_REQUESTS_TOTAL = Counter(
    "crawler_requests_total",
    "Total number of crawler requests",
    ["stock_code", "status"]
)

CRAWLER_COMMENTS_COLLECTED = Counter(
    "crawler_comments_collected_total",
    "Total number of comments collected",
    ["stock_code"]
)

CACHE_HITS = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_type"]
)

CACHE_MISSES = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_type"]
)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

ACTIVE_USERS = Gauge(
    "active_users",
    "Number of active users"
)

EMOTION_INDEX = Gauge(
    "emotion_index",
    "Current emotion index value",
    ["stock_code"]
)


# =====================================================
# 监控中间件
# =====================================================
class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Prometheus监控中间件
    收集HTTP请求指标
    """
    
    # 不监控的路径
    EXCLUDE_PATHS = {"/metrics", "/health", "/favicon.ico"}
    
    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path in self.EXCLUDE_PATHS:
            return await call_next(request)
        
        method = request.method
        # 简化路径（去除动态参数）
        endpoint = self._normalize_path(request.url.path)
        
        # 增加进行中请求计数
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        
        start_time = time.time()
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise
        finally:
            # 记录请求时长
            duration = time.time() - start_time
            HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            
            # 记录请求总数
            HTTP_REQUESTS_TOTAL.labels(
                method=method, 
                endpoint=endpoint, 
                status_code=status_code
            ).inc()
            
            # 减少进行中请求计数
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()
    
    def _normalize_path(self, path: str) -> str:
        """
        规范化路径，将动态参数替换为占位符
        /api/v1/stocks/000001 -> /api/v1/stocks/{stock_code}
        """
        parts = path.split("/")
        normalized = []
        for part in parts:
            if part.isdigit() or (len(part) == 6 and part[0] in "036"):
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/".join(normalized)


# =====================================================
# 指标端点
# =====================================================
async def metrics_endpoint():
    """
    暴露Prometheus指标的端点
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


# =====================================================
# 辅助函数
# =====================================================
def track_sentiment_analysis(label: str, duration: float):
    """记录情感分析指标"""
    SENTIMENT_ANALYSIS_TOTAL.labels(label=label).inc()
    SENTIMENT_ANALYSIS_DURATION.observe(duration)


def track_crawler_request(stock_code: str, status: str, comments_count: int = 0):
    """记录爬虫请求指标"""
    CRAWLER_REQUESTS_TOTAL.labels(stock_code=stock_code, status=status).inc()
    if comments_count > 0:
        CRAWLER_COMMENTS_COLLECTED.labels(stock_code=stock_code).inc(comments_count)


def track_cache_access(cache_type: str, hit: bool):
    """记录缓存访问指标"""
    if hit:
        CACHE_HITS.labels(cache_type=cache_type).inc()
    else:
        CACHE_MISSES.labels(cache_type=cache_type).inc()


def track_db_query(operation: str, duration: float):
    """记录数据库查询指标"""
    DB_QUERY_DURATION.labels(operation=operation).observe(duration)


def update_emotion_index(stock_code: str, value: float):
    """更新情绪指数"""
    EMOTION_INDEX.labels(stock_code=stock_code).set(value)


def set_active_users(count: int):
    """设置活跃用户数"""
    ACTIVE_USERS.set(count)
