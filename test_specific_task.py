#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试具体任务的结果展示

测试具体任务的结果展示功能。

作者: Agent OS Team
"""

import requests
import json
import time

base_url = "http://localhost:8001"

# 使用用户提供的DAG ID
dag_id = "50aa9d73-41d5-43f9-aec2-0e490a383483"

print("=" * 60)
print("测试具体任务的结果展示")
print("=" * 60)

print(f"\n[1] 获取任务状态 (DAG ID: {dag_id})...")
try:
    response = requests.get(f"{base_url}/api/tasks/{dag_id}")
    status = response.json()
    
    print(f"\n任务概览:")
    print(f"  DAG ID: {status.get('dag_id')}")
    print(f"  名称: {status.get('name')}")
    print(f"  描述: {status.get('description')}")
    print(f"  总任务数: {status.get('total_tasks')}")
    print(f"  状态统计: {status.get('status_counts')}")
    print(f"  是否完成: {status.get('is_completed')}")
    
    # 显示详细任务信息
    if status.get('tasks'):
        print(f"\n详细任务信息:")
        for i, task in enumerate(status['tasks'], 1):
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
                        print(f"          - 步骤{step.get('step')}: {step.get('action')} ({step.get('status')})")
                
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
    print(f"✗ 获取任务状态失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)