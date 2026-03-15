#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM执行测试脚本

测试当没有匹配技能时，LLM直接执行任务的功能。

作者: Agent OS Team
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import time


def test_llm_execution():
    """测试LLM执行功能"""
    
    print("=" * 60)
    print("LLM执行测试")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    
    # [1/4] 检查API状态
    print("\n[1/4] 检查API状态...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"✗ API连接失败: {e}")
        return
    
    # [2/4] 获取技能列表
    print("\n[2/4] 获取技能列表...")
    try:
        response = requests.get(f"{base_url}/api/skills")
        skills_data = response.json()
        print(f"技能数量: {skills_data.get('total', 0)}")
        for skill in skills_data.get('skills', []):
            print(f"  - {skill['name']}: {skill['description']}")
    except Exception as e:
        print(f"✗ 获取技能失败: {e}")
        return
    
    # [3/4] 创建一个没有对应技能的任务
    print("\n[3/4] 创建一个没有对应技能的任务...")
    task_description = {
        "name": "代码审查",
        "description": "审查Python代码的质量和安全性，提供改进建议",
        "payload": {
            "language": "Python",
            "focus": "安全性、性能、可读性"
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/tasks",
            json=task_description
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"DAG ID: {result.get('dag_id')}")
        print(f"消息: {result.get('message')}")
        
        dag_id = result.get('dag_id')
    except Exception as e:
        print(f"✗ 创建任务失败: {e}")
        return
    
    # [4/4] 监控任务执行
    print("\n[4/4] 监控任务执行...")
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(f"{base_url}/api/tasks/{dag_id}")
            status = response.json()
            
            total_tasks = status.get('total_tasks', 0)
            completed_tasks = status.get('completed_tasks', 0)
            is_completed = status.get('is_completed', False)
            
            print(f"[{attempt*2}s] 总任务: {total_tasks}, 已完成: {completed_tasks}")
            
            if is_completed:
                print(f"\n✓ 任务已完成！")
                
                # 获取详细的任务结果
                if 'tasks' in status:
                    for task in status['tasks']:
                        print(f"\n任务: {task.get('name')}")
                        print(f"状态: {task.get('status')}")
                        if task.get('result'):
                            print(f"结果: {json.dumps(task['result'], indent=2, ensure_ascii=False)}")
                        if task.get('error'):
                            print(f"错误: {task.get('error')}")
                
                break
            
            attempt += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"✗ 获取任务状态失败: {e}")
            break
    
    if attempt >= max_attempts:
        print(f"\n✗ 任务执行超时")
    
    print("\n" + "=" * 60)
    print("LLM执行测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_llm_execution()