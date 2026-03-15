#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务状态更新逻辑
验证任务创建后不会立即显示完成
"""

import requests
import time
import json

base_url = "http://localhost:8001"

print("=" * 60)
print("测试任务状态更新逻辑")
print("=" * 60)

# [1] 创建测试任务
print("\n[1] 创建测试任务...")
task_description = "测试任务状态更新逻辑"

response = requests.post(f"{base_url}/api/tasks", json={
    "description": task_description,
    "context": {}
})

if response.status_code == 200:
    result = response.json()
    dag_id = result.get("dag_id")
    print(f"  ✅ 任务创建成功")
    print(f"  dag_id: {dag_id}")
    print(f"  状态: {result.get('status')}")
else:
    print(f"  ❌ 任务创建失败")
    exit(1)

# [2] 立即检查任务状态（应该在规划中）
print("\n[2] 立即检查任务状态...")
time.sleep(2)

response = requests.get(f"{base_url}/api/tasks")

if response.status_code == 200:
    tasks_data = response.json()
    tasks = tasks_data.get('tasks', [])
    our_task = None
    for task in tasks:
        if task.get('dag_id') == dag_id:
            our_task = task
            break
    
    if our_task:
        print(f"  任务基本信息:")
        print(f"    名称: {our_task.get('name')}")
        print(f"    总任务数: {our_task.get('total_tasks')}")
        print(f"    是否完成: {our_task.get('is_completed')}")
        print(f"    完成数: {our_task.get('completed_count')}")
        
        # 验证状态
        if our_task.get('total_tasks') == 0:
            print(f"  ✅ 正确：任务刚创建，还没有子任务")
        else:
            print(f"  ⚠️  注意：任务已经有子任务了")
        
        if not our_task.get('is_completed'):
            print(f"  ✅ 正确：任务状态不是'已完成'")
        else:
            print(f"  ❌ 错误：任务状态显示为'已完成'，但任务刚创建")
        
        if not our_task.get('final_answer'):
            print(f"  ✅ 正确：还没有最终回答")
        else:
            print(f"  ⚠️  注意：已经有最终回答了")
    else:
        print(f"  ❌ 未找到刚创建的任务")
else:
    print(f"  ❌ 获取任务列表失败")

# [3] 等待任务规划完成
print("\n[3] 等待任务规划完成...")
time.sleep(10)

response = requests.get(f"{base_url}/api/tasks")

if response.status_code == 200:
    tasks_data = response.json()
    tasks = tasks_data.get('tasks', [])
    our_task = None
    for task in tasks:
        if task.get('dag_id') == dag_id:
            our_task = task
            break
    
    if our_task:
        print(f"  任务规划后的状态:")
        print(f"    总任务数: {our_task.get('total_tasks')}")
        print(f"    完成数: {our_task.get('completed_count')}")
        print(f"    是否完成: {our_task.get('is_completed')}")
        
        if our_task.get('total_tasks') > 0:
            print(f"  ✅ 正确：任务规划完成，有子任务了")
        else:
            print(f"  ❌ 错误：任务规划后还是没有子任务")
        
        if not our_task.get('is_completed'):
            print(f"  ✅ 正确：任务状态不是'已完成'")
        else:
            print(f"  ❌ 错误：任务状态显示为'已完成'")
    else:
        print(f"  ❌ 未找到刚创建的任务")
else:
    print(f"  ❌ 获取任务列表失败")

# [4] 等待任务执行完成
print("\n[4] 等待任务执行完成...")
time.sleep(30)

response = requests.get(f"{base_url}/api/tasks")

if response.status_code == 200:
    tasks_data = response.json()
    tasks = tasks_data.get('tasks', [])
    our_task = None
    for task in tasks:
        if task.get('dag_id') == dag_id:
            our_task = task
            break
    
    if our_task:
        print(f"  任务执行完成后的状态:")
        print(f"    总任务数: {our_task.get('total_tasks')}")
        print(f"    完成数: {our_task.get('completed_count')}")
        print(f"    是否完成: {our_task.get('is_completed')}")
        
        if our_task.get('is_completed'):
            print(f"  ✅ 正确：任务状态显示为'已完成'")
        else:
            print(f"  ⚠️  注意：任务状态还不是'已完成'")
        
        if our_task.get('final_answer'):
            print(f"  ✅ 正确：有最终回答")
        else:
            print(f"  ⚠️  注意：还没有最终回答")
        
        # 总结
        print(f"\n  总结:")
        print(f"    任务创建后状态: {'✅ 正确' if not our_task.get('is_completed') or our_task.get('total_tasks') > 0 else '❌ 错误'}")
        print(f"    任务完成后状态: {'✅ 正确' if our_task.get('is_completed') else '⚠️  注意'}")
    else:
        print(f"  ❌ 未找到刚创建的任务")
else:
    print(f"  ❌ 获取任务列表失败")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\n前端状态显示说明:")
print("1. 规划中（蓝色标签）- 任务刚创建，还没有子任务")
print("2. 执行中（黄色标签）- 任务有子任务，但还没有全部完成")
print("3. 已完成（绿色标签）- 所有子任务都已完成")
print("=" * 60)