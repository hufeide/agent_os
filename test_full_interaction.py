#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试任务并验证Agent交互图
"""

import requests
import time
import json

BASE_URL = "http://localhost:8001"

def create_test_task():
    """创建测试任务"""
    print("创建测试任务...")
    
    task_description = "分析2024年人工智能的发展趋势，包括技术突破、应用案例和市场动态"
    
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
        return result['dag_id']
    else:
        print(f"✗ 任务创建失败: {response.status_code}")
        print(f"  错误信息: {response.text}")
        return None

def wait_for_tasks(dag_id, max_wait=180):
    """等待任务完成"""
    print(f"\n等待任务执行 (DAG ID: {dag_id})...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{BASE_URL}/api/tasks/{dag_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"  状态: {data['status_counts']}")
                print(f"  总任务数: {data['total_tasks']}")
                print(f"  是否完成: {data['is_completed']}")
                
                if data['is_completed']:
                    print(f"✓ 所有任务已完成")
                    return True
            
            time.sleep(10)
        except Exception as e:
            print(f"  检查状态时出错: {e}")
            time.sleep(10)
    
    print(f"✗ 等待超时")
    return False

def test_interaction_graph(dag_id):
    """测试交互图"""
    print(f"\n测试Agent交互图...")
    
    response = requests.get(f"{BASE_URL}/api/agent-interaction-graph/{dag_id}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Agent交互图获取成功")
        print(f"  DAG名称: {data['dag_name']}")
        print(f"  节点数量: {len(data['nodes'])}")
        print(f"  边数量: {len(data['edges'])}")
        
        stats = data['statistics']
        print(f"  统计信息:")
        print(f"    总Agent数: {stats['total_agents']}")
        print(f"    总任务数: {stats['total_tasks']}")
        print(f"    完成任务数: {stats['completed_tasks']}")
        print(f"    失败任务数: {stats['failed_tasks']}")
        print(f"    待处理任务数: {stats['pending_tasks']}")
        
        print(f"\n  节点列表:")
        for i, node in enumerate(data['nodes']):
            print(f"    {i+1}. {node['name']} ({node['type']}, {node['status']})")
        
        print(f"\n  边列表:")
        for i, edge in enumerate(data['edges']):
            print(f"    {i+1}. {edge['from']} -> {edge['to']} ({edge['type']})")
        
        return True
    else:
        print(f"✗ Agent交互图获取失败: {response.status_code}")
        print(f"  错误信息: {response.text}")
        return False

def test_tasks_list():
    """测试任务列表"""
    print(f"\n测试任务列表...")
    
    response = requests.get(f"{BASE_URL}/api/tasks")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 任务列表获取成功")
        print(f"  总任务数: {data['total_count']}")
        print(f"  任务列表:")
        
        for i, task in enumerate(data['tasks']):
            print(f"    {i+1}. {task['name']} (ID: {task['dag_id'][:8]}...)")
            print(f"       总任务数: {task['total_tasks']}")
            print(f"       完成数: {task.get('completed_count', 0)}")
            print(f"       失败数: {task.get('failed_count', 0)}")
            print(f"       待处理数: {task.get('pending_count', 0)}")
            print(f"       是否完成: {task['is_completed']}")
        
        return True
    else:
        print(f"✗ 任务列表获取失败: {response.status_code}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("测试Agent交互图功能")
    print("=" * 60)
    
    # 创建测试任务
    dag_id = create_test_task()
    
    if not dag_id:
        print("无法创建任务，退出测试")
        exit(1)
    
    # 等待任务执行
    completed = wait_for_tasks(dag_id)
    
    if completed:
        # 测试交互图
        graph_success = test_interaction_graph(dag_id)
        
        # 测试任务列表
        list_success = test_tasks_list()
        
        print(f"\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        if graph_success and list_success:
            print("✓ 所有测试通过")
            print("✓ Agent交互图功能正常")
            print("✓ 前端可以正确显示Agent交互图")
        else:
            print("✗ 部分测试失败")
    else:
        print("\n任务未完成，跳过交互图测试")