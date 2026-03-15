#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的任务结论展示

验证：
1. 任务管理中是否正确展示任务和对应最终结论
2. 是否包含原始问题和直接回答

作者: Agent OS Team
"""

import requests
import json
import time

base_url = "http://localhost:8001"

print("=" * 60)
print("测试修复后的任务结论展示")
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
        # 检查单个任务的结论展示
        print("\n" + "=" * 60)
        print("检查单个任务的结论展示")
        print("=" * 60)
        
        response = requests.get(f"{base_url}/api/tasks/{dag_id}")
        detailed_status = response.json()
        
        print(f"\n任务基本信息:")
        print(f"  DAG ID: {detailed_status.get('dag_id')}")
        print(f"  名称: {detailed_status.get('name')}")
        print(f"  描述: {detailed_status.get('description')}")
        print(f"  总任务数: {detailed_status.get('total_tasks')}")
        
        # 检查每个子任务的结论
        has_complete_conclusion = True
        if detailed_status.get('tasks'):
            for i, task in enumerate(detailed_status['tasks'], 1):
                print(f"\n{'='*50}")
                print(f"子任务 {i}: {task.get('name')}")
                print(f"  状态: {task.get('status')}")
                
                if task.get('result'):
                    result_data = task['result']
                    print(f"\n  结果信息:")
                    print(f"    方法: {result_data.get('method')}")
                    print(f"    类型: {result_data.get('type')}")
                    print(f"    摘要: {result_data.get('summary', 'N/A')[:150]}...")
                    
                    # 检查关键结论字段
                    print(f"\n  关键结论字段:")
                    
                    # 检查原始问题
                    if result_data.get('original_question'):
                        print(f"    ✅ 原始问题: {result_data['original_question'][:100]}...")
                    else:
                        print(f"    ❌ 原始问题: 未找到")
                        has_complete_conclusion = False
                    
                    # 检查直接回答
                    if result_data.get('answer_to_original_question'):
                        print(f"    ✅ 直接回答: {result_data['answer_to_original_question'][:150]}...")
                    else:
                        print(f"    ❌ 直接回答: 未找到")
                        has_complete_conclusion = False
                    
                    # 检查其他字段
                    if result_data.get('findings'):
                        print(f"    ✅ 研究发现: {result_data['findings'][:100]}...")
                    else:
                        print(f"    ❌ 研究发现: 未找到")
                    
                    if result_data.get('key_points'):
                        print(f"    ✅ 关键点: {len(result_data['key_points'])}个")
                    else:
                        print(f"    ❌ 关键点: 未找到")
                else:
                    print(f"\n  ❌ 结果: 未找到")
                    has_complete_conclusion = False
        
        # 检查任务列表中的结论
        print(f"\n{'='*60}")
        print("检查任务列表中的结论展示")
        print("=" * 60)
        
        response = requests.get(f"{base_url}/api/tasks")
        tasks_list = response.json()
        
        found_task = None
        for task in tasks_list.get('tasks', []):
            if task.get('dag_id') == dag_id:
                found_task = task
                break
        
        if found_task:
            print(f"\n任务列表中的任务:")
            print(f"  任务: {found_task.get('name')}")
            print(f"  描述: {found_task.get('description')[:100]}...")
            
            # 检查最新结果
            if found_task.get('latest_result'):
                latest = found_task['latest_result']
                print(f"\n  最新结果:")
                print(f"    摘要: {latest.get('summary', 'N/A')[:150]}...")
                
                if latest.get('answer_to_original_question'):
                    print(f"    ✅ 直接回答: {latest['answer_to_original_question'][:150]}...")
                else:
                    print(f"    ❌ 直接回答: 未找到")
                    has_complete_conclusion = False
                
                if latest.get('original_question'):
                    print(f"    ✅ 原始问题: {latest['original_question'][:100]}...")
                else:
                    print(f"    ❌ 原始问题: 未找到")
                    has_complete_conclusion = False
            else:
                print(f"\n  ❌ 最新结果: 未找到")
                has_complete_conclusion = False
            
            # 检查完成结果列表
            if found_task.get('completed_results'):
                print(f"\n  完成结果列表 (共{len(found_task['completed_results'])}个):")
                for i, result in enumerate(found_task['completed_results'], 1):
                    print(f"\n    结果 {i}: {result.get('task_name')}")
                    result_data = result.get('result', {})
                    
                    if result_data.get('answer_to_original_question'):
                        print(f"      ✅ 直接回答: {result_data['answer_to_original_question'][:100]}...")
                    else:
                        print(f"      ❌ 直接回答: 未找到")
                        has_complete_conclusion = False
                    
                    if result_data.get('original_question'):
                        print(f"      ✅ 原始问题: {result_data['original_question'][:80]}...")
                    else:
                        print(f"      ❌ 原始问题: 未找到")
                        has_complete_conclusion = False
            else:
                print(f"\n  ❌ 完成结果列表: 未找到")
                has_complete_conclusion = False
        
        # 总结验证结果
        print(f"\n{'='*60}")
        print("验证总结")
        print("=" * 60)
        
        if has_complete_conclusion:
            print("✅ 任务管理中任务和对应最终结论展示正确")
            print("✅ 包含原始问题和直接回答")
            print("✅ 单个任务详情和任务列表都正确显示")
        else:
            print("❌ 任务管理中任务和对应最终结论展示有问题")
            print("❌ 部分字段缺失，需要进一步检查")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)