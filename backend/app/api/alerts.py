"""
预警管理API

提供预警列表查询、标记已读、触发扫描、预警统计等端点
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, timedelta

from app.core.database import get_db
from app.models.models import Alert, Stock
from app.models.schemas import Response, ListResponse
from app.services.alert.engine import get_alert_engine
from loguru import logger

router = APIRouter()


@router.get("/alerts", response_model=ListResponse, summary="获取预警列表")
async def get_alerts(
    stock_code: Optional[str] = None,
    severity: Optional[str] = Query(None, enum=["high", "medium", "low"]),
    alert_type: Optional[str] = None,
    is_read: Optional[int] = Query(None, ge=0, le=1),
    days: int = Query(30, ge=1, le=365),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取预警列表"""
    try:
        query = db.query(Alert).join(Stock, Alert.stock_code == Stock.stock_code)

        start_date = date.today() - timedelta(days=days)
        query = query.filter(Alert.triggered_at >= start_date)

        if stock_code:
            query = query.filter(Alert.stock_code == stock_code)
        if severity:
            query = query.filter(Alert.severity == severity)
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        if is_read is not None:
            query = query.filter(Alert.is_read == is_read)

        total = query.count()
        alerts = query.order_by(Alert.triggered_at.desc())\
            .offset((page - 1) * page_size).limit(page_size).all()

        data = []
        for a in alerts:
            data.append({
                "id": a.id,
                "stock_code": a.stock_code,
                "stock_name": a.stock.stock_name if a.stock else "",
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "metric_value": a.metric_value,
                "threshold": a.threshold,
                "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
                "is_read": a.is_read
            })

        return ListResponse(data=data, total=total, page=page, page_size=page_size)
    except Exception as e:
        logger.error(f"Get alerts error: {e}")
        return ListResponse(data=[], total=0, page=page, page_size=page_size)


@router.put("/alerts/{alert_id}/read", response_model=Response, summary="标记预警已读")
async def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    """标记单条预警为已读"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_read = 1
    db.commit()
    
    return Response(message="标记成功")


@router.put("/alerts/read-all", response_model=Response, summary="全部标记已读")
async def mark_all_read(
    stock_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """将所有未读预警标记为已读"""
    query = db.query(Alert).filter(Alert.is_read == 0)
    if stock_code:
        query = query.filter(Alert.stock_code == stock_code)
    
    count = query.update({"is_read": 1})
    db.commit()
    
    return Response(message=f"已标记{count}条预警为已读")


@router.post("/alerts/scan", response_model=Response, summary="触发预警扫描")
async def trigger_scan(
    stock_code: Optional[str] = None,
    lookback_days: int = Query(30, ge=7, le=90)
):
    """手动触发预警扫描"""
    try:
        engine = get_alert_engine()
        
        if stock_code:
            alerts = engine.scan_stock(stock_code, lookback_days)
        else:
            alerts = engine.scan_all_stocks(lookback_days)
        
        return Response(data={
            "scanned": stock_code or "all",
            "alerts_generated": len(alerts),
            "alerts": alerts[:20]  # 最多返回20条
        })
    except Exception as e:
        logger.error(f"Alert scan error: {e}")
        return Response(code=500, message=str(e))


@router.get("/alerts/stats", response_model=Response, summary="预警统计")
async def get_alert_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """获取预警统计信息"""
    try:
        start_date = date.today() - timedelta(days=days)

        # 总数 & 未读数
        total = db.query(Alert).filter(Alert.triggered_at >= start_date).count()
        unread = db.query(Alert).filter(
            Alert.triggered_at >= start_date,
            Alert.is_read == 0
        ).count()

        # 按严重程度统计
        severity_stats = db.query(
            Alert.severity,
            func.count(Alert.id).label("count")
        ).filter(
            Alert.triggered_at >= start_date
        ).group_by(Alert.severity).all()

        # 按类型统计
        type_stats = db.query(
            Alert.alert_type,
            func.count(Alert.id).label("count")
        ).filter(
            Alert.triggered_at >= start_date
        ).group_by(Alert.alert_type).all()

        # 按股票统计TOP10
        stock_stats = db.query(
            Alert.stock_code,
            Stock.stock_name,
            func.count(Alert.id).label("count")
        ).join(Stock, Alert.stock_code == Stock.stock_code).filter(
            Alert.triggered_at >= start_date
        ).group_by(Alert.stock_code, Stock.stock_name)\
         .order_by(func.count(Alert.id).desc()).limit(10).all()

        return Response(data={
            "period_days": days,
            "total": total,
            "unread": unread,
            "by_severity": {s.severity: s.count for s in severity_stats},
            "by_type": {t.alert_type: t.count for t in type_stats},
            "by_stock": [
                {"stock_code": s.stock_code, "stock_name": s.stock_name, "count": s.count}
                for s in stock_stats
            ]
        })
    except Exception as e:
        logger.error(f"Get alert stats error: {e}")
        return Response(data={
            "period_days": days,
            "total": 0,
            "unread": 0,
            "by_severity": {},
            "by_type": {},
            "by_stock": []
        })
