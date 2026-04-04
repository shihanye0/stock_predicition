"""
市场验证服务 - 情绪与行情相关性分析
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from scipy import stats
from loguru import logger

from app.core.database import SessionLocal
from app.models.models import Emotion, Quote


@dataclass
class CorrelationResult:
    """相关性分析结果"""
    stock_code: str
    correlation: float
    p_value: float
    sample_size: int
    lag_days: int = 0
    significance: str = "low"  # low/medium/high
    
    def to_dict(self) -> Dict:
        return {
            'stock_code': self.stock_code,
            'correlation': round(self.correlation, 4),
            'p_value': round(self.p_value, 4),
            'sample_size': self.sample_size,
            'lag_days': self.lag_days,
            'significance': self.significance
        }


@dataclass
class AccuracyResult:
    """准确率分析结果"""
    stock_code: str
    accuracy: float
    correct_count: int
    total_count: int
    
    def to_dict(self) -> Dict:
        return {
            'stock_code': self.stock_code,
            'accuracy': round(self.accuracy, 4),
            'correct_count': self.correct_count,
            'total_count': self.total_count
        }


class MarketValidator:
    """
    市场验证器
    
    验证情绪指标与市场走势的相关性
    """
    
    def calculate_correlation(self, emotion_values: List[float], 
                             quote_values: List[float]) -> Tuple[float, float]:
        """
        计算Pearson相关系数
        
        Returns:
            (correlation, p_value)
        """
        if len(emotion_values) < 3 or len(quote_values) < 3:
            return 0.0, 1.0
        
        try:
            correlation, p_value = stats.pearsonr(emotion_values, quote_values)
            if np.isnan(correlation):
                return 0.0, 1.0
            return float(correlation), float(p_value)
        except Exception as e:
            logger.error(f"Calculate correlation error: {e}")
            return 0.0, 1.0
    
    def calculate_spearman(self, emotion_values: List[float],
                          quote_values: List[float]) -> Tuple[float, float]:
        """
        计算Spearman秩相关系数
        """
        if len(emotion_values) < 3 or len(quote_values) < 3:
            return 0.0, 1.0
        
        try:
            correlation, p_value = stats.spearmanr(emotion_values, quote_values)
            if np.isnan(correlation):
                return 0.0, 1.0
            return float(correlation), float(p_value)
        except Exception as e:
            logger.error(f"Calculate spearman error: {e}")
            return 0.0, 1.0
    
    def get_significance_level(self, correlation: float, p_value: float) -> str:
        """判断相关性显著程度"""
        if p_value > 0.05:
            return "not_significant"
        
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            return "high"
        elif abs_corr >= 0.4:
            return "medium"
        else:
            return "low"
    
    def analyze_correlation(self, stock_code: str,
                           start_date: date,
                           end_date: date,
                           lag_days: int = 0) -> Optional[CorrelationResult]:
        """
        分析单只股票的情绪-行情相关性
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            lag_days: 情绪领先天数（0表示同日）
        
        Returns:
            CorrelationResult对象
        """
        db = SessionLocal()
        try:
            # 获取情绪数据
            emotions = db.query(
                Emotion.stat_date,
                Emotion.intensity
            ).filter(
                Emotion.stock_code == stock_code,
                Emotion.stat_date >= start_date,
                Emotion.stat_date <= end_date,
                Emotion.stat_hour.is_(None)
            ).order_by(Emotion.stat_date).all()
            
            # 获取行情数据
            quotes = db.query(
                Quote.trade_date,
                Quote.change_pct
            ).filter(
                Quote.stock_code == stock_code,
                Quote.trade_date >= start_date,
                Quote.trade_date <= end_date + timedelta(days=lag_days)
            ).order_by(Quote.trade_date).all()
            
            if len(emotions) < 10 or len(quotes) < 10:
                return None
            
            # 构建数据字典
            emotion_dict = {e.stat_date: float(e.intensity or 0) for e in emotions}
            quote_dict = {q.trade_date: float(q.change_pct or 0) for q in quotes}
            
            # 对齐数据（考虑lag）
            emotion_values = []
            quote_values = []
            
            for emotion_date, intensity in emotion_dict.items():
                target_date = emotion_date + timedelta(days=lag_days)
                if target_date in quote_dict:
                    emotion_values.append(intensity)
                    quote_values.append(quote_dict[target_date])
            
            if len(emotion_values) < 10:
                return None
            
            # 计算相关性
            correlation, p_value = self.calculate_correlation(emotion_values, quote_values)
            significance = self.get_significance_level(correlation, p_value)
            
            return CorrelationResult(
                stock_code=stock_code,
                correlation=correlation,
                p_value=p_value,
                sample_size=len(emotion_values),
                lag_days=lag_days,
                significance=significance
            )
            
        finally:
            db.close()
    
    def find_optimal_lag(self, stock_code: str,
                        start_date: date,
                        end_date: date,
                        max_lag: int = 5) -> Tuple[int, float]:
        """
        寻找最优领先天数
        
        Returns:
            (optimal_lag, max_correlation)
        """
        best_lag = 0
        best_corr = 0.0
        
        for lag in range(max_lag + 1):
            result = self.analyze_correlation(stock_code, start_date, end_date, lag)
            if result and abs(result.correlation) > abs(best_corr):
                best_lag = lag
                best_corr = result.correlation
        
        return best_lag, best_corr
    
    def analyze_direction_accuracy(self, stock_code: str,
                                   start_date: date,
                                   end_date: date,
                                   lag_days: int = 1) -> Optional[AccuracyResult]:
        """
        分析情绪预测涨跌方向的准确率
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            lag_days: 情绪领先天数
        
        Returns:
            AccuracyResult对象
        """
        db = SessionLocal()
        try:
            # 获取情绪数据
            emotions = db.query(
                Emotion.stat_date,
                Emotion.intensity
            ).filter(
                Emotion.stock_code == stock_code,
                Emotion.stat_date >= start_date,
                Emotion.stat_date <= end_date,
                Emotion.stat_hour.is_(None)
            ).all()
            
            # 获取行情数据
            quotes = db.query(
                Quote.trade_date,
                Quote.change_pct
            ).filter(
                Quote.stock_code == stock_code,
                Quote.trade_date >= start_date,
                Quote.trade_date <= end_date + timedelta(days=lag_days + 5)
            ).all()
            
            if len(emotions) < 10 or len(quotes) < 10:
                return None
            
            # 构建数据字典
            emotion_dict = {e.stat_date: float(e.intensity or 0) for e in emotions}
            quote_dict = {q.trade_date: float(q.change_pct or 0) for q in quotes}
            
            # 计算准确率
            correct = 0
            total = 0
            
            for emotion_date, intensity in emotion_dict.items():
                target_date = emotion_date + timedelta(days=lag_days)
                if target_date not in quote_dict:
                    continue
                
                change_pct = quote_dict[target_date]
                
                # 判断方向
                emotion_direction = 1 if intensity > 0 else (-1 if intensity < 0 else 0)
                price_direction = 1 if change_pct > 0 else (-1 if change_pct < 0 else 0)
                
                # 忽略中性情况
                if emotion_direction == 0:
                    continue
                
                total += 1
                if emotion_direction == price_direction:
                    correct += 1
            
            if total == 0:
                return None
            
            return AccuracyResult(
                stock_code=stock_code,
                accuracy=correct / total,
                correct_count=correct,
                total_count=total
            )
            
        finally:
            db.close()
    
    def granger_causality_test(self, emotion_values: List[float],
                               quote_values: List[float],
                               max_lag: int = 5) -> Dict:
        """
        格兰杰因果检验
        
        检验情绪是否是股价的格兰杰原因
        """
        try:
            from statsmodels.tsa.stattools import grangercausalitytests
            
            if len(emotion_values) < max_lag * 3:
                return {"error": "Insufficient data"}
            
            # 构建数据矩阵 [y, x] - 检验x是否是y的格兰杰原因
            data = np.column_stack([quote_values, emotion_values])
            
            # 进行检验
            results = grangercausalitytests(data, max_lag, verbose=False)
            
            # 提取结果
            test_results = {}
            for lag in range(1, max_lag + 1):
                if lag in results:
                    f_test = results[lag][0]['ssr_ftest']
                    test_results[f'lag_{lag}'] = {
                        'f_statistic': float(f_test[0]),
                        'p_value': float(f_test[1]),
                        'significant': f_test[1] < 0.05
                    }
            
            return test_results
            
        except ImportError:
            logger.warning("statsmodels not available for Granger test")
            return {"error": "statsmodels not installed"}
        except Exception as e:
            logger.error(f"Granger test error: {e}")
            return {"error": str(e)}
    
    def generate_validation_report(self, stock_code: str,
                                   start_date: date,
                                   end_date: date) -> Dict:
        """
        生成完整的验证报告
        """
        report = {
            'stock_code': stock_code,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'correlation_analysis': {},
            'accuracy_analysis': {},
            'optimal_lag': {},
            'granger_test': {}
        }
        
        # 相关性分析（不同lag）
        for lag in [0, 1, 2, 3]:
            result = self.analyze_correlation(stock_code, start_date, end_date, lag)
            if result:
                report['correlation_analysis'][f'lag_{lag}'] = result.to_dict()
        
        # 准确率分析
        accuracy = self.analyze_direction_accuracy(stock_code, start_date, end_date, 1)
        if accuracy:
            report['accuracy_analysis'] = accuracy.to_dict()
        
        # 最优领先天数
        optimal_lag, max_corr = self.find_optimal_lag(stock_code, start_date, end_date)
        report['optimal_lag'] = {
            'lag_days': optimal_lag,
            'correlation': round(max_corr, 4)
        }
        
        return report


# 验证器单例
_validator: Optional[MarketValidator] = None


def get_market_validator() -> MarketValidator:
    """获取市场验证器单例"""
    global _validator
    if _validator is None:
        _validator = MarketValidator()
    return _validator
