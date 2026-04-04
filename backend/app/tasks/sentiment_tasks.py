"""
情感分析异步任务
"""
from celery import shared_task
from loguru import logger
from typing import List, Dict


@shared_task(bind=True, max_retries=2)
def analyze_comments(self, comments: List[str]) -> List[Dict]:
    """
    批量分析评论情感
    
    Args:
        comments: 评论文本列表
    """
    try:
        logger.info(f"Task started: analyze_comments ({len(comments)} items)")
        
        from app.services.sentiment.analyzer import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer()
        results = []
        
        for comment in comments:
            result = analyzer.analyze(comment)
            results.append({
                "text": comment[:50],
                "label": result.label,
                "confidence": result.confidence,
            })
        
        logger.info(f"Task completed: analyzed {len(results)} comments")
        return results
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        self.retry(countdown=30)


@shared_task(bind=True)
def update_emotion_index(self):
    """
    更新情绪指数（定时任务）
    """
    try:
        logger.info("Task started: update_emotion_index")
        
        from app.services.emotion.quantifier import EmotionQuantifier
        from app.core.database import SessionLocal
        from datetime import datetime, timedelta
        
        db = SessionLocal()
        try:
            quantifier = EmotionQuantifier()
            
            # 获取最近的评论
            # 这里简化处理，实际应该从数据库获取
            recent_comments = []  # TODO: 从数据库获取
            
            if recent_comments:
                index = quantifier.calculate_index(recent_comments)
                logger.info(f"Emotion index updated: {index}")
                return {"index": index, "timestamp": datetime.now().isoformat()}
            else:
                logger.warning("No recent comments to analyze")
                return {"index": None, "message": "No data"}
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise


@shared_task(bind=True)
def batch_analyze_stock(self, stock_code: str):
    """
    分析指定股票的所有未分析评论
    """
    try:
        logger.info(f"Task started: batch_analyze_stock({stock_code})")
        
        from app.core.database import SessionLocal
        from app.services.sentiment.analyzer import SentimentAnalyzer
        
        db = SessionLocal()
        analyzer = SentimentAnalyzer()
        
        try:
            # TODO: 从数据库获取未分析的评论并批量分析
            analyzed_count = 0
            
            logger.info(f"Task completed: analyzed {analyzed_count} comments for {stock_code}")
            return {"stock_code": stock_code, "analyzed": analyzed_count}
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise
