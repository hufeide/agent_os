#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终验证测试 - 确认所有修复都正常工作
"""

import requests
import time
import json

base_url = "http://localhost:8001"

print("=" * 60)
print("最终验证测试")
print("=" * 60)

# [1] 创建测试任务
print("\n[1] 创建测试任务...")
task_description = "研究量子计算的基本原理和当前发展状况"

response = requests.post(f"{base_url}/api/tasks", json={
    "description": task_description,
    "context": {}
})

print(f"  状态码: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"  ✅ 任务创建成功")
    dag_id = result.get("dag_id")
    session_id = result.get("session_id")
    print(f"  dag_id: {dag_id}")
    print(f"  session_id: {session_id}")
else:
    print(f"  ❌ 任务创建失败")
    print(f"  错误信息: {response.text}")
    exit(1)

# [2] 等待任务分解和执行
print("\n[2] 等待任务分解和执行...")
time.sleep(15)  # 给足够的时间让任务完成

# [3] 检查最终状态
print("\n[3] 检查最终状态...")
response = requests.get(f"{base_url}/api/tasks/{dag_id}")

if response.status_code == 200:
    task_status = response.json()
    
    print(f"\n  最终状态:")
    print(f"    是否完成: {task_status.get('is_completed')}")
    print(f"    总任务数: {task_status.get('total_tasks')}")
    print(f"    完成数: {task_status.get('completed_count')}")
    print(f"    失败数: {task_status.get('failed_count')}")
    
    # 验证每个任务
    tasks = task_status.get('tasks', [])
    print(f"\n  任务验证:")
    
    all_passed = True
    for i, task in enumerate(tasks, 1):
        print(f"\n  [{i}] {task.get('name')}")
        
        # 验证任务ID
        task_id = task.get('task_id')
        if task_id:
            print(f"    ✅ 任务ID: {task_id}")
        else:
            print(f"    ❌ 任务ID缺失")
            all_passed = False
        
        # 验证代理ID
        agent_id = task.get('agent_id')
        if agent_id:
            print(f"    ✅ 代理ID: {agent_id}")
        else:
            print(f"    ❌ 代理ID缺失")
            all_passed = False
        
        # 验证任务状态
        status = task.get('status')
        if status == 'completed':
            print(f"    ✅ 任务状态: {status}")
        else:
            print(f"    ⚠️  任务状态: {status}")
        
        # 验证结果
        result = task.get('result')
        if result:
            print(f"    ✅ 有结果")
            
            # 验证技能名称
            skill_name = result.get('method')
            if skill_name:
                print(f"    ✅ 技能名称: {skill_name}")
            else:
                print(f"    ❌ 技能名称缺失")
                all_passed = False
            
            # 验证研究结果
            if result.get('type') == 'research':
                print(f"    ✅ 研究类型")
                
                # 验证原始问题
                if result.get('original_question'):
                    print(f"    ✅ 原始问题: {result.get('original_question')[:50]}...")
                else:
                    print(f"    ❌ 原始问题缺失")
                    all_passed = False
                
                # 验证直接回答
                if result.get('answer_to_original_question'):
                    print(f"    ✅ 直接回答: {result.get('answer_to_original_question')[:50]}...")
                else:
                    print(f"    ❌ 直接回答缺失")
                    all_passed = False
                
                # 验证研究发现
                if result.get('findings'):
                    print(f"    ✅ 研究发现: {len(result.get('findings'))} 项")
                else:
                    print(f"    ❌ 研究发现缺失")
                    all_passed = False
                
                # 验证关键点
                if result.get('key_points'):
                    print(f"    ✅ 关键点: {len(result.get('key_points'))} 项")
                else:
                    print(f"    ❌ 关键点缺失")
                    all_passed = False
                
                # 验证数据来源
                if result.get('data_sources'):
                    print(f"    ✅ 数据来源: {len(result.get('data_sources'))} 项")
                else:
                    print(f"    ❌ 数据来源缺失")
                    all_passed = False
                
                # 验证执行步骤
                if result.get('steps'):
                    print(f"    ✅ 执行步骤: {len(result.get('steps'))} 步")
                else:
                    print(f"    ❌ 执行步骤缺失")
                    all_passed = False
        else:
            print(f"    ❌ 结果缺失")
            all_passed = False
    
    # 总结
    print(f"\n  {'='*60}")
    if all_passed:
        print(f"  ✅ 所有验证通过！任务执行完全正常。")
    else:
        print(f"  ⚠️  部分验证失败，需要进一步检查。")
    print(f"  {'='*60}")

else:
    print(f"  ❌ 获取任务状态失败")
    print(f"  错误信息: {response.text}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)