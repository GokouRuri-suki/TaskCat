import json
import tempfile
import shutil
from pathlib import Path
from typing import List

from .schemas import TaskItemModel

DATA_PATH = Path(__file__).resolve().parent / "data" / "data.json"
BACKUP_PATH = Path(__file__).resolve().parent / "data" / "data.backup.json"


def ensure_store() -> None:
    """确保数据文件存在。"""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text("[]", encoding="utf-8")


def load_tasks() -> List[TaskItemModel]:
    """从文件中读取任务列表。如果主文件损坏，尝试恢复备份。"""
    ensure_store()
    
    try:
        with DATA_PATH.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return [TaskItemModel(**item) for item in raw]
    except (json.JSONDecodeError, ValueError):
        # 如果主文件损坏，尝试恢复备份
        if BACKUP_PATH.exists():
            try:
                with BACKUP_PATH.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
                return [TaskItemModel(**item) for item in raw]
            except Exception:
                pass
        # 如果备份也失败，返回空列表
        return []


def save_tasks(tasks: List[TaskItemModel]) -> None:
    """将任务列表保存到文件（原子操作）。
    
    步骤：
    1. 先备份现有数据
    2. 写入到临时文件
    3. 原子操作：临时文件重命名为主文件
    
    这样即使写入过程中崩溃，也不会损坏数据。
    """
    ensure_store()
    
    payload = [task.model_dump(mode="json") for task in tasks]
    
    # 备份现有数据
    if DATA_PATH.exists():
        shutil.copy2(DATA_PATH, BACKUP_PATH)
    
    # 写入临时文件
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=DATA_PATH.parent,
            delete=False,
            suffix='.json',
            encoding='utf-8'
        ) as tmp:
            json.dump(payload, tmp, ensure_ascii=False, indent=2)
            tmp_path = Path(tmp.name)
        
        # 原子操作：重命名（不会中途失败）
        tmp_path.replace(DATA_PATH)
    except Exception as e:
        # 如果写入失败，恢复备份
        if BACKUP_PATH.exists():
            shutil.copy2(BACKUP_PATH, DATA_PATH)
        raise RuntimeError(f"Save failed: {e}")
