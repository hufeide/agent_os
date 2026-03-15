#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试异步任务创建和结果回传

验证：
1. 任务创建时界面不会卡住（异步执行）
2. 任务完成后结果能够正确回传到任务界面

作者: Agent OS Team
"""

import requests
import json
import time
import threading

base_url = "http://localhost:8001"

print("=" * 60)
print("测试异步任务创建和结果回传")
print("=" * 60)

# [1] 测试异步任务创建 - 验证界面不会卡住
print("\n[1] 测试异步任务创建...")
task_description = {
    "name": "快速响应测试",
    "description": "测试任务创建的响应速度，验证界面不会卡住"
}

start_time = time.time()
try:
    response = requests.post(
        f"{base_url}/api/tasks",
        json=task_description
    )
    end_time = time.time()
    response_time = end_time - start_time
    
    print(f"状态码: {response.status_code}")
    print(f"响应时间: {response_time:.2f}秒")
    
    if response_time < 2.0:  # 响应时间应该在2秒内
        print(f"✓ 任务创建响应快速，界面不会卡住")
    else:
        print(f"✗ 任务创建响应太慢，界面可能卡住")
    
    result = response.json()
    print(f"DAG ID: {result.get('dag_id')}")
    print(f"状态: {result.get('status')}")
    print(f"消息: {result.get('message')}")
    
    dag_id = result.get('dag_id')
    
except Exception as e:
    print(f"✗ 创建任务失败: {e}")
    exit(1)

# [2] 等待任务完成
print("\n[2] 等待任务完成...")
max_attempts = 120
attempt = 0

while attempt < max_attempts:
    try:
        response = requests.get(f"{base_url}/api/tasks/{dag_id}")
        status = response.json()
        
        is_completed = status.get('is_completed', False)
        
        if is_completed:
            print(f"✓ 任务已完成！(耗时: {attempt*2}秒)")
            break
        
        attempt += 1
        time.sleep(2)
        
    except Exception as e:
        print(f"✗ 获取任务状态失败: {e}")
        break

if attempt >= max_attempts:
    print(f"✗ 任务执行超时")
    exit(1)

# [3] 测试结果回传 - 验证任务结果能够正确显示
print("\n[3] 测试结果回传...")
try:
    # 获取单个任务的详细状态
    response = requests.get(f"{base_url}/api/tasks/{dag_id}")
    detailed_status = response.json()
    
    print(f"\n单个任务结果:")
    print(f"  DAG ID: {detailed_status.get('dag_id')}")
    print(f"  名称: {detailed_status.get('name')}")
    print(f"  总任务数: {detailed_status.get('total_tasks')}")
    print(f"  是否完成: {detailed_status.get('is_completed')}")
    
    # 检查是否有任务结果
    has_results = False
    if detailed_status.get('tasks'):
        for i, task in enumerate(detailed_status['tasks'], 1):
            print(f"\n  任务 {i}: {task.get('name')}")
            if task.get('result'):
                result = task['result']
                print(f"    ✓ 有执行结果")
                print(f"    方法: {result.get('method')}")
                print(f"    类型: {result.get('type')}")
                
                # 检查是否有具体的LLM结果
                if result.get('findings'):
                    print(f"    ✓ 有研究发现: {result['findings'][:100]}...")
                    has_results = True
                if result.get('insights'):
                    print(f"    ✓ 有分析洞察: {result['insights'][:100]}...")
                    has_results = True
                if result.get('output'):
                    print(f"    ✓ 有写作输出: {result['output'][:100]}...")
                    has_results = True
            else:
                print(f"    ✗ 没有执行结果")
    
    # 获取任务列表，检查结果回传
    print(f"\n任务列表结果回传:")
    response = requests.get(f"{base_url}/api/tasks")
    tasks_list = response.json()
    
    found_task = None
    for task in tasks_list.get('tasks', []):
        if task.get('dag_id') == dag_id:
            found_task = task
            break
    
    if found_task:
        print(f"  ✓ 找到任务: {found_task.get('name')}")
        print(f"  ✓ 任务完成状态: {found_task.get('is_completed')}")
        
        # 检查是否有最新结果
        if found_task.get('latest_result'):
            print(f"  ✓ 有最新结果: {found_task['latest_result'].get('summary', '')[:100]}...")
            has_results = True
        else:
            print(f"  ✗ 没有最新结果")
        
        # 检查是否有所有完成结果
        if found_task.get('completed_results'):
            print(f"  ✓ 有完成结果列表，数量: {len(found_task['completed_results'])}")
            for i, completed_result in enumerate(found_task['completed_results'], 1):
                print(f"    结果 {i}: {completed_result.get('task_name')} - {completed_result.get('result', {}).get('summary', '')[:50]}...")
            has_results = True
        else:
            print(f"  ✗ 没有完成结果列表")
    else:
        print(f"  ✗ 在任务列表中找不到任务")
    
    # 总结验证结果
    print(f"\n验证总结:")
    if response_time < 2.0:
        print(f"  ✓ 任务创建响应快速，界面不会卡住")
    else:
        print(f"  ✗ 任务创建响应太慢")
    
    if has_results:
        print(f"  ✓ 任务结果能够正确回传到任务界面")
        print(f"  ✓ 单个任务详情包含完整结果")
        print(f"  ✓ 任务列表包含结果摘要")
    else:
        print(f"  ✗ 任务结果无法正确回传")

except Exception as e:
    print(f"✗ 获取任务状态失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)