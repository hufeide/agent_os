#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试API是否正常工作
"""

import requests
import time
import json

BASE_URL = "http://localhost:8001"

def test_api():
    """测试API"""
    print("测试API...")
    
    # 1. 测试任务列表
    print("\n1. 测试任务列表...")
    try:
        response = requests.get(f"{BASE_URL}/api/tasks", timeout=5)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 任务列表API正常")
            print(f"  总任务数: {data.get('total_count', 0)}")
            print(f"  任务列表: {len(data.get('tasks', []))}")
            
            if data.get('tasks'):
                first_task = data['tasks'][0]
                print(f"  第一个任务ID: {first_task.get('id')}")
                print(f"  第一个任务名称: {first_task.get('name')}")
                return first_task.get('id')
        else:
            print(f"✗ 任务列表API失败: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 任务列表API异常: {e}")
        return None

def create_task():
    """创建测试任务"""
    print("\n2. 创建测试任务...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/tasks",
            json={"description": "测试Agent交互图显示"},
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 任务创建成功")
            print(f"  DAG ID: {data.get('dag_id')}")
            print(f"  会话ID: {data.get('session_id')}")
            return data.get('dag_id')
        else:
            print(f"✗ 任务创建失败: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 任务创建异常: {e}")
        return None

def test_interaction_graph(dag_id):
    """测试交互图"""
    if not dag_id:
        print("\n3. 跳过交互图测试（没有DAG ID）")
        return False
    
    print(f"\n3. 测试交互图 (DAG ID: {dag_id})...")
    try:
        response = requests.get(f"{BASE_URL}/api/agent-interaction-graph/{dag_id}", timeout=10)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 交互图API正常")
            print(f"  DAG名称: {data.get('dag_name')}")
            print(f"  节点数量: {len(data.get('nodes', []))}")
            print(f"  边数量: {len(data.get('edges', []))}")
            
            stats = data.get('statistics', {})
            print(f"  统计信息:")
            print(f"    总Agent数: {stats.get('total_agents', 0)}")
            print(f"    总任务数: {stats.get('total_tasks', 0)}")
            print(f"    完成任务数: {stats.get('completed_tasks', 0)}")
            print(f"    进行中任务数: {stats.get('pending_tasks', 0)}")
            print(f"    失败任务数: {stats.get('failed_tasks', 0)}")
            
            # 显示前3个节点
            nodes = data.get('nodes', [])
            if nodes:
                print(f"  前3个节点:")
                for i, node in enumerate(nodes[:3]):
                    print(f"    {i+1}. {node.get('name')} ({node.get('type')}, {node.get('status')})")
            
            return True
        else:
            print(f"✗ 交互图API失败: {response.text}")
            return False
    except Exception as e:
        print(f"✗ 交互图API异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("测试Agent交互图API")
    print("=" * 60)
    
    # 先尝试获取现有任务
    dag_id = test_api()
    
    # 如果没有任务，创建一个
    if not dag_id:
        dag_id = create_task()
        
        # 等待任务开始执行
        if dag_id:
            print("\n等待任务开始执行...")
            time.sleep(5)
    
    # 测试交互图
    if dag_id:
        success = test_interaction_graph(dag_id)
        
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        if success:
            print("✓ API正常工作")
            print("✓ 前端应该能够显示Agent交互图")
        else:
            print("✗ API测试失败")
    else:
        print("\n✗ 无法获取或创建任务")