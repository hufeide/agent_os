#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务列表API

测试任务列表API是否正常工作。

作者: Agent OS Team
"""

import sys
import os
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_task_list_api():
    """测试任务列表API"""
    print("=" * 60)
    print("测试任务列表API")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    
    # 测试1: 检查服务器是否运行
    print("\n[测试1] 检查API服务器状态...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print("✓ API服务器正在运行")
        else:
            print(f"✗ API服务器状态异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到API服务器")
        print("  请确保服务器正在运行: python start.py")
        return False
    except Exception as e:
        print(f"✗ 连接错误: {e}")
        return False
    
    # 测试2: 获取任务列表
    print("\n[测试2] 获取任务列表...")
    try:
        response = requests.get(f"{base_url}/api/tasks", timeout=10)
        print(f"  响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 成功获取任务列表")
            print(f"  总任务数: {data.get('total_count', 0)}")
            print(f"  任务列表: {data.get('tasks', [])}")
            
            # 显示任务详情
            tasks = data.get('tasks', [])
            if tasks:
                print(f"\n  任务详情:")
                for i, task in enumerate(tasks, 1):
                    print(f"    [{i}] {task.get('name', 'Unknown')}")
                    print(f"        ID: {task.get('dag_id', 'N/A')}")
                    print(f"        描述: {task.get('description', 'N/A')[:50]}...")
                    print(f"        状态: {'已完成' if task.get('is_completed') else '进行中'}")
                    print(f"        创建时间: {task.get('created_at', 'N/A')}")
            else:
                print(f"  当前没有任务")
            
            return True
        else:
            print(f"✗ 获取任务列表失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ 连接错误")
        return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试3: 创建一个测试任务
    print("\n[测试3] 创建测试任务...")
    try:
        task_data = {
            "description": "测试任务 - 检查API功能",
            "context": {"test": True}
        }
        
        response = requests.post(
            f"{base_url}/api/tasks",
            json=task_data,
            timeout=10
        )
        print(f"  响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 任务创建成功")
            print(f"  DAG ID: {data.get('dag_id')}")
            print(f"  任务ID: {data.get('task_id')}")
            
            # 等待任务处理
            dag_id = data.get('dag_id')
            print(f"\n  等待任务处理...")
            for i in range(10):
                time.sleep(2)
                response = requests.get(f"{base_url}/api/tasks/{dag_id}", timeout=5)
                if response.status_code == 200:
                    status_data = response.json()
                    is_completed = status_data.get('is_completed', False)
                    print(f"    [{i+1}/10] 任务状态: {'已完成' if is_completed else '进行中'}")
                    if is_completed:
                        print(f"  ✓ 任务已完成")
                        break
            else:
                print(f"  ⚠ 任务仍在处理中")
            
            return True
        else:
            print(f"✗ 任务创建失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 创建任务失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """测试各个API端点"""
    print("\n" + "=" * 60)
    print("测试API端点")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    endpoints = [
        ("GET", "/api/tasks", "任务列表"),
        ("GET", "/api/agents", "Agent状态"),
        ("GET", "/api/events", "事件列表"),
        ("GET", "/api/memories", "记忆列表"),
    ]
    
    for method, endpoint, description in endpoints:
        print(f"\n测试 {method} {endpoint} ({description})...")
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                print(f"  ✓ 端点正常")
                print(f"    响应大小: {len(response.content)} bytes")
            else:
                print(f"  ✗ 端点异常: {response.status_code}")
                print(f"    错误信息: {response.text[:200]}")
        except Exception as e:
            print(f"  ✗ 请求失败: {e}")


if __name__ == "__main__":
    try:
        success = test_task_list_api()
        
        if success:
            test_api_endpoints()
        
        print("\n" + "=" * 60)
        if success:
            print("✅ API测试完成")
        else:
            print("❌ API测试失败")
        print("=" * 60)
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)