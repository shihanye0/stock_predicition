"""
股票相关API
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app.core.database import get_db
from app.models.models import Stock, Comment, Emotion, Quote, AspectSentiment
from app.models.schemas import (
    Response, ListResponse, StockResponse, CommentResponse
)
from app.services.sentiment.aspect_analyzer import get_aspect_analyzer
from app.services.quantify.profiler import get_profiler

router = APIRouter()


@router.get("/stocks", response_model=ListResponse, summary="获取股票列表")
async def get_stocks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    industry: Optional[str] = None,
    market: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取股票列表"""
    query = db.query(Stock).filter(Stock.status == 1)
    
    if industry:
        query = query.filter(Stock.industry == industry)
    if market:
        query = query.filter(Stock.market == market)
    if keyword:
        query = query.filter(
            (Stock.stock_code.like(f"%{keyword}%")) |
            (Stock.stock_name.like(f"%{keyword}%"))
        )
    
    total = query.count()
    stocks = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return ListResponse(
        data=[StockResponse.model_validate(s) for s in stocks],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/stocks/{code}", response_model=Response, summary="获取股票详情")
async def get_stock(code: str, db: Session = Depends(get_db)):
    """获取股票详情"""
    stock = db.query(Stock).filter(Stock.stock_code == code).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    return Response(data=StockResponse.model_validate(stock).model_dump())


@router.get("/stocks/{code}/comments", response_model=ListResponse, summary="获取股票评论")
async def get_stock_comments(
    code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    platform: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """获取股票评论列表"""
    query = db.query(Comment).filter(Comment.stock_code == code)
    
    if platform:
        query = query.filter(Comment.platform == platform)
    if start_date:
        query = query.filter(Comment.publish_time >= start_date)
    if end_date:
        query = query.filter(Comment.publish_time <= end_date)
    
    query = query.order_by(Comment.publish_time.desc())
    
    total = query.count()
    comments = query.offset((page - 1) * page_size).limit(page_size).all()
    
    result = []
    for c in comments:
        item = {
            "comment_id": c.comment_id,
            "platform": c.platform,
            "stock_code": c.stock_code,
            "content": c.content,
            "content_clean": c.content_clean,
            "author": c.author,
            "publish_time": c.publish_time.isoformat() if c.publish_time else None,
            "likes": c.likes,
            "replies": c.replies,
            "crawl_time": c.crawl_time.isoformat() if c.crawl_time else None,
            "sentiment_label": c.sentiment.label if c.sentiment else None,
            "sentiment_confidence": float(c.sentiment.confidence) if c.sentiment else None
        }
        result.append(item)
    
    return ListResponse(
        data=result,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/stocks/{code}/quotes", response_model=ListResponse, summary="获取股票行情")
async def get_stock_quotes(
    code: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """获取股票历史行情"""
    query = db.query(Quote).filter(Quote.stock_code == code)
    
    if start_date:
        query = query.filter(Quote.trade_date >= start_date)
    if end_date:
        query = query.filter(Quote.trade_date <= end_date)
    
    query = query.order_by(Quote.trade_date.desc())
    quotes = query.all()
    
    result = []
    for q in quotes:
        result.append({
            "trade_date": q.trade_date.isoformat(),
            "open_price": float(q.open_price) if q.open_price else None,
            "close_price": float(q.close_price) if q.close_price else None,
            "high_price": float(q.high_price) if q.high_price else None,
            "low_price": float(q.low_price) if q.low_price else None,
            "change_pct": float(q.change_pct) if q.change_pct else None,
            "volume": q.volume,
            "amount": float(q.amount) if q.amount else None
        })
    
    return ListResponse(data=result, total=len(result))


@router.get("/stocks/{code}/aspects", response_model=Response, summary="获取个股方面级情感分布")
async def get_stock_aspects(
    code: str,
    limit: int = Query(100, ge=10, le=500),
    db: Session = Depends(get_db)
):
    """获取个股的方面级情感分析结果"""
    stock = db.query(Stock).filter(Stock.stock_code == code).first()
    if not stock:
        return Response(code=404, message="Stock not found")
    
    # 查看是否已有方面分析结果
    existing = db.query(AspectSentiment).join(
        Comment, AspectSentiment.comment_id == Comment.comment_id
    ).filter(Comment.stock_code == code).count()
    
    if existing > 0:
        # 从数据库读取已有结果
        aspects_db = db.query(
            AspectSentiment.aspect,
            AspectSentiment.sentiment_label,
            AspectSentiment.confidence,
            AspectSentiment.keywords
        ).join(
            Comment, AspectSentiment.comment_id == Comment.comment_id
        ).filter(Comment.stock_code == code).all()
        
        # 汇总
        summary = {}
        for a in aspects_db:
            name = a.aspect
            if name not in summary:
                summary[name] = {"aspect": name, "total": 0, "positive": 0, "neutral": 0, "negative": 0}
            summary[name]["total"] += 1
            summary[name][a.sentiment_label] += 1
        
        for v in summary.values():
            t = v["total"]
            v["positive_ratio"] = round(v["positive"] / t, 4) if t else 0
            v["negative_ratio"] = round(v["negative"] / t, 4) if t else 0
        
        return Response(data={
            "stock_code": code,
            "stock_name": stock.stock_name,
            "aspects": list(summary.values()),
            "source": "database",
            "total_analyzed": existing
        })
    
    # 实时分析最新评论
    comments = db.query(Comment).filter(
        Comment.stock_code == code
    ).order_by(Comment.publish_time.desc()).limit(limit).all()
    
    if not comments:
        return Response(data={
            "stock_code": code,
            "stock_name": stock.stock_name,
            "aspects": [],
            "source": "realtime",
            "total_analyzed": 0
        })
    
    analyzer = get_aspect_analyzer()
    texts = [c.content for c in comments]
    results = analyzer.analyze_batch(texts)
    
    # 保存到数据库
    for comment, result in zip(comments, results):
        for asp in result.aspects:
            aspect_record = AspectSentiment(
                comment_id=comment.comment_id,
                aspect=asp.aspect,
                sentiment_label=asp.sentiment_label,
                confidence=asp.confidence,
                keywords=",".join(asp.keywords[:5])
            )
            db.add(aspect_record)
    
    try:
        db.commit()
    except Exception:
        db.rollback()
    
    summary = analyzer.get_stock_aspect_summary(results)
    
    return Response(data={
        "stock_code": code,
        "stock_name": stock.stock_name,
        "aspects": list(summary.values()),
        "source": "realtime",
        "total_analyzed": len(comments)
    })


@router.get("/stocks/{code}/profile", response_model=Response, summary="获取个股情绪画像")
async def get_stock_profile(
    code: str,
    days: int = Query(30, ge=7, le=90)
):
    """获取个股综合情绪画像"""
    profiler = get_profiler()
    profile = profiler.generate_profile(code, days)
    return Response(data=profile.to_dict())
