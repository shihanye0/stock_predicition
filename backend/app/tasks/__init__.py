"""
异步任务模块
"""
from app.tasks.crawler_tasks import crawl_stock_comments, crawl_hot_stocks
from app.tasks.sentiment_tasks import analyze_comments, update_emotion_index
from app.tasks.report_tasks import generate_daily_report

__all__ = [
    "crawl_stock_comments",
    "crawl_hot_stocks",
    "analyze_comments",
    "update_emotion_index",
    "generate_daily_report",
]
