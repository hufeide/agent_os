#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM驱动的技能执行 - 最终验证

验证技能能够真正调用LLM并返回实际的研究结果。

作者: Agent OS Team
"""

import requests
import json
import time

base_url = "http://localhost:8001"

print("=" * 60)
print("测试LLM驱动的技能执行 - 最终验证")
print("=" * 60)

# [1] 创建测试任务 - 爱情诗歌研究
print("\n[1] 创建爱情诗歌研究任务...")
task_description = {
    "name": "经典爱情诗歌深度研究",
    "description": "深入研究经典爱情诗歌，包括中国古代诗歌、西方经典爱情诗、现代爱情诗等，分析其意象、表达方式和情感特征"
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
max_attempts = 120  # 增加等待时间，因为LLM调用需要更长时间
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
        all_have_real_results = True
        
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
                
                # 检查是否有真正的LLM结果
                has_real_result = False
                
                if result.get('findings'):
                    findings = result['findings']
                    print(f"      研究发现: {findings[:300]}...")
                    # 检查是否是真正的LLM结果（长度大于100且不是占位符）
                    if len(findings) > 100 and '研究已完成' not in findings and '分析已完成' not in findings and '文档已完成' not in findings:
                        has_real_result = True
                        print(f"      ✓ 有真正的LLM研究结果")
                    else:
                        print(f"      ✗ 结果不是真正的LLM输出")
                        all_have_real_results = False
                
                if result.get('key_points'):
                    key_points = result['key_points']
                    print(f"      关键点数量: {len(key_points)}")
                    if len(key_points) > 0:
                        print(f"      ✓ 有关键点: {key_points[0][:100]}...")
                        has_real_result = True
                
                if result.get('data_sources'):
                    data_sources = result['data_sources']
                    print(f"      数据源数量: {len(data_sources)}")
                    if len(data_sources) > 0:
                        print(f"      ✓ 有数据源: {data_sources[0][:100]}...")
                        has_real_result = True
                
                if result.get('insights'):
                    insights = result['insights']
                    print(f"      分析洞察: {insights[:300]}...")
                    if len(insights) > 100 and '分析已完成' not in insights:
                        has_real_result = True
                        print(f"      ✓ 有真正的LLM分析结果")
                    else:
                        print(f"      ✗ 结果不是真正的LLM输出")
                        all_have_real_results = False
                
                if result.get('output'):
                    output = result['output']
                    print(f"      写作输出: {output[:300]}...")
                    if len(output) > 100 and '文档已完成' not in output:
                        has_real_result = True
                        print(f"      ✓ 有真正的LLM写作结果")
                    else:
                        print(f"      ✗ 结果不是真正的LLM输出")
                        all_have_real_results = False
                
                if result.get('steps'):
                    steps = result['steps']
                    print(f"      执行步骤数: {len(steps)}")
                    if len(steps) > 0:
                        print(f"      ✓ 有执行步骤")
                        has_real_result = True
                
                if not has_real_result:
                    print(f"      ✗ 任务没有真正的LLM执行结果")
                    all_have_real_results = False
            else:
                print(f"      ✗ 没有执行结果")
                all_have_real_results = False
        
        # 总结验证结果
        print(f"\n验证总结:")
        if all_have_real_results:
            print(f"  ✓ 所有任务都有真正的LLM执行结果")
            print(f"  ✓ 所有任务都调用了LLM并返回了实际内容")
            print(f"  ✓ 技能执行机制工作正常")
            print(f"  ✓ 每个agent都有明确的结论返回给主agent")
        else:
            print(f"  ✗ 部分任务缺少真正的LLM执行结果")
            print(f"  ✗ 部分任务可能没有调用LLM")
            print(f"  ✗ 需要检查技能执行逻辑")

except Exception as e:
    print(f"✗ 获取详细状态失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)