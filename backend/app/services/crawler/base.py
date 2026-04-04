"""
爬虫基类
"""
import asyncio
import random
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from loguru import logger
import aiohttp
from fake_useragent import UserAgent

from app.core.config import settings


@dataclass
class CommentItem:
    """评论数据项"""
    comment_id: str
    platform: str
    stock_code: str
    stock_name: str = ""
    content: str = ""
    author: str = ""
    publish_time: Optional[datetime] = None
    likes: int = 0
    replies: int = 0
    crawl_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "platform": self.platform,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "content": self.content,
            "author": self.author,
            "publish_time": self.publish_time,
            "likes": self.likes,
            "replies": self.replies,
            "crawl_time": self.crawl_time
        }


class BaseCrawler(ABC):
    """爬虫基类"""
    
    def __init__(self):
        self.platform = "base"
        self.ua = UserAgent()
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_running = False
        self.total_crawled = 0
        self.last_crawl_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        
        # 配置
        self.delay_min = settings.CRAWLER_DELAY_MIN
        self.delay_max = settings.CRAWLER_DELAY_MAX
        self.max_retry = settings.CRAWLER_MAX_RETRY
        self.timeout = settings.CRAWLER_TIMEOUT
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }
    
    async def random_delay(self):
        """随机延迟"""
        delay = random.uniform(self.delay_min, self.delay_max)
        await asyncio.sleep(delay)
    
    async def init_session(self):
        """初始化会话"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """关闭会话"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch(self, url: str, params: Optional[Dict] = None, 
                    retry: int = 0) -> Optional[str]:
        """发起HTTP请求"""
        await self.init_session()
        
        try:
            async with self.session.get(
                url, 
                headers=self.get_headers(),
                params=params
            ) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Request failed: {url}, status: {response.status}")
                    
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout: {url}")
        except Exception as e:
            logger.error(f"Request error: {url}, error: {e}")
        
        # 重试
        if retry < self.max_retry:
            await self.random_delay()
            return await self.fetch(url, params, retry + 1)
        
        return None
    
    async def fetch_json(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """发起HTTP请求并返回JSON"""
        text = await self.fetch(url, params)
        if text:
            import json
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                logger.error(f"JSON decode error: {url}")
        return None
    
    @abstractmethod
    async def crawl_stock(self, stock_code: str, 
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None) -> List[CommentItem]:
        """爬取单只股票的评论"""
        pass
    
    async def crawl(self, stock_codes: List[str],
                    start_date: Optional[date] = None,
                    end_date: Optional[date] = None,
                    callback=None) -> List[CommentItem]:
        """爬取多只股票的评论"""
        self.is_running = True
        self.error_message = None
        all_comments = []
        
        try:
            await self.init_session()
            
            for code in stock_codes:
                if not self.is_running:
                    break
                    
                logger.info(f"[{self.platform}] Crawling {code}...")
                
                try:
                    comments = await self.crawl_stock(code, start_date, end_date)
                    all_comments.extend(comments)
                    self.total_crawled += len(comments)
                    self.last_crawl_time = datetime.now()
                    
                    if callback:
                        await callback(comments)
                    
                    logger.info(f"[{self.platform}] {code}: {len(comments)} comments")
                    
                except Exception as e:
                    logger.error(f"[{self.platform}] Error crawling {code}: {e}")
                
                await self.random_delay()
                
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"[{self.platform}] Crawl error: {e}")
        finally:
            await self.close_session()
            self.is_running = False
        
        return all_comments
    
    def stop(self):
        """停止爬虫"""
        self.is_running = False
    
    def get_status(self) -> Dict[str, Any]:
        """获取爬虫状态"""
        return {
            "platform": self.platform,
            "status": "running" if self.is_running else "stopped",
            "total_crawled": self.total_crawled,
            "last_crawl_time": self.last_crawl_time.isoformat() if self.last_crawl_time else None,
            "error_message": self.error_message
        }
