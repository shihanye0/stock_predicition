"""
个股情绪画像模块

为每只股票生成综合情绪画像，包含：
- 情绪波动性
- 偏向性（偏多/偏空）
- 活跃度
- 情绪周期特征
- 与行情关联度
- 画像标签
"""
from datetime import date, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from loguru import logger
import numpy as np

from app.core.database import SessionLocal
from app.models.models import Emotion, Quote, Stock, Comment, Sentiment


@dataclass
class EmotionProfile:
    """个股情绪画像"""
    stock_code: str
    stock_name: str = ""
    period_days: int = 30
    
    # 核心特征
    volatility: float = 0.0  # 波动性 (0-1)
    bias: float = 0.0  # 偏向性 (-1偏空 ~ 1偏多)
    activity: float = 0.0  # 活跃度 (0-1)
    consistency: float = 0.0  # 一致性 (0-1)
    
    # 统计指标
    avg_bull_index: float = 50.0
    avg_bear_index: float = 50.0
    avg_intensity: float = 0.0
    avg_temperature: float = 50.0
    total_comments: int = 0
    daily_avg_comments: float = 0.0
    
    # 趋势特征
    trend_direction: str = "stable"  # rising/falling/stable
    momentum: float = 0.0  # 动量
    
    # 行情关联
    price_correlation: float = 0.0  # 与涨跌幅的相关性
    
    # 画像标签
    tags: List[str] = field(default_factory=list)
    
    # 雷达图数据
    radar_data: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "period_days": self.period_days,
            "features": {
                "volatility": round(self.volatility, 4),
                "bias": round(self.bias, 4),
                "activity": round(self.activity, 4),
                "consistency": round(self.consistency, 4)
            },
            "statistics": {
                "avg_bull_index": round(self.avg_bull_index, 2),
                "avg_bear_index": round(self.avg_bear_index, 2),
                "avg_intensity": round(self.avg_intensity, 4),
                "avg_temperature": round(self.avg_temperature, 2),
                "total_comments": self.total_comments,
                "daily_avg_comments": round(self.daily_avg_comments, 1)
            },
            "trend": {
                "direction": self.trend_direction,
                "momentum": round(self.momentum, 4)
            },
            "price_correlation": round(self.price_correlation, 4),
            "tags": self.tags,
            "radar_data": self.radar_data
        }


class StockEmotionProfiler:
    """
    个股情绪画像分析器
    """
    
    def generate_profile(self, stock_code: str, days: int = 30) -> EmotionProfile:
        """
        生成个股情绪画像
        
        Args:
            stock_code: 股票代码
            days: 分析周期天数
            
        Returns:
            EmotionProfile
        """
        db = SessionLocal()
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # 获取股票信息
            stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()
            stock_name = stock.stock_name if stock else ""
            
            profile = EmotionProfile(
                stock_code=stock_code,
                stock_name=stock_name,
                period_days=days
            )
            
            # 获取情绪数据
            emotions = db.query(Emotion).filter(
                Emotion.stock_code == stock_code,
                Emotion.stat_date >= start_date,
                Emotion.stat_date <= end_date,
                Emotion.stat_hour.is_(None)
            ).order_by(Emotion.stat_date).all()
            
            if not emotions:
                profile.tags = ["数据不足"]
                profile.radar_data = self._build_radar(profile)
                return profile
            
            # 提取序列数据
            bull_series = [float(e.bull_index or 50) for e in emotions]
            bear_series = [float(e.bear_index or 50) for e in emotions]
            intensity_series = [float(e.intensity or 0) for e in emotions]
            temp_series = [float(e.temperature or 50) for e in emotions]
            count_series = [e.total_count or 0 for e in emotions]
            
            # 1. 波动性
            if len(intensity_series) >= 2:
                profile.volatility = min(float(np.std(intensity_series)), 1.0)
            
            # 2. 偏向性 (正=偏多, 负=偏空)
            profile.bias = float(np.mean(intensity_series))
            
            # 3. 活跃度 (基于评论量)
            total = sum(count_series)
            profile.total_comments = total
            profile.daily_avg_comments = total / max(len(count_series), 1)
            # 归一化: 日均50条以上为高活跃
            profile.activity = min(profile.daily_avg_comments / 50.0, 1.0)
            
            # 4. 一致性 (情绪方向一致的天数占比)
            if len(intensity_series) >= 2:
                positive_days = sum(1 for x in intensity_series if x > 0.1)
                negative_days = sum(1 for x in intensity_series if x < -0.1)
                dominant_count = max(positive_days, negative_days)
                profile.consistency = dominant_count / len(intensity_series)
            
            # 5. 统计指标
            profile.avg_bull_index = float(np.mean(bull_series))
            profile.avg_bear_index = float(np.mean(bear_series))
            profile.avg_intensity = float(np.mean(intensity_series))
            profile.avg_temperature = float(np.mean(temp_series))
            
            # 6. 趋势方向
            if len(intensity_series) >= 3:
                recent = intensity_series[-3:]
                earlier = intensity_series[:3]
                recent_mean = np.mean(recent)
                earlier_mean = np.mean(earlier)
                diff = recent_mean - earlier_mean
                
                if diff > 0.1:
                    profile.trend_direction = "rising"
                elif diff < -0.1:
                    profile.trend_direction = "falling"
                else:
                    profile.trend_direction = "stable"
                
                profile.momentum = float(diff)
            
            # 7. 与行情关联度
            quotes = db.query(Quote).filter(
                Quote.stock_code == stock_code,
                Quote.trade_date >= start_date,
                Quote.trade_date <= end_date
            ).order_by(Quote.trade_date).all()
            
            if quotes and len(emotions) >= 3:
                profile.price_correlation = self._calc_correlation(emotions, quotes)
            
            # 8. 生成画像标签
            profile.tags = self._generate_tags(profile)
            
            # 9. 雷达图数据
            profile.radar_data = self._build_radar(profile)
            
            return profile
            
        except Exception as e:
            logger.error(f"Generate profile error for {stock_code}: {e}")
            return EmotionProfile(stock_code=stock_code, tags=["分析异常"])
        finally:
            db.close()
    
    def _calc_correlation(self, emotions: list, quotes: list) -> float:
        """计算情绪与行情的相关性"""
        try:
            # 按日期对齐
            emotion_map = {e.stat_date: float(e.intensity or 0) for e in emotions}
            quote_map = {}
            for q in quotes:
                if q.change_pct is not None:
                    quote_map[q.trade_date] = float(q.change_pct)
            
            common_dates = sorted(set(emotion_map.keys()) & set(quote_map.keys()))
            
            if len(common_dates) < 3:
                return 0.0
            
            emo_vals = [emotion_map[d] for d in common_dates]
            price_vals = [quote_map[d] for d in common_dates]
            
            if np.std(emo_vals) < 1e-10 or np.std(price_vals) < 1e-10:
                return 0.0
            
            corr = float(np.corrcoef(emo_vals, price_vals)[0, 1])
            return corr if not np.isnan(corr) else 0.0
            
        except Exception:
            return 0.0
    
    def _generate_tags(self, profile: EmotionProfile) -> List[str]:
        """基于画像特征生成标签"""
        tags = []
        
        # 偏向性标签
        if profile.bias > 0.2:
            tags.append("多头主导")
        elif profile.bias < -0.2:
            tags.append("空头主导")
        else:
            tags.append("多空均衡")
        
        # 波动性标签
        if profile.volatility > 0.3:
            tags.append("情绪敏感型")
        elif profile.volatility < 0.1:
            tags.append("情绪稳定型")
        else:
            tags.append("波动适中")
        
        # 活跃度标签
        if profile.activity > 0.6:
            tags.append("高关注度")
        elif profile.activity < 0.2:
            tags.append("低关注度")
        
        # 趋势标签
        if profile.trend_direction == "rising":
            tags.append("情绪升温")
        elif profile.trend_direction == "falling":
            tags.append("情绪降温")
        
        # 一致性标签
        if profile.consistency > 0.7:
            tags.append("方向明确")
        elif profile.consistency < 0.4:
            tags.append("分歧较大")
        
        # 关联度标签
        if abs(profile.price_correlation) > 0.5:
            tags.append("情绪-行情强关联")
        elif abs(profile.price_correlation) < 0.2:
            tags.append("情绪-行情弱关联")
        
        return tags
    
    def _build_radar(self, profile: EmotionProfile) -> Dict:
        """构建雷达图数据"""
        # 归一化到0-100
        return {
            "indicators": [
                {"name": "波动性", "max": 100},
                {"name": "偏多度", "max": 100},
                {"name": "活跃度", "max": 100},
                {"name": "一致性", "max": 100},
                {"name": "关联度", "max": 100}
            ],
            "values": [
                round(profile.volatility * 100, 1),
                round((profile.bias + 1) * 50, 1),  # -1~1 映射到 0~100
                round(profile.activity * 100, 1),
                round(profile.consistency * 100, 1),
                round(abs(profile.price_correlation) * 100, 1)
            ]
        }


# 全局单例
_profiler: Optional[StockEmotionProfiler] = None


def get_profiler() -> StockEmotionProfiler:
    """获取个股情绪画像分析器单例"""
    global _profiler
    if _profiler is None:
        _profiler = StockEmotionProfiler()
    return _profiler
