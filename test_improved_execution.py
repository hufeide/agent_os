#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务执行 - 改进版
"""

import requests
import time
import json

base_url = "http://localhost:8001"

print("=" * 60)
print("测试任务执行 - 改进版")
print("=" * 60)

# [1] 创建测试任务
print("\n[1] 创建测试任务...")
task_description = "研究人工智能的发展历程和主要技术突破"

response = requests.post(f"{base_url}/api/tasks", json={
    "description": task_description,
    "context": {}
})

print(f"  状态码: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"  ✅ 任务创建成功")
    dag_id = result.get("dag_id")
    session_id = result.get("session_id")
    print(f"  dag_id: {dag_id}")
    print(f"  session_id: {session_id}")
else:
    print(f"  ❌ 任务创建失败")
    print(f"  错误信息: {response.text}")
    exit(1)

# [2] 等待任务分解完成
print("\n[2] 等待任务分解完成...")
time.sleep(10)  # 给足够的时间让任务分解完成

# [3] 检查任务状态
print("\n[3] 检查任务状态...")
response = requests.get(f"{base_url}/api/tasks/{dag_id}")
print(f"  状态码: {response.status_code}")

if response.status_code == 200:
    task_status = response.json()
    print(f"\n  任务详情:")
    print(f"    DAG名称: {task_status.get('name')}")
    print(f"    总任务数: {task_status.get('total_tasks')}")
    print(f"    是否完成: {task_status.get('is_completed')}")
    print(f"    完成数: {task_status.get('completed_count')}")
    print(f"    失败数: {task_status.get('failed_count')}")
    print(f"    待处理数: {task_status.get('pending_count')}")
    
    # 显示任务列表
    tasks = task_status.get('tasks', [])
    print(f"\n  任务列表 ({len(tasks)} 个任务):")
    for i, task in enumerate(tasks, 1):
        print(f"    [{i}] 任务: {task.get('name')}")
        print(f"        状态: {task.get('status')}")
        print(f"        代理: {task.get('agent_id')}")
        print(f"        描述: {task.get('description', '')[:50]}...")
        if task.get('result'):
            print(f"        结果: {str(task.get('result'))[:100]}...")
        print()
else:
    print(f"  ❌ 获取任务状态失败")
    print(f"  错误信息: {response.text}")

# [4] 监控任务执行
print("\n[4] 监控任务执行...")
max_wait = 180  # 最多等待180秒
start_time = time.time()
last_status = {}

while time.time() - start_time < max_wait:
    response = requests.get(f"{base_url}/api/tasks/{dag_id}")
    
    if response.status_code == 200:
        task_status = response.json()
        
        # 只在有变化时打印
        current_status = {
            "total": task_status.get('total_tasks'),
            "completed": task_status.get('completed_count'),
            "failed": task_status.get('failed_count'),
            "pending": task_status.get('pending_count')
        }
        
        if current_status != last_status:
            print(f"\n  [{int(time.time() - start_time)}s] 状态更新:")
            print(f"    总任务数: {current_status['total']}")
            print(f"    完成: {current_status['completed']}")
            print(f"    失败: {current_status['failed']}")
            print(f"    待处理: {current_status['pending']}")
            last_status = current_status
            
            # 显示任务详情
            tasks = task_status.get('tasks', [])
            for task in tasks:
                print(f"      - {task.get('name')}: {task.get('status')}")
                if task.get('error'):
                    print(f"        错误: {task.get('error')}")
        
        # 检查是否完成
        if task_status.get('is_completed') and task_status.get('total_tasks', 0) > 0:
            print(f"\n  ✅ 所有任务已完成！")
            break
        
        # 检查是否有失败
        if task_status.get('failed_count', 0) > 0:
            print(f"\n  ⚠️  有任务失败")
            break
    
    time.sleep(5)

# [5] 检查最终结果
print("\n[5] 检查最终结果...")
response = requests.get(f"{base_url}/api/tasks/{dag_id}")

if response.status_code == 200:
    task_status = response.json()
    
    print(f"\n  最终状态:")
    print(f"    是否完成: {task_status.get('is_completed')}")
    print(f"    完成数: {task_status.get('completed_count')}")
    print(f"    失败数: {task_status.get('failed_count')}")
    
    # 显示所有任务的详细结果
    tasks = task_status.get('tasks', [])
    print(f"\n  所有任务结果:")
    for i, task in enumerate(tasks, 1):
        print(f"\n  [{i}] {task.get('name')}")
        print(f"      状态: {task.get('status')}")
        print(f"      代理: {task.get('agent_id')}")
        
        if task.get('result'):
            result = task.get('result')
            print(f"      结果类型: {result.get('method', 'unknown')}")
            
            # 显示不同类型的结果
            if result.get('skill_name'):
                print(f"      技能: {result.get('skill_name')}")
            
            if result.get('result'):
                inner_result = result.get('result')
                if isinstance(inner_result, dict):
                    # 显示研究/分析/写作结果
                    if 'findings' in inner_result:
                        print(f"      研究发现: {inner_result.get('findings')[:100]}...")
                    if 'answer_to_original_question' in inner_result:
                        print(f"      回答: {inner_result.get('answer_to_original_question')[:100]}...")
                    if 'output' in inner_result:
                        print(f"      输出: {inner_result.get('output')[:100]}...")
                else:
                    print(f"      结果: {str(inner_result)[:100]}...")
        
        if task.get('error'):
            print(f"      错误: {task.get('error')}")

# [6] 检查事件日志
print("\n[6] 检查事件日志...")
response = requests.get(f"{base_url}/api/events?limit=20")

if response.status_code == 200:
    events = response.json()
    if isinstance(events, list):
        print(f"  事件数: {len(events)}")
        
        # 显示最近的事件
        for event in events[:10]:
            print(f"    - {event.get('type')}: {event.get('data', {})}")
    else:
        print(f"  事件响应格式: {type(events)}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)