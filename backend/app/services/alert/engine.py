"""
情绪预警引擎

检测条件：
1. 情绪强度突变（超过2个标准差）
2. 看涨/看跌指数极端值（>85 或 <15）
3. 评论量暴增（超过均值3倍）
4. 情绪温度异常
"""
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger
import numpy as np

from app.core.database import SessionLocal
from app.models.models import Emotion, Stock, Alert, Comment


@dataclass
class AlertRule:
    """预警规则"""
    name: str
    alert_type: str
    description: str
    threshold_std: float = 2.0  # 标准差倍数
    extreme_high: float = 85.0  # 极端高值
    extreme_low: float = 15.0  # 极端低值
    volume_multiplier: float = 3.0  # 评论量倍数


# 预定义规则
DEFAULT_RULES = [
    AlertRule(
        name="情绪强度突变",
        alert_type="intensity_spike",
        description="情绪强度偏离历史均值超过2个标准差"
    ),
    AlertRule(
        name="看涨指数极端",
        alert_type="bull_extreme",
        description="看涨指数达到极端值(>85或<15)"
    ),
    AlertRule(
        name="看跌指数极端",
        alert_type="bear_extreme",
        description="看跌指数达到极端值(>85或<15)"
    ),
    AlertRule(
        name="评论量暴增",
        alert_type="volume_surge",
        description="单日评论量超过近期均值3倍"
    ),
    AlertRule(
        name="情绪温度异常",
        alert_type="temperature_anomaly",
        description="情绪温度偏离历史均值超过2个标准差"
    )
]


class AlertEngine:
    """
    情绪预警引擎
    
    定期扫描所有股票的情绪指标，当满足预警条件时生成预警记录
    """
    
    def __init__(self, rules: Optional[List[AlertRule]] = None):
        self.rules = rules or DEFAULT_RULES
    
    def scan_stock(self, stock_code: str, lookback_days: int = 30) -> List[Dict]:
        """
        扫描单只股票的情绪预警
        
        Args:
            stock_code: 股票代码
            lookback_days: 回溯天数
            
        Returns:
            预警列表
        """
        db = SessionLocal()
        alerts = []
        
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=lookback_days)
            
            # 获取历史情绪数据
            emotions = db.query(Emotion).filter(
                Emotion.stock_code == stock_code,
                Emotion.stat_date >= start_date,
                Emotion.stat_date <= end_date,
                Emotion.stat_hour.is_(None)
            ).order_by(Emotion.stat_date).all()
            
            if len(emotions) < 5:
                return alerts
            
            # 获取股票名
            stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()
            stock_name = stock.stock_name if stock else stock_code
            
            # 提取最新数据和历史序列
            latest = emotions[-1]
            history = emotions[:-1]
            
            intensity_history = [float(e.intensity or 0) for e in history]
            bull_history = [float(e.bull_index or 50) for e in history]
            bear_history = [float(e.bear_index or 50) for e in history]
            temp_history = [float(e.temperature or 50) for e in history]
            count_history = [e.total_count or 0 for e in history]
            
            latest_intensity = float(latest.intensity or 0)
            latest_bull = float(latest.bull_index or 50)
            latest_bear = float(latest.bear_index or 50)
            latest_temp = float(latest.temperature or 50)
            latest_count = latest.total_count or 0
            
            # 规则检查
            for rule in self.rules:
                alert = None
                
                if rule.alert_type == "intensity_spike":
                    alert = self._check_std_deviation(
                        rule, stock_code, stock_name,
                        latest_intensity, intensity_history,
                        "情绪强度", latest.stat_date
                    )
                
                elif rule.alert_type == "bull_extreme":
                    alert = self._check_extreme(
                        rule, stock_code, stock_name,
                        latest_bull, "看涨指数", latest.stat_date
                    )
                
                elif rule.alert_type == "bear_extreme":
                    alert = self._check_extreme(
                        rule, stock_code, stock_name,
                        latest_bear, "看跌指数", latest.stat_date
                    )
                
                elif rule.alert_type == "volume_surge":
                    alert = self._check_volume_surge(
                        rule, stock_code, stock_name,
                        latest_count, count_history, latest.stat_date
                    )
                
                elif rule.alert_type == "temperature_anomaly":
                    alert = self._check_std_deviation(
                        rule, stock_code, stock_name,
                        latest_temp, temp_history,
                        "情绪温度", latest.stat_date
                    )
                
                if alert:
                    alerts.append(alert)
            
            # 保存预警到数据库
            for alert_data in alerts:
                self._save_alert(db, alert_data)
            
            if alerts:
                db.commit()
                logger.info(f"Generated {len(alerts)} alerts for {stock_code}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Scan stock {stock_code} error: {e}")
        finally:
            db.close()
        
        return alerts
    
    def _check_std_deviation(self, rule: AlertRule, stock_code: str, 
                             stock_name: str, current_value: float,
                             history: List[float], metric_name: str,
                             trigger_date: date) -> Optional[Dict]:
        """检查标准差偏离"""
        if len(history) < 3:
            return None
        
        mean = float(np.mean(history))
        std = float(np.std(history))
        
        if std < 0.001:
            return None
        
        z_score = abs(current_value - mean) / std
        
        if z_score >= rule.threshold_std:
            direction = "上升" if current_value > mean else "下降"
            severity = "high" if z_score >= 3 else "medium"
            
            return {
                "stock_code": stock_code,
                "alert_type": rule.alert_type,
                "severity": severity,
                "title": f"{stock_name} {metric_name}异常{direction}",
                "message": (
                    f"{stock_name}({stock_code}) {metric_name}当前值为{current_value:.4f}，"
                    f"历史均值为{mean:.4f}，偏离{z_score:.1f}个标准差，"
                    f"触发{rule.name}预警。"
                ),
                "metric_value": current_value,
                "threshold": mean + rule.threshold_std * std if current_value > mean else mean - rule.threshold_std * std,
                "triggered_at": datetime.combine(trigger_date, datetime.min.time())
            }
        
        return None
    
    def _check_extreme(self, rule: AlertRule, stock_code: str,
                       stock_name: str, current_value: float,
                       metric_name: str, trigger_date: date) -> Optional[Dict]:
        """检查极端值"""
        if current_value >= rule.extreme_high:
            return {
                "stock_code": stock_code,
                "alert_type": rule.alert_type,
                "severity": "high" if current_value >= 90 else "medium",
                "title": f"{stock_name} {metric_name}极端偏高",
                "message": (
                    f"{stock_name}({stock_code}) {metric_name}达到{current_value:.1f}%，"
                    f"超过极端阈值{rule.extreme_high}%，市场情绪可能过热。"
                ),
                "metric_value": current_value,
                "threshold": rule.extreme_high,
                "triggered_at": datetime.combine(trigger_date, datetime.min.time())
            }
        elif current_value <= rule.extreme_low:
            return {
                "stock_code": stock_code,
                "alert_type": rule.alert_type,
                "severity": "high" if current_value <= 10 else "medium",
                "title": f"{stock_name} {metric_name}极端偏低",
                "message": (
                    f"{stock_name}({stock_code}) {metric_name}仅为{current_value:.1f}%，"
                    f"低于极端阈值{rule.extreme_low}%，市场情绪可能过冷。"
                ),
                "metric_value": current_value,
                "threshold": rule.extreme_low,
                "triggered_at": datetime.combine(trigger_date, datetime.min.time())
            }
        
        return None
    
    def _check_volume_surge(self, rule: AlertRule, stock_code: str,
                            stock_name: str, current_count: int,
                            history: List[int], trigger_date: date) -> Optional[Dict]:
        """检查评论量暴增"""
        if not history or current_count == 0:
            return None
        
        avg_count = float(np.mean(history))
        if avg_count < 1:
            return None
        
        ratio = current_count / avg_count
        
        if ratio >= rule.volume_multiplier:
            return {
                "stock_code": stock_code,
                "alert_type": rule.alert_type,
                "severity": "high" if ratio >= 5 else "medium",
                "title": f"{stock_name} 评论量暴增{ratio:.1f}倍",
                "message": (
                    f"{stock_name}({stock_code}) 今日评论量{current_count}条，"
                    f"是近期日均{avg_count:.0f}条的{ratio:.1f}倍，"
                    f"市场关注度异常升高。"
                ),
                "metric_value": float(current_count),
                "threshold": avg_count * rule.volume_multiplier,
                "triggered_at": datetime.combine(trigger_date, datetime.min.time())
            }
        
        return None
    
    def _save_alert(self, db, alert_data: Dict):
        """保存预警到数据库"""
        try:
            # 检查是否已存在相同预警（同一天同类型同股票）
            existing = db.query(Alert).filter(
                Alert.stock_code == alert_data["stock_code"],
                Alert.alert_type == alert_data["alert_type"],
                Alert.triggered_at >= alert_data["triggered_at"],
            ).first()
            
            if existing:
                return
            
            alert = Alert(
                stock_code=alert_data["stock_code"],
                alert_type=alert_data["alert_type"],
                severity=alert_data["severity"],
                title=alert_data["title"],
                message=alert_data["message"],
                metric_value=alert_data["metric_value"],
                threshold=alert_data["threshold"],
                triggered_at=alert_data["triggered_at"]
            )
            db.add(alert)
            
        except Exception as e:
            logger.error(f"Save alert error: {e}")
    
    def scan_all_stocks(self, lookback_days: int = 30) -> List[Dict]:
        """扫描所有股票"""
        db = SessionLocal()
        all_alerts = []
        
        try:
            stock_codes = db.query(Stock.stock_code).filter(Stock.status == 1).all()
            stock_codes = [s[0] for s in stock_codes]
            
            logger.info(f"Starting alert scan for {len(stock_codes)} stocks")
            
            for code in stock_codes:
                alerts = self.scan_stock(code, lookback_days)
                all_alerts.extend(alerts)
            
            logger.info(f"Alert scan complete: {len(all_alerts)} alerts generated")
            
        finally:
            db.close()
        
        return all_alerts


# 全局单例
_alert_engine: Optional[AlertEngine] = None


def get_alert_engine() -> AlertEngine:
    """获取预警引擎单例"""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine()
    return _alert_engine
