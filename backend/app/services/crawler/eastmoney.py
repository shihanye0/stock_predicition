"""
东方财富股吧爬虫
"""
import re
import json
from datetime import datetime, date
from typing import List, Optional, Dict
from loguru import logger

from app.services.crawler.base import BaseCrawler, CommentItem


class EastMoneyCrawler(BaseCrawler):
    """东方财富股吧爬虫"""
    
    def __init__(self):
        super().__init__()
        self.platform = "eastmoney"
        self.base_url = "https://guba.eastmoney.com"
        self.api_url = "https://guba.eastmoney.com"
    
    def get_headers(self) -> dict:
        """获取请求头"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Referer": "https://guba.eastmoney.com/"
        }
        
    def _get_stock_code_for_guba(self, stock_code: str) -> str:
        """转换股票代码格式"""
        # 去掉市场前缀
        code = stock_code.replace("SH", "").replace("SZ", "").replace(".", "")
        
        # 判断市场
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
            # 处理各种时间格式
            if "今天" in time_str or "分钟前" in time_str or "小时前" in time_str:
                return datetime.now()
            elif "昨天" in time_str:
                return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                # 标准格式: 2026-01-22 10:30:00
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%m-%d %H:%M"]:
                    try:
                        dt = datetime.strptime(time_str, fmt)
                        if dt.year == 1900:
                            dt = dt.replace(year=datetime.now().year)
                        return dt
                    except ValueError:
                        continue
        except Exception as e:
            logger.debug(f"Time parse error: {time_str}, {e}")
        
        return None
    
    async def crawl_stock(self, stock_code: str,
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None) -> List[CommentItem]:
        """爬取单只股票的评论"""
        comments = []
        code = self._get_stock_code_for_guba(stock_code)
        
        # 确保爬虫处于运行状态
        self.is_running = True
        
        page = 1
        max_pages = 5  # 限制最大页数
        
        while page <= max_pages and self.is_running:
            try:
                # 尝试使用网页爬取
                page_comments = await self._crawl_web_page(code, page, stock_code, start_date, end_date)
                
                if not page_comments:
                    break
                
                comments.extend(page_comments)
                page += 1
                await self.random_delay()
                
            except Exception as e:
                logger.error(f"Crawl page {page} error: {e}")
                break
        
        return comments
    
    async def _crawl_web_page(self, code: str, page: int, stock_code: str,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None) -> List[CommentItem]:
        """爬取股吧网页版"""
        comments = []
        
        try:
            # 构造URL - 东方财富股吧URL格式
            url = f"{self.base_url}/list,{code},f_{page}.html"
            logger.info(f"Fetching URL: {url}")
            
            html = await self.fetch(url)
            
            if not html:
                logger.warning(f"No HTML content from {url}")
                return comments
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找帖子列表 - 新版页面结构是 tr.listitem
            post_list = soup.select('tr.listitem')
            
            if not post_list:
                # 备用选择器
                post_list = soup.select('.listitem')
            
            logger.info(f"Found {len(post_list)} items")
            
            for item in post_list:
                try:
                    # 提取标题和链接
                    title_elem = item.select_one('div.title a') or item.select_one('.title a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get('href', '')
                    post_id = title_elem.get('data-postid', '')
                    
                    if not title or len(title) < 2:
                        continue
                    
                    # 如果没有data-postid，从链接提取
                    if not post_id and href:
                        match = re.search(r',(\d+)\.html', href)
                        if match:
                            post_id = match.group(1)
                    
                    if not post_id:
                        post_id = str(abs(hash(title)))[:8]
                    
                    # 提取作者
                    author_elem = item.select_one('div.author a') or item.select_one('.author a')
                    author = author_elem.get_text(strip=True) if author_elem else "股友"
                    
                    # 提取时间
                    time_elem = item.select_one('div.update') or item.select_one('.update')
                    time_str = time_elem.get_text(strip=True) if time_elem else ""
                    publish_time = self._parse_time(time_str)
                    
                    # 时间过滤
                    if start_date and publish_time and publish_time.date() < start_date:
                        continue
                    if end_date and publish_time and publish_time.date() > end_date:
                        continue
                    
                    # 提取阅读数
                    read_elem = item.select_one('div.read') or item.select_one('.read')
                    likes = 0
                    if read_elem:
                        try:
                            text = read_elem.get_text(strip=True)
                            text = text.replace('万', '0000').replace('亿', '00000000')
                            likes = int(float(text)) if text else 0
                        except:
                            pass
                    
                    # 提取回复数
                    reply_elem = item.select_one('div.reply') or item.select_one('.reply')
                    replies = 0
                    if reply_elem:
                        try:
                            text = reply_elem.get_text(strip=True)
                            replies = int(text) if text else 0
                        except:
                            pass
                    
                    comment = CommentItem(
                        comment_id=f"em_{code}_{post_id}",
                        platform=self.platform,
                        stock_code=stock_code,
                        content=title,
                        author=author,
                        publish_time=publish_time,
                        likes=likes,
                        replies=replies
                    )
                    comments.append(comment)
                    
                except Exception as e:
                    logger.debug(f"Parse item error: {e}")
                    continue
            
            logger.info(f"Page {page}: parsed {len(comments)} comments")
                    
        except Exception as e:
            logger.error(f"Crawl web page error: {e}")
            import traceback
            traceback.print_exc()
        
        return comments
