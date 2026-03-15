#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查任务列表中的结论展示

作者: Agent OS Team
"""

import requests
import json

base_url = "http://localhost:8001"

print("=" * 60)
print("检查任务列表中的结论展示")
print("=" * 60)

try:
    # 获取任务列表
    response = requests.get(f"{base_url}/api/tasks")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        tasks_data = response.json()
        print(f"\n总任务数: {tasks_data.get('total', 0)}")
        
        for i, task in enumerate(tasks_data.get('tasks', [])[:3], 1):  # 只显示前3个任务
            print(f"\n{'='*50}")
            print(f"任务 {i}:")
            print(f"  DAG ID: {task.get('dag_id')}")
            print(f"  名称: {task.get('name')}")
            print(f"  描述: {task.get('description')}")
            print(f"  总任务数: {task.get('total_tasks')}")
            print(f"  完成状态: {task.get('is_completed')}")
            
            # 检查最新结果
            if task.get('latest_result'):
                latest = task['latest_result']
                print(f"\n  最新结果:")
                print(f"    方法: {latest.get('method')}")
                print(f"    类型: {latest.get('type')}")
                print(f"    摘要: {latest.get('summary', 'N/A')[:200]}...")
                
                # 检查是否有原始问题和回答
                if latest.get('original_question'):
                    print(f"    原始问题: {latest.get('original_question')[:100]}...")
                else:
                    print(f"    原始问题: 未找到")
                
                if latest.get('answer_to_original_question'):
                    print(f"    直接回答: {latest.get('answer_to_original_question')[:200]}...")
                else:
                    print(f"    直接回答: 未找到")
            else:
                print(f"\n  最新结果: 未找到")
            
            # 检查完成结果列表
            if task.get('completed_results'):
                print(f"\n  完成结果列表 (共{len(task['completed_results'])}个):")
                for j, result in enumerate(task['completed_results'][:2], 1):  # 只显示前2个结果
                    print(f"    结果 {j}:")
                    print(f"      任务名称: {result.get('task_name')}")
                    result_data = result.get('result', {})
                    print(f"      原始问题: {result_data.get('original_question', 'N/A')[:80]}...")
                    print(f"      直接回答: {result_data.get('answer_to_original_question', 'N/A')[:80]}...")
                    print(f"      摘要: {result_data.get('summary', 'N/A')[:80]}...")
            else:
                print(f"\n  完成结果列表: 未找到")
        
        print(f"\n{'='*50}")
        print("\n问题分析:")
        
        # 检查是否有任务
        if not tasks_data.get('tasks'):
            print("  ❌ 没有找到任何任务")
        else:
            # 检查每个任务的结论展示
            has_conclusion_issues = False
            for task in tasks_data.get('tasks', []):
                if task.get('latest_result'):
                    latest = task['latest_result']
                    if not latest.get('answer_to_original_question'):
                        print(f"  ❌ 任务 {task.get('name')} 缺少直接回答")
                        has_conclusion_issues = True
                
                if task.get('completed_results'):
                    for result in task['completed_results']:
                        result_data = result.get('result', {})
                        if not result_data.get('answer_to_original_question'):
                            print(f"  ❌ 任务 {task.get('name')} 的子任务缺少直接回答")
                            has_conclusion_issues = True
            
            if not has_conclusion_issues:
                print("  ✅ 所有任务都包含直接回答")
            else:
                print("  ⚠️  部分任务缺少直接回答，需要检查format_task_result函数")
    
    else:
        print(f"错误: {response.text}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)