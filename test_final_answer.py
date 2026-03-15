#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试任务并验证最终回答功能

作者: Agent OS Team
"""

import requests
import json
import time

base_url = "http://localhost:8001"

print("=" * 60)
print("创建测试任务并验证最终回答功能")
print("=" * 60)

# 创建一个测试任务
print("\n创建测试任务...")
task_data = {
    "description": "分析爱情诗歌的主题特点",
    "context": {"original_question": "爱情诗歌通常表达哪些主题？"}
}

try:
    response = requests.post(f"{base_url}/api/tasks", json=task_data)
    print(f"状态码: {response.status_code}")
    result = response.json()
    dag_id = result.get('dag_id')
    print(f"DAG ID: {dag_id}")
    
    # 等待任务完成
    print("\n等待任务完成...")
    max_attempts = 60
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{base_url}/api/tasks/{dag_id}")
            status = response.json()
            
            is_completed = status.get('is_completed', False)
            total_tasks = status.get('total_tasks', 0)
            
            if attempt % 5 == 0:  # 每10秒打印一次
                print(f"  进度: 总任务数={total_tasks}, 是否完成={is_completed}")
            
            if is_completed and total_tasks > 0:
                print(f"\n✓ 任务已完成！(耗时: {attempt*2}秒)")
                break
            
            attempt += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"✗ 获取任务状态失败: {e}")
            break
    
    if attempt >= max_attempts:
        print(f"✗ 任务执行超时")
    else:
        # 检查任务列表中的最终回答
        print("\n" + "=" * 60)
        print("检查任务列表中的最终回答")
        print("=" * 60)
        
        response = requests.get(f"{base_url}/api/tasks")
        tasks_data = response.json()
        
        found_task = None
        for task in tasks_data.get('tasks', []):
            if task.get('dag_id') == dag_id:
                found_task = task
                break
        
        if found_task:
            print(f"\n任务: {found_task.get('name')}")
            print(f"描述: {found_task.get('description')[:50]}...")
            
            # 检查最新结果
            if found_task.get('latest_result'):
                latest = found_task['latest_result']
                print(f"\n最新结果:")
                print(f"  摘要: {latest.get('summary', 'N/A')[:100]}...")
                print(f"  方法: {latest.get('method', 'N/A')}")
                print(f"  类型: {latest.get('type', 'N/A')}")
                
                # 检查最终回答字段
                if found_task.get('final_answer'):
                    final_answer = found_task['final_answer']
                    print(f"\n✅ 最终回答字段:")
                    print(f"  问题: {final_answer.get('question', 'N/A')}")
                    print(f"  回答: {final_answer.get('answer', 'N/A')[:200]}...")
                    print(f"  摘要: {final_answer.get('summary', 'N/A')[:100]}...")
                    print(f"  方法: {final_answer.get('method', 'N/A')}")
                else:
                    print(f"\n❌ 缺少final_answer字段")
                
                # 检查综合最终回答
                if found_task.get('combined_final_answer'):
                    combined = found_task['combined_final_answer']
                    print(f"\n✅ 综合最终回答:")
                    print(f"  问题: {combined.get('question', 'N/A')}")
                    print(f"  回答: {combined.get('answer', 'N/A')[:200]}...")
                    print(f"  摘要: {combined.get('summary', 'N/A')[:100]}...")
                    print(f"  任务数: {combined.get('task_count', 0)}")
                else:
                    print(f"\n❌ 缺少combined_final_answer字段")
            
            # 检查完成结果列表
            if found_task.get('completed_results'):
                print(f"\n完成结果列表 (共{len(found_task['completed_results'])}个):")
                for i, result in enumerate(found_task['completed_results'], 1):
                    result_data = result.get('result', {})
                    print(f"\n  结果 {i}: {result.get('task_name')}")
                    
                    if result.get('final_answer'):
                        print(f"    ✅ 最终回答: {result['final_answer'][:100]}...")
                    else:
                        if result_data.get('answer_to_original_question'):
                            print(f"    ✅ 直接回答: {result_data['answer_to_original_question'][:100]}...")
                        else:
                            print(f"    ❌ 缺少最终回答")
        
        # 检查会话列表中的最终回答
        print(f"\n{'='*60}")
        print("检查会话列表中的最终回答")
        print("=" * 60)
        
        response = requests.get(f"{base_url}/api/sessions")
        sessions_data = response.json()
        
        found_session = None
        for session in sessions_data.get('sessions', []):
            if session.get('latest_task') and found_task and found_task.get('name') in session.get('latest_task', ''):
                found_session = session
                break
        
        if found_session:
            print(f"\n会话ID: {found_session.get('session_id')}")
            print(f"任务数: {found_session.get('task_count')}")
            print(f"最新任务: {found_session.get('latest_task')}")
            
            # 检查最新最终回答
            if found_session.get('latest_final_answer'):
                final_answer = found_session['latest_final_answer']
                print(f"\n✅ 最新最终回答:")
                print(f"  问题: {final_answer.get('question', 'N/A')}")
                print(f"  回答: {final_answer.get('answer', 'N/A')[:200]}...")
                print(f"  摘要: {final_answer.get('summary', 'N/A')[:100]}...")
                print(f"  方法: {final_answer.get('method', 'N/A')}")
            else:
                print(f"\n❌ 会话列表缺少latest_final_answer字段")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)