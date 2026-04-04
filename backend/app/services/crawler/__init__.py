"""
爬虫服务模块
"""
from app.services.crawler.base import BaseCrawler, CommentItem
from app.services.crawler.eastmoney import EastMoneyCrawler
from app.services.crawler.xueqiu import XueqiuCrawler
from app.services.crawler.sina import SinaCrawler
from app.services.crawler.manager import CrawlerManager

__all__ = [
    "BaseCrawler",
    "CommentItem",
    "EastMoneyCrawler",
    "XueqiuCrawler",
    "SinaCrawler",
    "CrawlerManager"
]
