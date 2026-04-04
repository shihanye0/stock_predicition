"""
基于Transformer的股票情绪预测系统 - 核心配置
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基本配置
    APP_NAME: str = "股票情绪预测系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API配置
    API_PREFIX: str = "/api/v1"
    
    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "stock_sentiment"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # 模型配置
    MODEL_NAME: str = "hfl/chinese-bert-wwm-ext"
    MODEL_MAX_LENGTH: int = 128
    MODEL_CACHE_DIR: str = "./data/models"
    
    # 爬虫配置
    CRAWLER_DELAY_MIN: float = 3.0
    CRAWLER_DELAY_MAX: float = 8.0
    CRAWLER_MAX_RETRY: int = 3
    CRAWLER_TIMEOUT: int = 30
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # JWT配置
    JWT_SECRET_KEY: str = "stock-sentiment-secret-key-2026-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24小时
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
