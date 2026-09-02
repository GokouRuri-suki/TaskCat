#!/usr/bin/env python3
"""
验证修复是否有效
测试：单机创建任务后同步的场景
"""
import json
import requests
import time

BASE_URL = "http://127.0.0.1:8000/TaskCat/api/ver1.0"

def test_fix():
    """测试修复后的同步逻辑"""
    print("="*60)
    print("验证修复：单机创建任务后同步")
    print("="*60)
    
    # 清空服务器
    print("\n[初始化] 清空服务器...")
    response = requests.get(f"{BASE_URL}/task")
    if response.status_code == 200:
        tasks = response.json()["tasks"]
        for i in range(len(tasks), 0, -1):
            requests.delete(f"{BASE_URL}/task/{i}")
    
    # 创建新任务
    print("\n[步骤1] 创建新任务...")
    task_data = {
        "title": "测试修复的任务",
        "content": "测试单机同步问题是否修复",
        "status": "todo",
        "priority": 1
    }
    
    response = requests.post(f"{BASE_URL}/task", json=task_data)
    if response.status_code != 200:
        print(f"创建任务失败: {response.status_code}")
        return
    
    created_task = response.json()["task"]
    task_id = created_task["id"]
    
    print(f"创建任务成功: {created_task['title']} (版本: {created_task['modify_int']})")
    
    # 模拟客户端有该任务（相同版本）
    print("\n[步骤2] 模拟客户端有相同版本的任务...")
    client_task = created_task.copy()
    
    response = requests.post(f"{BASE_URL}/tasks/sync", json=[client_task])
    if response.status_code == 200:
        result = response.json()
        items = result.get('items', [])
        
        print(f"同步结果: changed={result.get('changed')}")
        print(f"返回的任务数量: {len(items)}")
        
        if items:
            print("服务器返回了以下任务:")
            for item in items:
                print(f"  - {item.get('title')} (版本: {item.get('modify_int')}, ID: {item.get('id')})")
                
                # 检查是否返回了新创建的任务
                if item.get('id') == task_id:
                    print("  ✓ 服务器返回了新创建的任务（修复生效！）")
                else:
                    print("  ✗ 服务器没有返回新创建的任务")
        else:
            print("服务器没有返回任何任务")
            
            # 检查changed标志
            if result.get('changed'):
                print("警告: changed=True 但没有返回任务！")
    else:
        print(f"同步失败: {response.status_code}")
    
    # 测试空客户端场景
    print("\n[步骤3] 测试空客户端场景...")
    response = requests.post(f"{BASE_URL}/tasks/sync", json=[])
    if response.status_code == 200:
        result = response.json()
        items = result.get('items', [])
        
        print(f"同步结果: changed={result.get('changed')}")
        print(f"返回的任务数量: {len(items)}")
        
        found = False
        for item in items:
            if item.get('id') == task_id:
                found = True
                print(f"✓ 空客户端收到了新任务: {item.get('title')}")
                break
        
        if not found:
            print("✗ 空客户端没有收到新任务")
    else:
        print(f"同步失败: {response.status_code}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    
    # 验证服务器代码
    print("\n[验证] 检查服务器代码修改...")
    print("修改内容: 对于新创建的任务(modify_int=1)，即使客户端版本为0也返回")
    print("预期效果: 单机创建任务后，即使客户端有相同版本，也能在同步中看到")

if __name__ == "__main__":
    try:
        response = requests.get(f"{BASE_URL}/task", timeout=2)
        if response.status_code == 200:
            test_fix()
        else:
            print(f"服务器返回错误: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器。请先启动后端服务。")