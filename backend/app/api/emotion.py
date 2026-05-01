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

    # 查找最近有数据的日期
    latest_date = db.query(func.max(Emotion.stat_date)).filter(
        Emotion.stat_hour.is_(None)
    ).scalar()

    # 获取热门股票（按评论数排序）- 使用最近可用日期
    hot_stocks_query = db.query(
        Emotion.stock_code,
        Stock.stock_name,
        Emotion.bull_index,
        Emotion.bear_index,
        Emotion.total_count
    ).join(Stock, Emotion.stock_code == Stock.stock_code).filter(
        Emotion.stat_hour.is_(None)
    )

    if latest_date:
        hot_stocks_query = hot_stocks_query.filter(Emotion.stat_date == latest_date)
    else:
        hot_stocks_query = hot_stocks_query.filter(Emotion.stat_date == today)

    hot_stocks = hot_stocks_query.order_by(Emotion.total_count.desc()).limit(10).all()
    
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
    limit: Optional[int] = Query(None, ge=1, le=500, description="限制返回数据点数量，0或None表示返回全部"),
    db: Session = Depends(get_db)
):
    """获取情绪趋势数据"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # 当没有指定股票时，返回按日期聚合的市场平均情绪
    if not stock_code:
        query = db.query(
            Emotion.stat_date,
            func.avg(Emotion.bull_index).label('bull_index'),
            func.avg(Emotion.bear_index).label('bear_index'),
            func.avg(Emotion.intensity).label('intensity'),
            func.avg(Emotion.temperature).label('temperature'),
            func.sum(Emotion.total_count).label('total_count'),
            func.sum(Emotion.positive_count).label('positive_count'),
            func.sum(Emotion.neutral_count).label('neutral_count'),
            func.sum(Emotion.negative_count).label('negative_count')
        ).filter(
            Emotion.stat_date >= start_date,
            Emotion.stat_date <= end_date
        )

        if granularity == "hour":
            query = query.filter(Emotion.stat_hour.isnot(None))
            query = query.group_by(Emotion.stat_date, Emotion.stat_hour)
        else:
            query = query.filter(Emotion.stat_hour.is_(None))
            query = query.group_by(Emotion.stat_date)

        query = query.order_by(Emotion.stat_date, Emotion.stat_hour if granularity == "hour" else None)
        emotions = query.all()

        result = []
        for e in emotions:
            item = {
                "date": e.stat_date.isoformat() if hasattr(e, 'stat_date') else str(e[0]),
                "total_count": int(e.total_count) if e.total_count else 0,
                "positive_count": int(e.positive_count) if e.positive_count else 0,
                "neutral_count": int(e.neutral_count) if e.neutral_count else 0,
                "negative_count": int(e.negative_count) if e.negative_count else 0,
                "bull_index": round(float(e.bull_index), 2) if e.bull_index else 0,
                "bear_index": round(float(e.bear_index), 2) if e.bear_index else 0,
                "intensity": round(float(e.intensity), 4) if e.intensity else 0,
                "temperature": round(float(e.temperature), 2) if e.temperature else 0
            }
            result.append(item)

    else:
        # 指定了股票代码，返回该股票的数据
        query = db.query(Emotion).filter(
            Emotion.stock_code == stock_code,
            Emotion.stat_date >= start_date,
            Emotion.stat_date <= end_date
        )

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

    # 如果指定了limit，进行均匀采样
    if limit and limit > 0 and len(result) > limit:
        step = len(result) / limit
        result = [result[round(i * step)] for i in range(limit)]

    return Response(data={
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "granularity": granularity,
        "trend": result,
        "total_points": len(result),
        "is_sampled": limit > 0 if limit else False
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

    # 查找最近有数据的日期
    latest_date = db.query(func.max(Emotion.stat_date)).filter(
        Emotion.stat_hour.is_(None)
    ).scalar()

    if not latest_date:
        return ListResponse(data=[], total=0)

    query = db.query(
        Emotion.stock_code,
        Stock.stock_name,
        Emotion.bull_index,
        Emotion.bear_index,
        Emotion.intensity,
        Emotion.total_count,
        Emotion.temperature
    ).join(Stock, Emotion.stock_code == Stock.stock_code).filter(
        Emotion.stat_date == latest_date,
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
    limit: Optional[int] = Query(None, ge=1, le=500, description="限制返回数据点数量"),
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

    # 如果指定了limit，进行均匀采样
    if limit and limit > 0 and len(emotions) > limit:
        step = len(emotions) / limit
        emotions = [emotions[round(i * step)] for i in range(limit)]

    # 计算汇总（基于原始数据）
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
