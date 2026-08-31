from typing import List

from fastapi import APIRouter, HTTPException

from .schemas import TaskCreateModel, TaskItemModel, TaskUpdateModel
from .service import create_task, delete_task, get_all_tasks, sync_tasks, update_task

task_router = APIRouter()


@task_router.get("/task")
async def get_tasks():
    """返回所有任务，适合首次加载。"""
    return await get_all_tasks()


@task_router.post("/tasks/sync")
async def poll_tasks(client_tasks: list[TaskItemModel]):
    """2 秒轮询接口：客户端发送本地任务列表，服务端返回新版本任务。"""
    return await sync_tasks(client_tasks)


@task_router.post("/task")
async def add_task(task: TaskCreateModel):
    """新增任务。"""
    return await create_task(task)


@task_router.patch("/task/{sequence}")
async def patch_task(sequence: int, task: TaskUpdateModel):
    """按序号修改任务内容/状态/优先级。"""
    try:
        return await update_task(sequence, task)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="task not found") from exc


@task_router.delete("/task/{sequence}")
async def remove_task(sequence: int):
    """按序号删除任务（标记为已删除）。"""
    ok = await delete_task(sequence)
    if not ok:
        raise HTTPException(status_code=404, detail="task not found")
    return {"ok": True}
