#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查API返回的完整数据
"""

import requests
import json

base_url = "http://localhost:8001"

print("=" * 60)
print("检查API返回的完整数据")
print("=" * 60)

# 使用上一个测试创建的任务ID
dag_id = "eefbbd60-9d1f-4b9b-a820-70309fe516b4"

response = requests.get(f"{base_url}/api/tasks/{dag_id}")

if response.status_code == 200:
    task_status = response.json()
    
    print(f"\n完整的API响应:")
    print(json.dumps(task_status, indent=2, ensure_ascii=False))
    
    # 特别关注第一个任务的完整结果
    tasks = task_status.get('tasks', [])
    if tasks:
        first_task = tasks[0]
        print(f"\n\n第一个任务的完整结果:")
        print(json.dumps(first_task, indent=2, ensure_ascii=False))

else:
    print(f"❌ 获取任务状态失败: {response.status_code}")
    print(f"错误信息: {response.text}")

print("\n" + "=" * 60)