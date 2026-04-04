"""
定时任务调度器

自动执行数据采集、情感分析、指标计算等任务
"""
import asyncio
from datetime import datetime, time
from typing import Callable, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("APScheduler not available, scheduler will be disabled")


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScheduledTask:
    """调度任务"""
    name: str
    func: Callable
    trigger: str  # 'cron' or 'interval'
    trigger_args: Dict[str, Any]
    enabled: bool = True
    last_run: datetime = None
    last_status: TaskStatus = TaskStatus.PENDING
    last_error: str = None
    run_count: int = 0


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.scheduler = None
        self.is_running = False
        
        if APSCHEDULER_AVAILABLE:
            self.scheduler = AsyncIOScheduler()
    
    def add_task(
        self,
        name: str,
        func: Callable,
        trigger: str = "interval",
        **trigger_args
    ) -> bool:
        """
        添加调度任务
        
        Args:
            name: 任务名称
            func: 任务函数
            trigger: 触发器类型 ('cron' 或 'interval')
            **trigger_args: 触发器参数
                - interval: hours, minutes, seconds
                - cron: hour, minute, day_of_week 等
        """
        if not APSCHEDULER_AVAILABLE:
            logger.warning("Scheduler not available")
            return False
        
        task = ScheduledTask(
            name=name,
            func=func,
            trigger=trigger,
            trigger_args=trigger_args
        )
        
        self.tasks[name] = task
        
        # 添加到调度器
        if trigger == "cron":
            trigger_obj = CronTrigger(**trigger_args)
        else:
            trigger_obj = IntervalTrigger(**trigger_args)
        
        self.scheduler.add_job(
            self._run_task,
            trigger=trigger_obj,
            args=[name],
            id=name,
            replace_existing=True
        )
        
        logger.info(f"Task '{name}' added with {trigger} trigger")
        return True
    
    async def _run_task(self, task_name: str):
        """执行任务"""
        if task_name not in self.tasks:
            return
        
        task = self.tasks[task_name]
        
        if not task.enabled:
            logger.info(f"Task '{task_name}' is disabled, skipping")
            return
        
        logger.info(f"Starting task: {task_name}")
        task.last_run = datetime.now()
        task.last_status = TaskStatus.RUNNING
        
        try:
            # 执行任务
            if asyncio.iscoroutinefunction(task.func):
                await task.func()
            else:
                task.func()
            
            task.last_status = TaskStatus.COMPLETED
            task.last_error = None
            task.run_count += 1
            logger.info(f"Task '{task_name}' completed successfully")
            
        except Exception as e:
            task.last_status = TaskStatus.FAILED
            task.last_error = str(e)
            logger.error(f"Task '{task_name}' failed: {e}")
    
    def remove_task(self, name: str) -> bool:
        """移除任务"""
        if name in self.tasks:
            del self.tasks[name]
            if self.scheduler:
                try:
                    self.scheduler.remove_job(name)
                except:
                    pass
            logger.info(f"Task '{name}' removed")
            return True
        return False
    
    def enable_task(self, name: str) -> bool:
        """启用任务"""
        if name in self.tasks:
            self.tasks[name].enabled = True
            if self.scheduler:
                self.scheduler.resume_job(name)
            return True
        return False
    
    def disable_task(self, name: str) -> bool:
        """禁用任务"""
        if name in self.tasks:
            self.tasks[name].enabled = False
            if self.scheduler:
                self.scheduler.pause_job(name)
            return True
        return False
    
    def start(self):
        """启动调度器"""
        if not APSCHEDULER_AVAILABLE:
            logger.warning("Scheduler not available")
            return
        
        if not self.is_running and self.scheduler:
            self.scheduler.start()
            self.is_running = True
            logger.info("Task scheduler started")
    
    def stop(self):
        """停止调度器"""
        if self.is_running and self.scheduler:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Task scheduler stopped")
    
    def get_task_status(self, name: str = None) -> Dict:
        """获取任务状态"""
        if name:
            if name in self.tasks:
                task = self.tasks[name]
                return {
                    "name": task.name,
                    "enabled": task.enabled,
                    "trigger": task.trigger,
                    "trigger_args": task.trigger_args,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "last_status": task.last_status.value,
                    "last_error": task.last_error,
                    "run_count": task.run_count
                }
            return None
        
        return {
            "is_running": self.is_running,
            "tasks": [
                {
                    "name": t.name,
                    "enabled": t.enabled,
                    "trigger": t.trigger,
                    "last_run": t.last_run.isoformat() if t.last_run else None,
                    "last_status": t.last_status.value,
                    "run_count": t.run_count
                }
                for t in self.tasks.values()
            ]
        }
    
    async def run_task_now(self, name: str) -> bool:
        """立即执行任务"""
        if name in self.tasks:
            await self._run_task(name)
            return True
        return False


# 全局调度器实例
_scheduler: TaskScheduler = None


def get_scheduler() -> TaskScheduler:
    """获取调度器单例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler


# ============ 预定义任务 ============

async def task_sync_quotes():
    """同步股票行情任务"""
    from app.services.market.data_service import get_market_service
    
    logger.info("Running: sync quotes task")
    service = get_market_service()
    # 这里添加实际的同步逻辑
    logger.info("Sync quotes completed")


async def task_analyze_comments():
    """分析评论情感任务"""
    from app.services.sentiment.analyzer import get_analyzer
    from app.core.database import SessionLocal
    from app.models.models import Comment, Sentiment
    
    logger.info("Running: analyze comments task")
    
    db = SessionLocal()
    try:
        # 获取未处理的评论
        comments = db.query(Comment).filter(
            Comment.is_processed == 0
        ).limit(100).all()
        
        if not comments:
            logger.info("No new comments to analyze")
            return
        
        analyzer = get_analyzer()
        
        for comment in comments:
            result = analyzer.analyze(comment.content)
            
            # 保存结果
            sentiment = Sentiment(
                comment_id=comment.comment_id,
                label=result.label,
                confidence=result.confidence,
                positive_score=result.scores.get('positive', 0),
                neutral_score=result.scores.get('neutral', 0),
                negative_score=result.scores.get('negative', 0),
                model_version=analyzer.model_name
            )
            
            db.merge(sentiment)
            comment.is_processed = 1
        
        db.commit()
        logger.info(f"Analyzed {len(comments)} comments")
        
    except Exception as e:
        logger.error(f"Analyze comments error: {e}")
        db.rollback()
    finally:
        db.close()


async def task_calculate_emotions():
    """计算情绪指标任务"""
    from app.services.quantify.calculator import get_calculator
    from app.core.database import SessionLocal
    from app.models.models import Stock
    from datetime import date
    
    logger.info("Running: calculate emotions task")
    
    db = SessionLocal()
    try:
        calculator = get_calculator()
        
        # 获取所有股票
        stocks = db.query(Stock).filter(Stock.status == 1).all()
        
        today = date.today()
        
        for stock in stocks:
            try:
                # 计算日级情绪指标
                calculator.calculate_daily_emotion(db, stock.stock_code, today)
            except Exception as e:
                logger.error(f"Calculate emotion for {stock.stock_code} error: {e}")
        
        db.commit()
        logger.info(f"Calculated emotions for {len(stocks)} stocks")
        
    except Exception as e:
        logger.error(f"Calculate emotions error: {e}")
        db.rollback()
    finally:
        db.close()


def setup_default_tasks(scheduler: TaskScheduler):
    """设置默认任务"""
    
    # 每小时同步行情（交易时段）
    scheduler.add_task(
        name="sync_quotes",
        func=task_sync_quotes,
        trigger="cron",
        hour="9-15",
        minute="30"
    )
    
    # 每30分钟分析新评论
    scheduler.add_task(
        name="analyze_comments",
        func=task_analyze_comments,
        trigger="interval",
        minutes=30
    )
    
    # 每天收盘后计算情绪指标
    scheduler.add_task(
        name="calculate_emotions",
        func=task_calculate_emotions,
        trigger="cron",
        hour=16,
        minute=0
    )
    
    logger.info("Default tasks configured")
