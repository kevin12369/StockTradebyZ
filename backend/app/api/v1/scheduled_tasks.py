"""定时任务管理API"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.core.scheduler import scheduler
from app.models.scheduled_task import ScheduledTask
from app.schemas.common import ApiResponse, PageResponse


router = APIRouter(prefix='/scheduled-tasks', tags=['定时任务管理'])


@router.get(
    '',
    response_model=ApiResponse[List[dict]],
    summary='获取所有定时任务',
    description='获取系统中的所有定时任务配置'
)
async def get_tasks(db: Session = Depends(get_db)):
    """获取所有定时任务"""
    tasks = db.query(ScheduledTask).order_by(ScheduledTask.id).all()
    return ApiResponse[List[dict]](
        code=200,
        message='success',
        data=[task.to_dict() for task in tasks]
    )


@router.get(
    '/{task_id}',
    response_model=ApiResponse[dict],
    summary='获取任务详情',
    description='根据ID获取定时任务详情'
)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取任务详情"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在')

    return ApiResponse[dict](
        code=200,
        message='success',
        data=task.to_dict()
    )


@router.post(
    '',
    response_model=ApiResponse[dict],
    summary='创建定时任务',
    description='创建新的定时任务'
)
async def create_task(
    task_data: dict,
    db: Session = Depends(get_db)
):
    """创建定时任务"""
    try:
        task = ScheduledTask(
            name=task_data.get('name'),
            task_type=task_data.get('task_type'),
            description=task_data.get('description'),
            config=task_data.get('config'),  # 添加config字段支持
            enabled=task_data.get('enabled', True),
            cron_expression=task_data.get('cron_expression'),
            scheduled_time=task_data.get('scheduled_time')
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        # 重新加载任务
        scheduler.load_tasks_from_db()

        return ApiResponse[dict](
            code=200,
            message='创建成功',
            data=task.to_dict()
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f'创建失败: {str(e)}')


@router.put(
    '/{task_id}',
    response_model=ApiResponse[dict],
    summary='更新定时任务',
    description='更新定时任务配置'
)
async def update_task(
    task_id: int,
    task_data: dict,
    db: Session = Depends(get_db)
):
    """更新任务"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在')

    try:
        # 更新字段
        if 'name' in task_data:
            task.name = task_data['name']
        if 'task_type' in task_data:
            task.task_type = task_data['task_type']
        if 'description' in task_data:
            task.description = task_data['description']
        if 'config' in task_data:
            task.config = task_data['config']  # 添加config字段支持
        if 'enabled' in task_data:
            task.enabled = task_data['enabled']
        if 'cron_expression' in task_data:
            task.cron_expression = task_data['cron_expression']
        if 'scheduled_time' in task_data:
            task.scheduled_time = task_data['scheduled_time']

        task.updated_at = datetime.now()
        db.commit()
        db.refresh(task)

        # 重新加载任务
        scheduler.load_tasks_from_db()

        return ApiResponse[dict](
            code=200,
            message='更新成功',
            data=task.to_dict()
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f'更新失败: {str(e)}')


@router.delete(
    '/{task_id}',
    response_model=ApiResponse[dict],
    summary='删除定时任务',
    description='删除指定的定时任务'
)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在')

    try:
        # 从调度器中移除
        if scheduler.scheduler.get_job(task.name):
            scheduler.scheduler.remove_job(task.name)

        db.delete(task)
        db.commit()

        return ApiResponse[dict](
            code=200,
            message='删除成功',
            data={'id': task_id}
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f'删除失败: {str(e)}')


@router.post(
    '/{task_id}/run',
    response_model=ApiResponse[dict],
    summary='手动执行任务',
    description='立即执行指定的定时任务'
)
async def run_task(task_id: int, db: Session = Depends(get_db)):
    """手动执行任务"""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail='任务不存在')

    try:
        result = scheduler.run_task_now(task_id)
        return ApiResponse[dict](
            code=200,
            message='任务已触发',
            data=result
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'触发失败: {str(e)}')


@router.post(
    '/init',
    response_model=ApiResponse[dict],
    summary='初始化默认任务',
    description='初始化系统默认的定时任务'
)
async def init_default_tasks(db: Session = Depends(get_db)):
    """初始化默认任务"""
    try:
        # 检查是否已存在任务
        existing_count = db.query(ScheduledTask).count()
        if existing_count > 0:
            return ApiResponse[dict](
                code=200,
                message=f'已存在 {existing_count} 个任务，跳过初始化',
                data={'count': existing_count}
            )

        # 创建默认任务
        default_tasks = [
            {
                'name': 'full_sync_18pm',
                'task_type': 'full_sync',
                'description': '全量数据同步（每天18:00）',
                'enabled': True,
                'scheduled_time': '18:00'
            },
            {
                'name': 'calculate_top_performers_18pm',
                'task_type': 'calculate_top_performers',
                'description': '计算日涨幅榜（每天18:00）',
                'enabled': True,
                'scheduled_time': '18:00'
            },
            {
                'name': 'calculate_weekly_top_performers_18pm',
                'task_type': 'calculate_weekly_top_performers',
                'description': '计算周涨幅榜（每周五18:00）',
                'enabled': True,
                'cron_expression': '0 18 * * 5'  # 每周五18:00
            },
            {
                'name': 'calculate_monthly_top_performers_18pm',
                'task_type': 'calculate_monthly_top_performers',
                'description': '计算月涨幅榜（每月1号18:00）',
                'enabled': True,
                'cron_expression': '0 18 1 * *'  # 每月1号18:00
            }
        ]

        created_tasks = []
        for task_data in default_tasks:
            task = ScheduledTask(**task_data)
            db.add(task)
            created_tasks.append(task)

        db.commit()

        # 重新加载任务
        scheduler.load_tasks_from_db()

        return ApiResponse[dict](
            code=200,
            message=f'成功初始化 {len(created_tasks)} 个默认任务',
            data={
                'count': len(created_tasks),
                'tasks': [task.to_dict() for task in created_tasks]
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f'初始化失败: {str(e)}')
