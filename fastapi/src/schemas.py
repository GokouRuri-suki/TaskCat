from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """返回 UTC 时间，避免 datetime.utcnow() 的弃用警告。"""
    return datetime.now(timezone.utc)


class TaskItemModel(BaseModel):
    """任务实体。"""
    id: str
    title: str
    content: str = ""
    status: str = "todo"  # todo / doing / done / deleted
    priority: int = 5     # 优先级 1-10，数字越小优先级越高
    modify_int: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class TaskCreateModel(BaseModel):
    """新增任务请求体。"""
    title: str
    content: str = ""
    status: str = "todo"
    priority: int = 5


class TaskUpdateModel(BaseModel):
    """更新任务请求体。"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None


class SyncResponseModel(BaseModel):
    """轮询同步返回体。"""
    items: List[TaskItemModel] = []
    timestamp: datetime = Field(default_factory=utc_now)
    changed: bool = False

