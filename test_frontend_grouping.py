#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端事件分组数据获取

验证前端是否能正确获取和显示分组的事件数据

作者: Agent OS Team
"""

import requests
import json

base_url = "http://localhost:8001"

print("=" * 60)
print("测试前端事件分组数据获取")
print("=" * 60)

# [1] 测试分组数据获取
print("\n[1] 测试分组数据获取...")
try:
    response = requests.get(f"{base_url}/api/events?limit=20&grouped=true")
    data = response.json()
    
    print(f"  状态码: {response.status_code}")
    print(f"  总事件数: {data.get('total', 0)}")
    print(f"  会话数: {data.get('session_count', 0)}")
    print(f"  是否分组: {data.get('grouped', False)}")
    
    if data.get('grouped') and data.get('events'):
        print(f"\n  ✅ 数据已分组")
        
        # 检查每个会话的结构
        for i, session in enumerate(data['events'], 1):
            print(f"\n  会话 {i}:")
            print(f"    session_id: {session.get('session_id')}")
            print(f"    session_name: {session.get('session_name')}")
            print(f"    event_count: {session.get('event_count', 0)}")
            print(f"    有events字段: {'events' in session}")
            
            if 'events' in session:
                events = session['events']
                print(f"    events数组长度: {len(events)}")
                
                # 检查第一个事件的结构
                if events:
                    first_event = events[0]
                    print(f"    第一个事件:")
                    print(f"      id: {first_event.get('id')}")
                    print(f"      type: {first_event.get('type')}")
                    print(f"      timestamp: {first_event.get('timestamp')}")
                    print(f"      source: {first_event.get('source')}")
                    print(f"      有data字段: {'data' in first_event}")
    else:
        print(f"\n  ❌ 数据未分组")
        print(f"  events类型: {type(data.get('events'))}")
        if data.get('events'):
            print(f"  events长度: {len(data.get('events', []))}")
            if data.get('events'):
                print(f"  第一个元素类型: {type(data['events'][0])}")
                print(f"  第一个元素: {data['events'][0]}")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# [2] 测试不分组数据获取
print("\n[2] 测试不分组数据获取...")
try:
    response = requests.get(f"{base_url}/api/events?limit=10&grouped=false")
    data = response.json()
    
    print(f"  状态码: {response.status_code}")
    print(f"  总事件数: {data.get('total', 0)}")
    print(f"  是否分组: {data.get('grouped', False)}")
    
    if not data.get('grouped') and data.get('events'):
        print(f"\n  ✅ 数据未分组")
        print(f"  events类型: {type(data.get('events'))}")
        print(f"  events长度: {len(data.get('events', []))}")
        
        if data.get('events'):
            first_event = data['events'][0]
            print(f"  第一个事件:")
            print(f"    id: {first_event.get('id')}")
            print(f"    type: {first_event.get('type')}")
            print(f"    timestamp: {first_event.get('timestamp')}")
            print(f"    source: {first_event.get('source')}")
            print(f"    有session_id字段: {'session_id' in first_event}")
    else:
        print(f"\n  ❌ 数据格式不正确")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# [3] 测试默认行为（不指定grouped参数）
print("\n[3] 测试默认行为（不指定grouped参数）...")
try:
    response = requests.get(f"{base_url}/api/events?limit=10")
    data = response.json()
    
    print(f"  状态码: {response.status_code}")
    print(f"  总事件数: {data.get('total', 0)}")
    print(f"  是否分组: {data.get('grouped', False)}")
    
    if data.get('grouped'):
        print(f"\n  ✅ 默认行为是分组")
    else:
        print(f"\n  ❌ 默认行为不是分组")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# [4] 检查前端应该接收到的数据格式
print("\n[4] 检查前端应该接收到的数据格式...")
print("  前端期望的分组数据格式:")
print("  {")
print("    'total': 10,")
print("    'session_count': 2,")
print("    'grouped': true,")
print("    'events': [")
print("      {")
print("        'session_id': 'xxx',")
print("        'session_name': '会话 xxx',")
print("        'event_count': 5,")
print("        'events': [")
print("          {")
print("            'id': 'xxx',")
print("            'type': 'task_created',")
print("            'data': {...},")
print("            'source': 'scheduler',")
print("            'timestamp': '2026-03-16T02:02:45.993450'")
print("          }")
print("        ]")
print("      }")
print("    ]")
print("  }")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\n请检查前端控制台是否有错误信息")
print("前端访问地址: http://localhost:3050/events")