#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试界面改进功能

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
print("测试界面改进功能")
print("=" * 60)

# 创建一个测试会话
session_id = str(uuid.uuid4())
print(f"\n创建测试会话: {session_id}")

# [1] 测试日志按会话归类
print("\n[1] 测试日志按会话归类...")
try:
    # 创建几个任务来生成事件
    for i in range(3):
        task_data = {
            "description": f"测试任务{i+1} - 分析不同主题",
            "context": {"original_question": f"问题{i+1}：请分析相关主题"},
            "session_id": session_id
        }
        
        response = requests.post(f"{base_url}/api/tasks", json=task_data)
        print(f"  创建任务 {i+1}: {response.status_code}")
    
    # 等待任务完成
    print("  等待任务完成...")
    time.sleep(15)
    
    # 测试未分组的日志
    print("\n  测试未分组的日志:")
    response = requests.get(f"{base_url}/api/events?limit=20")
    events_data = response.json()
    print(f"    总事件数: {events_data.get('total', 0)}")
    print(f"    是否分组: {events_data.get('grouped', False)}")
    print(f"    事件数量: {len(events_data.get('events', []))}")
    
    # 测试按会话分组的日志
    print("\n  测试按会话分组的日志:")
    response = requests.get(f"{base_url}/api/events?limit=20&grouped=true")
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
            
            # 显示前几个事件
            events = session_group.get('events', [])
            for j, event in enumerate(events[:3], 1):
                print(f"        事件 {j}: {event.get('type')} - {event.get('timestamp')}")
        
        print(f"\n  ✅ 日志按会话归类功能正常")
    else:
        print(f"\n  ❌ 日志按会话归类功能失败")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# [2] 测试任务列表中的最终回答展示
print("\n[2] 测试任务列表中的最终回答展示...")
try:
    # 创建一个新任务
    task_data = {
        "description": "分析现代爱情诗歌的特点",
        "context": {"original_question": "现代爱情诗歌有什么特点？"},
        "session_id": session_id
    }
    
    response = requests.post(f"{base_url}/api/tasks", json=task_data)
    print(f"  创建任务: {response.status_code}")
    result = response.json()
    dag_id = result.get('dag_id')
    
    # 等待任务完成
    print("  等待任务完成...")
    max_attempts = 60
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{base_url}/api/tasks/{dag_id}")
            status = response.json()
            
            is_completed = status.get('is_completed', False)
            total_tasks = status.get('total_tasks', 0)
            
            if is_completed and total_tasks > 0:
                print(f"  ✓ 任务已完成！(耗时: {attempt*2}秒)")
                break
            
            attempt += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"  ✗ 获取任务状态失败: {e}")
            break
    
    if attempt >= max_attempts:
        print(f"  ✗ 任务执行超时")
    else:
        # 检查会话列表中的最终回答
        print("\n  检查会话列表中的最终回答:")
        response = requests.get(f"{base_url}/api/sessions")
        sessions_data = response.json()
        
        found_session = None
        for session in sessions_data.get('sessions', []):
            if session.get('session_id') == session_id:
                found_session = session
                break
        
        if found_session:
            print(f"    会话ID: {found_session.get('session_id')}")
            print(f"    任务数: {found_session.get('task_count')}")
            print(f"    最新任务: {found_session.get('latest_task')}")
            
            # 检查最新最终回答
            if found_session.get('latest_final_answer'):
                final_answer = found_session['latest_final_answer']
                print(f"\n    最新最终回答:")
                print(f"      问题: {final_answer.get('question', 'N/A')[:100]}...")
                print(f"      回答: {final_answer.get('answer', 'N/A')[:150]}...")
                print(f"      摘要: {final_answer.get('summary', 'N/A')[:100]}...")
                print(f"      方法: {final_answer.get('method', 'N/A')}")
                print(f"\n    ✅ 会话列表包含最终回答")
            else:
                print(f"\n    ❌ 会话列表缺少最终回答")
        
        # 检查任务列表中的最终回答
        print("\n  检查任务列表中的最终回答:")
        response = requests.get(f"{base_url}/api/sessions/{session_id}/tasks")
        session_tasks = response.json()
        
        for i, task in enumerate(session_tasks.get('tasks', []), 1):
            print(f"\n    任务 {i}: {task.get('name')}")
            print(f"      描述: {task.get('description')[:50]}...")
            print(f"      完成状态: {task.get('is_completed')}")
            
            # 检查最新结果中的最终回答
            if task.get('latest_result'):
                latest = task['latest_result']
                print(f"\n      最新结果:")
                print(f"        摘要: {latest.get('summary', 'N/A')[:100]}...")
                
                if task.get('final_answer'):
                    final_answer = task['final_answer']
                    print(f"\n      最终回答:")
                    print(f"        问题: {final_answer.get('question', 'N/A')[:80]}...")
                    print(f"        回答: {final_answer.get('answer', 'N/A')[:120]}...")
                    print(f"        摘要: {final_answer.get('summary', 'N/A')[:80]}...")
                    print(f"        方法: {final_answer.get('method', 'N/A')}")
                    print(f"\n      ✅ 任务包含最终回答字段")
                else:
                    print(f"\n      ❌ 任务缺少最终回答字段")
            
            # 检查综合最终回答
            if task.get('combined_final_answer'):
                combined = task['combined_final_answer']
                print(f"\n      综合最终回答:")
                print(f"        问题: {combined.get('question', 'N/A')[:80]}...")
                print(f"        回答: {combined.get('answer', 'N/A')[:120]}...")
                print(f"        摘要: {combined.get('summary', 'N/A')[:80]}...")
                print(f"        任务数: {combined.get('task_count', 0)}")
                print(f"\n      ✅ 任务包含综合最终回答")
            else:
                print(f"\n      ❌ 任务缺少综合最终回答")
            
            # 检查完成结果列表中的最终回答
            if task.get('completed_results'):
                print(f"\n      完成结果列表 (共{len(task['completed_results'])}个):")
                for j, completed_result in enumerate(task['completed_results'], 1):
                    result_data = completed_result.get('result', {})
                    print(f"        结果 {j}: {completed_result.get('task_name')}")
                    
                    if completed_result.get('final_answer'):
                        print(f"          最终回答: {completed_result['final_answer'][:80]}...")
                        print(f"          ✅ 包含最终回答")
                    else:
                        if result_data.get('answer_to_original_question'):
                            print(f"          最终回答: {result_data['answer_to_original_question'][:80]}...")
                            print(f"          ✅ 包含最终回答")
                        else:
                            print(f"          ❌ 缺少最终回答")

except Exception as e:
    print(f"  ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)