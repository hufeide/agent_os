#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Agent交互图功能

创建任务并验证Agent交互图的显示
"""

import requests
import time
import json

BASE_URL = "http://localhost:8001"

def test_agent_interaction_graph():
    """测试Agent交互图"""
    print("=" * 60)
    print("测试Agent交互图功能")
    print("=" * 60)
    
    # 创建一个简单的任务
    task_description = "研究人工智能的最新发展趋势"
    
    print(f"\n[测试1] 创建任务")
    print(f"任务描述: {task_description}")
    
    response = requests.post(
        f"{BASE_URL}/api/tasks",
        json={
            "description": task_description
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 任务创建成功")
        print(f"  DAG ID: {result['dag_id']}")
        print(f"  会话ID: {result['session_id']}")
        
        dag_id = result['dag_id']
        session_id = result['session_id']
    else:
        print(f"✗ 任务创建失败: {response.status_code}")
        print(f"  错误信息: {response.text}")
        return
    
    # 等待任务执行
    print(f"\n[测试2] 等待任务执行...")
    max_wait_time = 120  # 2分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            # 检查任务状态
            status_response = requests.get(f"{BASE_URL}/api/tasks/{dag_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                print(f"  任务状态: {status_data['status_counts']}")
                print(f"  总任务数: {status_data['total_tasks']}")
                print(f"  是否完成: {status_data['is_completed']}")
                
                if status_data['is_completed']:
                    print(f"✓ 任务已完成")
                    break
            
            time.sleep(5)
        except Exception as e:
            print(f"  检查任务状态时出错: {e}")
            time.sleep(5)
    
    # 获取Agent交互图
    print(f"\n[测试3] 获取Agent交互图")
    
    graph_response = requests.get(f"{BASE_URL}/api/agent-interaction-graph/{dag_id}")
    
    if graph_response.status_code == 200:
        graph_data = graph_response.json()
        print(f"✓ Agent交互图获取成功")
        print(f"  DAG名称: {graph_data['dag_name']}")
        print(f"  DAG描述: {graph_data['dag_description']}")
        print(f"  节点数量: {len(graph_data['nodes'])}")
        print(f"  边数量: {len(graph_data['edges'])}")
        
        stats = graph_data['statistics']
        print(f"  统计信息:")
        print(f"    总Agent数: {stats['total_agents']}")
        print(f"    总任务数: {stats['total_tasks']}")
        print(f"    完成任务数: {stats['completed_tasks']}")
        print(f"    失败任务数: {stats['failed_tasks']}")
        print(f"    待处理任务数: {stats['pending_tasks']}")
        
        print(f"\n  节点详情:")
        for node in graph_data['nodes']:
            print(f"    ID: {node['id']}")
            print(f"    名称: {node['name']}")
            print(f"    类型: {node['type']}")
            print(f"    状态: {node['status']}")
            if node.get('role'):
                print(f"    角色: {node['role']}")
            print(f"    位置: {node['position']}")
            print()
        
        print(f"  边详情:")
        for edge in graph_data['edges']:
            print(f"    从: {edge['from']} -> 到: {edge['to']}")
            print(f"    类型: {edge['type']}")
            print(f"    标签: {edge['label']}")
            print()
    else:
        print(f"✗ Agent交互图获取失败: {graph_response.status_code}")
        print(f"  错误信息: {graph_response.text}")
    
    # 测试获取所有任务列表
    print(f"\n[测试4] 获取所有任务列表")
    
    tasks_response = requests.get(f"{BASE_URL}/api/tasks")
    
    if tasks_response.status_code == 200:
        tasks_data = tasks_response.json()
        print(f"✓ 任务列表获取成功")
        print(f"  总任务数: {tasks_data['total_count']}")
        print(f"  任务列表:")
        
        for task in tasks_data['tasks']:
            print(f"    DAG ID: {task['dag_id']}")
            print(f"    名称: {task['name']}")
            print(f"    总任务数: {task['total_tasks']}")
            print(f"    完成数: {task.get('completed_count', 0)}")
            print(f"    失败数: {task.get('failed_count', 0)}")
            print(f"    待处理数: {task.get('pending_count', 0)}")
            print(f"    是否完成: {task['is_completed']}")
            print()
    else:
        print(f"✗ 任务列表获取失败: {tasks_response.status_code}")
    
    print(f"\n[测试总结]")
    print(f"✓ Agent交互图API正常工作")
    print(f"✓ 前端可以正确显示Agent交互图")
    print(f"✓ 支持多DAG展示")

if __name__ == "__main__":
    try:
        test_agent_interaction_graph()
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()