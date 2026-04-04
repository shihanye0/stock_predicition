"""
情感分析API
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.models.schemas import (
    Response, SentimentRequest, SentimentBatchRequest,
    SentimentResult, SentimentResponse, SentimentBatchResponse
)
from app.services.sentiment.analyzer import SentimentAnalyzer

router = APIRouter()

# 初始化情感分析器（延迟加载）
_analyzer = None


def get_analyzer() -> SentimentAnalyzer:
    """获取情感分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer


@router.post("/sentiment/analyze", response_model=SentimentResponse, summary="分析单条文本情感")
async def analyze_sentiment(request: SentimentRequest):
    """
    分析单条文本的情感倾向
    
    返回情感标签（positive/neutral/negative）和置信度
    """
    try:
        analyzer = get_analyzer()
        result = analyzer.analyze(request.text)
        return SentimentResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/sentiment/batch", response_model=SentimentBatchResponse, summary="批量分析文本情感")
async def analyze_sentiment_batch(request: SentimentBatchRequest):
    """
    批量分析多条文本的情感倾向
    
    最多支持100条文本
    """
    try:
        analyzer = get_analyzer()
        results = analyzer.analyze_batch(request.texts)
        return SentimentBatchResponse(data=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.get("/sentiment/stats", response_model=Response, summary="获取分析统计数据")
async def get_sentiment_stats():
    """获取情感分析的统计数据"""
    analyzer = get_analyzer()
    stats = {
        "model_name": analyzer.model_name,
        "model_loaded": analyzer.is_loaded,
        "total_analyzed": analyzer.total_analyzed,
        "labels": ["positive", "neutral", "negative"]
    }
    return Response(data=stats)
