"""
爬虫测试和数据采集脚本

测试真实爬虫功能并保存数据到数据库
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List

import pymysql

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.crawler.eastmoney import EastMoneyCrawler
from app.services.crawler.base import CommentItem
from app.services.processor.text_processor import get_processor
from app.services.sentiment.analyzer import get_analyzer

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'stock_sentiment',
    'charset': 'utf8mb4'
}


class CrawlerPipeline:
    """爬虫数据处理管道"""
    
    def __init__(self, use_model=False):
        self.conn = None
        self.cursor = None
        self.processor = get_processor()
        self.analyzer = None
        self.use_model = use_model
        self.saved_count = 0
        self.analyzed_count = 0
        
        if use_model:
            try:
                self.analyzer = get_analyzer()
            except Exception as e:
                print(f"模型加载失败，使用规则分析: {e}")
                self.use_model = False
    
    def connect(self):
        """连接数据库"""
        self.conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        print("数据库连接成功")
    
    def close(self):
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("数据库连接已关闭")
    
    def save_comment(self, comment: CommentItem) -> bool:
        """保存评论到数据库"""
        try:
            # 清洗文本
            content_clean = self.processor.clean(comment.content)
            
            # 插入评论
            self.cursor.execute("""
                INSERT INTO comments (
                    comment_id, platform, stock_code, content, content_clean,
                    author, publish_time, likes, replies, is_processed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    content = VALUES(content),
                    content_clean = VALUES(content_clean),
                    likes = VALUES(likes),
                    replies = VALUES(replies)
            """, (
                comment.comment_id,
                comment.platform,
                comment.stock_code,
                comment.content,
                content_clean,
                comment.author,
                comment.publish_time,
                comment.likes,
                comment.replies,
                0  # 未处理
            ))
            
            self.saved_count += 1
            return True
            
        except Exception as e:
            print(f"保存评论失败: {e}")
            return False
    
    def analyze_comment(self, comment_id: str, content: str) -> bool:
        """分析评论情感"""
        try:
            if self.analyzer and self.use_model:
                result = self.analyzer.analyze(content)
                label = result.label
                confidence = result.confidence
                pos_score = result.scores.get('positive', 0)
                neu_score = result.scores.get('neutral', 0)
                neg_score = result.scores.get('negative', 0)
                model_version = self.analyzer.model_name
            else:
                # 简单规则分析
                content_lower = content.lower()
                pos_words = ['涨', '涨停', '利好', '买入', '看涨', '大涨', '突破', '强势', '加仓', '物美价廉', '牛']
                neg_words = ['跌', '跌停', '利空', '卖出', '看跌', '大跌', '破位', '弱势', '清仓', '暴雷', '垃圾']
                
                pos_count = sum(1 for w in pos_words if w in content_lower)
                neg_count = sum(1 for w in neg_words if w in content_lower)
                
                if pos_count > neg_count:
                    label = 'positive'
                    confidence = min(0.6 + pos_count * 0.1, 0.9)
                    pos_score, neu_score, neg_score = confidence, 0.1, 0.1
                elif neg_count > pos_count:
                    label = 'negative'
                    confidence = min(0.6 + neg_count * 0.1, 0.9)
                    pos_score, neu_score, neg_score = 0.1, 0.1, confidence
                else:
                    label = 'neutral'
                    confidence = 0.6
                    pos_score, neu_score, neg_score = 0.2, 0.6, 0.2
                model_version = 'rule_based'
            
            self.cursor.execute("""
                INSERT INTO sentiments (
                    comment_id, label, confidence,
                    positive_score, neutral_score, negative_score,
                    model_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    label = VALUES(label),
                    confidence = VALUES(confidence),
                    positive_score = VALUES(positive_score),
                    neutral_score = VALUES(neutral_score),
                    negative_score = VALUES(negative_score)
            """, (
                comment_id,
                label,
                confidence,
                pos_score,
                neu_score,
                neg_score,
                model_version
            ))
            
            # 更新评论处理状态
            self.cursor.execute("""
                UPDATE comments SET is_processed = 1 WHERE comment_id = %s
            """, (comment_id,))
            
            self.analyzed_count += 1
            return True
            
        except Exception as e:
            print(f"分析评论失败: {e}")
            return False
    
    async def process_comments(self, comments: List[CommentItem]):
        """处理评论列表"""
        for comment in comments:
            # 保存
            if self.save_comment(comment):
                # 分析
                self.analyze_comment(comment.comment_id, comment.content)
        
        self.conn.commit()
        print(f"  处理完成: 保存 {len(comments)} 条, 分析 {len(comments)} 条")


async def test_eastmoney_crawler(stock_code: str = "000001", max_pages: int = 3):
    """测试东方财富爬虫"""
    print("=" * 60)
    print("测试东方财富股吧爬虫")
    print("=" * 60)
    
    crawler = EastMoneyCrawler()
    pipeline = CrawlerPipeline(use_model=False)  # 测试时不加载模型
    
    try:
        pipeline.connect()
        
        # 设置回调函数
        async def save_callback(comments: List[CommentItem]):
            await pipeline.process_comments(comments)
        
        # 开始爬取
        print(f"\n开始爬取股票: {stock_code}")
        
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        comments = await crawler.crawl_stock(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"爬取到 {len(comments)} 条评论")
        
        # 处理并保存
        if comments:
            await pipeline.process_comments(comments)
            
            # 显示示例
            print("\n示例评论:")
            for c in comments[:5]:
                print(f"  [{c.platform}] {c.author}: {c.content[:50]}...")
        
        print(f"\n总计: 保存 {pipeline.saved_count} 条, 分析 {pipeline.analyzed_count} 条")
        
    except Exception as e:
        print(f"爬虫测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pipeline.close()
        await crawler.close_session()


async def crawl_all_stocks(days: int = 7):
    """爬取所有股票"""
    print("=" * 60)
    print("开始爬取所有股票评论")
    print("=" * 60)
    
    # 获取股票列表
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT stock_code, stock_name FROM stocks WHERE status = 1")
    stocks = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print(f"共 {len(stocks)} 只股票\n")
    
    crawler = EastMoneyCrawler()
    pipeline = CrawlerPipeline(use_model=False)  # 批量爬取不加载模型
    
    try:
        pipeline.connect()
        
        start_date = date.today() - timedelta(days=days)
        end_date = date.today()
        
        total_comments = 0
        
        for stock_code, stock_name in stocks:
            print(f"正在爬取: {stock_name}({stock_code})")
            
            try:
                comments = await crawler.crawl_stock(
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if comments:
                    await pipeline.process_comments(comments)
                    total_comments += len(comments)
                    print(f"  采集 {len(comments)} 条评论")
                else:
                    print(f"  无新评论")
                
            except Exception as e:
                print(f"  采集失败: {e}")
            
            # 延迟避免被封
            await asyncio.sleep(2)
        
        print("\n" + "=" * 60)
        print(f"采集完成！总计 {total_comments} 条评论")
        print(f"保存: {pipeline.saved_count} 条")
        print(f"分析: {pipeline.analyzed_count} 条")
        print("=" * 60)
        
    except Exception as e:
        print(f"采集失败: {e}")
    finally:
        pipeline.close()
        await crawler.close_session()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="爬虫测试和数据采集")
    parser.add_argument("--mode", type=str, default="test", 
                        choices=["test", "all"],
                        help="模式: test=测试单只股票, all=爬取全部")
    parser.add_argument("--stock", type=str, default="000001",
                        help="测试股票代码（仅test模式）")
    parser.add_argument("--days", type=int, default=7,
                        help="采集最近多少天的数据")
    
    args = parser.parse_args()
    
    if args.mode == "test":
        asyncio.run(test_eastmoney_crawler(args.stock))
    else:
        asyncio.run(crawl_all_stocks(args.days))


if __name__ == "__main__":
    main()
