#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新任务的工作记忆是否完整
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent_factory import AgentFactory
from core.task_manager import TaskManager
from core.skill_registry import SkillRegistry
from core.llm_client import LLMClient
from core.tool_caller import ToolCaller
import json

def test_new_task_working_memory():
    """测试新任务的工作记忆是否完整"""
    print("=== 测试新任务的工作记忆完整性 ===\n")
    
    # 初始化组件
    skill_registry = SkillRegistry()
    llm_client = LLMClient()
    tool_caller = ToolCaller(skill_registry)
    agent_factory = AgentFactory(skill_registry, llm_client, tool_caller)
    task_manager = TaskManager(agent_factory)
    
    # 创建一个简单的测试任务
    test_task = {
        "id": "test_wm_task",
        "name": "测试工作记忆任务",
        "description": "测试工作记忆是否完整保存",
        "type": "research",
        "priority": "high",
        "agent_type": "researcher",
        "params": {
            "question": "What are the key periods in human history?"
        }
    }
    
    print(f"创建测试任务: {test_task['name']}")
    print(f"任务描述: {test_task['description']}")
    print()
    
    # 执行任务
    print("开始执行任务...")
    result = task_manager.execute_task(test_task)
    print(f"任务执行完成")
    print()
    
    # 检查工作记忆
    agent_id = result.get('agent_id', 'researcher_1')
    json_path = f"../agent_contexts/{agent_id}.json"
    
    print(f"检查工作记忆文件: {json_path}")
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            context_data = json.load(f)
            working_memory = context_data.get('working_memory', [])
            
            print(f"工作记忆数量: {len(working_memory)}")
            print()
            
            for i, item in enumerate(working_memory, 1):
                content = item['content']
                print(f"{i}. 工作记忆项:")
                print(f"   长度: {len(content)} 字符")
                print(f"   内容前300字符: {content[:300]}...")
                
                # 检查是否被截断
                if len(content) < 100 and "调用工具" in content:
                    print(f"   ⚠️ 可能被截断（长度小于100字符）")
                else:
                    print(f"   ✅ 内容完整")
                print()
            
            # 检查是否有Research和Analysis工具调用
            research_calls = [item for item in working_memory if "调用工具 Research" in item['content']]
            analysis_calls = [item for item in working_memory if "调用工具 Analysis" in item['content']]
            
            print(f"Research工具调用次数: {len(research_calls)}")
            print(f"Analysis工具调用次数: {len(analysis_calls)}")
            print()
            
            if research_calls:
                print("Research工具调用示例:")
                research_content = research_calls[0]['content']
                print(f"  长度: {len(research_content)} 字符")
                print(f"  内容: {research_content[:500]}...")
                print()
            
            if analysis_calls:
                print("Analysis工具调用示例:")
                analysis_content = analysis_calls[0]['content']
                print(f"  长度: {len(analysis_content)} 字符")
                print(f"  内容: {analysis_content[:500]}...")
                print()
    else:
        print(f"❌ 工作记忆文件不存在: {json_path}")
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_new_task_working_memory()