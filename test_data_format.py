#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Agent交互图API返回的数据格式
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_interaction_graph_data():
    """测试交互图数据格式"""
    print("=" * 60)
    print("测试Agent交互图API数据格式")
    print("=" * 60)
    
    # 创建任务
    print("\n1. 创建测试任务...")
    create_response = requests.post(
        f"{BASE_URL}/api/tasks",
        json={"description": "测试数据格式"},
        timeout=10
    )
    
    if create_response.status_code != 200:
        print(f"✗ 任务创建失败: {create_response.status_code}")
        return
    
    create_data = create_response.json()
    dag_id = create_data.get('dag_id')
    print(f"✓ 任务创建成功: {dag_id}")
    
    # 等待任务开始
    print("\n2. 等待任务开始...")
    time.sleep(5)
    
    # 获取交互图
    print(f"\n3. 获取交互图...")
    graph_response = requests.get(
        f"{BASE_URL}/api/agent-interaction-graph/{dag_id}",
        timeout=10
    )
    
    if graph_response.status_code != 200:
        print(f"✗ 交互图获取失败: {graph_response.status_code}")
        print(f"  错误信息: {graph_response.text}")
        return
    
    graph_data = graph_response.json()
    print(f"✓ 交互图获取成功")
    
    # 检查数据结构
    print("\n4. 检查数据结构...")
    print(f"  返回的keys: {list(graph_data.keys())}")
    
    required_keys = ['dag_id', 'dag_name', 'dag_description', 'nodes', 'edges', 'statistics']
    missing_keys = [key for key in required_keys if key not in graph_data]
    
    if missing_keys:
        print(f"  ✗ 缺少必要的keys: {missing_keys}")
    else:
        print(f"  ✓ 所有必要的keys都存在")
    
    # 检查nodes
    print(f"\n5. 检查nodes数据...")
    nodes = graph_data.get('nodes', [])
    print(f"  nodes类型: {type(nodes)}")
    print(f"  nodes长度: {len(nodes)}")
    
    if nodes:
        print(f"  第一个node的keys: {list(nodes[0].keys())}")
        
        # 检查每个node是否有必要的字段
        required_node_keys = ['id', 'name', 'type', 'status']
        for i, node in enumerate(nodes[:3]):
            missing_node_keys = [key for key in required_node_keys if key not in node]
            if missing_node_keys:
                print(f"  ✗ node[{i}]缺少字段: {missing_node_keys}")
            else:
                print(f"  ✓ node[{i}]字段完整")
    
    # 检查edges
    print(f"\n6. 检查edges数据...")
    edges = graph_data.get('edges', [])
    print(f"  edges类型: {type(edges)}")
    print(f"  edges长度: {len(edges)}")
    
    if edges:
        print(f"  第一个edge的keys: {list(edges[0].keys())}")
    
    # 检查statistics
    print(f"\n7. 检查statistics数据...")
    stats = graph_data.get('statistics', {})
    print(f"  statistics类型: {type(stats)}")
    print(f"  statistics的keys: {list(stats.keys())}")
    
    required_stats_keys = ['total_agents', 'total_tasks', 'completed_tasks', 'failed_tasks', 'pending_tasks']
    missing_stats_keys = [key for key in required_stats_keys if key not in stats]
    
    if missing_stats_keys:
        print(f"  ✗ statistics缺少字段: {missing_stats_keys}")
    else:
        print(f"  ✓ statistics字段完整")
    
    # 显示完整数据
    print(f"\n8. 完整数据:")
    print(json.dumps(graph_data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_interaction_graph_data()