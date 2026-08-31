import asyncio
import threading
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from .audio import play_task_sound
from .schemas import SyncResponseModel, TaskCreateModel, TaskItemModel, TaskUpdateModel
from .store import load_tasks, save_tasks

# 文件锁：确保并发访问时不会数据冲突
# 由于多个客户端可能同时访问服务端，使用线程锁保证数据一致性
_file_lock = threading.Lock()


async def get_all_tasks() -> List[TaskItemModel]:
    """
    获取所有活动的任务（按优先级排序，过滤已删除）。
    
    这是客户端首次连接时使用的接口，用于获取完整的任务列表。
    
    Returns:
        List[TaskItemModel]: 按优先级排序的活动任务列表（优先级数字越小越靠前）
        
    算法步骤：
    1. 从存储中加载所有任务
    2. 过滤掉状态为"deleted"的任务（软删除）
    3. 按优先级进行排序（priority越小优先级越高）
    
    注意：这个函数返回的是"用户视角"的任务列表，用户通过序号操作任务。
    """
    def _get():
        tasks = load_tasks()
        # 过滤已删除的任务，按优先级排序
        active_tasks = [t for t in tasks if t.status != "deleted"]
        # 优先级数字越小，优先级越高（1最高，10最低）
        return sorted(active_tasks, key=lambda t: t.priority)
    return await asyncio.to_thread(_get)


async def create_task(payload: TaskCreateModel) -> TaskItemModel:
    """
    创建新任务，初始版本号为 1。
    
    Args:
        payload (TaskCreateModel): 创建任务的请求体，包含标题、内容、状态、优先级等信息
        
    Returns:
        TaskItemModel: 创建成功后的完整任务对象，包含生成的ID和时间戳
        
    算法步骤：
    1. 获取文件锁，防止并发写入冲突
    2. 加载现有任务列表
    3. 生成唯一ID（UUID）
    4. 设置当前UTC时间作为创建和更新时间
    5. 设置初始版本号 modify_int = 1
    6. 将新任务添加到列表并保存
    7. 返回创建的任务对象
    
    设计说明：
    - 版本号从1开始：每个新任务都是第一个版本
    - 使用UUID作为内部标识：避免ID冲突，用户通过序号操作任务
    - 时间使用UTC：避免时区问题
    """
    def _create():
        with _file_lock:
            tasks = load_tasks()
            now = datetime.now(timezone.utc)
            task = TaskItemModel(
                id=str(uuid.uuid4()),
                title=payload.title,
                content=payload.content,
                status=payload.status,
                priority=payload.priority,
                modify_int=1,  # 新任务初始版本号为1
                created_at=now,
                updated_at=now,
            )
            tasks.append(task)
            save_tasks(tasks)
            return task
    return await asyncio.to_thread(_create)


async def update_task(sequence: int, payload: TaskUpdateModel) -> TaskItemModel:
    """
    按序号更新任务内容，版本号增加1。
    
    用户通过任务在列表中的序号来操作任务，而不是通过内部ID。
    
    Args:
        sequence (int): 任务序号（从1开始，基于优先级排序后的位置）
        payload (TaskUpdateModel): 更新任务的请求体，可以更新标题、内容、状态、优先级
        
    Returns:
        TaskItemModel: 更新后的任务对象
        
    Raises:
        ValueError: 如果序号超出范围或找不到对应任务
        
    算法步骤：
    1. 获取文件锁，防止并发写入冲突
    2. 加载所有任务，过滤已删除的任务
    3. 按优先级排序得到用户视角的任务列表
    4. 验证序号是否在有效范围内（1到任务数量）
    5. 根据序号找到对应的任务（序号-1得到索引）
    6. 在原任务列表中找到该任务（通过ID匹配）
    7. 更新提供的字段（只更新非None的字段）
    8. 版本号增加1（modify_int += 1）
    9. 更新修改时间为当前UTC时间
    10. 保存任务列表并返回更新后的任务
    
    设计说明：
    - 用户通过序号操作：这是设计文档中的关键设计，用户看到的是1,2,3...这样的序号
    - 部分更新：只更新payload中非None的字段
    - 版本号递增：每次修改都会增加版本号，用于同步时判断哪个版本更新
    """
    def _update():
        with _file_lock:
            tasks = load_tasks()
            # 按优先级排序，过滤已删除，得到用户视角的任务列表
            active_tasks = sorted(
                [t for t in tasks if t.status != "deleted"],
                key=lambda t: t.priority
            )
            
            # 验证序号有效性（序号从1开始）
            if sequence < 1 or sequence > len(active_tasks):
                raise ValueError("sequence out of range")
            
            # 根据序号找到目标任务（序号-1得到列表索引）
            target_task = active_tasks[sequence - 1]  # 序号从 1 开始
            
            # 在原列表中找到并修改（通过ID匹配）
            for task in tasks:
                if task.id == target_task.id:
                    # 部分更新：只更新非None的字段
                    if payload.title is not None:
                        task.title = payload.title
                    if payload.content is not None:
                        task.content = payload.content
                    if payload.status is not None:
                        task.status = payload.status
                    if payload.priority is not None:
                        task.priority = payload.priority
                    # 每次修改都增加版本号
                    task.modify_int += 1
                    task.updated_at = datetime.now(timezone.utc)
                    save_tasks(tasks)
                    return task
            
            raise ValueError("task not found")
    return await asyncio.to_thread(_update)


async def delete_task(sequence: int) -> bool:
    """
    按序号"软删除"任务（标记为删除状态，不真正从列表中移除）。
    
    这是软删除设计，任务仍然保留在数据中，只是状态变为"deleted"。
    这样做的好处是可以保留删除历史，也便于同步时告知其他客户端某个任务已被删除。
    
    Args:
        sequence (int): 任务序号（从1开始，基于优先级排序后的位置）
        
    Returns:
        bool: 删除是否成功（True表示成功，False表示序号无效）
        
    算法步骤：
    1. 获取文件锁，防止并发写入冲突
    2. 加载所有任务，过滤已删除的任务
    3. 按优先级排序得到用户视角的任务列表
    4. 验证序号是否在有效范围内
    5. 根据序号找到目标任务
    6. 在原列表中找到该任务（通过ID匹配）
    7. 将任务状态改为"deleted"
    8. 版本号增加1（表示删除操作也是一次修改）
    9. 更新修改时间为当前UTC时间
    10. 保存任务列表并返回成功状态
    
    设计说明：
    - 软删除：任务状态改为"deleted"，而不是物理删除
    - 版本号递增：删除操作也会增加版本号，同步时其他客户端会收到这个删除状态
    - 用户通过序号操作：与update_task保持一致的设计理念
    """
    def _delete():
        with _file_lock:
            tasks = load_tasks()
            # 按优先级排序，过滤已删除，得到用户视角的任务列表
            active_tasks = sorted(
                [t for t in tasks if t.status != "deleted"],
                key=lambda t: t.priority
            )
            
            # 验证序号有效性
            if sequence < 1 or sequence > len(active_tasks):
                return False
            
            # 根据序号找到目标任务
            target_task = active_tasks[sequence - 1]  # 序号从 1 开始
            
            # 在原列表中找到并标记为删除
            for task in tasks:
                if task.id == target_task.id:
                    task.status = "deleted"
                    task.modify_int += 1
                    task.updated_at = datetime.now(timezone.utc)
                    save_tasks(tasks)
                    return True
            
            return False
    return await asyncio.to_thread(_delete)


async def sync_tasks(client_tasks: Optional[List[TaskItemModel]] = None) -> SyncResponseModel:
    """双向增量同步：服务器吸收客户端更新，同时返回服务器的更新（按优先级排序）。"""
    def _sync():
        with _file_lock:
            server_tasks = load_tasks()

            if client_tasks is None:
                client_tasks_list = []
            else:
                client_tasks_list = client_tasks

            client_versions = {task.id: task.modify_int for task in client_tasks_list}

            # 第一步：服务器吸收客户端的更新（客户端版本更高）
            server_absorbed_updates = False
            for client_task in client_tasks_list:
                server_task = next((t for t in server_tasks if t.id == client_task.id), None)
                if server_task and client_task.modify_int > server_task.modify_int:
                    # 客户端版本更高，用客户端数据覆盖服务器
                    server_task.title = client_task.title
                    server_task.content = client_task.content
                    server_task.status = client_task.status
                    server_task.priority = client_task.priority
                    server_task.modify_int = client_task.modify_int
                    server_task.updated_at = client_task.updated_at
                    server_absorbed_updates = True

            if server_absorbed_updates:
                save_tasks(server_tasks)
                server_tasks = load_tasks()

            # 第二步：返回服务器有更新的任务给客户端
            updated_items = []
            for task in server_tasks:
                client_version = client_versions.get(task.id, 0)
                if task.modify_int > client_version:
                    updated_items.append(task)

            # 按优先级排序结果
            updated_items = sorted(updated_items, key=lambda t: t.priority)

            has_updates = server_absorbed_updates or len(updated_items) > 0

            if has_updates:
                play_task_sound("task_update")

            return SyncResponseModel(
                items=updated_items,
                changed=has_updates,
                timestamp=datetime.now(timezone.utc),
            )
    return await asyncio.to_thread(_sync)
