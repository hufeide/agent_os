#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API测试脚本

测试Agent OS API功能。

作者: Agent OS Team
"""

import requests
import json
import time


def test_api():
    """测试API功能"""
    
    base_url = "http://localhost:8001"
    
    print("=" * 60)
    print("Agent OS API测试")
    print("=" * 60)
    
    try:
        print("\n[1/5] 检查API状态...")
        response = requests.get(f"{base_url}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        
        print("\n[2/5] 获取Agent列表...")
        response = requests.get(f"{base_url}/api/agents")
        print(f"状态码: {response.status_code}")
        agents_data = response.json()
        print(f"主Agent: {agents_data.get('main_agent', {}).get('agent_id')}")
        print(f"子Agent数量: {len(agents_data.get('sub_agents', []))}")
        for agent in agents_data.get('sub_agents', []):
            print(f"  - {agent['agent_id']} ({agent['role']}): {agent['status']}")
        
        print("\n[3/5] 获取技能列表...")
        response = requests.get(f"{base_url}/api/skills")
        print(f"状态码: {response.status_code}")
        skills_data = response.json()
        print(f"技能数量: {skills_data.get('total', 0)}")
        for skill in skills_data.get('skills', []):
            print(f"  - {skill['name']}: {skill['description']}")
        
        print("\n[4/5] 创建测试任务...")
        task_data = {
            "description": "测试任务执行流程",
            "context": {
                "test": True
            }
        }
        
        response = requests.post(
            f"{base_url}/api/tasks",
            json=task_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"DAG ID: {result.get('dag_id')}")
        print(f"消息: {result.get('message')}")
        
        dag_id = result.get('dag_id')
        
        if dag_id:
            print("\n[5/5] 监控任务执行...")
            for i in range(10):
                time.sleep(2)
                
                response = requests.get(f"{base_url}/api/tasks/{dag_id}")
                print(f"状态码: {response.status_code}")
                dag_status = response.json()
                
                print(f"[{i*2}s] 总任务: {dag_status['total_tasks']}, "
                      f"已完成: {dag_status['is_completed']}")
                
                if dag_status.get('is_completed'):
                    print("\n✓ 任务已完成！")
                    break
        
        print("\n" + "=" * 60)
        print("API测试完成")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ 无法连接到API服务器")
        print("请确保服务器正在运行: python start.py")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")


if __name__ == "__main__":
    test_api()