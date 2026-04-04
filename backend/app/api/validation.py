"""
市场验证API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta
import numpy as np
from scipy import stats

from app.core.database import get_db
from app.models.models import Stock, Emotion, Quote
from app.models.schemas import Response

router = APIRouter()


@router.get("/validation/correlation", response_model=Response, summary="获取情绪-行情相关性")
async def get_correlation(
    stock_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    计算情绪指标与股票行情的相关性
    
    使用Pearson相关系数
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)
    
    # 获取情绪数据
    emotion_query = db.query(
        Emotion.stock_code,
        Emotion.stat_date,
        Emotion.intensity
    ).filter(
        Emotion.stat_date >= start_date,
        Emotion.stat_date <= end_date,
        Emotion.stat_hour.is_(None)
    )
    
    if stock_code:
        emotion_query = emotion_query.filter(Emotion.stock_code == stock_code)
    
    emotions = emotion_query.all()
    
    # 按股票分组
    emotion_dict = {}
    for e in emotions:
        if e.stock_code not in emotion_dict:
            emotion_dict[e.stock_code] = {}
        emotion_dict[e.stock_code][e.stat_date] = float(e.intensity) if e.intensity else 0
    
    # 获取行情数据
    quote_query = db.query(
        Quote.stock_code,
        Quote.trade_date,
        Quote.change_pct
    ).filter(
        Quote.trade_date >= start_date,
        Quote.trade_date <= end_date
    )
    
    if stock_code:
        quote_query = quote_query.filter(Quote.stock_code == stock_code)
    
    quotes = quote_query.all()
    
    # 按股票分组
    quote_dict = {}
    for q in quotes:
        if q.stock_code not in quote_dict:
            quote_dict[q.stock_code] = {}
        quote_dict[q.stock_code][q.trade_date] = float(q.change_pct) if q.change_pct else 0
    
    # 计算相关性
    results = []
    for code in emotion_dict:
        if code not in quote_dict:
            continue
        
        # 对齐日期
        common_dates = set(emotion_dict[code].keys()) & set(quote_dict[code].keys())
        if len(common_dates) < 10:
            continue
        
        sorted_dates = sorted(common_dates)
        emotion_values = [emotion_dict[code][d] for d in sorted_dates]
        quote_values = [quote_dict[code][d] for d in sorted_dates]
        
        # 计算Pearson相关系数
        if len(emotion_values) > 1:
            correlation = np.corrcoef(emotion_values, quote_values)[0, 1]
            if not np.isnan(correlation):
                # 获取股票名称
                stock = db.query(Stock).filter(Stock.stock_code == code).first()
                stock_name = stock.stock_name if stock else code
                
                results.append({
                    "stock_code": code,
                    "stock_name": stock_name,
                    "correlation": round(correlation, 4),
                    "sample_size": len(sorted_dates),
                    "significance": "high" if abs(correlation) > 0.5 else "medium" if abs(correlation) > 0.3 else "low"
                })
    
    # 按相关性排序
    results.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    
    return Response(data={
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "correlations": results[:50]  # 返回前50个
    })


@router.get("/validation/accuracy", response_model=Response, summary="获取预测准确率")
async def get_accuracy(
    stock_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    lag_days: int = Query(1, ge=0, le=5),
    db: Session = Depends(get_db)
):
    """
    计算情绪预测股价方向的准确率
    
    lag_days: 情绪领先天数
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)
    
    # 获取情绪数据
    emotion_query = db.query(
        Emotion.stock_code,
        Emotion.stat_date,
        Emotion.intensity
    ).filter(
        Emotion.stat_date >= start_date,
        Emotion.stat_date <= end_date,
        Emotion.stat_hour.is_(None)
    )
    
    if stock_code:
        emotion_query = emotion_query.filter(Emotion.stock_code == stock_code)
    
    emotions = emotion_query.all()
    
    # 获取行情数据（需要多取几天用于计算lag）
    extended_end = end_date + timedelta(days=lag_days + 5)
    quote_query = db.query(
        Quote.stock_code,
        Quote.trade_date,
        Quote.change_pct
    ).filter(
        Quote.trade_date >= start_date,
        Quote.trade_date <= extended_end
    )
    
    if stock_code:
        quote_query = quote_query.filter(Quote.stock_code == stock_code)
    
    quotes = quote_query.all()
    
    # 构建数据字典
    emotion_dict = {}
    for e in emotions:
        key = (e.stock_code, e.stat_date)
        emotion_dict[key] = float(e.intensity) if e.intensity else 0
    
    quote_dict = {}
    for q in quotes:
        key = (q.stock_code, q.trade_date)
        quote_dict[key] = float(q.change_pct) if q.change_pct else 0
    
    # 计算准确率
    results = {}
    for (code, emotion_date), intensity in emotion_dict.items():
        # 计算目标日期（考虑lag）
        target_date = emotion_date + timedelta(days=lag_days)
        target_key = (code, target_date)
        
        if target_key not in quote_dict:
            continue
        
        if code not in results:
            results[code] = {"correct": 0, "total": 0}
        
        change_pct = quote_dict[target_key]
        
        # 判断方向是否一致
        emotion_direction = 1 if intensity > 0 else -1 if intensity < 0 else 0
        price_direction = 1 if change_pct > 0 else -1 if change_pct < 0 else 0
        
        if emotion_direction == price_direction:
            results[code]["correct"] += 1
        results[code]["total"] += 1
    
    # 计算每只股票的准确率
    accuracy_list = []
    for code, stats in results.items():
        if stats["total"] >= 10:
            accuracy = stats["correct"] / stats["total"]
            stock = db.query(Stock).filter(Stock.stock_code == code).first()
            accuracy_list.append({
                "stock_code": code,
                "stock_name": stock.stock_name if stock else code,
                "accuracy": round(accuracy, 4),
                "sample_size": stats["total"]
            })
    
    # 计算整体准确率
    total_correct = sum(r["correct"] for r in results.values())
    total_samples = sum(r["total"] for r in results.values())
    overall_accuracy = total_correct / total_samples if total_samples > 0 else 0
    
    accuracy_list.sort(key=lambda x: x["accuracy"], reverse=True)
    
    return Response(data={
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "lag_days": lag_days,
        "overall_accuracy": round(overall_accuracy, 4),
        "total_samples": total_samples,
        "stock_accuracies": accuracy_list[:50]
    })


@router.get("/validation/report", response_model=Response, summary="获取验证报告")
async def get_validation_report(
    stock_code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """生成单只股票的完整验证报告"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)
    
    # 获取股票信息
    stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()
    if not stock:
        return Response(code=404, message="Stock not found", data=None)
    
    # 获取情绪数据
    emotions = db.query(Emotion).filter(
        Emotion.stock_code == stock_code,
        Emotion.stat_date >= start_date,
        Emotion.stat_date <= end_date,
        Emotion.stat_hour.is_(None)
    ).order_by(Emotion.stat_date).all()
    
    # 获取行情数据
    quotes = db.query(Quote).filter(
        Quote.stock_code == stock_code,
        Quote.trade_date >= start_date,
        Quote.trade_date <= end_date
    ).order_by(Quote.trade_date).all()
    
    # 对齐数据
    emotion_dict = {e.stat_date: e for e in emotions}
    quote_dict = {q.trade_date: q for q in quotes}
    common_dates = sorted(set(emotion_dict.keys()) & set(quote_dict.keys()))
    
    # 构建对比数据
    comparison = []
    correct_predictions = 0
    total_predictions = 0
    
    for d in common_dates:
        e = emotion_dict[d]
        q = quote_dict[d]
        
        intensity = float(e.intensity) if e.intensity else 0
        change_pct = float(q.change_pct) if q.change_pct else 0
        
        # 判断预测是否正确
        is_correct = (intensity > 0 and change_pct > 0) or (intensity < 0 and change_pct < 0)
        if intensity != 0:
            total_predictions += 1
            if is_correct:
                correct_predictions += 1
        
        comparison.append({
            "date": d.isoformat(),
            "emotion_intensity": round(intensity, 4),
            "bull_index": float(e.bull_index) if e.bull_index else 0,
            "bear_index": float(e.bear_index) if e.bear_index else 0,
            "change_pct": round(change_pct, 2),
            "close_price": float(q.close_price) if q.close_price else 0,
            "volume": q.volume,
            "prediction_correct": is_correct
        })
    
    # 计算相关系数
    if len(common_dates) > 1:
        intensities = [float(emotion_dict[d].intensity or 0) for d in common_dates]
        changes = [float(quote_dict[d].change_pct or 0) for d in common_dates]
        correlation = np.corrcoef(intensities, changes)[0, 1]
        correlation = round(correlation, 4) if not np.isnan(correlation) else 0
    else:
        correlation = 0
    
    accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
    
    return Response(data={
        "stock_code": stock_code,
        "stock_name": stock.stock_name,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "summary": {
            "correlation": correlation,
            "accuracy": round(accuracy, 4),
            "total_samples": len(common_dates),
            "correct_predictions": correct_predictions
        },
        "comparison": comparison
    })


@router.get("/validation/granger", response_model=Response, summary="格兰杰因果检验")
async def granger_causality_test(
    stock_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    max_lag: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    格兰杰因果检验
    
    检验情绪指标是否对股价变化具有预测能力
    
    Args:
        stock_code: 股票代码（留空则检验所有股票）
        start_date: 开始日期
        end_date: 结束日期
        max_lag: 最大滞后期数
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=90)
    
    # 获取情绪数据
    emotion_query = db.query(
        Emotion.stock_code,
        Emotion.stat_date,
        Emotion.bull_index,
        Emotion.intensity
    ).filter(
        Emotion.stat_date >= start_date,
        Emotion.stat_date <= end_date,
        Emotion.stat_hour.is_(None)
    )
    
    if stock_code:
        emotion_query = emotion_query.filter(Emotion.stock_code == stock_code)
    
    emotions = emotion_query.order_by(Emotion.stock_code, Emotion.stat_date).all()
    
    # 获取行情数据
    quote_query = db.query(
        Quote.stock_code,
        Quote.trade_date,
        Quote.change_pct
    ).filter(
        Quote.trade_date >= start_date,
        Quote.trade_date <= end_date
    )
    
    if stock_code:
        quote_query = quote_query.filter(Quote.stock_code == stock_code)
    
    quotes = quote_query.order_by(Quote.stock_code, Quote.trade_date).all()
    
    # 按股票分组
    emotion_dict = {}
    for e in emotions:
        if e.stock_code not in emotion_dict:
            emotion_dict[e.stock_code] = {}
        emotion_dict[e.stock_code][e.stat_date] = {
            'bull_index': float(e.bull_index) if e.bull_index else 50,
            'intensity': float(e.intensity) if e.intensity else 0
        }
    
    quote_dict = {}
    for q in quotes:
        if q.stock_code not in quote_dict:
            quote_dict[q.stock_code] = {}
        quote_dict[q.stock_code][q.trade_date] = float(q.change_pct) if q.change_pct else 0
    
    # 对每只股票进行格兰杰检验
    results = []
    
    for code in emotion_dict:
        if code not in quote_dict:
            continue
        
        # 对齐日期
        common_dates = sorted(set(emotion_dict[code].keys()) & set(quote_dict[code].keys()))
        
        if len(common_dates) < max_lag + 10:
            continue
        
        # 构建时间序列
        emotion_series = [emotion_dict[code][d]['bull_index'] for d in common_dates]
        price_series = [quote_dict[code][d] for d in common_dates]
        
        # 简化的格兰杰因果检验
        granger_results = simple_granger_test(emotion_series, price_series, max_lag)
        
        if granger_results:
            stock = db.query(Stock).filter(Stock.stock_code == code).first()
            stock_name = stock.stock_name if stock else code
            
            # 找出最佳滞后期
            best_lag = min(granger_results.items(), key=lambda x: x[1]['p_value'])
            
            results.append({
                "stock_code": code,
                "stock_name": stock_name,
                "sample_size": len(common_dates),
                "best_lag": best_lag[0],
                "best_p_value": round(best_lag[1]['p_value'], 4),
                "is_significant": best_lag[1]['p_value'] < 0.05,
                "causality_direction": "emotion_causes_price" if best_lag[1]['p_value'] < 0.05 else "no_causality",
                "lag_results": {
                    str(lag): {
                        "f_statistic": round(res['f_statistic'], 4),
                        "p_value": round(res['p_value'], 4),
                        "is_significant": res['p_value'] < 0.05
                    }
                    for lag, res in granger_results.items()
                }
            })
    
    # 按显著性排序
    results.sort(key=lambda x: x['best_p_value'])
    
    # 统计摘要
    significant_count = sum(1 for r in results if r['is_significant'])
    
    return Response(data={
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "max_lag": max_lag,
        "summary": {
            "total_stocks": len(results),
            "significant_count": significant_count,
            "significance_rate": round(significant_count / len(results), 4) if results else 0
        },
        "results": results[:50]  # 返回前50个
    })


def simple_granger_test(x_series, y_series, max_lag):
    """
    简化的格兰杰因果检验
    
    检验x是否格兰杰引起y
    
    原理：比较仅用y的滞后项预测y vs 用y和x的滞后项共同预测y
    如果后者显著更好，则x对y有格兰杰因果关系
    """
    import numpy as np
    
    n = len(x_series)
    results = {}
    
    for lag in range(1, max_lag + 1):
        if n <= lag * 2:
            continue
        
        # 构建滞后矩阵
        y = np.array(y_series[lag:])
        
        # 只用y的滞后项（受限模型）
        X_restricted = np.zeros((n - lag, lag))
        for i in range(lag):
            X_restricted[:, i] = y_series[lag - 1 - i:n - 1 - i]
        
        # 加入x的滞后项（完整模型）
        X_unrestricted = np.zeros((n - lag, lag * 2))
        X_unrestricted[:, :lag] = X_restricted
        for i in range(lag):
            X_unrestricted[:, lag + i] = x_series[lag - 1 - i:n - 1 - i]
        
        try:
            # 受限模型回归
            X_r = np.column_stack([np.ones(len(y)), X_restricted])
            beta_r = np.linalg.lstsq(X_r, y, rcond=None)[0]
            y_pred_r = X_r @ beta_r
            rss_r = np.sum((y - y_pred_r) ** 2)
            
            # 完整模型回归
            X_u = np.column_stack([np.ones(len(y)), X_unrestricted])
            beta_u = np.linalg.lstsq(X_u, y, rcond=None)[0]
            y_pred_u = X_u @ beta_u
            rss_u = np.sum((y - y_pred_u) ** 2)
            
            # F统计量
            df1 = lag  # 限制数量
            df2 = len(y) - 2 * lag - 1  # 残差自由度
            
            if df2 > 0 and rss_u > 0:
                f_stat = ((rss_r - rss_u) / df1) / (rss_u / df2)
                p_value = 1 - stats.f.cdf(f_stat, df1, df2)
                
                results[lag] = {
                    'f_statistic': f_stat,
                    'p_value': p_value
                }
        except Exception:
            continue
    
    return results if results else None
