#!/usr/bin/env python3
"""
模拟真实单机使用场景
1. 启动应用（首次运行，本地无数据）
2. 创建任务
3. 查看是否能同步
"""
import json
import requests
import time

BASE_URL = "http://127.0.0.1:8000/TaskCat/api/ver1.0"

def simulate_real_usage():
    """模拟真实使用场景"""
    print("="*60)
    print("模拟真实单机使用场景")
    print("="*60)
    
    print("\n[场景1] 首次运行，本地无数据")
    print("1. 用户启动应用")
    print("2. 应用发送空列表同步")
    
    response = requests.post(f"{BASE_URL}/tasks/sync", json=[])
    if response.status_code == 200:
        result = response.json()
        print(f"  同步结果: changed={result.get('changed')}")
        print(f"  收到任务数: {len(result.get('items', []))}")
        
        if result.get('items'):
            print("  初始任务:")
            for item in result.get('items', []):
                if item.get('status') != 'deleted':
                    print(f"    - {item.get('title')} (状态: {item.get('status')})")
    else:
        print(f"  同步失败: {response.status_code}")
    
    print("\n[场景2] 创建新任务")
    print("1. 用户点击'新建'按钮")
    print("2. 输入任务信息")
    print("3. 点击保存")
    
    task_data = {
        "title": "买菜",
        "content": "去超市买牛奶和面包",
        "status": "todo",
        "priority": 2
    }
    
    response = requests.post(f"{BASE_URL}/task", json=task_data)
    if response.status_code == 200:
        created = response.json()["task"]
        print(f"  创建成功: {created['title']} (版本: {created['modify_int']})")
        
        # 模拟客户端本地存储了这个任务
        local_task = created.copy()
    else:
        print(f"  创建失败: {response.status_code}")
        return
    
    print("\n[场景3] 创建后立即同步")
    print("1. 应用自动触发同步（2秒后）")
    print("2. 发送本地所有任务（包括刚创建的）")
    
    # 模拟客户端有本地缓存
    local_tasks = [local_task]
    
    response = requests.post(f"{BASE_URL}/tasks/sync", json=local_tasks)
    if response.status_code == 200:
        result = response.json()
        print(f"  同步结果: changed={result.get('changed')}")
        print(f"  收到更新数: {len(result.get('items', []))}")
        
        items = result.get('items', [])
        if items:
            print("  服务器返回的更新:")
            for item in items:
                print(f"    - {item.get('title')} (版本: {item.get('modify_int')})")
        else:
            print("  没有收到更新")
            
            if result.get('changed'):
                print("  警告: changed=True 但没有返回项目!")
    else:
        print(f"  同步失败: {response.status_code}")
    
    print("\n[场景4] 修改任务后同步")
    print("1. 用户修改任务内容")
    print("2. 应用发送更新到服务器")
    print("3. 然后同步")
    
    # 先更新任务
    update_data = {
        "title": "买菜（修改）",
        "content": "去超市买牛奶、面包和鸡蛋",
        "priority": 1
    }
    
    # 需要知道任务序号
    response = requests.get(f"{BASE_URL}/task")
    if response.status_code == 200:
        tasks = response.json()["tasks"]
        active_tasks = [t for t in tasks if t.get('status') != 'deleted']
        
        if active_tasks:
            # 找到我们刚创建的任务
            target_task = None
            for i, task in enumerate(active_tasks):
                if task.get('id') == created['id']:
                    target_task = task
                    sequence = i + 1
                    break
            
            if target_task:
                response = requests.patch(f"{BASE_URL}/task/{sequence}", json=update_data)
                if response.status_code == 200:
                    updated = response.json()
                    print(f"  更新成功: {updated['title']} (新版本: {updated['modify_int']})")
                    
                    # 现在客户端有旧版本(1)，服务器有新版本(2)
                    # 模拟同步
                    response = requests.post(f"{BASE_URL}/tasks/sync", json=[local_task])  # 旧版本
                    if response.status_code == 200:
                        result = response.json()
                        print(f"  同步结果: changed={result.get('changed')}")
                        
                        items = result.get('items', [])
                        if items:
                            print("  收到服务器更新:")
                            for item in items:
                                if item.get('id') == created['id']:
                                    print(f"    ✓ 收到了任务更新: {item.get('title')} (版本: {item.get('modify_int')})")
                                else:
                                    print(f"    - {item.get('title')} (版本: {item.get('modify_int')})")
                        else:
                            print("  没有收到更新")
                    else:
                        print(f"  同步失败: {response.status_code}")
                else:
                    print(f"  更新失败: {response.status_code}")
    
    print("\n" + "="*60)
    print("问题诊断")
    print("="*60)
    
    print("\n可能的问题:")
    print("1. 单机创建任务后，同步时服务器不返回该任务（因为版本相同）")
    print("   - 这是正常行为，不是bug")
    print("   - 客户端已经有这个任务，不需要从服务器获取")
    
    print("\n2. 真正的'无法sync'可能指:")
    print("   a) 任务没有保存到服务器")
    print("   b) 其他客户端收不到这个任务")
    print("   c) 修改后不同步")
    
    print("\n3. 验证方法:")
    print("   a) 检查数据文件是否保存")
    print("   b) 用另一个'客户端'（如curl）测试是否能收到任务")
    print("   c) 测试修改后的同步")

if __name__ == "__main__":
    try:
        response = requests.get(f"{BASE_URL}/task", timeout=2)
        if response.status_code == 200:
            simulate_real_usage()
        else:
            print(f"服务器返回错误: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器。请先启动后端服务。")