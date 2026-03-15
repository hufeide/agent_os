#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查单个任务的结论展示

作者: Agent OS Team
"""

import requests
import json
import time

base_url = "http://localhost:8001"

print("=" * 60)
print("快速检查单个任务的结论展示")
print("=" * 60)

# 创建一个简单的测试任务
print("\n创建测试任务...")
task_data = {
    "description": "分析爱情诗歌的主题特点"
}

try:
    response = requests.post(f"{base_url}/api/tasks", json=task_data)
    print(f"状态码: {response.status_code}")
    result = response.json()
    dag_id = result.get('dag_id')
    print(f"DAG ID: {dag_id}")
    
    # 等待任务完成
    print("\n等待任务完成...")
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{base_url}/api/tasks/{dag_id}")
            status = response.json()
            
            is_completed = status.get('is_completed', False)
            total_tasks = status.get('total_tasks', 0)
            
            print(f"  尝试 {attempt+1}/{max_attempts}: 总任务数={total_tasks}, 是否完成={is_completed}")
            
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
        # 检查单个任务的结论展示
        print("\n检查单个任务的结论展示:")
        response = requests.get(f"{base_url}/api/tasks/{dag_id}")
        detailed_status = response.json()
        
        print(f"\n任务基本信息:")
        print(f"  DAG ID: {detailed_status.get('dag_id')}")
        print(f"  名称: {detailed_status.get('name')}")
        print(f"  描述: {detailed_status.get('description')}")
        print(f"  总任务数: {detailed_status.get('total_tasks')}")
        
        # 检查每个子任务的结论
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
                    
                    # 检查直接回答
                    if result_data.get('answer_to_original_question'):
                        print(f"    ✅ 直接回答: {result_data['answer_to_original_question'][:150]}...")
                    else:
                        print(f"    ❌ 直接回答: 未找到")
                    
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
        
        print(f"\n{'='*50}")
        print("\n问题诊断:")
        
        # 检查format_task_result是否正确工作
        if detailed_status.get('tasks'):
            has_all_fields = True
            for task in detailed_status['tasks']:
                if task.get('result'):
                    result_data = task['result']
                    if not result_data.get('answer_to_original_question'):
                        print("  ❌ 子任务缺少answer_to_original_question字段")
                        has_all_fields = False
                    if not result_data.get('original_question'):
                        print("  ❌ 子任务缺少original_question字段")
                        has_all_fields = False
            
            if has_all_fields:
                print("  ✅ 所有子任务都包含完整的结论字段")
            else:
                print("  ⚠️  部分子任务缺少结论字段，需要检查format_task_result函数")
        
        # 检查任务列表中的结论
        print("\n检查任务列表中的结论:")
        response = requests.get(f"{base_url}/api/tasks")
        tasks_list = response.json()
        
        found_task = None
        for task in tasks_list.get('tasks', []):
            if task.get('dag_id') == dag_id:
                found_task = task
                break
        
        if found_task:
            print(f"\n  任务: {found_task.get('name')}")
            
            # 检查最新结果
            if found_task.get('latest_result'):
                latest = found_task['latest_result']
                print(f"\n  最新结果:")
                print(f"    摘要: {latest.get('summary', 'N/A')[:150]}...")
                
                if latest.get('answer_to_original_question'):
                    print(f"    ✅ 直接回答: {latest['answer_to_original_question'][:150]}...")
                else:
                    print(f"    ❌ 直接回答: 未找到")
                
                if latest.get('original_question'):
                    print(f"    ✅ 原始问题: {latest['original_question'][:100]}...")
                else:
                    print(f"    ❌ 原始问题: 未找到")
            else:
                print(f"\n  ❌ 最新结果: 未找到")
            
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
                    
                    if result_data.get('original_question'):
                        print(f"      ✅ 原始问题: {result_data['original_question'][:80]}...")
                    else:
                        print(f"      ❌ 原始问题: 未找到")
            else:
                print(f"\n  ❌ 完成结果列表: 未找到")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)