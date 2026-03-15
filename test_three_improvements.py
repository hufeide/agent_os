#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试三大改进功能

验证：
1. 技能结合原始问题回答
2. 界面中事件按照会话进行归类
3. 任务管理中展示任务和对应最终结论

作者: Agent OS Team
"""

import requests
import json
import time
import uuid

base_url = "http://localhost:8001"

print("=" * 60)
print("测试三大改进功能")
print("=" * 60)

# [1] 测试技能结合原始问题回答
print("\n[1] 测试技能结合原始问题回答...")
session_id = str(uuid.uuid4())
print(f"创建会话: {session_id}")

task_description = {
    "name": "爱情诗歌研究",
    "description": "明确诗歌要表达的爱情主题，如浪漫、承诺、失恋等",
    "context": {"original_question": "爱情诗歌通常表达哪些主题？"},
    "session_id": session_id
}

try:
    response = requests.post(
        f"{base_url}/api/tasks",
        json=task_description
    )
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"DAG ID: {result.get('dag_id')}")
    print(f"Session ID: {result.get('session_id')}")
    print(f"消息: {result.get('message')}")
    
    dag_id = result.get('dag_id')
    
    # 等待任务完成
    print("等待任务完成...")
    max_attempts = 120
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{base_url}/api/tasks/{dag_id}")
            status = response.json()
            
            is_completed = status.get('is_completed', False)
            total_tasks = status.get('total_tasks', 0)
            
            if is_completed and total_tasks > 0:
                print(f"✓ 任务已完成！(耗时: {attempt*2}秒)")
                break
            
            attempt += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"✗ 获取任务状态失败: {e}")
            break
    
    if attempt >= max_attempts:
        print(f"✗ 任务执行超时")
    else:
        # 检查是否结合原始问题回答
        print("\n检查技能是否结合原始问题回答:")
        response = requests.get(f"{base_url}/api/tasks/{dag_id}")
        detailed_status = response.json()
        
        has_answer_to_original = False
        if detailed_status.get('tasks'):
            for task in detailed_status['tasks']:
                if task.get('result'):
                    result_data = task['result']
                    print(f"\n任务: {task.get('name')}")
                    print(f"  原始问题: {result_data.get('original_question', 'N/A')}")
                    print(f"  直接回答: {result_data.get('answer_to_original_question', 'N/A')[:100]}...")
                    
                    if result_data.get('answer_to_original_question'):
                        has_answer_to_original = True
                        print(f"  ✓ 技能结合原始问题回答")
                    else:
                        print(f"  ✗ 技能没有结合原始问题回答")
        
        if has_answer_to_original:
            print(f"\n✓ 技能能够结合原始问题回答")
        else:
            print(f"\n✗ 技能无法结合原始问题回答")

except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# [2] 测试会话归类功能
print("\n[2] 测试会话归类功能...")
try:
    # 创建多个任务，使用相同的session_id
    for i in range(3):
        task_description = {
            "name": f"会话任务_{i+1}",
            "description": f"这是会话中的第{i+1}个任务",
            "session_id": session_id
        }
        
        response = requests.post(
            f"{base_url}/api/tasks",
            json=task_description
        )
        print(f"创建任务 {i+1}: {response.status_code}")
    
    # 等待任务完成
    print("等待所有任务完成...")
    time.sleep(10)
    
    # 获取会话列表
    response = requests.get(f"{base_url}/api/sessions")
    sessions = response.json()
    
    print(f"\n会话列表:")
    print(f"  总会话数: {sessions.get('total_count', 0)}")
    
    found_session = None
    for session in sessions.get('sessions', []):
        print(f"  会话ID: {session.get('session_id')}")
        print(f"    任务数: {session.get('task_count')}")
        print(f"    最新任务: {session.get('latest_task')}")
        
        if session.get('session_id') == session_id:
            found_session = session
    
    if found_session:
        print(f"\n✓ 找到会话: {session_id}")
        print(f"  任务数: {found_session.get('task_count')}")
        
        # 获取会话的任务列表
        response = requests.get(f"{base_url}/api/sessions/{session_id}/tasks")
        session_tasks = response.json()
        
        print(f"\n会话任务列表:")
        print(f"  总任务数: {session_tasks.get('total_tasks', 0)}")
        for task in session_tasks.get('tasks', []):
            print(f"    任务: {task.get('name')} - {task.get('description')}")
        
        print(f"\n✓ 会话归类功能正常工作")
    else:
        print(f"\n✗ 找不到会话: {session_id}")

except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# [3] 测试任务结论展示
print("\n[3] 测试任务结论展示...")
try:
    # 创建一个新任务来测试结论展示
    task_description = {
        "name": "结论测试任务",
        "description": "分析现代爱情诗歌的特点和表达方式",
        "context": {"original_question": "现代爱情诗歌有什么特点？"},
        "session_id": str(uuid.uuid4())
    }
    
    response = requests.post(
        f"{base_url}/api/tasks",
        json=task_description
    )
    result = response.json()
    dag_id = result.get('dag_id')
    
    print(f"创建任务: {dag_id}")
    
    # 等待任务完成
    print("等待任务完成...")
    max_attempts = 120
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{base_url}/api/tasks/{dag_id}")
            status = response.json()
            
            is_completed = status.get('is_completed', False)
            total_tasks = status.get('total_tasks', 0)
            
            if is_completed and total_tasks > 0:
                print(f"✓ 任务已完成！(耗时: {attempt*2}秒)")
                break
            
            attempt += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"✗ 获取任务状态失败: {e}")
            break
    
    if attempt >= max_attempts:
        print(f"✗ 任务执行超时")
    else:
        # 检查任务结论展示
        print("\n检查任务结论展示:")
        response = requests.get(f"{base_url}/api/tasks/{dag_id}")
        detailed_status = response.json()
        
        print(f"\n单个任务详情:")
        print(f"  DAG ID: {detailed_status.get('dag_id')}")
        print(f"  名称: {detailed_status.get('name')}")
        print(f"  描述: {detailed_status.get('description')}")
        print(f"  总任务数: {detailed_status.get('total_tasks')}")
        
        has_conclusion = False
        if detailed_status.get('tasks'):
            for task in detailed_status['tasks']:
                if task.get('result'):
                    result_data = task['result']
                    print(f"\n  任务: {task.get('name')}")
                    print(f"    原始问题: {result_data.get('original_question', 'N/A')}")
                    print(f"    最终结论: {result_data.get('answer_to_original_question', 'N/A')[:150]}...")
                    print(f"    详细发现: {result_data.get('findings', 'N/A')[:100]}...")
                    
                    if result_data.get('answer_to_original_question'):
                        has_conclusion = True
        
        # 检查任务列表中的结论展示
        print(f"\n任务列表中的结论展示:")
        response = requests.get(f"{base_url}/api/tasks")
        tasks_list = response.json()
        
        found_task = None
        for task in tasks_list.get('tasks', []):
            if task.get('dag_id') == dag_id:
                found_task = task
                break
        
        if found_task:
            print(f"  任务: {found_task.get('name')}")
            print(f"    最新结果: {found_task.get('latest_result', {}).get('summary', 'N/A')[:150]}...")
            
            if found_task.get('completed_results'):
                print(f"    完成结果数: {len(found_task['completed_results'])}")
                for i, completed_result in enumerate(found_task['completed_results'], 1):
                    print(f"      结果 {i}: {completed_result.get('result', {}).get('answer_to_original_question', 'N/A')[:100]}...")
        
        if has_conclusion:
            print(f"\n✓ 任务结论能够正确展示")
        else:
            print(f"\n✗ 任务结论无法正确展示")

except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)