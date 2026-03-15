#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试改进的任务展示功能

测试任务和Agent执行结果的详细展示功能。

作者: Agent OS Team
"""

import requests
import json
import time

base_url = "http://localhost:8001"

print("=" * 60)
print("完整测试改进的任务展示功能")
print("=" * 60)

# [1] 创建测试任务
print("\n[1] 创建测试任务...")
task_description = {
    "name": "AI技术调研",
    "description": "调研最新的AI技术趋势，包括大语言模型、多模态AI、AI Agent等",
    "context": {
        "focus": "技术趋势",
        "timeframe": "2024-2025"
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
    print(f"  创建时间: {detailed_status.get('created_at')}")
    print(f"  完成时间: {detailed_status.get('completed_at')}")
    
    # 显示详细任务信息
    if detailed_status.get('tasks'):
        print(f"\n详细任务信息:")
        for i, task in enumerate(detailed_status['tasks'], 1):
            print(f"\n  [{i}] {task.get('name')}")
            print(f"      ID: {task.get('task_id')[:8]}...")
            print(f"      描述: {task.get('description')[:50]}...")
            print(f"      状态: {task.get('status')}")
            print(f"      优先级: {task.get('priority')}")
            print(f"      角色: {task.get('agent_role')}")
            print(f"      Agent: {task.get('agent_id')}")
            print(f"      创建时间: {task.get('created_at')}")
            print(f"      开始时间: {task.get('started_at')}")
            print(f"      完成时间: {task.get('completed_at')}")
            print(f"      重试次数: {task.get('retry_count')}/{task.get('max_retries')}")
            
            # 显示依赖关系
            if task.get('dependencies'):
                print(f"      依赖任务:")
                for dep in task['dependencies']:
                    print(f"        - {dep.get('name')} ({dep.get('task_id')[:8]}...)")
            
            # 显示执行结果
            if task.get('result'):
                result = task['result']
                print(f"      执行方法: {result.get('method')}")
                print(f"      执行类型: {result.get('type', '通用')}")
                print(f"      完成时间: {result.get('completed_at')}")
                
                if result.get('steps'):
                    print(f"      执行步骤 ({result.get('step_count', 0)}步):")
                    for step in result['steps']:
                        print(f"        - {step}")
                
                if result.get('output'):
                    print(f"      输出: {result.get('output')[:100]}...")
                
                if result.get('findings'):
                    print(f"      发现: {result.get('findings')[:100]}...")
                
                if result.get('metrics'):
                    print(f"      指标:")
                    for key, value in result['metrics'].items():
                        print(f"        {key}: {value}")
                
                # 特定技能的结果
                if result.get('type') == 'research':
                    print(f"      研究主题: {result.get('topic')}")
                    print(f"      数据点数: {result.get('data_points')}")
                    print(f"      置信度: {result.get('confidence')}")
                
                elif result.get('type') == 'analysis':
                    print(f"      分析指标: {result.get('metrics', {})}")
                
                elif result.get('type') == 'writing':
                    print(f"      字数: {result.get('word_count')}")
                    print(f"      可读性评分: {result.get('readability_score')}")
                
                print(f"      摘要: {result.get('summary')}")
            
            # 显示错误信息
            if task.get('error'):
                print(f"      错误: {task.get('error')}")

except Exception as e:
    print(f"✗ 获取详细状态失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# [4] 获取所有任务列表
print("\n[4] 获取所有任务列表...")
try:
    response = requests.get(f"{base_url}/api/tasks")
    tasks_list = response.json()
    
    print(f"总任务数: {tasks_list.get('total')}")
    print(f"\n任务列表:")
    for i, task in enumerate(tasks_list.get('tasks', []), 1):
        print(f"\n  [{i}] {task.get('name')}")
        print(f"      DAG ID: {task.get('dag_id')[:8]}...")
        print(f"      描述: {task.get('description')[:50]}...")
        print(f"      总任务数: {task.get('total_tasks')}")
        print(f"      创建时间: {task.get('created_at')}")
        print(f"      是否完成: {task.get('is_completed')}")
        print(f"      完成时间: {task.get('completed_at')}")
        
        # 显示任务统计
        if 'completed_count' in task:
            print(f"      完成数: {task.get('completed_count')}")
            print(f"      失败数: {task.get('failed_count')}")
            print(f"      待处理数: {task.get('pending_count')}")
        
        # 显示最新结果
        if task.get('latest_result'):
            latest = task['latest_result']
            print(f"      最新结果:")
            print(f"        方法: {latest.get('method')}")
            print(f"        类型: {latest.get('type', '通用')}")
            print(f"        摘要: {latest.get('summary')}")
            
            if latest.get('steps'):
                print(f"        步骤数: {latest.get('step_count', 0)}")
            
            if latest.get('metrics'):
                print(f"        指标: {list(latest.get('metrics', {}).keys())}")

except Exception as e:
    print(f"✗ 获取任务列表失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# [5] 获取Agent状态
print("\n[5] 获取Agent状态...")
try:
    response = requests.get(f"{base_url}/api/agents")
    agents_status = response.json()
    
    print(f"主Agent状态:")
    main_agent = agents_status.get('main_agent', {})
    print(f"  ID: {main_agent.get('agent_id')}")
    print(f"  状态: {main_agent.get('status')}")
    current_task = main_agent.get('current_task_id', '无')
    print(f"  当前任务: {current_task[:8] if current_task and current_task != '无' else '无'}...")
    
    print(f"\n子Agent数量: {len(agents_status.get('sub_agents', []))}")
    for agent in agents_status.get('sub_agents', []):
        print(f"\n  Agent: {agent.get('name')} ({agent.get('agent_id')})")
        print(f"    角色: {agent.get('role')}")
        print(f"    状态: {agent.get('status')}")
        current_task = agent.get('current_task_id', '无')
        print(f"    当前任务: {current_task[:8] if current_task and current_task != '无' else '无'}...")
        print(f"    能力: {', '.join(agent.get('capabilities', []))}")
    
    # 显示动态Agent统计
    if agents_status.get('dynamic_stats'):
        stats = agents_status['dynamic_stats']
        print(f"\n动态Agent统计:")
        print(f"  总Agent数: {stats.get('total_agents')}")
        print(f"  角色分布: {stats.get('role_counts', {})}")
        print(f"  Agent IDs: {[aid[:8]+'...' for aid in stats.get('agent_ids', [])]}")

except Exception as e:
    print(f"✗ 获取Agent状态失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("完整测试完成！")
print("=" * 60)