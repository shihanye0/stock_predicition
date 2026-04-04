"""
爬虫管理器
"""
import asyncio
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from loguru import logger

from app.services.crawler.base import BaseCrawler, CommentItem
from app.services.crawler.eastmoney import EastMoneyCrawler
from app.services.crawler.xueqiu import XueqiuCrawler
from app.services.crawler.sina import SinaCrawler
from app.core.database import SessionLocal
from app.models.models import Comment, Stock


class CrawlerManager:
    """爬虫管理器"""
    
    def __init__(self):
        self.crawlers: Dict[str, BaseCrawler] = {
            "eastmoney": EastMoneyCrawler(),
            "xueqiu": XueqiuCrawler(),
            "sina": SinaCrawler()
        }
        self._tasks: Dict[str, asyncio.Task] = {}
    
    def get_crawler(self, platform: str) -> Optional[BaseCrawler]:
        """获取指定平台的爬虫"""
        return self.crawlers.get(platform)
    
    async def _save_comments(self, comments: List[CommentItem]):
        """保存评论到数据库"""
        if not comments:
            return
        
        db = SessionLocal()
        try:
            for item in comments:
                # 检查是否已存在
                existing = db.query(Comment).filter(
                    Comment.comment_id == item.comment_id
                ).first()
                
                if existing:
                    continue
                
                # 检查股票是否存在
                stock = db.query(Stock).filter(
                    Stock.stock_code == item.stock_code
                ).first()
                
                if not stock and item.stock_code:
                    # 创建股票记录
                    stock = Stock(
                        stock_code=item.stock_code,
                        stock_name=item.stock_name or item.stock_code
                    )
                    db.add(stock)
                    db.flush()
                
                # 创建评论记录
                comment = Comment(
                    comment_id=item.comment_id,
                    platform=item.platform,
                    stock_code=item.stock_code if item.stock_code else None,
                    content=item.content,
                    author=item.author,
                    publish_time=item.publish_time,
                    likes=item.likes,
                    replies=item.replies,
                    crawl_time=item.crawl_time
                )
                
                if item.stock_code:
                    db.add(comment)
            
            db.commit()
            logger.info(f"Saved {len(comments)} comments to database")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Save comments error: {e}")
        finally:
            db.close()
    
    async def start_crawl(self, platform: str,
                          stock_codes: Optional[List[str]] = None,
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None):
        """启动爬虫任务"""
        crawler = self.get_crawler(platform)
        if not crawler:
            logger.error(f"Unknown platform: {platform}")
            return
        
        if platform in self._tasks and not self._tasks[platform].done():
            logger.warning(f"Crawler {platform} is already running")
            return
        
        # 如果没有指定股票，获取数据库中的股票列表
        if not stock_codes:
            db = SessionLocal()
            try:
                stocks = db.query(Stock).filter(Stock.status == 1).limit(100).all()
                stock_codes = [s.stock_code for s in stocks]
            finally:
                db.close()
        
        if not stock_codes:
            # 使用默认热门股票
            stock_codes = [
                "000001", "000002", "600036", "600519", "000651",
                "300750", "002475", "600276", "601318", "000858"
            ]
        
        logger.info(f"Starting crawler {platform} for {len(stock_codes)} stocks")
        
        # 创建任务
        task = asyncio.create_task(
            crawler.crawl(
                stock_codes=stock_codes,
                start_date=start_date,
                end_date=end_date,
                callback=self._save_comments
            )
        )
        self._tasks[platform] = task
    
    def stop_crawl(self, platform: str):
        """停止爬虫任务"""
        crawler = self.get_crawler(platform)
        if crawler:
            crawler.stop()
            logger.info(f"Stopping crawler {platform}")
        
        if platform in self._tasks:
            task = self._tasks[platform]
            if not task.done():
                task.cancel()
    
    def get_status(self, platform: str) -> Dict[str, Any]:
        """获取指定平台爬虫状态"""
        crawler = self.get_crawler(platform)
        if crawler:
            return crawler.get_status()
        return {"platform": platform, "status": "unknown"}
    
    def get_all_status(self) -> List[Dict[str, Any]]:
        """获取所有爬虫状态"""
        return [crawler.get_status() for crawler in self.crawlers.values()]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取爬虫统计数据"""
        db = SessionLocal()
        try:
            from sqlalchemy import func
            
            # 统计各平台数据量
            platform_stats = db.query(
                Comment.platform,
                func.count(Comment.id).label('count')
            ).group_by(Comment.platform).all()
            
            # 统计今日采集量
            today = date.today()
            today_count = db.query(func.count(Comment.id)).filter(
                func.date(Comment.crawl_time) == today
            ).scalar()
            
            # 总数据量
            total_count = db.query(func.count(Comment.id)).scalar()
            
            return {
                "total_comments": total_count or 0,
                "today_crawled": today_count or 0,
                "platform_stats": {p: c for p, c in platform_stats},
                "crawlers": self.get_all_status()
            }
        finally:
            db.close()
