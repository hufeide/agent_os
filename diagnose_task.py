#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断任务执行问题

作者: Agent OS Team
"""

import requests
import json
import time
import uuid

base_url = "http://localhost:8001"

print("=" * 60)
print("诊断任务执行问题")
print("=" * 60)

# 创建一个简单的测试任务
print("\n创建测试任务...")
task_data = {
    "description": "简单测试任务",
    "context": {"original_question": "这是一个测试问题"}
}

try:
    response = requests.post(f"{base_url}/api/tasks", json=task_data)
    print(f"创建任务状态码: {response.status_code}")
    result = response.json()
    dag_id = result.get('dag_id')
    print(f"DAG ID: {dag_id}")
    
    # 立即检查任务状态
    print("\n立即检查任务状态...")
    response = requests.get(f"{base_url}/api/tasks/{dag_id}")
    status = response.json()
    print(f"任务名称: {status.get('name')}")
    print(f"任务描述: {status.get('description')}")
    print(f"总任务数: {status.get('total_tasks')}")
    print(f"是否完成: {status.get('is_completed')}")
    
    # 检查子任务
    if status.get('tasks'):
        print(f"\n子任务数量: {len(status['tasks'])}")
        for i, task in enumerate(status['tasks'], 1):
            print(f"  子任务 {i}: {task.get('name')}")
            print(f"    状态: {task.get('status')}")
            print(f"    代理角色: {task.get('agent_role')}")
    else:
        print("\n没有子任务")
    
    # 等待一段时间再检查
    print("\n等待10秒后再次检查...")
    time.sleep(10)
    
    response = requests.get(f"{base_url}/api/tasks/{dag_id}")
    status = response.json()
    print(f"\n10秒后状态:")
    print(f"总任务数: {status.get('total_tasks')}")
    print(f"是否完成: {status.get('is_completed')}")
    
    if status.get('tasks'):
        print(f"\n子任务状态:")
        for i, task in enumerate(status['tasks'], 1):
            print(f"  子任务 {i}: {task.get('name')} - {task.get('status')}")
    
    # 检查任务列表
    print("\n检查任务列表...")
    response = requests.get(f"{base_url}/api/tasks")
    tasks_data = response.json()
    print(f"总任务数: {tasks_data.get('total_count')}")
    
    for i, task in enumerate(tasks_data.get('tasks', []), 1):
        print(f"  任务 {i}: {task.get('name')} - 完成: {task.get('is_completed')}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成！")
print("=" * 60)