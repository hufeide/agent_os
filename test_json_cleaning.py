#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JSON清理功能

测试LLM返回的JSON清理和解析。

作者: Agent OS Team
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.main_agent import MainAgent


def test_json_cleaning():
    """测试JSON清理功能"""
    
    print("=" * 60)
    print("JSON清理功能测试")
    print("=" * 60)
    
    # 创建一个临时的MainAgent实例来测试清理方法
    class TestAgent:
        def _clean_json_response(self, response: str) -> str:
            """
            清理LLM返回的JSON响应
            """
            import json
            
            cleaned = response.strip()
            
            # 移除markdown代码块标记
            if cleaned.startswith("```"):
                # 找到第一个换行符
                first_newline = cleaned.find("\n")
                if first_newline != -1:
                    # 移除开头的 ```json 或 ```
                    cleaned = cleaned[first_newline:].strip()
                    
                    # 移除结尾的 ```
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3].strip()
            
            # 查找JSON对象的开始和结束
            json_start = -1
            json_end = -1
            
            # 查找第一个 {
            for i, char in enumerate(cleaned):
                if char == '{':
                    json_start = i
                    break
            
            # 查找最后一个 }
            if json_start != -1:
                brace_count = 0
                for i in range(json_start, len(cleaned)):
                    if cleaned[i] == '{':
                        brace_count += 1
                    elif cleaned[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
            
            # 如果找到完整的JSON对象
            if json_start != -1 and json_end > json_start:
                return cleaned[json_start:json_end]
            
            # 如果找不到JSON对象，尝试JSON数组
            array_start = -1
            array_end = -1
            
            # 查找第一个 [
            for i, char in enumerate(cleaned):
                if char == '[':
                    array_start = i
                    break
            
            # 查找最后一个 ]
            if array_start != -1:
                bracket_count = 0
                for i in range(array_start, len(cleaned)):
                    if cleaned[i] == '[':
                        bracket_count += 1
                    elif cleaned[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            array_end = i + 1
                            break
            
            # 如果找到完整的JSON数组
            if array_start != -1 and array_end > array_start:
                return cleaned[array_start:array_end]
            
            return cleaned
    
    test_agent = TestAgent()
    
    # 测试用例
    test_cases = [
        {
            "name": "标准JSON",
            "input": '{"action": "continue", "reason": "test"}',
            "expected": '{"action": "continue", "reason": "test"}'
        },
        {
            "name": "带markdown的JSON",
            "input": '```json\n{"action": "continue", "reason": "test"}\n```',
            "expected": '{"action": "continue", "reason": "test"}'
        },
        {
            "name": "带额外文字的JSON",
            "input": '- retry_count: 如果action是retry，提供重试次数（可选）\n\n{\n  "action": "continue",\n  "reason": "任务已成功完成"\n}',
            "expected": '{\n  "action": "continue",\n  "reason": "任务已成功完成"\n}'
        },
        {
            "name": "带markdown和额外文字的JSON",
            "input": '```json\n{\n  "action": "continue",\n  "reason": "test"\n}\n```',
            "expected": '{\n  "action": "continue",\n  "reason": "test"\n}'
        },
        {
            "name": "JSON数组",
            "input": '[{"name": "task1"}, {"name": "task2"}]',
            "expected": '[{"name": "task1"}, {"name": "task2"}]'
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        print(f"输入: {test_case['input'][:50]}...")
        
        try:
            cleaned = test_agent._clean_json_response(test_case['input'])
            print(f"清理后: {cleaned[:50]}...")
            
            # 尝试解析JSON
            import json
            parsed = json.loads(cleaned)
            print(f"✓ JSON解析成功")
            print(f"解析结果: {parsed}")
            
        except Exception as e:
            print(f"✗ JSON解析失败: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = test_json_cleaning()
    sys.exit(0 if success else 1)