#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查API返回的数据结构

作者: Agent OS Team
"""

import requests
import json

base_url = "http://localhost:8001"

# 获取上一个任务的结果
dag_id = "b4a44434-a816-4476-b5a1-a56bba392772"

print("=" * 60)
print("详细检查API返回的数据结构")
print("=" * 60)

try:
    response = requests.get(f"{base_url}/api/tasks/{dag_id}")
    detailed_status = response.json()
    
    print(f"\n完整数据结构:")
    print(json.dumps(detailed_status, indent=2, ensure_ascii=False))
    
    if detailed_status.get('tasks'):
        for i, task in enumerate(detailed_status['tasks'], 1):
            print(f"\n任务 {i}: {task.get('name')}")
            print(f"完整结果数据:")
            print(json.dumps(task.get('result'), indent=2, ensure_ascii=False))

except Exception as e:
    print(f"✗ 获取详细状态失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)