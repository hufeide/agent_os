#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务列表的最终结果显示
"""

import requests
import time
import json

base_url = "http://localhost:8001"

print("=" * 60)
print("测试任务列表的最终结果显示")
print("=" * 60)

# [1] 创建测试任务
print("\n[1] 创建测试任务...")
task_description = "分析区块链技术的发展趋势和应用场景"

response = requests.post(f"{base_url}/api/tasks", json={
    "description": task_description,
    "context": {}
})

if response.status_code == 200:
    result = response.json()
    dag_id = result.get("dag_id")
    print(f"  ✅ 任务创建成功")
    print(f"  dag_id: {dag_id}")
else:
    print(f"  ❌ 任务创建失败")
    exit(1)

# [2] 等待任务执行完成
print("\n[2] 等待任务执行完成...")
time.sleep(25)

# [3] 获取任务列表
print("\n[3] 获取任务列表...")
response = requests.get(f"{base_url}/api/tasks")

if response.status_code == 200:
    tasks_data = response.json()
    print(f"\n  任务列表概览:")
    print(f"    总任务数: {tasks_data.get('total_count')}")
    print(f"    返回任务数: {len(tasks_data.get('tasks', []))}")
    
    # 查找刚创建的任务
    tasks = tasks_data.get('tasks', [])
    our_task = None
    for task in tasks:
        if task.get('dag_id') == dag_id:
            our_task = task
            break
    
    if our_task:
        print(f"\n  找到刚创建的任务:")
        print(f"    dag_id: {our_task.get('dag_id')}")
        print(f"    名称: {our_task.get('name')}")
        print(f"    描述: {our_task.get('description')}")
        print(f"    总任务数: {our_task.get('total_tasks')}")
        print(f"    完成数: {our_task.get('completed_count')}")
        print(f"    失败数: {our_task.get('failed_count')}")
        print(f"    待处理数: {our_task.get('pending_count')}")
        print(f"    是否完成: {our_task.get('is_completed')}")
        
        # 检查最新结果
        if our_task.get('latest_result'):
            print(f"\n  最新结果:")
            latest_result = our_task.get('latest_result')
            print(f"    方法: {latest_result.get('method')}")
            print(f"    类型: {latest_result.get('type')}")
            print(f"    摘要: {latest_result.get('summary', '')[:100]}...")
            
            if latest_result.get('original_question'):
                print(f"    原始问题: {latest_result.get('original_question', '')[:50]}...")
            
            if latest_result.get('answer_to_original_question'):
                print(f"    最终回答: {latest_result.get('answer_to_original_question', '')[:100]}...")
        
        # 检查最终回答
        if our_task.get('final_answer'):
            print(f"\n  最终回答:")
            final_answer = our_task.get('final_answer')
            print(f"    问题: {final_answer.get('question', '')[:50]}...")
            print(f"    回答: {final_answer.get('answer', '')[:100]}...")
            print(f"    摘要: {final_answer.get('summary', '')[:100]}...")
            print(f"    方法: {final_answer.get('method')}")
        
        # 检查所有完成结果
        if our_task.get('completed_results'):
            print(f"\n  所有完成结果 ({len(our_task.get('completed_results'))} 个):")
            for i, completed_result in enumerate(our_task.get('completed_results'), 1):
                print(f"\n    [{i}] 任务: {completed_result.get('task_name')}")
                result = completed_result.get('result')
                print(f"        方法: {result.get('method')}")
                print(f"        类型: {result.get('type')}")
                
                if result.get('original_question'):
                    print(f"        原始问题: {result.get('original_question', '')[:50]}...")
                
                if result.get('answer_to_original_question'):
                    print(f"        最终回答: {result.get('answer_to_original_question', '')[:80]}...")
                
                if result.get('findings'):
                    findings = result.get('findings')
                    if isinstance(findings, list):
                        print(f"        研究发现: {len(findings)} 项")
                    else:
                        print(f"        研究发现: {str(findings)[:80]}...")
                
                if completed_result.get('final_answer'):
                    print(f"        最终回答: {completed_result.get('final_answer', '')[:80]}...")
        
        # 检查综合最终回答
        if our_task.get('combined_final_answer'):
            print(f"\n  综合最终回答:")
            combined = our_task.get('combined_final_answer')
            print(f"    问题: {combined.get('question', '')[:50]}...")
            print(f"    回答: {combined.get('answer', '')[:150]}...")
            print(f"    摘要: {combined.get('summary', '')[:100]}...")
            print(f"    任务数: {combined.get('task_count')}")
        
        # 验证结果完整性
        print(f"\n  验证结果完整性:")
        has_latest_result = bool(our_task.get('latest_result'))
        has_final_answer = bool(our_task.get('final_answer'))
        has_completed_results = bool(our_task.get('completed_results'))
        has_combined_answer = bool(our_task.get('combined_final_answer'))
        
        print(f"    有最新结果: {has_latest_result}")
        print(f"    有最终回答: {has_final_answer}")
        print(f"    有完成结果列表: {has_completed_results}")
        print(f"    有综合回答: {has_combined_answer}")
        
        if has_latest_result and has_final_answer and has_completed_results:
            print(f"\n  ✅ 任务列表显示完整的最终结果")
        else:
            print(f"\n  ❌ 任务列表缺少某些结果字段")
    else:
        print(f"\n  ❌ 未找到刚创建的任务")
else:
    print(f"  ❌ 获取任务列表失败: {response.status_code}")
    print(f"  错误信息: {response.text}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)