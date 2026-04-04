"""
情感分析服务模块
"""
from app.services.sentiment.analyzer import SentimentAnalyzer, SentimentConfig, get_analyzer

__all__ = ["SentimentAnalyzer", "SentimentConfig", "get_analyzer"]
