#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试事件日志默认按会话归类

验证：事件日志默认按会话单位进行归类

作者: Agent OS Team
"""

import requests
import json
import time

base_url = "http://localhost:8001"

print("=" * 60)
print("测试事件日志默认按会话归类")
print("=" * 60)

# [1] 测试默认行为（应该按会话分组）
print("\n[1] 测试默认行为（不指定grouped参数）...")
try:
    response = requests.get(f"{base_url}/api/events?limit=20")
    events_data = response.json()
    
    print(f"  总事件数: {events_data.get('total', 0)}")
    print(f"  会话数: {events_data.get('session_count', 0)}")
    print(f"  是否分组: {events_data.get('grouped', False)}")
    
    if events_data.get('grouped'):
        print(f"\n  ✅ 默认按会话分组")
        print(f"\n  会话分组详情:")
        for i, session_group in enumerate(events_data.get('events', []), 1):
            print(f"    会话 {i}:")
            print(f"      会话ID: {session_group.get('session_id')}")
            print(f"      会话名称: {session_group.get('session_name')}")
            print(f"      事件数: {session_group.get('event_count', 0)}")
    else:
        print(f"\n  ❌ 默认未按会话分组")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")

# [2] 测试显式指定grouped=true
print("\n[2] 测试显式指定grouped=true...")
try:
    response = requests.get(f"{base_url}/api/events?limit=20&grouped=true")
    events_data = response.json()
    
    print(f"  总事件数: {events_data.get('total', 0)}")
    print(f"  会话数: {events_data.get('session_count', 0)}")
    print(f"  是否分组: {events_data.get('grouped', False)}")
    
    if events_data.get('grouped'):
        print(f"\n  ✅ 显式指定grouped=true正常工作")
    else:
        print(f"\n  ❌ 显式指定grouped=true失败")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")

# [3] 测试显式指定grouped=false
print("\n[3] 测试显式指定grouped=false...")
try:
    response = requests.get(f"{base_url}/api/events?limit=20&grouped=false")
    events_data = response.json()
    
    print(f"  总事件数: {events_data.get('total', 0)}")
    print(f"  会话数: {events_data.get('session_count', 0)}")
    print(f"  是否分组: {events_data.get('grouped', False)}")
    
    if not events_data.get('grouped'):
        print(f"\n  ✅ 显式指定grouped=false正常工作")
        print(f"\n  事件列表（未分组）:")
        for i, event in enumerate(events_data.get('events', [])[:5], 1):
            print(f"    事件 {i}: {event.get('type')} - {event.get('timestamp')}")
    else:
        print(f"\n  ❌ 显式指定grouped=false失败")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")

# [4] 测试按会话筛选
print("\n[4] 测试按会话筛选...")
try:
    # 先获取会话列表
    response = requests.get(f"{base_url}/api/sessions")
    sessions_data = response.json()
    
    if sessions_data.get('sessions'):
        first_session = sessions_data['sessions'][0]
        session_id = first_session.get('session_id')
        
        print(f"  使用会话ID: {session_id}")
        
        # 获取该会话的事件
        response = requests.get(f"{base_url}/api/events?session_id={session_id}&limit=10")
        events_data = response.json()
        
        print(f"  总事件数: {events_data.get('total', 0)}")
        print(f"  会话ID: {events_data.get('session_id')}")
        print(f"  是否分组: {events_data.get('grouped', False)}")
        
        print(f"\n  ✅ 按会话筛选正常工作")
    else:
        print(f"  ⚠️  没有可用的会话")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)