"""
基于Transformer的股票情绪预测系统 - 主入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from app.core.config import settings
from app.core.database import init_db
from app.core.rate_limit import RateLimitMiddleware, get_rate_limit_status
from app.core.logging import RequestLoggingMiddleware
from app.core.metrics import PrometheusMiddleware, metrics_endpoint
from app.api import stocks, sentiment, emotion, validation, crawler, auth, experiment, alerts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # 初始化数据库
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down application")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于Transformer的股票情绪预测系统API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加速率限制中间件
app.add_middleware(RateLimitMiddleware)

# 添加请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 添加Prometheus监控中间件
app.add_middleware(PrometheusMiddleware)

# 注册路由
app.include_router(auth.router, prefix="/api", tags=["认证"])
app.include_router(stocks.router, prefix=settings.API_PREFIX, tags=["股票"])
app.include_router(sentiment.router, prefix=settings.API_PREFIX, tags=["情感分析"])
app.include_router(emotion.router, prefix=settings.API_PREFIX, tags=["情绪指标"])
app.include_router(validation.router, prefix=settings.API_PREFIX, tags=["市场验证"])
app.include_router(crawler.router, prefix=settings.API_PREFIX, tags=["爬虫管理"])
app.include_router(experiment.router, prefix=settings.API_PREFIX, tags=["实验对比"])
app.include_router(alerts.router, prefix=settings.API_PREFIX, tags=["情绪预警"])


@app.get("/", tags=["健康检查"])
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/api/rate-limit", tags=["健康检查"])
async def rate_limit_status(request: Request):
    """获取当前速率限制状态"""
    return get_rate_limit_status(request)


@app.get("/metrics", tags=["监控"])
async def metrics():
    """Prometheus指标端点"""
    return await metrics_endpoint()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
