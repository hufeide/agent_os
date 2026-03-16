#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终集成测试

验证ReAct机制在实际系统中的完整功能。

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


def test_complete_workflow():
    """测试完整工作流程"""
    print("=" * 60)
    print("最终集成测试")
    print("=" * 60)
    
    # 1. 创建LLM处理器
    print("\n[1/6] 创建LLM处理器...")
    llm_handler = create_llm_handler(
        api_url="http://192.168.1.159:19000",
        model_name="Qwen3Coder",
        timeout=120,
        max_tokens=1000
    )
    print("✓ LLM处理器已创建")
    
    # 2. 创建上下文管理器
    print("\n[2/6] 创建上下文管理器...")
    context_dir = "test_final_integration"
    os.makedirs(context_dir, exist_ok=True)
    
    context_manager = AgentContextManager(
        agent_id="integration_test_agent",
        agent_role="researcher",
        capabilities=["research", "analysis"],
        context_dir=context_dir
    )
    print("✓ 上下文管理器已创建")
    
    # 3. 创建技能和工具
    print("\n[3/6] 创建技能和工具...")
    skill_registry = SkillRegistry()
    
    def research_skill(**kwargs):
        topic = kwargs.get('topic', 'unknown')
        return {
            "topic": topic,
            "findings": f"关于{topic}的研究发现：这是重要的研究领域",
            "confidence": 0.9
        }
    
    def analysis_skill(**kwargs):
        data = kwargs.get('data', 'unknown')
        return {
            "data": data,
            "insights": f"关于{data}的分析洞察",
            "metrics": {"accuracy": 0.95, "completeness": 0.9}
        }
    
    research = create_function_skill(
        name="Research",
        description="研究技能，用于收集和分析信息",
        handler=research_skill,
        capabilities=["research"]
    )
    
    analysis = create_function_skill(
        name="Analysis",
        description="分析技能，用于数据分析",
        handler=analysis_skill,
        capabilities=["analysis"]
    )
    
    skill_registry.register(research)
    skill_registry.register(analysis)
    print(f"✓ 已注册 {len(skill_registry.get_all_skills())} 个技能")
    
    # 4. 创建工具调用器
    print("\n[4/6] 创建工具调用器...")
    tool_caller = ToolCaller(skill_registry=skill_registry)
    available_tools = tool_caller.get_available_tools()
    print(f"✓ 工具调用器已创建，可用工具: {len(available_tools)}")
    for tool in available_tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    # 5. 创建ReAct循环
    print("\n[5/6] 创建ReAct循环...")
    react_loop = ReActLoop(
        agent_id="integration_test_agent",
        agent_role="researcher",
        context_manager=context_manager,
        tool_caller=tool_caller,
        llm_handler=llm_handler,
        max_steps=5
    )
    print("✓ ReAct循环已创建")
    
    # 6. 执行多个测试任务
    print("\n[6/6] 执行测试任务...")
    
    test_tasks = [
        {
            "name": "研究Python编程",
            "description": "研究Python编程的最佳实践和常用技巧"
        },
        {
            "name": "分析用户行为",
            "description": "分析用户行为数据并提供洞察"
        }
    ]
    
    all_passed = True
    
    for i, task in enumerate(test_tasks, 1):
        print(f"\n{'='*60}")
        print(f"测试任务 {i}/{len(test_tasks)}: {task['name']}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            result = react_loop.run(task)
            
            elapsed_time = time.time() - start_time
            
            print(f"\n✓ 任务执行完成")
            print(f"  执行时间: {elapsed_time:.2f}秒")
            print(f"  状态: {result.get('status')}")
            print(f"  步骤数: {result.get('steps', 0)}")
            
            summary = react_loop.get_execution_summary()
            print(f"  完成原因: {summary['finish_reason']}")
            
            # 验证结果
            if result.get('status') == 'completed' and result.get('steps', 0) > 0:
                print(f"  ✓ 任务执行成功")
            else:
                print(f"  ✗ 任务执行异常")
                all_passed = False
                
        except Exception as e:
            print(f"\n✗ 任务执行失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # 清理
    import shutil
    if os.path.exists(context_dir):
        shutil.rmtree(context_dir)
        print(f"\n✓ 测试环境已清理")
    
    return all_passed


def test_edge_cases():
    """测试边缘情况"""
    print("\n" + "=" * 60)
    print("边缘情况测试")
    print("=" * 60)
    
    # 测试1: 无可用工具
    print("\n[测试1] 无可用工具情况...")
    context_dir = "test_edge_cases"
    os.makedirs(context_dir, exist_ok=True)
    
    context_manager = AgentContextManager(
        agent_id="edge_test_agent",
        agent_role="assistant",
        capabilities=["general"],
        context_dir=context_dir
    )
    
    tool_caller = ToolCaller()  # 不提供skill_registry
    
    llm_handler = create_llm_handler(
        api_url="http://192.168.1.159:19000",
        model_name="Qwen3Coder",
        timeout=60,
        max_tokens=500
    )
    
    react_loop = ReActLoop(
        agent_id="edge_test_agent",
        agent_role="assistant",
        context_manager=context_manager,
        tool_caller=tool_caller,
        llm_handler=llm_handler,
        max_steps=3
    )
    
    task = {
        "name": "简单任务",
        "description": "回答一个简单的问题"
    }
    
    try:
        result = react_loop.run(task)
        print(f"✓ 无工具情况测试通过，状态: {result.get('status')}")
    except Exception as e:
        print(f"✗ 无工具情况测试失败: {e}")
    
    # 清理
    import shutil
    if os.path.exists(context_dir):
        shutil.rmtree(context_dir)
    
    print()


if __name__ == "__main__":
    try:
        # 运行完整工作流程测试
        workflow_passed = test_complete_workflow()
        
        # 运行边缘情况测试
        test_edge_cases()
        
        # 总结
        print("=" * 60)
        if workflow_passed:
            print("✅ 所有集成测试通过！")
        else:
            print("⚠️  部分测试失败")
        print("=" * 60)
        
        if not workflow_passed:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)