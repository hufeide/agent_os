#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试Agent交互图API，不等待任务完成
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_interaction_graph_direct():
    """直接测试交互图API"""
    print("测试Agent交互图API...")
    
    # 先获取任务列表
    response = requests.get(f"{BASE_URL}/api/tasks", timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 任务列表获取成功")
        print(f"  总任务数: {data['total_count']}")
        
        if data['tasks']:
            first_task = data['tasks'][0]
            dag_id = first_task['dag_id']
            print(f"  第一个任务ID: {dag_id}")
            
            # 测试交互图API
            print(f"\n测试交互图API...")
            graph_response = requests.get(f"{BASE_URL}/api/agent-interaction-graph/{dag_id}", timeout=10)
            
            if graph_response.status_code == 200:
                graph_data = graph_response.json()
                print(f"✓ Agent交互图获取成功")
                print(f"  返回数据结构: {list(graph_data.keys())}")
                print(f"  DAG名称: {graph_data['dag_name']}")
                print(f"  节点数量: {len(graph_data['nodes'])}")
                print(f"  边数量: {len(graph_data['edges'])}")
                
                stats = graph_data['statistics']
                print(f"  统计信息:")
                print(f"    总Agent数: {stats['total_agents']}")
                print(f"    总任务数: {stats['total_tasks']}")
                print(f"    完成任务数: {stats['completed_tasks']}")
                print(f"    失败任务数: {stats['failed_tasks']}")
                print(f"    待处理任务数: {stats['pending_tasks']}")
                
                print(f"\n  前5个节点:")
                for i, node in enumerate(graph_data['nodes'][:5]):
                    print(f"    {i+1}. {node['name']} ({node['type']}, {node['status']})")
                    if node.get('role'):
                        print(f"       角色: {node['role']}")
                
                print(f"\n  前5条边:")
                for i, edge in enumerate(graph_data['edges'][:5]):
                    print(f"    {i+1}. {edge['from']} -> {edge['to']} ({edge['type']})")
                
                return True
            else:
                print(f"✗ Agent交互图获取失败: {graph_response.status_code}")
                print(f"  错误信息: {graph_response.text}")
                return False
        else:
            print("没有任务，创建测试任务...")
            
            # 创建测试任务
            create_response = requests.post(
                f"{BASE_URL}/api/tasks",
                json={"description": "测试任务"},
                timeout=10
            )
            
            if create_response.status_code == 200:
                result = create_response.json()
                dag_id = result['dag_id']
                print(f"✓ 测试任务创建成功: {dag_id}")
                
                # 等待一下让任务开始执行
                import time
                time.sleep(10)
                
                # 测试交互图
                graph_response = requests.get(f"{BASE_URL}/api/agent-interaction-graph/{dag_id}", timeout=10)
                
                if graph_response.status_code == 200:
                    graph_data = graph_response.json()
                    print(f"✓ Agent交互图获取成功")
                    print(f"  节点数量: {len(graph_data['nodes'])}")
                    print(f"  边数量: {len(graph_data['edges'])}")
                    return True
                else:
                    print(f"✗ Agent交互图获取失败: {graph_response.status_code}")
                    print(f"  错误信息: {graph_response.text}")
                    return False
            else:
                print(f"✗ 测试任务创建失败: {create_response.status_code}")
                return False
    else:
        print(f"✗ 任务列表获取失败: {response.status_code}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("测试Agent交互图API")
    print("=" * 60)
    
    success = test_interaction_graph_direct()
    
    print(f"\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if success:
        print("✓ Agent交互图API正常工作")
        print("✓ 前端可以正确显示Agent交互图")
    else:
        print("✗ Agent交互图API测试失败")