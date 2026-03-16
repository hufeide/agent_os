#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际LLM调用

测试使用真实LLM的ReAct循环。

作者: Agent OS Team
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm.llm_handler import create_llm_handler
from core.agent_context_manager import AgentContextManager
from core.tool_caller import ToolCaller
from core.react_loop import ReActLoop
from core.skill_registry import SkillRegistry, create_function_skill


def test_real_llm():
    """测试真实LLM调用"""
    print("=" * 60)
    print("测试: 真实LLM ReAct循环")
    print("=" * 60)
    
    # 创建LLM处理器
    print("\n创建LLM处理器...")
    llm_handler = create_llm_handler(
        api_url="http://192.168.1.159:19000",
        model_name="Qwen3Coder",
        timeout=120,  # 增加超时时间
        max_tokens=1000
    )
    print(f"✓ LLM处理器已创建")
    
    # 创建上下文管理器
    context_dir = "test_real_llm"
    os.makedirs(context_dir, exist_ok=True)
    
    context_manager = AgentContextManager(
        agent_id="test_real_agent",
        agent_role="researcher",
        capabilities=["research"],
        context_dir=context_dir
    )
    print(f"✓ 上下文管理器已创建")
    
    # 创建技能注册表和工具调用器
    skill_registry = SkillRegistry()
    
    def simple_research(**kwargs):
        topic = kwargs.get('topic', 'unknown')
        print(f"[Research Skill] 开始研究: {topic}")
        return {
            "topic": topic,
            "findings": f"关于{topic}的研究发现：这是一个重要的研究领域",
            "confidence": 0.9
        }
    
    research_skill = create_function_skill(
        name="Research",
        description="研究技能，用于收集和分析信息",
        handler=simple_research,
        capabilities=["research"]
    )
    
    skill_registry.register(research_skill)
    print(f"✓ 技能已注册")
    
    tool_caller = ToolCaller(skill_registry=skill_registry)
    print(f"✓ 工具调用器已创建")
    
    # 创建ReAct循环
    react_loop = ReActLoop(
        agent_id="test_real_agent",
        agent_role="researcher",
        context_manager=context_manager,
        tool_caller=tool_caller,
        llm_handler=llm_handler,
        max_steps=5
    )
    print(f"✓ ReAct循环已创建")
    
    # 执行任务
    task = {
        "name": "研究Python编程",
        "description": "研究Python编程的最佳实践和常用技巧"
    }
    
    print(f"\n开始执行任务: {task['name']}")
    print("=" * 60)
    start_time = time.time()
    
    try:
        result = react_loop.run(task)
        
        elapsed_time = time.time() - start_time
        
        print("=" * 60)
        print(f"\n任务执行完成！")
        print(f"执行时间: {elapsed_time:.2f}秒")
        print(f"状态: {result.get('status')}")
        print(f"步骤数: {result.get('steps', 0)}")
        
        # 获取执行摘要
        summary = react_loop.get_execution_summary()
        print(f"\n执行摘要:")
        print(f"  总步骤: {summary['total_steps']}")
        print(f"  工具调用: {summary['tool_calls']}")
        print(f"  完成原因: {summary['finish_reason']}")
        
        # 显示工具调用详情
        if 'tool_calls' in result:
            print(f"\n工具调用详情:")
            for i, call in enumerate(result['tool_calls'], 1):
                print(f"  [{i}] {call['tool']}")
                print(f"      参数: {call['params']}")
                print(f"      结果: {str(call['result'])[:100]}...")
        
        print(f"\n✅ 测试成功！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理
        import shutil
        if os.path.exists(context_dir):
            shutil.rmtree(context_dir)
    
    return True


if __name__ == "__main__":
    try:
        success = test_real_llm()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ 所有测试通过！")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ 测试失败")
            print("=" * 60)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)