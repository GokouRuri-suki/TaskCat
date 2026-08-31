import json
from pathlib import Path
from typing import List

from .schemas import TaskItemModel

DATA_PATH = Path(__file__).resolve().parent / "data" / "data.json"


def ensure_store() -> None:
    """确保数据文件存在。"""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text("[]", encoding="utf-8")


def load_tasks() -> List[TaskItemModel]:
    """从文件中读取任务列表。"""
    ensure_store()
    with DATA_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return [TaskItemModel(**item) for item in raw]


def save_tasks(tasks: List[TaskItemModel]) -> None:
    """将任务列表保存到文件。"""
    ensure_store()
    payload = [task.model_dump(mode="json") for task in tasks]
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
