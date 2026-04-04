"""
Celery异步任务配置
"""
from celery import Celery
from app.core.config import settings

# 创建Celery实例
celery_app = Celery(
    "stock_sentiment",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.crawler_tasks",
        "app.tasks.sentiment_tasks",
        "app.tasks.report_tasks",
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # 任务结果
    result_expires=3600,  # 1小时后过期
    task_track_started=True,
    
    # 并发
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    
    # 任务限制
    task_time_limit=1800,  # 30分钟
    task_soft_time_limit=1500,  # 25分钟
    
    # 重试
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # 定时任务
    beat_schedule={
        # 每天早上8点爬取热门股票评论
        "crawl-hot-stocks": {
            "task": "app.tasks.crawler_tasks.crawl_hot_stocks",
            "schedule": {"hour": 8, "minute": 0},
        },
        # 每小时更新情绪指数
        "update-emotion-index": {
            "task": "app.tasks.sentiment_tasks.update_emotion_index",
            "schedule": 3600,
        },
        # 每天生成日报
        "generate-daily-report": {
            "task": "app.tasks.report_tasks.generate_daily_report",
            "schedule": {"hour": 20, "minute": 0},
        },
    }
)
