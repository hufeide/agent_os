#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进的Agent执行逻辑

验证每个agent都能真正实施具体的action并返回明确结论。

作者: Agent OS Team
"""

import requests
import json
import time

base_url = "http://localhost:8001"

print("=" * 60)
print("测试改进的Agent执行逻辑")
print("=" * 60)

# [1] 创建测试任务
print("\n[1] 创建测试任务...")
task_description = {
    "name": "AI技术深度调研",
    "description": "深入研究2024-2025年人工智能技术的最新发展趋势，重点关注大语言模型、多模态AI、AI Agent等关键领域的技术突破和应用场景",
    "context": {
        "focus": "技术趋势",
        "timeframe": "2024-2025",
        "depth": "深度调研"
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
    
    # 验证每个任务都有明确的结论
    if detailed_status.get('tasks'):
        print(f"\n验证任务执行结果:")
        all_have_conclusions = True
        
        for i, task in enumerate(detailed_status['tasks'], 1):
            print(f"\n  [{i}] {task.get('name')}")
            print(f"      ID: {task.get('task_id')}")
            print(f"      状态: {task.get('status')}")
            print(f"      角色: {task.get('agent_role')}")
            
            # 检查执行结果
            if task.get('result'):
                result = task['result']
                print(f"      执行方法: {result.get('method')}")
                print(f"      执行类型: {result.get('type', '通用')}")
                
                # 检查是否有明确的结论
                has_conclusion = False
                
                if result.get('findings'):
                    findings = result['findings']
                    print(f"      发现/结论: {findings}")
                    if findings and 'unknown' not in findings.lower() and findings != '':
                        has_conclusion = True
                        print(f"      ✓ 有明确结论")
                    else:
                        print(f"      ✗ 结论不明确或为'unknown'")
                        all_have_conclusions = False
                
                if result.get('output'):
                    output = result['output']
                    print(f"      输出: {output[:100]}...")
                    if output and 'unknown' not in output.lower() and output != '':
                        has_conclusion = True
                        print(f"      ✓ 有明确输出")
                    else:
                        print(f"      ✗ 输出不明确或为'unknown'")
                        all_have_conclusions = False
                
                if result.get('topic'):
                    topic = result['topic']
                    print(f"      研究主题: {topic}")
                    if topic and 'unknown' not in topic.lower() and topic != '':
                        has_conclusion = True
                        print(f"      ✓ 主题明确")
                    else:
                        print(f"      ✗ 主题不明确或为'unknown'")
                        all_have_conclusions = False
                
                if result.get('steps'):
                    steps = result['steps']
                    print(f"      执行步骤数: {len(steps)}")
                    if len(steps) > 0:
                        print(f"      ✓ 有执行步骤")
                        # 检查步骤是否实际执行
                        actual_steps = 0
                        for step in steps:
                            if isinstance(step, dict):
                                if step.get('status') == 'completed':
                                    actual_steps += 1
                            elif isinstance(step, str) and step:
                                actual_steps += 1
                        
                        if actual_steps > 0:
                            print(f"      ✓ 实际执行了{actual_steps}个步骤")
                        else:
                            print(f"      ✗ 步骤没有实际执行")
                            all_have_conclusions = False
                    else:
                        print(f"      ✗ 没有执行步骤")
                        all_have_conclusions = False
                
                if not has_conclusion:
                    print(f"      ✗ 任务没有明确的结论或输出")
                    all_have_conclusions = False
            else:
                print(f"      ✗ 没有执行结果")
                all_have_conclusions = False
        
        # 总结验证结果
        print(f"\n验证总结:")
        if all_have_conclusions:
            print(f"  ✓ 所有任务都有明确的结论")
            print(f"  ✓ 所有任务都有实际的执行")
            print(f"  ✓ 所有任务都有具体的输出")
        else:
            print(f"  ✗ 部分任务缺少明确结论")
            print(f"  ✗ 部分任务没有实际执行")
            print(f"  ✗ 部分任务缺少具体输出")

except Exception as e:
    print(f"✗ 获取详细状态失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)