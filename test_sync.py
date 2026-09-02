#!/usr/bin/env python3
"""
测试同步逻辑
"""
import json
import requests
import time
from typing import List, Dict, Any

BASE_URL = "http://127.0.0.1:8000/TaskCat/api/ver1.0"

def print_response(response):
    """打印响应信息"""
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        except:
            print(f"响应文本: {response.text}")
    else:
        print(f"错误: {response.text}")
    print("-" * 50)

def test_create_task():
    """测试创建任务"""
    print("1. 测试创建任务")
    task_data = {
        "title": "测试任务1",
        "content": "这是测试内容",
        "status": "todo",
        "priority": 3
    }
    
    response = requests.post(f"{BASE_URL}/task", json=task_data)
    print_response(response)
    
    if response.status_code == 200:
        return response.json()["task"]
    return None

def test_get_tasks():
    """测试获取任务"""
    print("2. 测试获取任务")
    response = requests.get(f"{BASE_URL}/task")
    print_response(response)
    return response.json()["tasks"] if response.status_code == 200 else []

def test_sync_with_empty_client():
    """测试同步 - 客户端空列表"""
    print("3. 测试同步（客户端空列表）")
    response = requests.post(f"{BASE_URL}/tasks/sync", json=[])
    print_response(response)
    return response.json() if response.status_code == 200 else {}

def test_sync_with_client_tasks(client_tasks: List[Dict]):
    """测试同步 - 客户端有任务列表"""
    print("4. 测试同步（客户端有任务列表）")
    response = requests.post(f"{BASE_URL}/tasks/sync", json=client_tasks)
    print_response(response)
    return response.json() if response.status_code == 200 else {}

def analyze_sync_logic():
    """分析同步逻辑"""
    print("\n" + "="*60)
    print("同步逻辑分析")
    print("="*60)
    
    # 1. 创建新任务
    created_task = test_create_task()
    if not created_task:
        print("创建任务失败，退出测试")
        return
    
    print(f"创建的任务ID: {created_task['id']}")
    print(f"创建的任务版本: {created_task['modify_int']}")
    
    # 等待一下
    time.sleep(1)
    
    # 2. 获取所有任务
    server_tasks = test_get_tasks()
    print(f"服务器任务数量: {len(server_tasks)}")
    
    # 3. 测试空客户端同步
    sync_result1 = test_sync_with_empty_client()
    
    # 4. 测试带客户端任务的同步
    # 模拟客户端有相同的任务，但版本号低
    client_task_low_version = created_task.copy()
    client_task_low_version["modify_int"] = 0  # 客户端版本比服务器低
    
    sync_result2 = test_sync_with_client_tasks([client_task_low_version])
    
    # 5. 模拟客户端有更新的版本（理论上不应该发生，因为刚创建）
    client_task_high_version = created_task.copy()
    client_task_high_version["modify_int"] = 5  # 客户端版本比服务器高
    client_task_high_version["title"] = "客户端修改的标题"
    
    sync_result3 = test_sync_with_client_tasks([client_task_high_version])
    
    print("\n" + "="*60)
    print("问题分析")
    print("="*60)
    
    # 检查同步逻辑
    print(f"1. 创建任务时设置的版本号: {created_task.get('modify_int')}")
    print(f"2. 空客户端同步结果 - changed: {sync_result1.get('changed', False)}")
    print(f"3. 低版本客户端同步结果 - changed: {sync_result2.get('changed', False)}")
    print(f"4. 高版本客户端同步结果 - changed: {sync_result3.get('changed', False)}")
    
    if sync_result1.get('changed'):
        print("✓ 空客户端同步检测到服务器有更新（正确）")
    else:
        print("✗ 空客户端同步未检测到服务器更新（可能有问题）")
    
    # 再次获取任务查看是否被更新
    time.sleep(1)
    final_tasks = test_get_tasks()
    if final_tasks:
        final_task = final_tasks[0]
        print(f"最终任务标题: {final_task.get('title')}")
        print(f"最终任务版本: {final_task.get('modify_int')}")

if __name__ == "__main__":
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/task", timeout=2)
        if response.status_code == 200:
            print("服务器正在运行，开始测试...")
            analyze_sync_logic()
        else:
            print(f"服务器返回错误: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器。请先启动后端服务。")
        print("运行: cd fastapi && source .venv/bin/activate && python -m uvicorn src:app --host 127.0.0.1 --port 8000")