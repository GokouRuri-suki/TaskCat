from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

from .schemas import TaskCreateModel, TaskItemModel, TaskUpdateModel
from .service import create_task, delete_task, get_all_tasks, sync_tasks, update_task

task_router = APIRouter()


@task_router.get("/task")
async def get_tasks():
    """返回所有任务，适合首次加载。"""
    tasks = await get_all_tasks()
    return {
        "tasks": tasks,
        "sound": "/sounds/notification.wav"
    }


@task_router.post("/tasks/sync")
async def poll_tasks(client_tasks: list[TaskItemModel]):
    """2 秒轮询接口：客户端发送本地任务列表，服务端返回新版本任务。"""
    result = await sync_tasks(client_tasks)
    # 如果有更新，返回音频 URL 给前端
    response_data = result.model_dump()
    if result.changed:
        response_data["sound"] = "/sounds/notification.wav"
    return response_data


@task_router.post("/task")
async def add_task(task: TaskCreateModel):
    """新增任务。"""
    created = await create_task(task)
    return {
        "task": created,
        "sound": "/sounds/notification.wav"
    }


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


@task_router.get("/sounds/{filename}")
async def get_sound(filename: str):
    """提供音频文件给前端（Java 应用）下载并播放。"""
    sound_dir = Path(__file__).parent / "sounds"
    file_path = sound_dir / filename
    
    # 安全检查：防止路径遍历攻击
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="sound file not found")
    
    if not str(file_path).startswith(str(sound_dir)):
        raise HTTPException(status_code=403, detail="forbidden")
    
    return FileResponse(file_path, media_type="audio/wav")
