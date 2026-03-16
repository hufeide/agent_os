#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试任务列表API

测试任务列表API并输出详细错误信息。

作者: Agent OS Team
"""

import sys
import os
import traceback
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.task_scheduler import TaskDAGScheduler
from core.models import DAG, Task, TaskStatus


def test_api_with_debug():
    """测试API并输出详细错误信息"""
    print("=" * 60)
    print("调试任务列表API")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    
    # 测试1: 直接调用API
    print("\n[测试1] 直接调用API...")
    try:
        response = requests.get(f"{base_url}/api/tasks", timeout=10)
        print(f"响应状态码: {response.status_code}")
        if response.status_code == 200:
            print("✓ API调用成功")
            print(f"响应内容: {response.json()}")
        else:
            print(f"✗ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"✗ API调用异常: {e}")
        traceback.print_exc()
    
    # 测试2: 直接测试format_task_result函数
    print("\n[测试2] 测试format_task_result函数...")
    try:
        from api.server import format_task_result
        
        # 测试不同类型的输入
        test_cases = [
            {"result": {"steps": 5}},
            {"result": {"steps": [1, 2, 3]}},
            {"result": {"output": "test output"}},
            {"result": {"output": 123}},
            {"result": {"findings": "test findings"}},
            {"result": {"findings": 456}},
            {"result": {"research_result": {"answer_to_original_question": 123}}},
            {"result": {"analysis_result": {"answer_to_original_question": 456}}},
            {"result": {"writing_result": {"answer_to_original_question": 789}}},
            {"result": 123},
            {"result": "test"},
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n  测试用例 {i+1}: {test_case}")
            try:
                result = format_task_result(test_case)
                print(f"    ✓ 成功: {result}")
            except Exception as e:
                print(f"    ✗ 失败: {e}")
                traceback.print_exc()
    
    except Exception as e:
        print(f"✗ 测试format_task_result函数失败: {e}")
        traceback.print_exc()
    
    # 测试3: 直接测试TaskDAGScheduler
    print("\n[测试3] 测试TaskDAGScheduler...")
    try:
        # 这里需要从app.state获取scheduler
        print("  需要通过API获取scheduler")
    except Exception as e:
        print(f"✗ 测试TaskScheduler失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    try:
        test_api_with_debug()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        traceback.print_exc()
        sys.exit(1)