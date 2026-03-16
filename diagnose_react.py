#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断ReAct循环问题

测试ReAct循环的各个组件，找出任务卡住的原因。

作者: Agent OS Team
"""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent_context_manager import AgentContextManager
from core.tool_caller import ToolCaller
from core.react_loop import ReActLoop
from core.skill_registry import SkillRegistry, create_function_skill


def test_llm_response():
    """测试LLM响应解析"""
    print("=" * 60)
    print("测试1: LLM响应解析")
    print("=" * 60)
    
    # 创建模拟LLM
    class TestLLMHandler:
        def __init__(self):
            self.call_count = 0
            
        def complete(self, prompt):
            self.call_count += 1
            print(f"\n[LLM调用 #{self.call_count}]")
            print(f"提示词长度: {len(prompt)}")
            print(f"提示词前300字符:\n{prompt[:300]}...")
            
            # 根据调用次数返回不同的响应
            if self.call_count == 1:
                response = """{
    "action_type": "tool_call",
    "thought": "需要使用Research工具来收集信息",
    "action": "调用Research工具",
    "tool_name": "Research",
    "tool_params": {"topic": "测试主题"}
}"""
            elif self.call_count == 2:
                response = """{
    "action_type": "finish",
    "thought": "已经完成任务",
    "action": "完成任务",
    "observation": "任务成功完成"
}"""
            else:
                response = """{
    "action_type": "think",
    "thought": "继续思考",
    "action": "继续思考"
}"""
            
            print(f"\n[LLM响应]\n{response}")
            return response
    
    # 创建测试环境
    context_dir = "test_diagnosis"
    Path(context_dir).mkdir(exist_ok=True)
    
    context_manager = AgentContextManager(
        agent_id="test_agent",
        agent_role="researcher",
        capabilities=["research"],
        context_dir=context_dir
    )
    
    skill_registry = SkillRegistry()
    
    def test_research(**kwargs):
        topic = kwargs.get('topic', 'unknown')
        return {
            "topic": topic,
            "result": f"关于{topic}的研究结果"
        }
    
    research_skill = create_function_skill(
        name="Research",
        description="研究技能",
        handler=test_research,
        capabilities=["research"]
    )
    
    skill_registry.register(research_skill)
    
    tool_caller = ToolCaller(skill_registry=skill_registry)
    
    llm_handler = TestLLMHandler()
    
    react_loop = ReActLoop(
        agent_id="test_agent",
        agent_role="researcher",
        context_manager=context_manager,
        tool_caller=tool_caller,
        llm_handler=llm_handler,
        max_steps=10
    )
    
    # 执行任务
    task = {
        "name": "测试任务",
        "description": "测试ReAct循环"
    }
    
    print(f"\n开始执行任务...")
    print("=" * 60)
    
    result = react_loop.run(task)
    
    print("=" * 60)
    print(f"\n任务执行完成！")
    print(f"结果: {result}")
    print(f"LLM调用次数: {llm_handler.call_count}")
    
    # 检查执行步骤
    summary = react_loop.get_execution_summary()
    print(f"\n执行摘要:")
    print(f"  总步骤: {summary['total_steps']}")
    print(f"  工具调用: {summary['tool_calls']}")
    print(f"  完成原因: {summary['finish_reason']}")
    
    print()


def test_infinite_loop_prevention():
    """测试无限循环防护"""
    print("=" * 60)
    print("测试2: 无限循环防护")
    print("=" * 60)
    
    context_dir = "test_diagnosis"
    Path(context_dir).mkdir(exist_ok=True)
    
    context_manager = AgentContextManager(
        agent_id="test_agent2",
        agent_role="researcher",
        capabilities=["research"],
        context_dir=context_dir
    )
    
    skill_registry = SkillRegistry()
    
    def test_research(**kwargs):
        return {"result": "测试结果"}
    
    research_skill = create_function_skill(
        name="Research",
        description="研究技能",
        handler=test_research,
        capabilities=["research"]
    )
    
    skill_registry.register(research_skill)
    
    tool_caller = ToolCaller(skill_registry=skill_registry)
    
    # 创建一个总是返回think的LLM
    class AlwaysThinkLLM:
        def __init__(self):
            self.call_count = 0
            
        def complete(self, prompt):
            self.call_count += 1
            print(f"  [LLM调用 #{self.call_count}] 返回think")
            return """{
    "action_type": "think",
    "thought": "继续思考",
    "action": "继续思考"
}"""
    
    llm_handler = AlwaysThinkLLM()
    
    react_loop = ReActLoop(
        agent_id="test_agent2",
        agent_role="researcher",
        context_manager=context_manager,
        tool_caller=tool_caller,
        llm_handler=llm_handler,
        max_steps=3  # 限制最大步骤
    )
    
    task = {
        "name": "无限循环测试",
        "description": "测试无限循环防护"
    }
    
    print(f"\n开始执行任务（最大3步）...")
    start_time = time.time()
    
    result = react_loop.run(task)
    
    elapsed_time = time.time() - start_time
    
    print(f"\n任务执行完成！")
    print(f"执行时间: {elapsed_time:.2f}秒")
    print(f"LLM调用次数: {llm_handler.call_count}")
    print(f"结果状态: {result.get('status')}")
    
    summary = react_loop.get_execution_summary()
    print(f"执行步骤: {summary['total_steps']}")
    
    if summary['total_steps'] <= 3:
        print("✅ 无限循环防护正常工作")
    else:
        print("❌ 无限循环防护失败")
    
    print()


def test_tool_call_failure():
    """测试工具调用失败处理"""
    print("=" * 60)
    print("测试3: 工具调用失败处理")
    print("=" * 60)
    
    context_dir = "test_diagnosis"
    Path(context_dir).mkdir(exist_ok=True)
    
    context_manager = AgentContextManager(
        agent_id="test_agent3",
        agent_role="researcher",
        capabilities=["research"],
        context_dir=context_dir
    )
    
    skill_registry = SkillRegistry()
    
    def failing_research(**kwargs):
        raise Exception("模拟工具调用失败")
    
    research_skill = create_function_skill(
        name="Research",
        description="研究技能",
        handler=failing_research,
        capabilities=["research"]
    )
    
    skill_registry.register(research_skill)
    
    tool_caller = ToolCaller(skill_registry=skill_registry)
    
    class NormalLLM:
        def __init__(self):
            self.call_count = 0
            
        def complete(self, prompt):
            self.call_count += 1
            if self.call_count == 1:
                return """{
    "action_type": "tool_call",
    "thought": "调用工具",
    "action": "调用Research工具",
    "tool_name": "Research",
    "tool_params": {}
}"""
            else:
                return """{
    "action_type": "finish",
    "thought": "完成任务",
    "action": "完成任务",
    "observation": "完成"
}"""
    
    llm_handler = NormalLLM()
    
    react_loop = ReActLoop(
        agent_id="test_agent3",
        agent_role="researcher",
        context_manager=context_manager,
        tool_caller=tool_caller,
        llm_handler=llm_handler,
        max_steps=10
    )
    
    task = {
        "name": "工具失败测试",
        "description": "测试工具调用失败处理"
    }
    
    print(f"\n开始执行任务...")
    
    result = react_loop.run(task)
    
    print(f"\n任务执行完成！")
    print(f"结果状态: {result.get('status')}")
    print(f"LLM调用次数: {llm_handler.call_count}")
    
    summary = react_loop.get_execution_summary()
    print(f"执行步骤: {summary['total_steps']}")
    
    print()


def cleanup():
    """清理测试环境"""
    import shutil
    if Path("test_diagnosis").exists():
        shutil.rmtree("test_diagnosis")
        print("✅ 测试环境清理完成")


if __name__ == "__main__":
    try:
        test_llm_response()
        test_infinite_loop_prevention()
        test_tool_call_failure()
        cleanup()
        
        print("=" * 60)
        print("✅ 所有诊断测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)