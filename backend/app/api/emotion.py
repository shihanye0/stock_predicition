"""
情绪指标API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta

from app.core.database import get_db
from app.models.models import Stock, Emotion, Comment, Sentiment
from app.models.schemas import Response, ListResponse

router = APIRouter()


@router.get("/emotion/overview", response_model=Response, summary="获取市场情绪概览")
async def get_emotion_overview(db: Session = Depends(get_db)):
    """获取市场整体情绪概览"""
    today = date.today()
    week_ago = today - timedelta(days=7)
    
    # 获取最近一周的情绪数据
    emotions = db.query(
        Emotion.stat_date,
        func.avg(Emotion.bull_index).label('avg_bull'),
        func.avg(Emotion.bear_index).label('avg_bear'),
        func.avg(Emotion.intensity).label('avg_intensity'),
        func.sum(Emotion.total_count).label('total_comments')
    ).filter(
        Emotion.stat_date >= week_ago,
        Emotion.stat_hour.is_(None)  # 日级数据
    ).group_by(Emotion.stat_date).order_by(Emotion.stat_date).all()
    
    # 计算整体情绪
    if emotions:
        latest = emotions[-1]
        avg_bull = float(latest.avg_bull) if latest.avg_bull else 50
        avg_bear = float(latest.avg_bear) if latest.avg_bear else 50
        
        if avg_bull > avg_bear + 10:
            market_sentiment = "bullish"
        elif avg_bear > avg_bull + 10:
            market_sentiment = "bearish"
        else:
            market_sentiment = "neutral"
    else:
        market_sentiment = "neutral"
        avg_bull = 50
        avg_bear = 50
    
    # 获取热门股票（按评论数排序）
    hot_stocks = db.query(
        Emotion.stock_code,
        Stock.stock_name,
        Emotion.bull_index,
        Emotion.bear_index,
        Emotion.total_count
    ).join(Stock, Emotion.stock_code == Stock.stock_code).filter(
        Emotion.stat_date == today,
        Emotion.stat_hour.is_(None)
    ).order_by(Emotion.total_count.desc()).limit(10).all()
    
    # 构建趋势数据
    trend = []
    for e in emotions:
        trend.append({
            "date": e.stat_date.isoformat(),
            "bull_index": float(e.avg_bull) if e.avg_bull else 0,
            "bear_index": float(e.avg_bear) if e.avg_bear else 0,
            "intensity": float(e.avg_intensity) if e.avg_intensity else 0,
            "comment_count": int(e.total_comments) if e.total_comments else 0
        })
    
    return Response(data={
        "market_sentiment": market_sentiment,
        "avg_bull_index": round(avg_bull, 2),
        "avg_bear_index": round(avg_bear, 2),
        "hot_stocks": [
            {
                "stock_code": s.stock_code,
                "stock_name": s.stock_name,
                "bull_index": float(s.bull_index) if s.bull_index else 0,
                "bear_index": float(s.bear_index) if s.bear_index else 0,
                "comment_count": s.total_count
            } for s in hot_stocks
        ],
        "recent_trend": trend
    })


@router.get("/emotion/trend", response_model=Response, summary="获取情绪趋势数据")
async def get_emotion_trend(
    stock_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    granularity: str = Query("day", enum=["hour", "day", "week"]),
    db: Session = Depends(get_db)
):
    """获取情绪趋势数据"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    query = db.query(Emotion).filter(
        Emotion.stat_date >= start_date,
        Emotion.stat_date <= end_date
    )
    
    if stock_code:
        query = query.filter(Emotion.stock_code == stock_code)
    
    if granularity == "hour":
        query = query.filter(Emotion.stat_hour.isnot(None))
    else:
        query = query.filter(Emotion.stat_hour.is_(None))
    
    emotions = query.order_by(Emotion.stat_date, Emotion.stat_hour).all()
    
    result = []
    for e in emotions:
        item = {
            "date": e.stat_date.isoformat(),
            "stock_code": e.stock_code,
            "total_count": e.total_count,
            "positive_count": e.positive_count,
            "neutral_count": e.neutral_count,
            "negative_count": e.negative_count,
            "bull_index": float(e.bull_index) if e.bull_index else 0,
            "bear_index": float(e.bear_index) if e.bear_index else 0,
            "intensity": float(e.intensity) if e.intensity else 0,
            "temperature": float(e.temperature) if e.temperature else 0
        }
        if e.stat_hour is not None:
            item["hour"] = e.stat_hour
        result.append(item)
    
    return Response(data={
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "granularity": granularity,
        "trend": result
    })


@router.get("/emotion/ranking", response_model=ListResponse, summary="获取情绪排行榜")
async def get_emotion_ranking(
    sort_by: str = Query("bull_index", enum=["bull_index", "bear_index", "intensity", "total_count"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取股票情绪排行榜"""
    today = date.today()
    
    query = db.query(
        Emotion.stock_code,
        Stock.stock_name,
        Emotion.bull_index,
        Emotion.bear_index,
        Emotion.intensity,
        Emotion.total_count,
        Emotion.temperature
    ).join(Stock, Emotion.stock_code == Stock.stock_code).filter(
        Emotion.stat_date == today,
        Emotion.stat_hour.is_(None)
    )
    
    # 排序
    sort_column = getattr(Emotion, sort_by)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    results = query.limit(limit).all()
    
    data = []
    for r in results:
        data.append({
            "stock_code": r.stock_code,
            "stock_name": r.stock_name,
            "bull_index": float(r.bull_index) if r.bull_index else 0,
            "bear_index": float(r.bear_index) if r.bear_index else 0,
            "intensity": float(r.intensity) if r.intensity else 0,
            "total_count": r.total_count,
            "temperature": float(r.temperature) if r.temperature else 0
        })
    
    return ListResponse(data=data, total=len(data))


@router.get("/stocks/{code}/emotion", response_model=Response, summary="获取股票情绪")
async def get_stock_emotion(
    code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    granularity: str = Query("day", enum=["hour", "day"]),
    db: Session = Depends(get_db)
):
    """获取指定股票的情绪数据"""
    # 获取股票信息
    stock = db.query(Stock).filter(Stock.stock_code == code).first()
    if not stock:
        return Response(code=404, message="Stock not found", data=None)
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    query = db.query(Emotion).filter(
        Emotion.stock_code == code,
        Emotion.stat_date >= start_date,
        Emotion.stat_date <= end_date
    )
    
    if granularity == "hour":
        query = query.filter(Emotion.stat_hour.isnot(None))
    else:
        query = query.filter(Emotion.stat_hour.is_(None))
    
    emotions = query.order_by(Emotion.stat_date, Emotion.stat_hour).all()
    
    # 计算汇总
    total_comments = sum(e.total_count for e in emotions)
    avg_bull = sum(float(e.bull_index or 0) for e in emotions) / len(emotions) if emotions else 0
    avg_bear = sum(float(e.bear_index or 0) for e in emotions) / len(emotions) if emotions else 0
    avg_intensity = sum(float(e.intensity or 0) for e in emotions) / len(emotions) if emotions else 0
    
    # 构建趋势数据
    trend = []
    for e in emotions:
        item = {
            "date": e.stat_date.isoformat(),
            "bull_index": float(e.bull_index) if e.bull_index else 0,
            "bear_index": float(e.bear_index) if e.bear_index else 0,
            "intensity": float(e.intensity) if e.intensity else 0,
            "temperature": float(e.temperature) if e.temperature else 0,
            "comment_count": e.total_count
        }
        if e.stat_hour is not None:
            item["hour"] = e.stat_hour
        trend.append(item)
    
    return Response(data={
        "stock_code": code,
        "stock_name": stock.stock_name,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "summary": {
            "avg_bull_index": round(avg_bull, 2),
            "avg_bear_index": round(avg_bear, 2),
            "avg_intensity": round(avg_intensity, 4),
            "total_comments": total_comments
        },
        "trend": trend
    })
