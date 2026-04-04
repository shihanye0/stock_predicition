"""
Pydantic数据模式定义
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


# ============== 通用响应 ==============

class ResponseBase(BaseModel):
    """通用响应基类"""
    code: int = 200
    message: str = "success"
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()))


class Response(ResponseBase):
    """通用响应"""
    data: Optional[dict] = None


class ListResponse(ResponseBase):
    """列表响应"""
    data: List = []
    total: int = 0
    page: int = 1
    page_size: int = 20


# ============== 股票相关 ==============

class StockBase(BaseModel):
    """股票基础信息"""
    stock_code: str
    stock_name: str
    industry: Optional[str] = None
    market: Optional[str] = None


class StockCreate(StockBase):
    """创建股票"""
    list_date: Optional[date] = None


class StockResponse(StockBase):
    """股票响应"""
    list_date: Optional[date] = None
    status: int = 1
    
    class Config:
        from_attributes = True


# ============== 评论相关 ==============

class CommentBase(BaseModel):
    """评论基础信息"""
    platform: str
    stock_code: str
    content: str
    author: Optional[str] = None
    publish_time: datetime


class CommentCreate(CommentBase):
    """创建评论"""
    comment_id: str
    likes: int = 0
    replies: int = 0


class CommentResponse(CommentBase):
    """评论响应"""
    comment_id: str
    content_clean: Optional[str] = None
    likes: int = 0
    replies: int = 0
    crawl_time: datetime
    sentiment_label: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    
    class Config:
        from_attributes = True


# ============== 情感分析相关 ==============

class SentimentRequest(BaseModel):
    """情感分析请求"""
    text: str = Field(..., min_length=1, max_length=512)


class SentimentBatchRequest(BaseModel):
    """批量情感分析请求"""
    texts: List[str] = Field(..., min_items=1, max_items=100)


class SentimentResult(BaseModel):
    """情感分析结果"""
    text: str
    label: str  # positive/neutral/negative
    confidence: float
    scores: dict = Field(default_factory=dict)


class SentimentResponse(ResponseBase):
    """情感分析响应"""
    data: SentimentResult


class SentimentBatchResponse(ResponseBase):
    """批量情感分析响应"""
    data: List[SentimentResult]


# ============== 情绪指标相关 ==============

class EmotionIndicator(BaseModel):
    """情绪指标"""
    date: date
    hour: Optional[int] = None
    total_count: int = 0
    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0
    bull_index: float = 0.0
    bear_index: float = 0.0
    intensity: float = 0.0
    temperature: float = 0.0
    volatility: float = 0.0


class EmotionSummary(BaseModel):
    """情绪摘要"""
    avg_bull_index: float
    avg_bear_index: float
    avg_intensity: float
    total_comments: int


class StockEmotionResponse(ResponseBase):
    """股票情绪响应"""
    data: dict = Field(default_factory=dict)


class EmotionOverview(BaseModel):
    """市场情绪概览"""
    market_sentiment: str  # bullish/bearish/neutral
    avg_bull_index: float
    avg_bear_index: float
    hot_stocks: List[dict] = []
    recent_trend: List[dict] = []


# ============== 行情相关 ==============

class QuoteData(BaseModel):
    """行情数据"""
    stock_code: str
    trade_date: date
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    change_pct: float
    volume: int
    amount: float


# ============== 验证报告相关 ==============

class CorrelationResult(BaseModel):
    """相关性分析结果"""
    stock_code: str
    correlation: float
    p_value: float
    lag_days: int = 0


class ValidationReport(BaseModel):
    """验证报告"""
    period: dict
    correlation_analysis: List[CorrelationResult]
    accuracy_rate: float
    granger_test: Optional[dict] = None


# ============== 爬虫相关 ==============

class CrawlerTask(BaseModel):
    """爬虫任务"""
    platform: str
    stock_codes: List[str] = []
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CrawlerStatus(BaseModel):
    """爬虫状态"""
    platform: str
    status: str  # running/stopped/error
    total_crawled: int = 0
    last_crawl_time: Optional[datetime] = None
    error_message: Optional[str] = None
