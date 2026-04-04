"""
情绪量化计算模块
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from loguru import logger

from app.core.database import SessionLocal
from app.models.models import Comment, Sentiment, Emotion, Stock


@dataclass
class EmotionMetrics:
    """情绪指标"""
    total_count: int = 0
    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0
    bull_index: float = 0.0
    bear_index: float = 0.0
    intensity: float = 0.0
    temperature: float = 0.0
    volatility: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'total_count': self.total_count,
            'positive_count': self.positive_count,
            'neutral_count': self.neutral_count,
            'negative_count': self.negative_count,
            'bull_index': round(self.bull_index, 2),
            'bear_index': round(self.bear_index, 2),
            'intensity': round(self.intensity, 4),
            'temperature': round(self.temperature, 2),
            'volatility': round(self.volatility, 4)
        }


class EmotionCalculator:
    """
    情绪量化计算器
    
    计算指标：
    - 看涨指数(BullIndex): 积极评论占比
    - 看跌指数(BearIndex): 消极评论占比
    - 情绪强度(Intensity): 情绪净值
    - 情绪温度(Temperature): 综合热度
    - 情绪波动(Volatility): 情绪稳定性
    """
    
    def __init__(self):
        self.label_map = {
            'positive': 1,
            'neutral': 0,
            'negative': -1
        }
    
    def calculate_bull_index(self, positive_count: int, total_count: int) -> float:
        """
        计算看涨指数
        
        公式: 积极评论数 / 总评论数 * 100
        """
        if total_count == 0:
            return 50.0
        return (positive_count / total_count) * 100
    
    def calculate_bear_index(self, negative_count: int, total_count: int) -> float:
        """
        计算看跌指数
        
        公式: 消极评论数 / 总评论数 * 100
        """
        if total_count == 0:
            return 50.0
        return (negative_count / total_count) * 100
    
    def calculate_intensity(self, positive_count: int, negative_count: int, 
                           total_count: int) -> float:
        """
        计算情绪强度
        
        公式: (积极数 - 消极数) / 总数
        范围: -1 到 1
        """
        if total_count == 0:
            return 0.0
        return (positive_count - negative_count) / total_count
    
    def calculate_temperature(self, sentiments: List[Dict], 
                             total_count: int) -> float:
        """
        计算情绪温度
        
        基于置信度加权的情绪分数
        范围: 0 到 100
        """
        if not sentiments or total_count == 0:
            return 50.0
        
        weighted_sum = 0.0
        weight_total = 0.0
        
        for s in sentiments:
            label = s.get('label', 'neutral')
            confidence = s.get('confidence', 0.5)
            
            # 映射标签到分数
            if label == 'positive':
                score = 1.0
            elif label == 'negative':
                score = 0.0
            else:
                score = 0.5
            
            weighted_sum += score * confidence
            weight_total += confidence
        
        if weight_total == 0:
            return 50.0
        
        # 归一化到0-100
        return (weighted_sum / weight_total) * 100
    
    def calculate_volatility(self, intensities: List[float]) -> float:
        """
        计算情绪波动
        
        使用情绪强度的标准差
        """
        if len(intensities) < 2:
            return 0.0
        return float(np.std(intensities))
    
    def calculate_metrics(self, sentiments: List[Dict]) -> EmotionMetrics:
        """
        计算所有情绪指标
        
        Args:
            sentiments: 情感分析结果列表
                [{'label': 'positive', 'confidence': 0.9}, ...]
        
        Returns:
            EmotionMetrics对象
        """
        total_count = len(sentiments)
        
        if total_count == 0:
            return EmotionMetrics()
        
        # 统计各类别数量
        positive_count = sum(1 for s in sentiments if s.get('label') == 'positive')
        neutral_count = sum(1 for s in sentiments if s.get('label') == 'neutral')
        negative_count = sum(1 for s in sentiments if s.get('label') == 'negative')
        
        # 计算指标
        bull_index = self.calculate_bull_index(positive_count, total_count)
        bear_index = self.calculate_bear_index(negative_count, total_count)
        intensity = self.calculate_intensity(positive_count, negative_count, total_count)
        temperature = self.calculate_temperature(sentiments, total_count)
        
        return EmotionMetrics(
            total_count=total_count,
            positive_count=positive_count,
            neutral_count=neutral_count,
            negative_count=negative_count,
            bull_index=bull_index,
            bear_index=bear_index,
            intensity=intensity,
            temperature=temperature,
            volatility=0.0  # 需要历史数据计算
        )
    
    def aggregate_by_stock(self, db_session, stock_code: str, 
                          target_date: date) -> EmotionMetrics:
        """
        按股票聚合当日情绪指标
        """
        # 获取当日评论的情感分析结果
        results = db_session.query(
            Sentiment.label,
            Sentiment.confidence
        ).join(
            Comment, Comment.comment_id == Sentiment.comment_id
        ).filter(
            Comment.stock_code == stock_code,
            Comment.publish_time >= target_date,
            Comment.publish_time < target_date + timedelta(days=1)
        ).all()
        
        sentiments = [{'label': r.label, 'confidence': float(r.confidence)} 
                     for r in results]
        
        return self.calculate_metrics(sentiments)
    
    def aggregate_by_hour(self, db_session, stock_code: str,
                         target_date: date, hour: int) -> EmotionMetrics:
        """
        按小时聚合情绪指标
        """
        start_time = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=hour)
        end_time = start_time + timedelta(hours=1)
        
        results = db_session.query(
            Sentiment.label,
            Sentiment.confidence
        ).join(
            Comment, Comment.comment_id == Sentiment.comment_id
        ).filter(
            Comment.stock_code == stock_code,
            Comment.publish_time >= start_time,
            Comment.publish_time < end_time
        ).all()
        
        sentiments = [{'label': r.label, 'confidence': float(r.confidence)} 
                     for r in results]
        
        return self.calculate_metrics(sentiments)


class EmotionService:
    """情绪量化服务"""
    
    def __init__(self):
        self.calculator = EmotionCalculator()
    
    def compute_daily_emotion(self, stock_code: str, target_date: date) -> Optional[Emotion]:
        """
        计算并保存单只股票的日级情绪指标
        """
        db = SessionLocal()
        try:
            metrics = self.calculator.aggregate_by_stock(db, stock_code, target_date)
            
            if metrics.total_count == 0:
                return None
            
            # 查找或创建记录
            emotion = db.query(Emotion).filter(
                Emotion.stock_code == stock_code,
                Emotion.stat_date == target_date,
                Emotion.stat_hour.is_(None)
            ).first()
            
            if emotion:
                # 更新
                emotion.total_count = metrics.total_count
                emotion.positive_count = metrics.positive_count
                emotion.neutral_count = metrics.neutral_count
                emotion.negative_count = metrics.negative_count
                emotion.bull_index = metrics.bull_index
                emotion.bear_index = metrics.bear_index
                emotion.intensity = metrics.intensity
                emotion.temperature = metrics.temperature
                emotion.volatility = metrics.volatility
            else:
                # 创建
                emotion = Emotion(
                    stock_code=stock_code,
                    stat_date=target_date,
                    stat_hour=None,
                    total_count=metrics.total_count,
                    positive_count=metrics.positive_count,
                    neutral_count=metrics.neutral_count,
                    negative_count=metrics.negative_count,
                    bull_index=metrics.bull_index,
                    bear_index=metrics.bear_index,
                    intensity=metrics.intensity,
                    temperature=metrics.temperature,
                    volatility=metrics.volatility
                )
                db.add(emotion)
            
            db.commit()
            logger.info(f"Computed emotion for {stock_code} on {target_date}")
            return emotion
            
        except Exception as e:
            db.rollback()
            logger.error(f"Compute daily emotion error: {e}")
            return None
        finally:
            db.close()
    
    def compute_hourly_emotion(self, stock_code: str, target_date: date) -> List[Emotion]:
        """
        计算单只股票的小时级情绪指标
        """
        db = SessionLocal()
        emotions = []
        
        try:
            for hour in range(24):
                metrics = self.calculator.aggregate_by_hour(db, stock_code, target_date, hour)
                
                if metrics.total_count == 0:
                    continue
                
                # 查找或创建记录
                emotion = db.query(Emotion).filter(
                    Emotion.stock_code == stock_code,
                    Emotion.stat_date == target_date,
                    Emotion.stat_hour == hour
                ).first()
                
                if emotion:
                    emotion.total_count = metrics.total_count
                    emotion.positive_count = metrics.positive_count
                    emotion.neutral_count = metrics.neutral_count
                    emotion.negative_count = metrics.negative_count
                    emotion.bull_index = metrics.bull_index
                    emotion.bear_index = metrics.bear_index
                    emotion.intensity = metrics.intensity
                    emotion.temperature = metrics.temperature
                else:
                    emotion = Emotion(
                        stock_code=stock_code,
                        stat_date=target_date,
                        stat_hour=hour,
                        total_count=metrics.total_count,
                        positive_count=metrics.positive_count,
                        neutral_count=metrics.neutral_count,
                        negative_count=metrics.negative_count,
                        bull_index=metrics.bull_index,
                        bear_index=metrics.bear_index,
                        intensity=metrics.intensity,
                        temperature=metrics.temperature
                    )
                    db.add(emotion)
                
                emotions.append(emotion)
            
            db.commit()
            logger.info(f"Computed {len(emotions)} hourly emotions for {stock_code} on {target_date}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Compute hourly emotion error: {e}")
        finally:
            db.close()
        
        return emotions
    
    def compute_all_stocks(self, target_date: date):
        """
        计算所有股票的情绪指标
        """
        db = SessionLocal()
        try:
            # 获取有评论的股票列表
            stocks = db.query(Comment.stock_code).filter(
                Comment.publish_time >= target_date,
                Comment.publish_time < target_date + timedelta(days=1)
            ).distinct().all()
            
            stock_codes = [s[0] for s in stocks if s[0]]
            
            logger.info(f"Computing emotions for {len(stock_codes)} stocks on {target_date}")
            
            for code in stock_codes:
                self.compute_daily_emotion(code, target_date)
            
        finally:
            db.close()
    
    def calculate_volatility_for_period(self, stock_code: str, 
                                        start_date: date, 
                                        end_date: date) -> float:
        """
        计算一段时间内的情绪波动
        """
        db = SessionLocal()
        try:
            emotions = db.query(Emotion.intensity).filter(
                Emotion.stock_code == stock_code,
                Emotion.stat_date >= start_date,
                Emotion.stat_date <= end_date,
                Emotion.stat_hour.is_(None)
            ).all()
            
            intensities = [float(e[0]) for e in emotions if e[0] is not None]
            
            return self.calculator.calculate_volatility(intensities)
            
        finally:
            db.close()


# 服务单例
_emotion_service: Optional[EmotionService] = None


def get_emotion_service() -> EmotionService:
    """获取情绪量化服务单例"""
    global _emotion_service
    if _emotion_service is None:
        _emotion_service = EmotionService()
    return _emotion_service
