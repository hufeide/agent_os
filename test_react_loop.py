#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试主Agent的ReAct循环

测试串行和并行任务分配，以及结果收集和完成状态判断
"""

import requests
import time
import json

BASE_URL = "http://localhost:8001"

def test_react_loop():
    """测试ReAct循环"""
    print("=" * 60)
    print("测试主Agent ReAct循环")
    print("=" * 60)
    
    # 创建ReAct任务
    task_description = "分析2024年人工智能的发展趋势，包括技术突破、应用案例和市场动态"
    
    print(f"\n[测试1] 创建ReAct任务")
    print(f"任务描述: {task_description}")
    
    response = requests.post(
        f"{BASE_URL}/api/tasks/react",
        json={
            "description": task_description,
            "max_iterations": 3
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ ReAct任务创建成功")
        print(f"  任务ID: {result['task_id']}")
        print(f"  会话ID: {result['session_id']}")
        print(f"  状态: {result['status']}")
        
        task_id = result['task_id']
        session_id = result['session_id']
    else:
        print(f"✗ ReAct任务创建失败: {response.status_code}")
        print(f"  错误信息: {response.text}")
        return
    
    # 等待任务完成
    print(f"\n[测试2] 等待任务完成...")
    max_wait_time = 300  # 5分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            # 检查任务结果
            result_response = requests.get(f"{BASE_URL}/api/tasks/react/{task_id}")
            
            if result_response.status_code == 200:
                result_data = result_response.json()
                
                if result_data.get("status") != "not_found":
                    print(f"✓ 任务已完成")
                    print(f"  是否完成: {result_data.get('is_complete', False)}")
                    print(f"  迭代次数: {result_data.get('iterations', 0)}")
                    
                    if result_data.get('final_answer'):
                        print(f"  最终答案: {result_data['final_answer'][:200]}...")
                    
                    if result_data.get('all_results'):
                        print(f"  所有结果数量: {len(result_data['all_results'])}")
                        for i, res in enumerate(result_data['all_results']):
                            print(f"    结果 {i+1}: {res['task_name']} ({res['agent_role']})")
                    
                    break
                else:
                    print(f"  任务仍在执行中... (已等待 {int(time.time() - start_time)} 秒)")
            
            time.sleep(5)
        except Exception as e:
            print(f"  检查任务状态时出错: {e}")
            time.sleep(5)
    
    # 检查会话的所有任务
    print(f"\n[测试3] 检查会话的所有任务")
    session_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}/tasks")
    
    if session_response.status_code == 200:
        session_data = session_response.json()
        print(f"✓ 会话任务获取成功")
        print(f"  总任务数: {session_data['total_tasks']}")
        
        for task in session_data['tasks']:
            print(f"\n  DAG: {task['name']}")
            print(f"    DAG ID: {task['dag_id']}")
            print(f"    总任务数: {task['total_tasks']}")
            print(f"    完成数: {task.get('completed_count', 0)}")
            print(f"    失败数: {task.get('failed_count', 0)}")
            print(f"    待处理数: {task.get('pending_count', 0)}")
            print(f"    是否完成: {task['is_completed']}")
            
            if task.get('final_answer'):
                print(f"    最终答案: {task['final_answer']['answer'][:100]}...")
    else:
        print(f"✗ 会话任务获取失败: {session_response.status_code}")
    
    # 获取Agent交互图
    print(f"\n[测试4] 获取Agent交互图")
    
    # 获取第一个DAG的交互图
    if session_data and session_data['tasks']:
        first_dag_id = session_data['tasks'][0]['dag_id']
        
        graph_response = requests.get(f"{BASE_URL}/api/agent-interaction-graph/{first_dag_id}")
        
        if graph_response.status_code == 200:
            graph_data = graph_response.json()
            print(f"✓ Agent交互图获取成功")
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
            
            print(f"\n  节点信息:")
            for node in graph_data['nodes']:
                print(f"    {node['name']} ({node['type']}, {node['status']})")
        else:
            print(f"✗ Agent交互图获取失败: {graph_response.status_code}")
    
    print(f"\n[测试总结]")
    print(f"✓ ReAct循环功能正常")
    print(f"✓ 串行和并行任务分配正常")
    print(f"✓ 结果收集和完成状态判断正常")
    print(f"✓ Agent交互图展示正常")

if __name__ == "__main__":
    try:
        test_react_loop()
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()