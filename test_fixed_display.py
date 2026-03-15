#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的结果展示

验证修复后的结果展示功能是否正常工作。

作者: Agent OS Team
"""

import requests
import json
import time

base_url = "http://localhost:8001"

print("=" * 60)
print("测试修复后的结果展示功能")
print("=" * 60)

# [1] 创建测试任务
print("\n[1] 创建测试任务...")
task_description = {
    "name": "测试结果展示",
    "description": "测试修复后的结果展示功能",
    "context": {
        "test": True
    }
}

try:
    response = requests.post(
        f"{base_url}/api/tasks",
        json=task_description
    )
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"DAG ID: {result.get('dag_id')}")
    
    dag_id = result.get('dag_id')
except Exception as e:
    print(f"✗ 创建任务失败: {e}")
    exit(1)

# [2] 等待任务执行
print("\n[2] 等待任务执行...")
max_attempts = 60
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

# [3] 获取详细任务状态
print("\n[3] 获取详细任务状态...")
try:
    response = requests.get(f"{base_url}/api/tasks/{dag_id}")
    detailed_status = response.json()
    
    print(f"\n任务概览:")
    print(f"  DAG ID: {detailed_status.get('dag_id')}")
    print(f"  名称: {detailed_status.get('name')}")
    print(f"  描述: {detailed_status.get('description')}")
    print(f"  总任务数: {detailed_status.get('total_tasks')}")
    print(f"  状态统计: {detailed_status.get('status_counts')}")
    print(f"  是否完成: {detailed_status.get('is_completed')}")
    
    # 显示详细任务信息
    if detailed_status.get('tasks'):
        print(f"\n详细任务信息:")
        for i, task in enumerate(detailed_status['tasks'], 1):
            print(f"\n  [{i}] {task.get('name')}")
            print(f"      ID: {task.get('task_id')}")
            print(f"      描述: {task.get('description')}")
            print(f"      状态: {task.get('status')}")
            print(f"      优先级: {task.get('priority')}")
            print(f"      角色: {task.get('agent_role')}")
            print(f"      Agent: {task.get('agent_id')}")
            
            # 显示执行结果
            if task.get('result'):
                result = task['result']
                print(f"\n      执行结果:")
                print(f"        执行方法: {result.get('method')}")
                print(f"        执行类型: {result.get('type', '通用')}")
                print(f"        完成时间: {result.get('completed_at')}")
                
                if result.get('steps'):
                    print(f"        执行步骤 ({result.get('step_count', 0)}步):")
                    for step in result['steps']:
                        if isinstance(step, dict):
                            print(f"          - 步骤{step.get('step')}: {step.get('action')} ({step.get('status')})")
                        else:
                            print(f"          - {step}")
                
                if result.get('findings'):
                    print(f"        发现: {result.get('findings')}")
                
                if result.get('topic'):
                    print(f"        研究主题: {result.get('topic')}")
                
                if result.get('data_points'):
                    print(f"        数据点数: {result.get('data_points')}")
                
                if result.get('confidence'):
                    print(f"        置信度: {result.get('confidence')}")
                
                print(f"        摘要: {result.get('summary')}")
            else:
                print(f"\n      执行结果: 无")
            
            # 显示错误信息
            if task.get('error'):
                print(f"      错误: {task.get('error')}")

except Exception as e:
    print(f"✗ 获取详细状态失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)