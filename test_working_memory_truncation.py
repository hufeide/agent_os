#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工作记忆截断问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent_context_manager import AgentContextManager
from core.tool_caller import ToolCaller
from datetime import datetime

def test_working_memory_truncation():
    """测试工作记忆是否被截断"""
    print("=== 测试工作记忆截断问题 ===\n")
    
    # 创建一个模拟的长工具结果
    long_result = {
        'success': True,
        'result': {
            'research_result': {
                'topic': 'historical periods and events with significant impact on human development throughout the ages including ancient civilizations medieval periods renaissance industrial revolution and modern era',
                'findings': 'Detailed research findings about various historical periods including their cultural political economic and social impacts on human development',
                'key_points': [
                    'Ancient civilizations developed writing systems',
                    'Medieval period saw the rise of feudalism',
                    'Renaissance brought scientific revolution',
                    'Industrial revolution changed production methods',
                    'Modern era is characterized by globalization'
                ],
                'data_sources': [
                    'Historical records from ancient archives',
                    'Archaeological evidence from excavation sites',
                    'Contemporary accounts from historians',
                    'Modern research and analysis'
                ],
                'confidence': 0.95
            }
        }
    }
    
    result_str = str(long_result)
    print(f"原始结果长度: {len(result_str)}")
    print(f"原始结果前200字符: {result_str[:200]}...")
    print()
    
    # 创建上下文管理器
    context_manager = AgentContextManager(
        agent_id="test_agent",
        agent_role="researcher",
        capabilities=["research", "analysis"]
    )
    
    # 模拟添加到工作记忆
    observation = result_str
    working_memory_item = f"调用工具 Research: {observation}"
    
    print(f"工作记忆项长度: {len(working_memory_item)}")
    print(f"工作记忆项前200字符: {working_memory_item[:200]}...")
    print()
    
    # 添加到工作记忆
    context_manager.add_to_working_memory(working_memory_item)
    
    # 检查保存的内容
    print("检查保存的内容:")
    print(f"工作记忆数量: {len(context_manager._context['working_memory'])}")
    
    saved_item = context_manager._context['working_memory'][0]
    print(f"保存的content长度: {len(saved_item['content'])}")
    print(f"保存的content: {saved_item['content']}")
    print()
    
    # 检查JSON文件
    json_path = context_manager.json_file_path
    print(f"JSON文件路径: {json_path}")
    
    if json_path.exists():
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            loaded_item = loaded_data['working_memory'][0]
            print(f"从JSON加载的content长度: {len(loaded_item['content'])}")
            print(f"从JSON加载的content: {loaded_item['content']}")
            print()
            
            # 比较是否一致
            if len(saved_item['content']) == len(loaded_item['content']):
                print("✅ 内存和JSON中的内容长度一致")
            else:
                print(f"❌ 内存和JSON中的内容长度不一致: {len(saved_item['content'])} vs {len(loaded_item['content'])}")
            
            if saved_item['content'] == loaded_item['content']:
                print("✅ 内存和JSON中的内容完全一致")
            else:
                print("❌ 内存和JSON中的内容不一致")
    else:
        print("❌ JSON文件不存在")
    
    print()
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_working_memory_truncation()