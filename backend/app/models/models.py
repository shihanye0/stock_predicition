"""
数据库模型定义
"""
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, Date, DECIMAL, Float, ForeignKey, Index, SmallInteger, JSON
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from app.core.database import Base


class Stock(Base):
    """股票信息表"""
    __tablename__ = "stocks"
    
    stock_code = Column(String(10), primary_key=True, comment="股票代码")
    stock_name = Column(String(50), nullable=False, comment="股票名称")
    industry = Column(String(50), comment="所属行业")
    market = Column(String(10), comment="市场(SH/SZ)")
    list_date = Column(Date, comment="上市日期")
    status = Column(TINYINT, default=1, comment="状态:1正常0退市")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    comments = relationship("Comment", back_populates="stock")
    emotions = relationship("Emotion", back_populates="stock")
    quotes = relationship("Quote", back_populates="stock")
    
    __table_args__ = (
        Index("idx_industry", "industry"),
        Index("idx_market", "market"),
    )


class Comment(Base):
    """评论数据表"""
    __tablename__ = "comments"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    comment_id = Column(String(64), unique=True, nullable=False, comment="评论唯一ID")
    platform = Column(String(20), nullable=False, comment="来源平台")
    stock_code = Column(String(10), ForeignKey("stocks.stock_code"), nullable=False, comment="股票代码")
    content = Column(Text, nullable=False, comment="评论内容")
    content_clean = Column(Text, comment="清洗后内容")
    author = Column(String(100), comment="作者")
    publish_time = Column(DateTime, nullable=False, comment="发布时间")
    likes = Column(Integer, default=0, comment="点赞数")
    replies = Column(Integer, default=0, comment="回复数")
    crawl_time = Column(DateTime, default=datetime.now, comment="采集时间")
    is_processed = Column(TINYINT, default=0, comment="是否已处理")
    
    # 关系
    stock = relationship("Stock", back_populates="comments")
    sentiment = relationship("Sentiment", back_populates="comment", uselist=False)
    
    __table_args__ = (
        Index("idx_stock_code", "stock_code"),
        Index("idx_platform", "platform"),
        Index("idx_publish_time", "publish_time"),
        Index("idx_is_processed", "is_processed"),
    )


class Sentiment(Base):
    """情感分析结果表"""
    __tablename__ = "sentiments"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    comment_id = Column(String(64), ForeignKey("comments.comment_id"), unique=True, nullable=False, comment="评论ID")
    label = Column(String(20), nullable=False, comment="情感标签")
    confidence = Column(DECIMAL(5, 4), nullable=False, comment="置信度")
    positive_score = Column(DECIMAL(5, 4), comment="积极得分")
    neutral_score = Column(DECIMAL(5, 4), comment="中性得分")
    negative_score = Column(DECIMAL(5, 4), comment="消极得分")
    model_version = Column(String(50), comment="模型版本")
    analyzed_at = Column(DateTime, default=datetime.now, comment="分析时间")
    
    # 关系
    comment = relationship("Comment", back_populates="sentiment")
    
    __table_args__ = (
        Index("idx_label", "label"),
        Index("idx_analyzed_at", "analyzed_at"),
    )


class Emotion(Base):
    """情绪指标表"""
    __tablename__ = "emotions"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), ForeignKey("stocks.stock_code"), nullable=False, comment="股票代码")
    stat_date = Column(Date, nullable=False, comment="统计日期")
    stat_hour = Column(TINYINT, comment="统计小时(0-23,NULL表示日级)")
    total_count = Column(Integer, default=0, comment="总评论数")
    positive_count = Column(Integer, default=0, comment="积极评论数")
    neutral_count = Column(Integer, default=0, comment="中性评论数")
    negative_count = Column(Integer, default=0, comment="消极评论数")
    bull_index = Column(DECIMAL(5, 2), comment="看涨指数")
    bear_index = Column(DECIMAL(5, 2), comment="看跌指数")
    intensity = Column(DECIMAL(5, 4), comment="情绪强度")
    temperature = Column(DECIMAL(5, 2), comment="情绪温度")
    volatility = Column(DECIMAL(5, 4), comment="情绪波动")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    stock = relationship("Stock", back_populates="emotions")
    
    __table_args__ = (
        Index("uk_stock_date_hour", "stock_code", "stat_date", "stat_hour", unique=True),
        Index("idx_stat_date", "stat_date"),
    )


class Quote(Base):
    """股票行情表"""
    __tablename__ = "quotes"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), ForeignKey("stocks.stock_code"), nullable=False, comment="股票代码")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    open_price = Column(DECIMAL(10, 2), comment="开盘价")
    close_price = Column(DECIMAL(10, 2), comment="收盘价")
    high_price = Column(DECIMAL(10, 2), comment="最高价")
    low_price = Column(DECIMAL(10, 2), comment="最低价")
    pre_close = Column(DECIMAL(10, 2), comment="昨收价")
    change_amount = Column(DECIMAL(10, 2), comment="涨跌额")
    change_pct = Column(DECIMAL(8, 4), comment="涨跌幅(%)")
    volume = Column(BigInteger, comment="成交量(手)")
    amount = Column(DECIMAL(18, 2), comment="成交额(元)")
    turnover_rate = Column(DECIMAL(8, 4), comment="换手率(%)")
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    stock = relationship("Stock", back_populates="quotes")
    
    __table_args__ = (
        Index("uk_stock_date", "stock_code", "trade_date", unique=True),
        Index("idx_trade_date", "trade_date"),
    )


class ExperimentResult(Base):
    """实验结果表"""
    __tablename__ = "experiment_results"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False, comment="模型名称")
    dataset_name = Column(String(100), nullable=False, comment="数据集名称")
    accuracy = Column(Float, comment="准确率")
    f1_score = Column(Float, comment="F1分数")
    precision_score = Column(Float, comment="精确率")
    recall_score = Column(Float, comment="召回率")
    confusion_matrix = Column(JSON, comment="混淆矩阵")
    classification_report = Column(JSON, comment="分类报告")
    run_time = Column(Float, comment="运行耗时(秒)")
    sample_count = Column(Integer, comment="样本数量")
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index("idx_model_name", "model_name"),
        Index("idx_created_at_exp", "created_at"),
    )


class AspectSentiment(Base):
    """方面级情感分析表"""
    __tablename__ = "aspect_sentiments"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    comment_id = Column(String(64), ForeignKey("comments.comment_id"), nullable=False, comment="评论ID")
    aspect = Column(String(30), nullable=False, comment="方面类别")
    sentiment_label = Column(String(20), nullable=False, comment="情感标签")
    confidence = Column(DECIMAL(5, 4), comment="置信度")
    keywords = Column(String(500), comment="匹配关键词")
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index("idx_comment_aspect", "comment_id", "aspect"),
        Index("idx_aspect", "aspect"),
    )


class Alert(Base):
    """情绪预警表"""
    __tablename__ = "alerts"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), ForeignKey("stocks.stock_code"), nullable=False, comment="股票代码")
    alert_type = Column(String(50), nullable=False, comment="预警类型")
    severity = Column(String(10), nullable=False, comment="严重程度:high/medium/low")
    title = Column(String(200), nullable=False, comment="预警标题")
    message = Column(Text, comment="预警详情")
    metric_value = Column(Float, comment="触发指标值")
    threshold = Column(Float, comment="阈值")
    triggered_at = Column(DateTime, default=datetime.now, comment="触发时间")
    is_read = Column(TINYINT, default=0, comment="是否已读")
    
    # 关系
    stock = relationship("Stock")
    
    __table_args__ = (
        Index("idx_stock_alert", "stock_code"),
        Index("idx_severity", "severity"),
        Index("idx_is_read", "is_read"),
        Index("idx_triggered_at", "triggered_at"),
    )
