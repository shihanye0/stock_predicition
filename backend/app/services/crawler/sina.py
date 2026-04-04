"""
新浪财经爬虫
"""
import re
import json
from datetime import datetime, date
from typing import List, Optional, Dict
from loguru import logger

from app.services.crawler.base import BaseCrawler, CommentItem


class SinaCrawler(BaseCrawler):
    """新浪财经爬虫"""
    
    def __init__(self):
        super().__init__()
        self.platform = "sina"
        self.base_url = "https://finance.sina.com.cn"
        self.comment_url = "https://comment.sina.com.cn"
        
    def _get_sina_symbol(self, stock_code: str) -> str:
        """转换股票代码为新浪格式"""
        code = stock_code.replace("SH", "").replace("SZ", "").replace(".", "")
        
        if code.startswith("6"):
            return f"sh{code}"
        elif code.startswith(("0", "3")):
            return f"sz{code}"
        else:
            return code
    
    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """解析时间字符串"""
        if not time_str:
            return None
        
        try:
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y年%m月%d日 %H:%M"]:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
        except:
            pass
        
        return None
    
    async def crawl_stock(self, stock_code: str,
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None) -> List[CommentItem]:
        """爬取单只股票的新闻评论"""
        comments = []
        symbol = self._get_sina_symbol(stock_code)
        
        # 先获取相关新闻
        news_list = await self._get_stock_news(symbol)
        
        for news in news_list[:20]:  # 限制新闻数量
            if not self.is_running:
                break
                
            news_id = news.get("id", "")
            if not news_id:
                continue
            
            # 获取新闻评论
            news_comments = await self._get_news_comments(news_id, stock_code)
            
            for comment in news_comments:
                if start_date and comment.publish_time and comment.publish_time.date() < start_date:
                    continue
                if end_date and comment.publish_time and comment.publish_time.date() > end_date:
                    continue
                comments.append(comment)
            
            await self.random_delay()
        
        return comments
    
    async def _get_stock_news(self, symbol: str) -> List[Dict]:
        """获取股票相关新闻列表"""
        news_list = []
        
        try:
            # 新浪财经股票新闻API
            url = f"https://finance.sina.com.cn/realstock/company/{symbol}/nc.shtml"
            html = await self.fetch(url)
            
            if not html:
                return news_list
            
            # 解析新闻链接
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            news_items = soup.select('.datelist ul li a, .news_list li a')
            
            for item in news_items[:30]:
                href = item.get('href', '')
                title = item.get_text(strip=True)
                
                if not href or not title:
                    continue
                
                # 提取新闻ID
                news_id_match = re.search(r'doc-(\w+)', href)
                if news_id_match:
                    news_list.append({
                        "id": news_id_match.group(1),
                        "title": title,
                        "url": href
                    })
                    
        except Exception as e:
            logger.error(f"Get stock news error: {e}")
        
        return news_list
    
    async def _get_news_comments(self, news_id: str, stock_code: str) -> List[CommentItem]:
        """获取新闻评论"""
        comments = []
        
        try:
            # 新浪评论API
            url = f"{self.comment_url}/page/info"
            params = {
                "channel": "cj",
                "newsid": f"comos-{news_id}",
                "page": 1,
                "page_size": 50
            }
            
            data = await self.fetch_json(url, params)
            
            if not data or "result" not in data:
                return comments
            
            result = data.get("result", {})
            comment_list = result.get("cmntlist", [])
            
            for item in comment_list:
                try:
                    publish_time = self._parse_time(item.get("time", ""))
                    
                    comment = CommentItem(
                        comment_id=f"sina_{item.get('mid', '')}",
                        platform=self.platform,
                        stock_code=stock_code,
                        content=item.get("content", ""),
                        author=item.get("nick", ""),
                        publish_time=publish_time,
                        likes=int(item.get("agree", 0))
                    )
                    comments.append(comment)
                    
                except Exception as e:
                    logger.debug(f"Parse comment error: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Get news comments error: {e}")
        
        return comments
    
    async def crawl_hot_comments(self, 
                                  start_date: Optional[date] = None,
                                  end_date: Optional[date] = None) -> List[CommentItem]:
        """爬取热门财经新闻评论"""
        comments = []
        
        try:
            # 获取热门财经新闻
            url = "https://feed.mix.sina.com.cn/api/roll/get"
            params = {
                "pageid": "153",
                "lid": "2516",
                "num": 30,
                "page": 1
            }
            
            data = await self.fetch_json(url, params)
            
            if not data or "result" not in data:
                return comments
            
            news_list = data.get("result", {}).get("data", [])
            
            for news in news_list:
                if not self.is_running:
                    break
                
                # 提取新闻ID
                url = news.get("url", "")
                news_id_match = re.search(r'doc-(\w+)', url)
                if not news_id_match:
                    continue
                
                news_id = news_id_match.group(1)
                news_comments = await self._get_news_comments(news_id, "")
                
                for comment in news_comments:
                    if start_date and comment.publish_time and comment.publish_time.date() < start_date:
                        continue
                    if end_date and comment.publish_time and comment.publish_time.date() > end_date:
                        continue
                    comments.append(comment)
                
                await self.random_delay()
                
        except Exception as e:
            logger.error(f"Crawl hot comments error: {e}")
        
        return comments
