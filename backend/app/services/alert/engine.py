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
    ),
    # ========== 新增预警规则 ==========
    AlertRule(
        name="情绪趋势反转",
        alert_type="sentiment_reversal",
        description="连续3天同向变化后突然反向"
    ),
    AlertRule(
        name="舆情爆发",
        alert_type="burst_activity",
        description="单小时评论量超过近期峰值2倍"
    ),
    AlertRule(
        name="行业联动预警",
        alert_type="sector_linkage",
        description="同行业3只以上股票同时异常"
    ),
    AlertRule(
        name="波动率异常",
        alert_type="volatility_anomaly",
        description="情绪波动率超过历史均值2个标准差"
    ),
    AlertRule(
        name="极值突破",
        alert_type="new_high_low",
        description="创30天新高或新低"
    ),
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
            
            # 获取股票信息
            stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()
            stock_name = stock.stock_name if stock else stock_code
            stock_industry = stock.industry if stock else None

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

                elif rule.alert_type == "sentiment_reversal":
                    alert = self._check_sentiment_reversal(
                        rule, stock_code, stock_name,
                        bull_history, latest.stat_date
                    )

                elif rule.alert_type == "volatility_anomaly":
                    volatility_history = [float(e.volatility or 0) for e in history]
                    latest_volatility = float(latest.volatility or 0)
                    if latest_volatility > 0:
                        alert = self._check_std_deviation(
                            rule, stock_code, stock_name,
                            latest_volatility, volatility_history,
                            "波动率", latest.stat_date
                        )

                elif rule.alert_type == "new_high_low":
                    alert = self._check_new_high_low(
                        rule, stock_code, stock_name,
                        latest_bull, bull_history, "看涨指数", latest.stat_date
                    )

                if alert:
                    alerts.append(alert)

            # 检查行业联动预警（在循环外进行，避免重复检查）
            if stock_industry:
                sector_alert = self._check_sector_linkage(
                    stock_code, stock_name, stock_industry, db
                )
                if sector_alert:
                    alerts.append(sector_alert)

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

    def _check_sentiment_reversal(self, rule: AlertRule, stock_code: str,
                                   stock_name: str, history: List[float],
                                   trigger_date: date) -> Optional[Dict]:
        """
        检查情绪趋势反转
        连续3天同向变化后突然反向
        """
        if len(history) < 4:
            return None

        changes = []
        for i in range(1, len(history)):
            changes.append(history[i] - history[i-1])

        if len(changes) < 3:
            return None

        last_3 = changes[-3:]
        same_direction = all(d > 0 for d in last_3) or all(d < 0 for d in last_3)

        if not same_direction:
            return None

        today_change = history[-1] - history[-2] if len(history) >= 2 else 0
        is_reversal = (last_3[0] > 0 and today_change < 0) or (last_3[0] < 0 and today_change > 0)

        if is_reversal:
            direction = "转跌" if last_3[0] > 0 else "转涨"
            return {
                "stock_code": stock_code,
                "alert_type": rule.alert_type,
                "severity": "medium",
                "title": f"{stock_name} 情绪趋势{direction}",
                "message": (
                    f"{stock_name}({stock_code}) 看涨指数连续3天{'上涨' if last_3[0] > 0 else '下跌'}后出现反转，"
                    f"可能预示短期趋势改变。"
                ),
                "metric_value": float(np.mean(last_3)),
                "threshold": 0,
                "triggered_at": datetime.combine(trigger_date, datetime.min.time())
            }

        return None

    def _check_new_high_low(self, rule: AlertRule, stock_code: str,
                            stock_name: str, current_value: float,
                            history: List[float], metric_name: str,
                            trigger_date: date) -> Optional[Dict]:
        """
        检查极值突破
        创30天新高或新低
        """
        if not history:
            return None

        max_val = max(history)
        min_val = min(history)

        if current_value > max_val:
            return {
                "stock_code": stock_code,
                "alert_type": rule.alert_type,
                "severity": "high",
                "title": f"{stock_name} {metric_name}创30日新高",
                "message": (
                    f"{stock_name}({stock_code}) {metric_name}达到{current_value:.1f}，"
                    f"创30日新高，市场情绪极度乐观。"
                ),
                "metric_value": current_value,
                "threshold": max_val,
                "triggered_at": datetime.combine(trigger_date, datetime.min.time())
            }
        elif current_value < min_val:
            return {
                "stock_code": stock_code,
                "alert_type": rule.alert_type,
                "severity": "high",
                "title": f"{stock_name} {metric_name}创30日新低",
                "message": (
                    f"{stock_name}({stock_code}) {metric_name}降至{current_value:.1f}，"
                    f"创30日新低，市场情绪极度悲观。"
                ),
                "metric_value": current_value,
                "threshold": min_val,
                "triggered_at": datetime.combine(trigger_date, datetime.min.time())
            }

        return None

    def _check_sector_linkage(self, stock_code: str, stock_name: str,
                              industry: str, db) -> Optional[Dict]:
        """
        检查行业联动预警
        同行业3只以上股票同时异常
        """
        if not industry:
            return None

        try:
            same_industry = db.query(Stock).filter(
                Stock.industry == industry,
                Stock.status == 1,
                Stock.stock_code != stock_code
            ).all()

            if len(same_industry) < 2:
                return None

            end_date = date.today()
            start_date = end_date - timedelta(days=7)

            anomalous_stocks = []
            for s in same_industry:
                emotions = db.query(Emotion).filter(
                    Emotion.stock_code == s.stock_code,
                    Emotion.stat_date >= start_date,
                    Emotion.stat_date <= end_date,
                    Emotion.stat_hour.is_(None)
                ).order_by(Emotion.stat_date.desc()).first()

                if emotions:
                    intensity = float(emotions.intensity or 0.5)
                    if intensity > 0.7 or intensity < 0.3:
                        anomalous_stocks.append(s.stock_name)

            if len(anomalous_stocks) >= 2:
                return {
                    "stock_code": stock_code,
                    "alert_type": "sector_linkage",
                    "severity": "high",
                    "title": f"{industry}板块出现联动异动",
                    "message": (
                        f"{stock_name}({stock_code})触发的{industry}板块预警，"
                        f"该板块多只股票同时出现情绪异常：{', '.join(anomalous_stocks[:3])}等。"
                        f"可能存在行业性重大事件。"
                    ),
                    "metric_value": float(len(anomalous_stocks)),
                    "threshold": 2,
                    "triggered_at": datetime.now()
                }

        except Exception as e:
            logger.error(f"Check sector linkage error for {stock_code}: {e}")

        return None

    def _check_hourly_burst(self, stock_code: str, stock_name: str, db) -> Optional[Dict]:
        """
        检查小时级别舆情爆发
        需要检查小时级情绪数据
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)

            hourly_data = db.query(Emotion).filter(
                Emotion.stock_code == stock_code,
                Emotion.stat_hour.isnot(None),
                Emotion.stat_date >= start_time.date()
            ).order_by(Emotion.stat_date, Emotion.stat_hour).all()

            if len(hourly_data) < 5:
                return None

            counts = [d.total_count for d in hourly_data]
            max_count = max(counts)
            max_idx = counts.index(max_count)

            avg_count = np.mean(counts)
            if max_count > avg_count * 3 and max_count > 50:
                return {
                    "stock_code": stock_code,
                    "alert_type": "burst_activity",
                    "severity": "high" if max_count > avg_count * 5 else "medium",
                    "title": f"{stock_name} 舆情突然爆发",
                    "message": (
                        f"{stock_name}({stock_code}) 在最近24小时内出现评论激增，"
                        f"峰值达到{max_count}条/小时，是均值的{max_count/avg_count:.1f}倍，"
                        f"可能存在重大消息刺激。"
                    ),
                    "metric_value": float(max_count),
                    "threshold": avg_count * 3,
                    "triggered_at": hourly_data[max_idx].triggered_at if hasattr(hourly_data[max_idx], 'triggered_at') else datetime.now()
                }

        except Exception as e:
            logger.error(f"Check hourly burst error for {stock_code}: {e}")

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
