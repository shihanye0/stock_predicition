"""
爬虫管理API
"""
from fastapi import APIRouter, BackgroundTasks
from typing import List, Optional
from datetime import date

from app.models.schemas import Response, CrawlerTask, CrawlerStatus
from app.services.crawler.manager import CrawlerManager

router = APIRouter()

# 爬虫管理器实例
crawler_manager = CrawlerManager()


@router.post("/crawler/start", response_model=Response, summary="启动爬虫任务")
async def start_crawler(
    task: CrawlerTask,
    background_tasks: BackgroundTasks
):
    """
    启动爬虫任务
    
    - platform: 平台名称 (eastmoney/xueqiu/sina)
    - stock_codes: 股票代码列表，为空则爬取全部
    - start_date: 开始日期
    - end_date: 结束日期
    """
    try:
        # 添加后台任务
        background_tasks.add_task(
            crawler_manager.start_crawl,
            platform=task.platform,
            stock_codes=task.stock_codes,
            start_date=task.start_date,
            end_date=task.end_date
        )
        
        return Response(
            message=f"Crawler task for {task.platform} started",
            data={"platform": task.platform, "status": "starting"}
        )
    except Exception as e:
        return Response(code=500, message=str(e), data=None)


@router.post("/crawler/stop", response_model=Response, summary="停止爬虫任务")
async def stop_crawler(platform: str):
    """停止指定平台的爬虫任务"""
    try:
        crawler_manager.stop_crawl(platform)
        return Response(
            message=f"Crawler for {platform} stopped",
            data={"platform": platform, "status": "stopped"}
        )
    except Exception as e:
        return Response(code=500, message=str(e), data=None)


@router.get("/crawler/status", response_model=Response, summary="获取爬虫状态")
async def get_crawler_status(platform: Optional[str] = None):
    """获取爬虫任务状态"""
    if platform:
        status = crawler_manager.get_status(platform)
        return Response(data=status)
    else:
        statuses = crawler_manager.get_all_status()
        return Response(data={"crawlers": statuses})


@router.get("/crawler/stats", response_model=Response, summary="获取爬虫统计")
async def get_crawler_stats():
    """获取爬虫采集统计数据"""
    stats = crawler_manager.get_stats()
    return Response(data=stats)
