"""
日志系统模块
使用loguru实现结构化日志和日志轮转
"""
import sys
import os
import json
from datetime import datetime
from typing import Callable
from pathlib import Path
from loguru import logger
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time

from app.core.config import settings


def setup_logging():
    """
    配置日志系统
    """
    # 确保日志目录存在
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 移除默认处理器
    logger.remove()
    
    # 控制台输出 - 彩色格式
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=settings.DEBUG,
    )
    
    # 主日志文件 - 结构化JSON格式，轮转
    logger.add(
        str(log_dir / "app_{time:YYYY-MM-DD}.log"),
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
        enqueue=True,  # 异步写入
    )
    
    # 错误日志单独文件
    logger.add(
        str(log_dir / "error_{time:YYYY-MM-DD}.log"),
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
        rotation="00:00",
        retention="90 days",  # 错误日志保留更长
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )
    
    # API访问日志
    logger.add(
        str(log_dir / "access_{time:YYYY-MM-DD}.log"),
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
        rotation="00:00",
        retention="14 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: record["extra"].get("access_log", False),
    )
    
    # JSON格式日志（用于日志分析系统）
    logger.add(
        str(log_dir / "app_{time:YYYY-MM-DD}.json"),
        level=settings.LOG_LEVEL,
        format="{message}",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
        serialize=True,  # JSON序列化
    )
    
    logger.info(f"Logging system initialized. Log directory: {log_dir}")
    
    return logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    记录所有API请求的详细信息
    """
    
    # 不记录的路径
    EXCLUDE_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}
    
    async def dispatch(self, request: Request, call_next: Callable):
        # 跳过不需要记录的路径
        if request.url.path in self.EXCLUDE_PATHS:
            return await call_next(request)
        
        # 记录请求开始
        start_time = time.time()
        request_id = f"{int(start_time * 1000)}-{id(request)}"
        
        # 获取客户端信息
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"
        
        # 获取用户代理
        user_agent = request.headers.get("User-Agent", "unknown")[:100]
        
        # 执行请求
        response = None
        error_msg = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            error_msg = str(e)
            raise
        finally:
            # 计算处理时间
            process_time = (time.time() - start_time) * 1000  # 毫秒
            
            # 构建访问日志
            access_info = {
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params) if request.query_params else None,
                "status_code": status_code,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "process_time_ms": round(process_time, 2),
                "error": error_msg,
            }
            
            # 使用特殊标记写入访问日志
            access_logger = logger.bind(access_log=True)
            
            # 根据状态码决定日志级别
            if status_code >= 500:
                logger.error(
                    f"[{request_id}] {request.method} {request.url.path} "
                    f"- {status_code} - {process_time:.2f}ms - {error_msg}"
                )
            elif status_code >= 400:
                logger.warning(
                    f"[{request_id}] {request.method} {request.url.path} "
                    f"- {status_code} - {process_time:.2f}ms"
                )
            else:
                access_logger.info(json.dumps(access_info, ensure_ascii=False))
        
        return response


def log_function_call(func_name: str, **kwargs):
    """
    记录函数调用日志
    用于关键业务函数的追踪
    """
    logger.info(f"Function call: {func_name} | params: {kwargs}")


def log_database_query(query: str, duration_ms: float):
    """
    记录数据库查询日志
    """
    if duration_ms > 1000:  # 慢查询
        logger.warning(f"Slow query ({duration_ms:.2f}ms): {query[:200]}")
    else:
        logger.debug(f"DB query ({duration_ms:.2f}ms): {query[:100]}")


def log_external_api(api_name: str, method: str, url: str, status: int, duration_ms: float):
    """
    记录外部API调用日志
    """
    logger.info(
        f"External API: {api_name} | {method} {url} | "
        f"status={status} | duration={duration_ms:.2f}ms"
    )


def log_crawler_activity(action: str, stock_code: str, **details):
    """
    记录爬虫活动日志
    """
    logger.info(
        f"Crawler: {action} | stock={stock_code} | "
        f"details={json.dumps(details, ensure_ascii=False)}"
    )


def log_sentiment_analysis(text_count: int, duration_ms: float, model: str = "bert"):
    """
    记录情感分析日志
    """
    logger.info(
        f"Sentiment analysis: {text_count} texts | "
        f"model={model} | duration={duration_ms:.2f}ms"
    )


# 初始化日志
setup_logging()
