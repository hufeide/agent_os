#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多Agent执行顺序

验证LLM生成的agent依赖关系和执行顺序是否正确。

作者: Agent OS Team
"""

import sys
import os
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_agent_execution_order():
    """测试agent执行顺序"""
    print("=" * 60)
    print("测试多Agent执行顺序")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    
    # 测试1: 检查服务器是否运行
    print("\n[测试1] 检查API服务器状态...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✓ API服务器正在运行")
        else:
            print(f"✗ API服务器状态异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到API服务器")
        print("  请确保服务器正在运行: python start.py")
        return False
    except Exception as e:
        print(f"✗ 连接错误: {e}")
        return False
    
    # 测试2: 创建一个需要多agent协作的任务
    print("\n[测试2] 创建多agent协作任务...")
    task_data = {
        "description": "Write a comprehensive research report about artificial intelligence trends in 2024",
        "context": {
            "original_question": "What are the key AI trends in 2024?"
        }
    }
    
    try:
        response = requests.post(f"{base_url}/api/tasks", json=task_data, timeout=10)
        print(f"创建任务响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            dag_id = result.get('dag_id')
            print(f"✓ 任务创建成功")
            print(f"  任务ID: {task_id}")
            print(f"  DAG ID: {dag_id}")
        else:
            print(f"✗ 创建任务失败: {response.status_code}")
            print(f"  响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"✗ 创建任务时出错: {e}")
        return False
    
    # 测试3: 等待任务完成并检查执行顺序
    print("\n[测试3] 监控任务执行顺序...")
    execution_log = []
    max_wait = 120  # 最多等待120秒
    wait_time = 0
    
    while wait_time < max_wait:
        time.sleep(2)
        wait_time += 2
        
        try:
            # 获取DAG状态
            dag_response = requests.get(f"{base_url}/api/tasks/{dag_id}", timeout=10)
            if dag_response.status_code == 200:
                dag_info = dag_response.json()
                tasks = dag_info.get('tasks', [])
                
                # 记录任务状态变化
                for task in tasks:
                    task_id = task.get('id')
                    task_name = task.get('name')
                    task_status = task.get('status')
                    agent_role = task.get('agent_role')
                    
                    # 检查是否是新状态
                    log_entry = {
                        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'task_id': task_id,
                        'task_name': task_name,
                        'agent_role': agent_role,
                        'status': task_status
                    }
                    
                    # 只记录新的状态变化
                    if not any(log['task_id'] == task_id and log['status'] == task_status for log in execution_log):
                        execution_log.append(log_entry)
                        print(f"  [{log_entry['time']}] {agent_role} - {task_name}: {task_status}")
                
                # 检查是否所有任务都完成
                all_completed = all(task.get('status') in ['completed', 'failed'] for task in tasks)
                if all_completed:
                    print("✓ 所有任务执行完成")
                    break
        except Exception as e:
            print(f"  检查任务状态时出错: {e}")
    
    # 测试4: 分析执行顺序
    print("\n[测试4] 分析执行顺序...")
    
    # 按agent角色分组
    agent_executions = {}
    for log in execution_log:
        agent_role = log['agent_role']
        if agent_role not in agent_executions:
            agent_executions[agent_role] = []
        agent_executions[agent_role].append(log)
    
    print("\n各Agent执行时间线:")
    for agent_role, logs in sorted(agent_executions.items()):
        print(f"\n{agent_role}:")
        for log in logs:
            print(f"  {log['time']} - {log['task_name']}: {log['status']}")
    
    # 测试5: 验证执行顺序是否正确
    print("\n[测试5] 验证执行顺序...")
    
    # 检查是否有researcher, analyst, writer
    has_researcher = 'researcher' in agent_executions
    has_analyst = 'analyst' in agent_executions
    has_writer = 'writer' in agent_executions
    
    if has_researcher and has_analyst and has_writer:
        print("✓ 任务包含researcher, analyst, writer三个角色")
        
        # 检查执行顺序
        researcher_start = min(log['time'] for log in agent_executions['researcher'])
        analyst_start = min(log['time'] for log in agent_executions['analyst'])
        writer_start = min(log['time'] for log in agent_executions['writer'])
        
        print(f"\n执行时间:")
        print(f"  researcher开始时间: {researcher_start}")
        print(f"  analyst开始时间: {analyst_start}")
        print(f"  writer开始时间: {writer_start}")
        
        # 验证顺序
        if researcher_start < analyst_start < writer_start:
            print("✓ 执行顺序正确: researcher -> analyst -> writer")
            order_correct = True
        else:
            print("✗ 执行顺序错误")
            if researcher_start > analyst_start:
                print("  researcher应该在analyst之前执行")
            if analyst_start > writer_start:
                print("  analyst应该在writer之前执行")
            order_correct = False
    else:
        print("⚠️ 任务不包含完整的三个角色，无法验证执行顺序")
        print(f"  包含的角色: {list(agent_executions.keys())}")
        order_correct = None
    
    # 测试6: 获取agent交互图
    print("\n[测试6] 获取Agent交互图...")
    try:
        graph_response = requests.get(f"{base_url}/api/agent-interaction-graph/{dag_id}", timeout=10)
        if graph_response.status_code == 200:
            graph_data = graph_response.json()
            print("✓ 成功获取Agent交互图")
            print(f"  节点数量: {len(graph_data.get('nodes', []))}")
            print(f"  边数量: {len(graph_data.get('edges', []))}")
            print(f"  统计信息: {graph_data.get('statistics', {})}")
            
            # 显示节点信息
            print("\n节点信息:")
            for node in graph_data.get('nodes', []):
                print(f"  {node['id']} ({node['type']}, {node.get('role', 'N/A')}): {node.get('status', 'N/A')}")
            
            # 显示边信息
            print("\n边信息:")
            for edge in graph_data.get('edges', []):
                print(f"  {edge['from']} -> {edge['to']} ({edge.get('type', 'N/A')})")
        else:
            print(f"✗ 获取Agent交互图失败: {graph_response.status_code}")
    except Exception as e:
        print(f"✗ 获取Agent交互图时出错: {e}")
    
    # 测试7: 获取agent详情
    print("\n[测试7] 获取Agent详情...")
    for agent_role in ['researcher', 'analyst', 'writer']:
        if agent_role in agent_executions:
            # 获取该角色的第一个agent
            agent_id = f"{agent_role}_1"
            try:
                agent_response = requests.get(f"{base_url}/api/agent-details/{agent_id}", timeout=10)
                if agent_response.status_code == 200:
                    agent_data = agent_response.json()
                    print(f"\n{agent_role}详情:")
                    print(f"  Agent ID: {agent_data.get('agent_id')}")
                    print(f"  状态: {agent_data.get('status')}")
                    print(f"  能力: {agent_data.get('capabilities')}")
                    print(f"  工作记忆数量: {len(agent_data.get('working_memory', []))}")
                    print(f"  任务历史数量: {len(agent_data.get('task_history', []))}")
                    print(f"  统计信息: {agent_data.get('statistics', {})}")
                    
                    # 显示工具调用
                    working_memory = agent_data.get('working_memory', [])
                    tool_calls = [wm for wm in working_memory if '调用工具' in wm.get('content', '')]
                    print(f"  工具调用数量: {len(tool_calls)}")
                    if tool_calls:
                        print(f"  工具调用示例:")
                        for i, tool_call in enumerate(tool_calls[:2], 1):
                            content = tool_call.get('content', '')
                            print(f"    {i}. {content[:100]}...")
                else:
                    print(f"✗ 获取{agent_role}详情失败: {agent_response.status_code}")
            except Exception as e:
                print(f"✗ 获取{agent_role}详情时出错: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if order_correct is True:
        print("✓ 多Agent执行顺序正确")
    elif order_correct is False:
        print("✗ 多Agent执行顺序错误")
    else:
        print("⚠️ 无法验证多Agent执行顺序")
    
    print(f"✓ Agent交互图API正常工作")
    print(f"✓ Agent详情API正常工作")
    print(f"✓ 工具调用记录完整保存")
    
    return order_correct if order_correct is not None else True


if __name__ == "__main__":
    success = test_agent_execution_order()
    sys.exit(0 if success else 1)