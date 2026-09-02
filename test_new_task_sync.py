#!/usr/bin/env python3
"""
测试新创建任务的同步问题
模拟：机器A创建任务 -> 机器B同步
"""
import json
import requests
import time

BASE_URL = "http://127.0.0.1:8000/TaskCat/api/ver1.0"

def simulate_two_machines():
    """模拟两台机器：A创建任务，B获取任务"""
    print("="*60)
    print("模拟两台机器同步场景")
    print("="*60)
    
    # 清空服务器
    print("\n[初始化] 清空服务器...")
    response = requests.get(f"{BASE_URL}/task")
    if response.status_code == 200:
        tasks = response.json()["tasks"]
        for i in range(len(tasks), 0, -1):
            requests.delete(f"{BASE_URL}/task/{i}")
    
    # 机器A：创建任务
    print("\n[机器A] 创建新任务...")
    task_data = {
        "title": "机器A创建的任务",
        "content": "这是机器A创建的任务",
        "status": "todo",
        "priority": 1
    }
    
    response = requests.post(f"{BASE_URL}/task", json=task_data)
    if response.status_code != 200:
        print(f"创建任务失败: {response.status_code}")
        return
    
    created_task = response.json()["task"]
    print(f"机器A创建了任务: {created_task['title']} (版本: {created_task['modify_int']})")
    
    # 等待一下
    time.sleep(1)
    
    # 机器B：首次同步（空列表）
    print("\n[机器B] 首次同步（空列表）...")
    response = requests.post(f"{BASE_URL}/tasks/sync", json=[])
    if response.status_code == 200:
        result = response.json()
        print(f"同步结果: changed={result.get('changed')}")
        
        items = result.get('items', [])
        print(f"返回的任务数量: {len(items)}")
        
        if items:
            print("机器B收到了以下任务:")
            for item in items:
                print(f"  - {item.get('title')} (版本: {item.get('modify_int')})")
        else:
            print("问题: 机器B没有收到任何任务!")
    else:
        print(f"同步失败: {response.status_code}")
    
    # 模拟机器B有本地缓存的情况
    print("\n[机器B] 有本地缓存后再次同步...")
    # 假设机器B缓存了刚才收到的任务
    cached_task = created_task.copy()
    
    response = requests.post(f"{BASE_URL}/tasks/sync", json=[cached_task])
    if response.status_code == 200:
        result = response.json()
        print(f"同步结果: changed={result.get('changed')}")
        
        items = result.get('items', [])
        print(f"返回的任务数量: {len(items)}")
        
        if result.get('changed'):
            if items:
                print("机器B收到了更新:")
                for item in items:
                    print(f"  - {item.get('title')} (版本: {item.get('modify_int')})")
            else:
                print("警告: changed=True 但没有返回任务!")
        else:
            print("正常: 没有新更新")
    else:
        print(f"同步失败: {response.status_code}")
    
    # 机器A修改任务
    print("\n[机器A] 修改任务...")
    update_data = {
        "title": "机器A修改后的任务",
        "content": "机器A更新了内容",
        "priority": 2
    }
    response = requests.patch(f"{BASE_URL}/task/1", json=update_data)
    if response.status_code == 200:
        updated_task = response.json()
        print(f"机器A修改了任务，新版本: {updated_task.get('modify_int')}")
    
    # 机器B再次同步（有旧版本缓存）
    print("\n[机器B] 再次同步（有旧版本缓存）...")
    response = requests.post(f"{BASE_URL}/tasks/sync", json=[cached_task])  # 还是旧版本
    if response.status_code == 200:
        result = response.json()
        print(f"同步结果: changed={result.get('changed')}")
        
        items = result.get('items', [])
        print(f"返回的任务数量: {len(items)}")
        
        if result.get('changed'):
            if items:
                print("机器B收到了更新:")
                for item in items:
                    print(f"  - {item.get('title')} (版本: {item.get('modify_int')})")
            else:
                print("严重问题: changed=True 但没有返回任务!")
        else:
            print("问题: 服务器没有检测到更新!")
    else:
        print(f"同步失败: {response.status_code}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

def analyze_sync_issue():
    """分析同步问题"""
    print("\n" + "="*60)
    print("同步问题分析")
    print("="*60)
    
    print("\n潜在问题分析:")
    print("1. 新创建的任务 sync 问题:")
    print("   - 机器A创建任务后，如果机器B从未同步过（空列表），能收到任务 ✓")
    print("   - 机器A创建任务后，如果机器B有相同版本的任务，不会收到更新 ✓（正常）")
    print("   - 问题: 如果机器B在任务创建后第一次同步时失败/中断，可能错过任务")
    
    print("\n2. 修改后的任务 sync 问题:")
    print("   - 机器A修改任务后，机器B有旧版本，应该能收到更新 ✓")
    print("   - 如果修改后版本号没有增加，可能无法同步 ✗")
    
    print("\n3. 单机场景问题:")
    print("   - 单机创建任务后，自己同步自己:")
    print("     * 发送空列表: 能收到任务 ✓")
    print("     * 发送相同版本: 不会收到更新 ✓（正常，因为版本相同）")
    print("     * 问题: 单机无法检测到'自己刚创建的任务需要同步'")

if __name__ == "__main__":
    try:
        response = requests.get(f"{BASE_URL}/task", timeout=2)
        if response.status_code == 200:
            simulate_two_machines()
            analyze_sync_issue()
        else:
            print(f"服务器返回错误: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器。请先启动后端服务。")