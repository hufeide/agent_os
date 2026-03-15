#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试事件时间戳修复和前端显示

验证：
1. 事件时间戳格式是否正确
2. 前端是否能正确显示时间
3. 事件按会话分组是否正常工作

作者: Agent OS Team
"""

import requests
import json
from datetime import datetime

base_url = "http://localhost:8001"

print("=" * 60)
print("测试事件时间戳修复和前端显示")
print("=" * 60)

# [1] 测试事件时间戳格式
print("\n[1] 测试事件时间戳格式...")
try:
    response = requests.get(f"{base_url}/api/events?limit=10&grouped=true")
    events_data = response.json()
    
    print(f"  总事件数: {events_data.get('total', 0)}")
    print(f"  会话数: {events_data.get('session_count', 0)}")
    print(f"  是否分组: {events_data.get('grouped', False)}")
    
    # 检查时间戳格式
    if events_data.get('events'):
        for i, session_group in enumerate(events_data['events'], 1):
            print(f"\n  会话 {i}:")
            print(f"    会话ID: {session_group.get('session_id')}")
            print(f"    会话名称: {session_group.get('session_name')}")
            print(f"    事件数: {session_group.get('event_count', 0)}")
            
            events = session_group.get('events', [])
            for j, event in enumerate(events[:3], 1):
                timestamp = event.get('timestamp')
                print(f"    事件 {j}:")
                print(f"      类型: {event.get('type')}")
                print(f"      时间戳: {timestamp}")
                
                # 验证时间戳格式
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        print(f"      ✅ 时间戳格式正确: {dt}")
                    except Exception as e:
                        print(f"      ❌ 时间戳格式错误: {e}")
                else:
                    print(f"      ❌ 时间戳为空")
    
    print(f"\n  ✅ 事件时间戳格式检查完成")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# [2] 测试创建新事件并验证时间戳
print("\n[2] 测试创建新事件并验证时间戳...")
try:
    # 创建一个测试任务来生成新事件
    task_data = {
        "description": "测试事件时间戳显示",
        "context": {"original_question": "测试问题"}
    }
    
    response = requests.post(f"{base_url}/api/tasks", json=task_data)
    print(f"  创建任务状态码: {response.status_code}")
    
    if response.status_code == 200:
        print(f"  ✅ 任务创建成功")
        
        # 等待几秒后检查事件
        import time
        time.sleep(3)
        
        # 获取最新事件
        response = requests.get(f"{base_url}/api/events?limit=10&grouped=true")
        events_data = response.json()
        
        print(f"\n  最新事件:")
        if events_data.get('events'):
            for session_group in events_data['events'][:2]:
                events = session_group.get('events', [])
                for event in events[:3]:
                    timestamp = event.get('timestamp')
                    print(f"    类型: {event.get('type')}, 时间戳: {timestamp}")
                    
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            print(f"    ✅ 时间戳有效: {dt}")
                        except Exception as e:
                            print(f"    ❌ 时间戳无效: {e}")
                    else:
                        print(f"    ❌ 时间戳为空")
    else:
        print(f"  ❌ 任务创建失败")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# [3] 测试不分组的事件
print("\n[3] 测试不分组的事件...")
try:
    response = requests.get(f"{base_url}/api/events?limit=5&grouped=false")
    events_data = response.json()
    
    print(f"  总事件数: {events_data.get('total', 0)}")
    print(f"  是否分组: {events_data.get('grouped', False)}")
    
    if events_data.get('events'):
        for i, event in enumerate(events_data['events'][:3], 1):
            timestamp = event.get('timestamp')
            print(f"  事件 {i}:")
            print(f"    类型: {event.get('type')}")
            print(f"    时间戳: {timestamp}")
            
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    print(f"    ✅ 时间戳格式正确: {dt}")
                except Exception as e:
                    print(f"    ❌ 时间戳格式错误: {e}")
            else:
                print(f"    ❌ 时间戳为空")
    
    print(f"\n  ✅ 不分组事件测试完成")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\n前端访问地址: http://localhost:3050")
print("请在前端检查事件日志页面，确认时间戳显示正常")