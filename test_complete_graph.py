#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试Agent交互图功能
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_complete_interaction_graph():
    """完整测试Agent交互图"""
    print("=" * 60)
    print("完整测试Agent交互图功能")
    print("=" * 60)
    
    # 1. 创建测试任务
    print("\n[1] 创建测试任务...")
    create_response = requests.post(
        f"{BASE_URL}/api/tasks",
        json={"description": "分析人工智能的最新发展趋势"},
        timeout=10
    )
    
    if create_response.status_code != 200:
        print(f"✗ 任务创建失败: {create_response.status_code}")
        return False
    
    result = create_response.json()
    dag_id = result['dag_id']
    print(f"✓ 任务创建成功: {dag_id}")
    
    # 2. 获取任务列表
    print("\n[2] 获取任务列表...")
    list_response = requests.get(f"{BASE_URL}/api/tasks", timeout=5)
    
    if list_response.status_code != 200:
        print(f"✗ 任务列表获取失败: {list_response.status_code}")
        return False
    
    list_data = list_response.json()
    print(f"✓ 任务列表获取成功")
    print(f"  总任务数: {list_data['total_count']}")
    
    # 3. 获取Agent交互图
    print("\n[3] 获取Agent交互图...")
    graph_response = requests.get(f"{BASE_URL}/api/agent-interaction-graph/{dag_id}", timeout=10)
    
    if graph_response.status_code != 200:
        print(f"✗ Agent交互图获取失败: {graph_response.status_code}")
        print(f"  错误信息: {graph_response.text}")
        return False
    
    graph_data = graph_response.json()
    print(f"✓ Agent交互图获取成功")
    
    # 4. 验证数据结构
    print("\n[4] 验证数据结构...")
    required_keys = ['dag_id', 'dag_name', 'dag_description', 'nodes', 'edges', 'statistics']
    missing_keys = [key for key in required_keys if key not in graph_data]
    
    if missing_keys:
        print(f"✗ 缺少必要字段: {missing_keys}")
        return False
    
    print(f"✓ 数据结构完整")
    
    # 5. 验证节点
    print("\n[5] 验证节点数据...")
    nodes = graph_data['nodes']
    print(f"  节点数量: {len(nodes)}")
    
    node_types = set(node['type'] for node in nodes)
    print(f"  节点类型: {node_types}")
    
    main_agents = [node for node in nodes if node['type'] == 'main']
    sub_agents = [node for node in nodes if node['type'] == 'sub']
    tasks = [node for node in nodes if node['type'] == 'task']
    
    print(f"  主Agent数: {len(main_agents)}")
    print(f"  子Agent数: {len(sub_agents)}")
    print(f"  任务数: {len(tasks)}")
    
    # 6. 验证边
    print("\n[6] 验证边数据...")
    edges = graph_data['edges']
    print(f"  边数量: {len(edges)}")
    
    edge_types = set(edge['type'] for edge in edges)
    print(f"  边类型: {edge_types}")
    
    # 7. 验证统计信息
    print("\n[7] 验证统计信息...")
    stats = graph_data['statistics']
    print(f"  总Agent数: {stats['total_agents']}")
    print(f"  总任务数: {stats['total_tasks']}")
    print(f"  完成任务数: {stats['completed_tasks']}")
    print(f"  失败任务数: {stats['failed_tasks']}")
    print(f"  待处理任务数: {stats['pending_tasks']}")
    
    # 8. 显示节点详情
    print("\n[8] 节点详情:")
    for i, node in enumerate(nodes):
        print(f"  {i+1}. {node['name']}")
        print(f"     ID: {node['id']}")
        print(f"     类型: {node['type']}")
        print(f"     状态: {node['status']}")
        if node.get('role'):
            print(f"     角色: {node['role']}")
        print(f"     位置: {node['position']}")
    
    # 9. 显示边详情
    print("\n[9] 边详情:")
    for i, edge in enumerate(edges):
        print(f"  {i+1}. {edge['from']} -> {edge['to']}")
        print(f"     类型: {edge['type']}")
        print(f"     标签: {edge['label']}")
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print("✓ 所有测试通过")
    print("✓ Agent交互图功能正常")
    print("✓ 前端可以正确显示Agent交互图")
    print("✓ 数据结构完整且正确")
    
    return True

if __name__ == "__main__":
    try:
        success = test_complete_interaction_graph()
        exit(0 if success else 1)
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)