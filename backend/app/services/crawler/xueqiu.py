"""
雪球爬虫
"""
import re
import json
from datetime import datetime, date
from typing import List, Optional, Dict
from loguru import logger

from app.services.crawler.base import BaseCrawler, CommentItem


class XueqiuCrawler(BaseCrawler):
    """雪球爬虫"""
    
    def __init__(self):
        super().__init__()
        self.platform = "xueqiu"
        self.base_url = "https://xueqiu.com"
        self.api_url = "https://xueqiu.com/query/v1"
        
    def get_headers(self) -> Dict[str, str]:
        """获取请求头（雪球需要特殊headers）"""
        headers = super().get_headers()
        headers.update({
            "Referer": "https://xueqiu.com/",
            "Origin": "https://xueqiu.com",
            "X-Requested-With": "XMLHttpRequest"
        })
        return headers
    
    def _get_xueqiu_symbol(self, stock_code: str) -> str:
        """转换股票代码为雪球格式"""
        code = stock_code.replace("SH", "").replace("SZ", "").replace(".", "")
        
        if code.startswith("6"):
            return f"SH{code}"
        elif code.startswith(("0", "3")):
            return f"SZ{code}"
        else:
            return code
    
    def _parse_timestamp(self, ts: int) -> Optional[datetime]:
        """解析时间戳"""
        if not ts:
            return None
        try:
            # 雪球使用毫秒时间戳
            return datetime.fromtimestamp(ts / 1000)
        except:
            return None
    
    async def _get_cookie(self):
        """获取访问cookie"""
        try:
            # 先访问首页获取cookie
            await self.fetch(self.base_url)
        except:
            pass
    
    async def crawl_stock(self, stock_code: str,
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None) -> List[CommentItem]:
        """爬取单只股票的评论"""
        comments = []
        symbol = self._get_xueqiu_symbol(stock_code)
        
        # 先获取cookie
        await self._get_cookie()
        await self.random_delay()
        
        # 爬取股票讨论
        page = 1
        max_pages = 10
        
        while page <= max_pages and self.is_running:
            try:
                url = f"{self.base_url}/statuses/stock_timeline.json"
                params = {
                    "symbol": symbol,
                    "count": 20,
                    "page": page,
                    "source": "all"
                }
                
                data = await self.fetch_json(url, params)
                
                if not data or "list" not in data:
                    logger.debug(f"No data for {symbol} page {page}")
                    break
                
                posts = data.get("list", [])
                if not posts:
                    break
                
                for post in posts:
                    try:
                        publish_time = self._parse_timestamp(post.get("created_at"))
                        
                        # 时间过滤
                        if start_date and publish_time and publish_time.date() < start_date:
                            continue
                        if end_date and publish_time and publish_time.date() > end_date:
                            continue
                        
                        # 提取内容（去除HTML标签）
                        text = post.get("text", "")
                        text = re.sub(r'<[^>]+>', '', text)
                        text = text.strip()
                        
                        if not text:
                            continue
                        
                        # 提取用户信息
                        user = post.get("user", {})
                        
                        comment = CommentItem(
                            comment_id=f"xq_{post.get('id', '')}",
                            platform=self.platform,
                            stock_code=stock_code,
                            stock_name=post.get("target", ""),
                            content=text,
                            author=user.get("screen_name", ""),
                            publish_time=publish_time,
                            likes=int(post.get("like_count", 0)),
                            replies=int(post.get("reply_count", 0))
                        )
                        comments.append(comment)
                        
                    except Exception as e:
                        logger.debug(f"Parse post error: {e}")
                        continue
                
                page += 1
                await self.random_delay()
                
            except Exception as e:
                logger.error(f"Crawl page error: {e}")
                break
        
        return comments
    
    async def search_stock(self, keyword: str, 
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None) -> List[CommentItem]:
        """搜索股票相关讨论"""
        comments = []
        
        await self._get_cookie()
        await self.random_delay()
        
        page = 1
        max_pages = 5
        
        while page <= max_pages and self.is_running:
            try:
                url = f"{self.base_url}/search"
                params = {
                    "q": keyword,
                    "page": page,
                    "size": 20,
                    "sort": "time"
                }
                
                data = await self.fetch_json(url, params)
                
                if not data or "list" not in data:
                    break
                
                posts = data.get("list", [])
                if not posts:
                    break
                
                for post in posts:
                    try:
                        publish_time = self._parse_timestamp(post.get("created_at"))
                        
                        if start_date and publish_time and publish_time.date() < start_date:
                            continue
                        if end_date and publish_time and publish_time.date() > end_date:
                            continue
                        
                        text = post.get("text", "")
                        text = re.sub(r'<[^>]+>', '', text).strip()
                        
                        if not text:
                            continue
                        
                        user = post.get("user", {})
                        
                        comment = CommentItem(
                            comment_id=f"xq_search_{post.get('id', '')}",
                            platform=self.platform,
                            stock_code="",
                            content=text,
                            author=user.get("screen_name", ""),
                            publish_time=publish_time,
                            likes=int(post.get("like_count", 0)),
                            replies=int(post.get("reply_count", 0))
                        )
                        comments.append(comment)
                        
                    except Exception as e:
                        logger.debug(f"Parse search result error: {e}")
                        continue
                
                page += 1
                await self.random_delay()
                
            except Exception as e:
                logger.error(f"Search error: {e}")
                break
        
        return comments
