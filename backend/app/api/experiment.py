"""
实验对比API

提供多模型对比分析、基准测试、历史实验结果查询等端点
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger

from app.core.database import get_db
from app.models.models import ExperimentResult, Comment, Sentiment
from app.models.schemas import Response, ListResponse
from app.services.sentiment.multi_model import get_multi_model_manager

router = APIRouter()


class CompareRequest(BaseModel):
    """多模型对比请求"""
    text: str = Field(..., min_length=1, max_length=512, description="待分析文本")


class BenchmarkRequest(BaseModel):
    """基准测试请求"""
    stock_code: Optional[str] = Field(None, description="指定股票代码，不填则使用全部")
    sample_size: int = Field(100, ge=10, le=1000, description="样本量")
    use_labeled: bool = Field(True, description="是否使用已标注数据作为真实标签")


@router.post("/experiment/compare", response_model=Response, summary="多模型对比分析")
async def compare_models(req: CompareRequest):
    """
    使用多个模型同时分析同一文本，返回对比结果
    """
    try:
        manager = get_multi_model_manager()
        result = manager.compare(req.text)
        
        return Response(data={
            "text": result.text,
            "consensus": result.consensus,
            "agreement_rate": result.agreement_rate,
            "results": [
                {
                    "model_name": r.model_name,
                    "label": r.label,
                    "confidence": r.confidence,
                    "scores": r.scores,
                    "elapsed_ms": r.elapsed_ms
                }
                for r in result.results
            ]
        })
    except Exception as e:
        logger.error(f"Compare models error: {e}")
        return Response(code=500, message=str(e))


@router.post("/experiment/benchmark", response_model=Response, summary="运行基准测试")
async def run_benchmark(req: BenchmarkRequest, db: Session = Depends(get_db)):
    """
    在数据库中已标注的评论上运行基准测试
    """
    try:
        # 获取已标注的评论数据
        query = db.query(
            Comment.content,
            Sentiment.label
        ).join(
            Sentiment, Comment.comment_id == Sentiment.comment_id
        )
        
        if req.stock_code:
            query = query.filter(Comment.stock_code == req.stock_code)
        
        samples = query.order_by(Comment.publish_time.desc()).limit(req.sample_size).all()
        
        if not samples:
            return Response(code=404, message="没有找到已标注的评论数据")
        
        texts = [s.content for s in samples]
        labels = [s.label for s in samples] if req.use_labeled else None
        
        # 运行基准测试
        manager = get_multi_model_manager()
        benchmark_results = manager.benchmark(texts, labels)
        
        # 保存实验结果到数据库
        dataset_name = f"stock_{req.stock_code}" if req.stock_code else "all_stocks"
        for model_name, metrics in benchmark_results.items():
            exp = ExperimentResult(
                model_name=model_name,
                dataset_name=dataset_name,
                accuracy=metrics.get("accuracy"),
                f1_score=metrics.get("f1_score"),
                precision_score=metrics.get("precision_score"),
                recall_score=metrics.get("recall_score"),
                confusion_matrix=metrics.get("confusion_matrix"),
                classification_report=metrics.get("classification_report"),
                run_time=metrics.get("run_time"),
                sample_count=metrics.get("sample_count")
            )
            db.add(exp)
        
        db.commit()
        
        return Response(data={
            "dataset": dataset_name,
            "sample_count": len(texts),
            "has_labels": labels is not None,
            "results": benchmark_results
        })
        
    except Exception as e:
        db.rollback()
        logger.error(f"Benchmark error: {e}")
        return Response(code=500, message=str(e))


@router.get("/experiment/results", response_model=ListResponse, summary="获取历史实验结果")
async def get_experiment_results(
    model_name: Optional[str] = None,
    dataset_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取历史实验结果列表"""
    query = db.query(ExperimentResult)
    
    if model_name:
        query = query.filter(ExperimentResult.model_name == model_name)
    if dataset_name:
        query = query.filter(ExperimentResult.dataset_name == dataset_name)
    
    total = query.count()
    results = query.order_by(ExperimentResult.created_at.desc())\
        .offset((page - 1) * page_size).limit(page_size).all()
    
    data = []
    for r in results:
        data.append({
            "id": r.id,
            "model_name": r.model_name,
            "dataset_name": r.dataset_name,
            "accuracy": r.accuracy,
            "f1_score": r.f1_score,
            "precision_score": r.precision_score,
            "recall_score": r.recall_score,
            "confusion_matrix": r.confusion_matrix,
            "classification_report": r.classification_report,
            "run_time": r.run_time,
            "sample_count": r.sample_count,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })
    
    return ListResponse(data=data, total=total, page=page, page_size=page_size)


@router.get("/experiment/metrics", response_model=Response, summary="获取模型性能指标汇总")
async def get_experiment_metrics(db: Session = Depends(get_db)):
    """获取各模型最新一次实验的性能指标对比"""
    from sqlalchemy import func
    
    # 获取每个模型最新的实验结果
    subq = db.query(
        ExperimentResult.model_name,
        func.max(ExperimentResult.id).label("max_id")
    ).group_by(ExperimentResult.model_name).subquery()
    
    latest_results = db.query(ExperimentResult).join(
        subq, ExperimentResult.id == subq.c.max_id
    ).all()
    
    if not latest_results:
        # 返回默认的模型状态
        manager = get_multi_model_manager()
        model_status = manager.get_model_status()
        return Response(data={
            "models": model_status,
            "comparison": [],
            "message": "暂无实验结果，请先运行基准测试"
        })
    
    comparison = []
    for r in latest_results:
        comparison.append({
            "model_name": r.model_name,
            "accuracy": r.accuracy,
            "f1_score": r.f1_score,
            "precision_score": r.precision_score,
            "recall_score": r.recall_score,
            "run_time": r.run_time,
            "sample_count": r.sample_count,
            "confusion_matrix": r.confusion_matrix,
            "classification_report": r.classification_report,
            "tested_at": r.created_at.isoformat() if r.created_at else None
        })
    
    return Response(data={"comparison": comparison})


@router.get("/experiment/models", response_model=Response, summary="获取可用模型列表")
async def get_available_models():
    """获取所有可用的情感分析模型及其状态"""
    manager = get_multi_model_manager()
    status = manager.get_model_status()
    return Response(data={"models": status})
