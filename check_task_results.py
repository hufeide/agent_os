#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查任务结果详情
"""

import requests
import json

base_url = "http://localhost:8001"

print("=" * 60)
print("检查任务结果详情")
print("=" * 60)

# 使用上一个测试创建的任务ID
dag_id = "eefbbd60-9d1f-4b9b-a820-70309fe516b4"

response = requests.get(f"{base_url}/api/tasks/{dag_id}")

if response.status_code == 200:
    task_status = response.json()
    
    print(f"\nDAG信息:")
    print(f"  名称: {task_status.get('name')}")
    print(f"  总任务数: {task_status.get('total_tasks')}")
    print(f"  是否完成: {task_status.get('is_completed')}")
    
    # 显示每个任务的详细信息
    tasks = task_status.get('tasks', [])
    print(f"\n任务详情 ({len(tasks)} 个任务):")
    
    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*60}")
        print(f"任务 {i}: {task.get('name')}")
        print(f"{'='*60}")
        print(f"  ID: {task.get('task_id')}")
        print(f"  状态: {task.get('status')}")
        print(f"  代理ID: {task.get('agent_id')}")
        print(f"  代理角色: {task.get('agent_role')}")
        print(f"  描述: {task.get('description')}")
        print(f"  创建时间: {task.get('created_at')}")
        print(f"  开始时间: {task.get('started_at')}")
        print(f"  完成时间: {task.get('completed_at')}")
        
        # 显示任务载荷
        if task.get('payload'):
            print(f"\n  载荷:")
            for key, value in task.get('payload').items():
                print(f"    {key}: {value}")
        
        # 显示任务结果
        if task.get('result'):
            print(f"\n  结果:")
            result = task.get('result')
            print(f"    结果类型: {result.get('method', 'unknown')}")
            print(f"    技能名称: {result.get('skill_name', 'N/A')}")
            print(f"    完成时间: {result.get('completed_at', 'N/A')}")
            
            if result.get('result'):
                inner_result = result.get('result')
                print(f"\n  内部结果:")
                if isinstance(inner_result, dict):
                    for key, value in inner_result.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"    {key}: {value[:100]}...")
                        elif isinstance(value, list):
                            print(f"    {key}: [{len(value)} items]")
                        else:
                            print(f"    {key}: {value}")
                else:
                    print(f"    {inner_result}")
        
        # 显示错误信息
        if task.get('error'):
            print(f"\n  错误: {task.get('error')}")

else:
    print(f"❌ 获取任务状态失败: {response.status_code}")
    print(f"错误信息: {response.text}")

print("\n" + "=" * 60)