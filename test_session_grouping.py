#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试事件按会话归类功能
"""

import requests
import time
import json

base_url = "http://localhost:8001"

print("=" * 60)
print("测试事件按会话归类功能")
print("=" * 60)

# [1] 创建第一个任务
print("\n[1] 创建第一个任务...")
task1_description = "研究人工智能的发展历程"

response1 = requests.post(f"{base_url}/api/tasks", json={
    "description": task1_description,
    "context": {}
})

if response1.status_code == 200:
    result1 = response1.json()
    dag_id1 = result1.get("dag_id")
    session_id1 = result1.get("session_id")
    print(f"  ✅ 任务1创建成功")
    print(f"  dag_id1: {dag_id1}")
    print(f"  session_id1: {session_id1}")
else:
    print(f"  ❌ 任务1创建失败")
    exit(1)

# [2] 创建第二个任务
print("\n[2] 创建第二个任务...")
task2_description = "研究量子计算的基本原理"

response2 = requests.post(f"{base_url}/api/tasks", json={
    "description": task2_description,
    "context": {}
})

if response2.status_code == 200:
    result2 = response2.json()
    dag_id2 = result2.get("dag_id")
    session_id2 = result2.get("session_id")
    print(f"  ✅ 任务2创建成功")
    print(f"  dag_id2: {dag_id2}")
    print(f"  session_id2: {session_id2}")
else:
    print(f"  ❌ 任务2创建失败")
    exit(1)

# [3] 等待任务执行
print("\n[3] 等待任务执行...")
time.sleep(20)

# [4] 获取事件列表（按会话分组）
print("\n[4] 获取事件列表（按会话分组）...")
response = requests.get(f"{base_url}/api/events?grouped=true&limit=50")

if response.status_code == 200:
    events_data = response.json()
    print(f"\n  事件数据结构:")
    print(f"    total: {events_data.get('total')}")
    print(f"    session_count: {events_data.get('session_count')}")
    print(f"    grouped: {events_data.get('grouped')}")
    
    # 检查分组事件
    grouped_events = events_data.get('events', [])
    print(f"\n  分组事件数量: {len(grouped_events)}")
    
    for i, session_group in enumerate(grouped_events, 1):
        print(f"\n  [{i}] 会话组:")
        print(f"      session_id: {session_group.get('session_id')}")
        print(f"      session_name: {session_group.get('session_name')}")
        print(f"      event_count: {session_group.get('event_count')}")
        
        # 显示前几个事件
        events = session_group.get('events', [])
        print(f"      事件列表（前3个）:")
        for j, event in enumerate(events[:3], 1):
            event_type = event.get('type')
            event_data = event.get('data', {})
            event_session_id = event_data.get('session_id', 'N/A')
            print(f"        [{j}] {event_type}")
            print(f"            事件中的session_id: {event_session_id}")
            print(f"            事件数据: {event_data}")
    
    # 验证会话分组是否正确
    print(f"\n  验证会话分组:")
    session_ids_found = set()
    for session_group in grouped_events:
        session_ids_found.add(session_group.get('session_id'))
    
    print(f"    创建的会话ID: {session_id1}, {session_id2}")
    print(f"    找到的会话ID: {session_ids_found}")
    
    if len(session_ids_found) >= 2:
        print(f"    ✅ 事件正确按会话分组")
    else:
        print(f"    ❌ 事件没有正确按会话分组")
        
        # 检查每个事件的session_id
        print(f"\n  检查所有事件的session_id:")
        for session_group in grouped_events:
            for event in session_group.get('events', []):
                event_data = event.get('data', {})
                event_session_id = event_data.get('session_id', 'MISSING')
                event_type = event.get('type')
                print(f"    {event_type}: session_id = {event_session_id}")

else:
    print(f"  ❌ 获取事件失败: {response.status_code}")
    print(f"  错误信息: {response.text}")

# [5] 检查不分组的事件列表
print("\n[5] 检查不分组的事件列表...")
response = requests.get(f"{base_url}/api/events?grouped=false&limit=20")

if response.status_code == 200:
    events_data = response.json()
    print(f"\n  不分组事件数量: {len(events_data.get('events', []))}")
    
    # 检查每个事件的session_id
    print(f"\n  检查每个事件的session_id:")
    for event in events_data.get('events', []):
        event_type = event.get('type')
        event_data = event.get('data', {})
        event_session_id = event_data.get('session_id', 'MISSING')
        print(f"    {event_type}: session_id = {event_session_id}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)