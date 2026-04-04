"""
爬虫异步任务
"""
from celery import shared_task
from loguru import logger
from typing import List


@shared_task(bind=True, max_retries=3)
def crawl_stock_comments(self, stock_code: str, pages: int = 5):
    """
    异步爬取股票评论
    
    Args:
        stock_code: 股票代码
        pages: 爬取页数
    """
    try:
        logger.info(f"Task started: crawl_stock_comments({stock_code}, {pages})")
        
        from app.services.crawler.eastmoney import EastMoneyCrawler
        import asyncio
        
        crawler = EastMoneyCrawler()
        
        # 运行异步爬虫
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                crawler.crawl_stock(stock_code, max_pages=pages)
            )
        finally:
            loop.close()
        
        logger.info(f"Task completed: crawled {len(result)} comments for {stock_code}")
        return {"stock_code": stock_code, "count": len(result)}
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        self.retry(countdown=60 * (self.request.retries + 1))


@shared_task(bind=True)
def crawl_hot_stocks(self):
    """
    爬取热门股票评论（定时任务）
    """
    try:
        logger.info("Task started: crawl_hot_stocks")
        
        # 热门股票列表
        hot_stocks = [
            "000001",  # 平安银行
            "600519",  # 贵州茅台
            "300750",  # 宁德时代
            "002594",  # 比亚迪
            "600036",  # 招商银行
        ]
        
        results = []
        for stock in hot_stocks:
            try:
                result = crawl_stock_comments.delay(stock, pages=3)
                results.append({"stock": stock, "task_id": result.id})
            except Exception as e:
                logger.warning(f"Failed to queue {stock}: {e}")
        
        logger.info(f"Task completed: queued {len(results)} crawl tasks")
        return results
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise
