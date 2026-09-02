#!/usr/bin/env python3
"""
测试单机同步问题
模拟只有一台机器创建任务后的同步情况
"""
import json
import requests
import time

BASE_URL = "http://127.0.0.1:8000/TaskCat/api/ver1.0"

def test_single_machine_scenario():
    """测试单机场景：创建任务后立即同步"""
    print("="*60)
    print("测试单机同步场景")
    print("="*60)
    
    # 1. 首先清空服务器数据（为了测试）
    print("\n1. 清空服务器数据...")
    # 获取当前所有任务
    response = requests.get(f"{BASE_URL}/task")
    if response.status_code == 200:
        tasks = response.json()["tasks"]
        # 删除所有任务
        for i, task in enumerate(tasks, 1):
            requests.delete(f"{BASE_URL}/task/{i}")
    
    # 2. 创建新任务
    print("\n2. 创建新任务...")
    task_data = {
        "title": "单机测试任务",
        "content": "只有一台机器",
        "status": "todo",
        "priority": 1
    }
    
    response = requests.post(f"{BASE_URL}/task", json=task_data)
    if response.status_code != 200:
        print(f"创建任务失败: {response.status_code}")
        return
    
    created_task = response.json()["task"]
    task_id = created_task["id"]
    task_version = created_task["modify_int"]
    
    print(f"创建的任务ID: {task_id}")
    print(f"创建的任务版本: {task_version}")
    
    # 3. 模拟场景A：客户端发送空列表（首次同步）
    print("\n3. 场景A: 客户端首次同步（空列表）")
    response = requests.post(f"{BASE_URL}/tasks/sync", json=[])
    if response.status_code == 200:
        result = response.json()
        print(f"同步结果 changed: {result.get('changed')}")
        print(f"返回的任务数量: {len(result.get('items', []))}")
        
        if result.get('changed'):
            items = result.get('items', [])
            if items:
                print(f"返回的任务: {items[0].get('title')} (版本: {items[0].get('modify_int')})")
            else:
                print("警告: changed=True 但没有返回任务!")
        else:
            print("问题: 服务器没有检测到更新!")
    else:
        print(f"同步失败: {response.status_code}")
    
    # 4. 模拟场景B：客户端发送包含该任务的列表（版本相同）
    print("\n4. 场景B: 客户端发送包含该任务的列表（版本相同）")
    client_task = created_task.copy()
    response = requests.post(f"{BASE_URL}/tasks/sync", json=[client_task])
    if response.status_code == 200:
        result = response.json()
        print(f"同步结果 changed: {result.get('changed')}")
        print(f"返回的任务数量: {len(result.get('items', []))}")
        
        if result.get('changed'):
            print("服务器检测到更新")
            items = result.get('items', [])
            if items:
                for item in items:
                    print(f"  - {item.get('title')} (版本: {item.get('modify_int')})")
        else:
            print("服务器没有检测到更新（正常，因为版本相同）")
    else:
        print(f"同步失败: {response.status_code}")
    
    # 5. 模拟场景C：客户端修改任务后同步
    print("\n5. 场景C: 客户端修改任务后同步")
    # 先更新任务
    update_data = {
        "title": "修改后的任务",
        "content": "客户端修改了内容",
        "priority": 2
    }
    response = requests.patch(f"{BASE_URL}/task/1", json=update_data)
    if response.status_code == 200:
        updated_task = response.json()
        print(f"更新后的任务版本: {updated_task.get('modify_int')}")
        
        # 现在客户端有旧版本(1)，服务器有新版本(2)
        old_client_task = created_task.copy()  # 版本1
        
        response = requests.post(f"{BASE_URL}/tasks/sync", json=[old_client_task])
        if response.status_code == 200:
            result = response.json()
            print(f"同步结果 changed: {result.get('changed')}")
            print(f"返回的任务数量: {len(result.get('items', []))}")
            
            if result.get('changed'):
                items = result.get('items', [])
                if items:
                    print(f"服务器返回了更新: {items[0].get('title')} (版本: {items[0].get('modify_int')})")
                else:
                    print("警告: changed=True 但没有返回任务!")
            else:
                print("严重问题: 服务器没有返回更新!")
        else:
            print(f"同步失败: {response.status_code}")
    else:
        print(f"更新任务失败: {response.status_code}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    try:
        response = requests.get(f"{BASE_URL}/task", timeout=2)
        if response.status_code == 200:
            test_single_machine_scenario()
        else:
            print(f"服务器返回错误: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器。请先启动后端服务。")