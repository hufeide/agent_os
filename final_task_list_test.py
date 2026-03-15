#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证任务列表的最终结果显示
"""

import requests
import time
import json

base_url = "http://localhost:8001"

print("=" * 60)
print("最终验证任务列表的最终结果显示")
print("=" * 60)

# [1] 创建测试任务
print("\n[1] 创建测试任务...")
task_description = "研究机器学习的主要算法和应用领域"

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
time.sleep(30)

# [3] 获取任务列表
print("\n[3] 获取任务列表...")
response = requests.get(f"{base_url}/api/tasks")

if response.status_code == 200:
    tasks_data = response.json()
    print(f"\n  任务列表概览:")
    print(f"    总任务数: {tasks_data.get('total_count')}")
    
    # 查找刚创建的任务
    tasks = tasks_data.get('tasks', [])
    our_task = None
    for task in tasks:
        if task.get('dag_id') == dag_id:
            our_task = task
            break
    
    if our_task:
        print(f"\n  任务基本信息:")
        print(f"    名称: {our_task.get('name')}")
        print(f"    描述: {our_task.get('description')}")
        print(f"    总任务数: {our_task.get('total_tasks')}")
        print(f"    完成数: {our_task.get('completed_count')}")
        print(f"    是否完成: {our_task.get('is_completed')}")
        
        # 验证最终结果显示
        print(f"\n  最终结果验证:")
        
        # 1. 检查最终回答
        if our_task.get('final_answer'):
            print(f"  ✅ 有最终回答字段")
            final_answer = our_task.get('final_answer')
            print(f"      问题: {final_answer.get('question', '')[:50]}...")
            print(f"      回答: {final_answer.get('answer', '')[:100]}...")
            print(f"      方法: {final_answer.get('method')}")
        else:
            print(f"  ❌ 缺少最终回答字段")
        
        # 2. 检查最新结果
        if our_task.get('latest_result'):
            print(f"  ✅ 有最新结果字段")
            latest_result = our_task.get('latest_result')
            print(f"      方法: {latest_result.get('method')}")
            print(f"      类型: {latest_result.get('type')}")
            if latest_result.get('answer_to_original_question'):
                print(f"      有直接回答: 是")
        else:
            print(f"  ❌ 缺少最新结果字段")
        
        # 3. 检查完成结果列表
        if our_task.get('completed_results'):
            completed_results = our_task.get('completed_results')
            print(f"  ✅ 有完成结果列表 ({len(completed_results)} 个)")
            for i, result in enumerate(completed_results[:2], 1):
                print(f"      [{i}] {result.get('task_name')}")
                if result.get('final_answer'):
                    print(f"          有最终回答: 是")
                if result.get('result', {}).get('findings'):
                    print(f"          有研究发现: 是")
        else:
            print(f"  ❌ 缺少完成结果列表字段")
        
        # 4. 检查综合回答
        if our_task.get('combined_final_answer'):
            print(f"  ✅ 有综合回答字段")
            combined = our_task.get('combined_final_answer')
            print(f"      任务数: {combined.get('task_count')}")
            print(f"      回答长度: {len(combined.get('answer', ''))} 字符")
        else:
            print(f"  ❌ 缺少综合回答字段")
        
        # 5. 总结
        print(f"\n  总结:")
        has_final_answer = bool(our_task.get('final_answer'))
        has_latest_result = bool(our_task.get('latest_result'))
        has_completed_results = bool(our_task.get('completed_results'))
        has_combined_answer = bool(our_task.get('combined_final_answer'))
        
        if has_final_answer and has_latest_result and has_completed_results and has_combined_answer:
            print(f"  ✅ 所有最终结果字段都存在")
            print(f"  ✅ 任务列表API返回完整的结果数据")
            print(f"  ✅ 前端可以正确显示最终结果")
        else:
            print(f"  ⚠️  部分字段缺失")
            print(f"      final_answer: {has_final_answer}")
            print(f"      latest_result: {has_latest_result}")
            print(f"      completed_results: {has_completed_results}")
            print(f"      combined_final_answer: {has_combined_answer}")
    else:
        print(f"  ❌ 未找到刚创建的任务")
else:
    print(f"  ❌ 获取任务列表失败: {response.status_code}")
    print(f"  错误信息: {response.text}")

print("\n" + "=" * 60)
print("验证完成！")
print("=" * 60)
print("\n前端显示说明:")
print("1. 任务列表页面会显示每个任务的最终回答（蓝色背景框）")
print("2. 点击'查看详情'可以看到详细的结果信息")
print("3. 详情页面包含:")
print("   - 最终回答（绿色背景框）")
print("   - 最新结果（如果没有综合回答）")
print("   - 完成任务详情（所有子任务的结果）")
print("   - 综合最终回答（整合所有任务的回答）")
print("=" * 60)