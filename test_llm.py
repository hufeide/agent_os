#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM调试脚本

专门用于调试LLM调用过程。

作者: Agent OS Team
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.llm_handler import create_llm_handler


def test_llm_simple():
    """测试简单的LLM调用"""
    
    print("=" * 60)
    print("LLM简单调用测试")
    print("=" * 60)
    
    print("\n[1/3] 创建LLM处理器...")
    llm_handler = create_llm_handler(
        api_url="http://192.168.1.159:19000",
        model_name="Qwen3Coder"
    )
    print(f"✓ LLM处理器已创建")
    
    print("\n[2/3] 测试简单文本生成...")
    simple_prompt = "请用一句话介绍人工智能。"
    print(f"提示词: {simple_prompt}")
    
    try:
        result = llm_handler.complete(simple_prompt)
        print(f"✓ LLM响应: {result}")
    except Exception as e:
        print(f"✗ 调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n[3/3] 测试JSON生成...")
    json_prompt = """
请返回一个JSON格式的任务分解结果，不要添加任何其他文字：
{
  "subtasks": [
    {
      "name": "测试任务",
      "description": "这是一个测试任务",
      "priority": 1,
      "agent_role": "researcher"
    }
  ]
}
"""
    print(f"提示词: {json_prompt[:100]}...")
    
    try:
        result = llm_handler.complete(json_prompt)
        print(f"✓ LLM原始响应:")
        print(result)
        
        import json
        try:
            parsed = json.loads(result)
            print(f"✓ JSON解析成功: {parsed}")
        except json.JSONDecodeError as e:
            print(f"✗ JSON解析失败: {e}")
            print("尝试清理响应...")
            
            cleaned = result.strip()
            if cleaned.startswith("```"):
                first_newline = cleaned.find("\n")
                if first_newline != -1:
                    cleaned = cleaned[first_newline:].strip()
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3].strip()
            
            print(f"清理后的内容: {cleaned}")
            
            try:
                parsed = json.loads(cleaned)
                print(f"✓ 清理后JSON解析成功: {parsed}")
            except json.JSONDecodeError as e2:
                print(f"✗ 清理后JSON解析仍然失败: {e2}")
    
    except Exception as e:
        print(f"✗ 调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


def test_llm_task_decomposition():
    """测试任务分解"""
    
    print("=" * 60)
    print("LLM任务分解测试")
    print("=" * 60)
    
    print("\n[1/2] 创建LLM处理器...")
    llm_handler = create_llm_handler(
        api_url="http://192.168.1.159:19000",
        model_name="Qwen3Coder"
    )
    print(f"✓ LLM处理器已创建")
    
    print("\n[2/2] 测试任务分解...")
    task_description = "测试任务执行流程"
    context = {"test": True}
    
    prompt = f"""
请将以下任务分解为多个子任务：

任务描述: {task_description}
上下文: {context}

请直接返回JSON格式的子任务列表，不要添加任何其他文字说明。
JSON必须包含以下结构：
{{
  "subtasks": [
    {{
      "name": "子任务名称",
      "description": "子任务描述",
      "priority": 1,
      "agent_role": "researcher",
      "dependencies": [0],
      "payload": {{}}
    }}
  ]
}}

或者直接返回子任务数组：
[
  {{
    "name": "子任务名称",
    "description": "子任务描述",
    "priority": 1,
    "agent_role": "researcher"
  }}
]
"""
    
    print(f"提示词长度: {len(prompt)}")
    
    try:
        result = llm_handler.complete(prompt)
        print(f"✓ LLM原始响应:")
        print(result)
        print(f"\n响应长度: {len(result)}")
        
        import json
        
        cleaned_result = result.strip()
        
        print(f"\n清理步骤1: 移除首尾空白")
        print(f"长度: {len(cleaned_result)}")
        
        if cleaned_result.startswith("```"):
            print(f"\n清理步骤2: 移除markdown代码块")
            first_newline = cleaned_result.find("\n")
            if first_newline != -1:
                cleaned_result = cleaned_result[first_newline:].strip()
                if cleaned_result.endswith("```"):
                    cleaned_result = cleaned_result[:-3].strip()
            print(f"长度: {len(cleaned_result)}")
        
        print(f"\n最终清理结果:")
        print(cleaned_result)
        
        try:
            parsed = json.loads(cleaned_result)
            print(f"✓ JSON解析成功")
            print(f"解析结果: {parsed}")
            
            if "subtasks" in parsed:
                subtasks = parsed["subtasks"]
                print(f"✓ 找到subtasks，数量: {len(subtasks)}")
                for i, task in enumerate(subtasks):
                    print(f"  任务{i+1}: {task.get('name')}")
            elif isinstance(parsed, list):
                print(f"✓ 返回列表，数量: {len(parsed)}")
                for i, task in enumerate(parsed):
                    print(f"  任务{i+1}: {task.get('name')}")
            else:
                print(f"✗ 未知格式: {type(parsed)}")
        
        except json.JSONDecodeError as e:
            print(f"✗ JSON解析失败: {e}")
            print(f"错误位置: {e.pos}")
            if e.pos < len(cleaned_result):
                print(f"错误附近内容: {cleaned_result[max(0, e.pos-20):e.pos+20]}")
    
    except Exception as e:
        print(f"✗ 调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "simple":
            test_llm_simple()
        elif command == "decompose":
            test_llm_task_decomposition()
        else:
            print(f"未知命令: {command}")
            print("可用命令: simple, decompose")
    else:
        print("LLM调试工具")
        print("\n使用方法:")
        print("  python test_llm.py simple      - 测试简单调用")
        print("  python test_llm.py decompose  - 测试任务分解")