#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试界面改进功能

验证：
1. 界面上的日志需要根据对话进行归类
2. 界面上任务管理的任务列表中，需要展示最终完成的回答

作者: Agent OS Team
"""

import requests
import json
import time
import uuid

base_url = "http://localhost:8001"

print("=" * 60)
print("快速测试界面改进功能")
print("=" * 60)

# [1] 测试日志按会话归类
print("\n[1] 测试日志按会话归类...")
try:
    # 测试未分组的日志
    print("  测试未分组的日志:")
    response = requests.get(f"{base_url}/api/events?limit=10")
    events_data = response.json()
    print(f"    总事件数: {events_data.get('total', 0)}")
    print(f"    是否分组: {events_data.get('grouped', False)}")
    
    # 测试按会话分组的日志
    print("\n  测试按会话分组的日志:")
    response = requests.get(f"{base_url}/api/events?limit=10&grouped=true")
    grouped_events_data = response.json()
    print(f"    总事件数: {grouped_events_data.get('total', 0)}")
    print(f"    会话数: {grouped_events_data.get('session_count', 0)}")
    print(f"    是否分组: {grouped_events_data.get('grouped', False)}")
    
    if grouped_events_data.get('grouped'):
        print(f"\n  会话分组详情:")
        for i, session_group in enumerate(grouped_events_data.get('events', []), 1):
            print(f"    会话 {i}:")
            print(f"      会话ID: {session_group.get('session_id')}")
            print(f"      会话名称: {session_group.get('session_name')}")
            print(f"      事件数: {session_group.get('event_count', 0)}")
        
        print(f"\n  ✅ 日志按会话归类功能正常")
    else:
        print(f"\n  ❌ 日志按会话归类功能失败")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")

# [2] 测试任务列表中的最终回答展示
print("\n[2] 测试任务列表中的最终回答展示...")
try:
    # 获取所有任务
    response = requests.get(f"{base_url}/api/tasks")
    tasks_data = response.json()
    
    print(f"  总任务数: {tasks_data.get('total_count', 0)}")
    
    # 检查第一个有最终回答的任务
    found_final_answer = False
    for i, task in enumerate(tasks_data.get('tasks', []), 1):
        print(f"\n  任务 {i}: {task.get('name')}")
        
        # 检查最新结果
        if task.get('latest_result'):
            latest = task['latest_result']
            print(f"    最新结果摘要: {latest.get('summary', 'N/A')[:80]}...")
            
            # 检查最终回答字段
            if task.get('final_answer'):
                final_answer = task['final_answer']
                print(f"    ✅ 最终回答:")
                print(f"      问题: {final_answer.get('question', 'N/A')[:60]}...")
                print(f"      回答: {final_answer.get('answer', 'N/A')[:80]}...")
                found_final_answer = True
                break
            else:
                # 检查是否有直接回答
                if latest.get('answer_to_original_question'):
                    print(f"    ⚠️  有直接回答但缺少final_answer字段")
                    print(f"      直接回答: {latest.get('answer_to_original_question')[:80]}...")
                    found_final_answer = True
                    break
        
        # 检查综合最终回答
        if task.get('combined_final_answer'):
            combined = task['combined_final_answer']
            print(f"    ✅ 综合最终回答:")
            print(f"      问题: {combined.get('question', 'N/A')[:60]}...")
            print(f"      回答: {combined.get('answer', 'N/A')[:80]}...")
            print(f"      任务数: {combined.get('task_count', 0)}")
            found_final_answer = True
            break
    
    if found_final_answer:
        print(f"\n  ✅ 任务列表包含最终回答")
    else:
        print(f"\n  ⚠️  未找到包含最终回答的任务")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")

# [3] 测试会话列表中的最终回答
print("\n[3] 测试会话列表中的最终回答...")
try:
    response = requests.get(f"{base_url}/api/sessions")
    sessions_data = response.json()
    
    print(f"  总会话数: {sessions_data.get('total_count', 0)}")
    
    # 检查第一个有最终回答的会话
    found_session_answer = False
    for i, session in enumerate(sessions_data.get('sessions', []), 1):
        print(f"\n  会话 {i}:")
        print(f"    会话ID: {session.get('session_id')}")
        print(f"    任务数: {session.get('task_count')}")
        print(f"    最新任务: {session.get('latest_task')}")
        
        # 检查最新最终回答
        if session.get('latest_final_answer'):
            final_answer = session['latest_final_answer']
            print(f"    ✅ 最新最终回答:")
            print(f"      问题: {final_answer.get('question', 'N/A')[:60]}...")
            print(f"      回答: {final_answer.get('answer', 'N/A')[:80]}...")
            print(f"      摘要: {final_answer.get('summary', 'N/A')[:60]}...")
            found_session_answer = True
            break
    
    if found_session_answer:
        print(f"\n  ✅ 会话列表包含最终回答")
    else:
        print(f"\n  ⚠️  未找到包含最终回答的会话")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")

print("\n" + "=" * 60)
print("快速测试完成！")
print("=" * 60)