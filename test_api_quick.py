#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试Agent交互图API
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_api():
    """测试API"""
    print("测试1: 获取任务列表")
    try:
        response = requests.get(f"{BASE_URL}/api/tasks", timeout=5)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"返回数据结构: {list(data.keys())}")
            print(f"总任务数: {data.get('total_count', 0)}")
            print(f"任务列表长度: {len(data.get('tasks', []))}")
            
            if data.get('tasks'):
                first_task = data['tasks'][0]
                print(f"第一个任务ID: {first_task.get('dag_id')}")
                print(f"第一个任务名称: {first_task.get('name')}")
                
                return first_task.get('dag_id')
        else:
            print(f"错误响应: {response.text}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def test_interaction_graph(dag_id):
    """测试交互图API"""
    if not dag_id:
        print("没有DAG ID，跳过交互图测试")
        return
    
    print(f"\n测试2: 获取Agent交互图 (DAG ID: {dag_id})")
    try:
        response = requests.get(f"{BASE_URL}/api/agent-interaction-graph/{dag_id}", timeout=10)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"返回数据结构: {list(data.keys())}")
            print(f"DAG名称: {data.get('dag_name')}")
            print(f"节点数量: {len(data.get('nodes', []))}")
            print(f"边数量: {len(data.get('edges', []))}")
            
            stats = data.get('statistics', {})
            print(f"统计信息: {stats}")
            
            # 显示前几个节点
            nodes = data.get('nodes', [])
            if nodes:
                print(f"\n前3个节点:")
                for i, node in enumerate(nodes[:3]):
                    print(f"  {i+1}. {node.get('name')} ({node.get('type')}, {node.get('status')})")
        else:
            print(f"错误响应: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    dag_id = test_api()
    test_interaction_graph(dag_id)