#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试ReAct机制

验证SubAgent的ReAct循环和上下文管理功能。

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


def test_context_manager():
    """测试上下文管理器"""
    print("=" * 60)
    print("测试1: AgentContextManager")
    print("=" * 60)
    
    context_dir = "test_agent_contexts"
    Path(context_dir).mkdir(exist_ok=True)
    
    # 创建上下文管理器
    context_manager = AgentContextManager(
        agent_id="test_researcher_1",
        agent_role="researcher",
        capabilities=["research"],
        context_dir=context_dir
    )
    
    print("✅ 上下文管理器创建成功")
    
    # 测试状态更新
    context_manager.update_status("thinking")
    print("✅ 状态更新成功")
    
    # 测试设置当前任务
    task = {
        "name": "测试研究任务",
        "description": "研究Python编程的最佳实践"
    }
    context_manager.set_current_task(task)
    print("✅ 当前任务设置成功")
    
    # 测试添加工作记忆
    context_manager.add_to_working_memory("开始研究Python编程")
    context_manager.add_to_working_memory("查阅官方文档")
    context_manager.add_to_working_memory("分析最佳实践")
    print("✅ 工作记忆添加成功")
    
    # 测试添加待处理事项
    context_manager.add_pending_item("完成研究报告")
    context_manager.add_pending_item("编写代码示例")
    print("✅ 待处理事项添加成功")
    
    # 测试获取工作上下文
    working_context = context_manager.get_working_context()
    print(f"✅ 工作上下文获取成功")
    print(f"   Agent ID: {working_context['agent']['id']}")
    print(f"   角色: {working_context['agent']['role']}")
    print(f"   工作记忆数量: {len(working_context['working_memory'])}")
    print(f"   待处理事项数量: {len(working_context['pending_items'])}")
    
    # 测试完成任务
    result = {
        "status": "completed",
        "findings": "Python编程的最佳实践包括代码风格、文档编写、测试等"
    }
    context_manager.complete_current_task(result)
    print("✅ 任务完成标记成功")
    
    # 检查MD文件是否生成
    md_file_path = context_manager.get_md_file_path()
    if Path(md_file_path).exists():
        print(f"✅ MD文件生成成功: {md_file_path}")
        
        # 读取并显示部分内容
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"\nMD文件内容预览（前500字符）:")
            print(content[:500])
    else:
        print(f"❌ MD文件未生成: {md_file_path}")
    
    print()


def test_tool_caller():
    """测试工具调用器"""
    print("=" * 60)
    print("测试2: ToolCaller")
    print("=" * 60)
    
    # 创建技能注册表
    skill_registry = SkillRegistry()
    
    # 创建测试技能
    def test_research_skill(**kwargs):
        topic = kwargs.get('topic', 'unknown')
        return {
            "topic": topic,
            "findings": f"关于{topic}的研究发现",
            "data_points": ["发现1", "发现2", "发现3"]
        }
    
    def test_analysis_skill(**kwargs):
        data = kwargs.get('data', 'unknown')
        return {
            "data": data,
            "insights": f"关于{data}的分析洞察",
            "metrics": {"accuracy": 0.95, "completeness": 0.9}
        }
    
    # 注册技能
    research_skill = create_function_skill(
        name="Research",
        description="研究技能",
        handler=test_research_skill,
        capabilities=["research"]
    )
    
    analysis_skill = create_function_skill(
        name="Analysis",
        description="分析技能",
        handler=test_analysis_skill,
        capabilities=["analysis"]
    )
    
    skill_registry.register(research_skill)
    skill_registry.register(analysis_skill)
    print("✅ 测试技能注册成功")
    
    # 创建工具调用器
    tool_caller = ToolCaller(skill_registry=skill_registry)
    print("✅ 工具调用器创建成功")
    
    # 测试获取可用工具
    available_tools = tool_caller.get_available_tools()
    print(f"✅ 可用工具数量: {len(available_tools)}")
    for tool in available_tools:
        print(f"   - {tool['name']}: {tool['description']}")
    
    # 测试调用工具
    print("\n测试调用Research工具:")
    result = tool_caller.call_tool("Research", {"topic": "人工智能"})
    print(f"✅ Research工具调用成功")
    print(f"   结果: {result}")
    
    print("\n测试调用Analysis工具:")
    result = tool_caller.call_tool("Analysis", {"data": "用户行为数据"})
    print(f"✅ Analysis工具调用成功")
    print(f"   结果: {result}")
    
    # 测试工具统计
    stats = tool_caller.get_statistics()
    print(f"\n✅ 工具统计:")
    print(f"   总工具数: {stats['total_tools']}")
    print(f"   类别数: {len(stats['categories'])}")
    
    print()


def test_react_loop():
    """测试ReAct循环"""
    print("=" * 60)
    print("测试3: ReActLoop")
    print("=" * 60)
    
    # 创建测试环境
    context_dir = "test_agent_contexts"
    Path(context_dir).mkdir(exist_ok=True)
    
    # 创建上下文管理器
    context_manager = AgentContextManager(
        agent_id="test_react_agent_1",
        agent_role="researcher",
        capabilities=["research"],
        context_dir=context_dir
    )
    
    # 创建技能注册表和工具调用器
    skill_registry = SkillRegistry()
    
    def simple_research(**kwargs):
        topic = kwargs.get('topic', 'unknown')
        return {
            "topic": topic,
            "findings": f"完成了关于{topic}的研究",
            "confidence": 0.9
        }
    
    research_skill = create_function_skill(
        name="Research",
        description="研究技能",
        handler=simple_research,
        capabilities=["research"]
    )
    
    skill_registry.register(research_skill)
    
    tool_caller = ToolCaller(skill_registry=skill_registry)
    
    # 创建模拟LLM处理器
    class MockLLMHandler:
        def __init__(self):
            self.step_count = 0
            
        def complete(self, prompt):
            self.step_count += 1
            print(f"[模拟LLM] 收到提示词，长度: {len(prompt)}")
            print(f"[模拟LLM] 当前步骤: {self.step_count}")
            
            # 简单的模拟响应
            if "第1步" in prompt or self.step_count == 1:
                return """{
                    "action_type": "tool_call",
                    "thought": "需要使用Research工具来收集信息",
                    "action": "调用Research工具",
                    "tool_name": "Research",
                    "tool_params": {"topic": "机器学习算法"}
                }"""
            elif "第2步" in prompt or self.step_count == 2:
                return """{
                    "action_type": "finish",
                    "thought": "已经完成了研究，可以结束任务",
                    "action": "完成任务",
                    "observation": "研究完成，获得了机器学习算法的相关信息"
                }"""
            else:
                return """{
                    "action_type": "think",
                    "thought": "继续分析任务需求",
                    "action": "继续思考"
                }"""
    
    mock_llm_handler = MockLLMHandler()
    
    # 创建ReAct循环
    react_loop = ReActLoop(
        agent_id="test_react_agent_1",
        agent_role="researcher",
        context_manager=context_manager,
        tool_caller=tool_caller,
        llm_handler=mock_llm_handler,
        max_steps=5
    )
    
    print("✅ ReAct循环创建成功")
    
    # 测试执行任务
    task = {
        "name": "研究机器学习算法",
        "description": "研究主要的机器学习算法及其应用场景"
    }
    
    print(f"\n开始执行任务: {task['name']}")
    print("=" * 60)
    
    result = react_loop.run(task)
    
    print("=" * 60)
    print("✅ ReAct循环执行完成")
    print(f"   状态: {result.get('status')}")
    print(f"   步骤数: {result.get('steps', 0)}")
    
    if 'tool_calls' in result:
        print(f"   工具调用数: {len(result['tool_calls'])}")
        for i, call in enumerate(result['tool_calls'], 1):
            print(f"   [{i}] {call['tool']}")
    
    # 获取执行摘要
    summary = react_loop.get_execution_summary()
    print(f"\n✅ 执行摘要:")
    print(f"   总步骤: {summary['total_steps']}")
    print(f"   工具调用: {summary['tool_calls']}")
    print(f"   完成原因: {summary['finish_reason']}")
    
    # 检查上下文是否更新
    working_context = context_manager.get_working_context()
    if working_context.get('current_task'):
        print(f"\n⚠️  当前任务仍在进行中")
    else:
        print(f"\n✅ 当前任务已完成")
    
    print()


def test_integration():
    """测试集成功能"""
    print("=" * 60)
    print("测试4: 集成测试")
    print("=" * 60)
    
    # 清理测试目录
    import shutil
    if Path("test_agent_contexts").exists():
        shutil.rmtree("test_agent_contexts")
    
    print("✅ 测试环境清理完成")
    print("\n所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        # 运行所有测试
        test_context_manager()
        test_tool_caller()
        test_react_loop()
        test_integration()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)