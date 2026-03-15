#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务执行流程

验证：创建任务后，任务是否能正常执行和完成

作者: Agent OS Team
"""

import requests
import json
import time

base_url = "http://localhost:8001"

print("=" * 60)
print("测试任务执行流程")
print("=" * 60)

# [1] 创建一个简单的测试任务
print("\n[1] 创建测试任务...")
task_data = {
    "description": "简单测试任务：计算1+1",
    "context": {"original_question": "1+1等于多少？"}
}

response = requests.post(f"{base_url}/api/tasks", json=task_data)
print(f"  状态码: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    dag_id = result.get('dag_id')
    session_id = result.get('session_id', 'unknown')
    print(f"  ✅ 任务创建成功")
    print(f"  dag_id: {dag_id}")
    print(f"  session_id: {session_id}")
else:
    print(f"  ❌ 任务创建失败: {response.text}")
    exit(1)

# [2] 监控任务执行状态
print("\n[2] 监控任务执行状态...")
max_wait = 60  # 最多等待60秒
start_time = time.time()

while time.time() - start_time < max_wait:
    # 获取任务状态
    response = requests.get(f"{base_url}/api/tasks/{dag_id}")
    if response.status_code == 200:
        task_status = response.json()
        
        print(f"\n  当前状态:")
        print(f"    DAG名称: {task_status.get('name')}")
        print(f"    总任务数: {task_status.get('total_tasks')}")
        print(f"    是否完成: {task_status.get('is_completed')}")
        print(f"    完成数: {task_status.get('completed_count')}")
        print(f"    失败数: {task_status.get('failed_count')}")
        print(f"    待处理数: {task_status.get('pending_count')}")
        
        # 显示任务详情
        tasks = task_status.get('tasks', [])
        if tasks:
            for task in tasks:
                print(f"    任务: {task.get('name')}")
                print(f"      状态: {task.get('status')}")
                print(f"      代理: {task.get('agent_id')}")
                print(f"      开始时间: {task.get('started_at')}")
                print(f"      完成时间: {task.get('completed_at')}")
        
        # 检查是否完成
        if task_status.get('is_completed'):
            print(f"\n  ✅ 任务已完成！")
            break
        
        # 检查是否有失败
        if task_status.get('failed_count', 0) > 0:
            print(f"\n  ❌ 任务执行失败")
            break
    
    # 等待3秒后再次检查
    time.sleep(3)

# [3] 检查事件日志
print("\n[3] 检查事件日志...")
response = requests.get(f"{base_url}/api/events?session_id={session_id}&limit=20&grouped=false")
if response.status_code == 200:
    events_data = response.json()
    print(f"  事件数: {events_data.get('total', 0)}")
    
    if events_data.get('events'):
        print(f"  事件列表:")
        for i, event in enumerate(events_data['events'], 1):
            print(f"    {i}. {event.get('type')} - {event.get('timestamp')}")
            print(f"       数据: {event.get('data')}")

# [4] 检查最终结果
print("\n[4] 检查最终结果...")
response = requests.get(f"{base_url}/api/tasks/{dag_id}")
if response.status_code == 200:
    task_status = response.json()
    
    if task_status.get('is_completed'):
        print(f"  ✅ 任务已完成")
        
        # 检查是否有最终结果
        tasks = task_status.get('tasks', [])
        if tasks:
            for task in tasks:
                if task.get('result'):
                    print(f"  任务结果: {task.get('result')}")
    else:
        print(f"  ❌ 任务未完成")
        print(f"  当前状态: {task_status.get('status_counts')}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)