#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试任务分解功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.main_agent import MainAgent
from core.event_bus import EventBus
from core.blackboard import Blackboard
from core.task_scheduler import TaskDAGScheduler
from core.skill_registry import SkillRegistry
from core.vector_memory import VectorMemoryService
from llm.llm_handler import create_llm_handler

print("=" * 60)
print("测试任务分解功能")
print("=" * 60)

# 初始化组件
event_bus = EventBus()
blackboard = Blackboard()
scheduler = TaskDAGScheduler(event_bus, blackboard)
skill_registry = SkillRegistry()
vector_memory = VectorMemoryService()

# 初始化LLM处理器
try:
    llm_handler = create_llm_handler()
    print("✅ LLM处理器初始化成功")
except Exception as e:
    print(f"❌ LLM处理器初始化失败: {e}")
    llm_handler = None

# 初始化主Agent
main_agent = MainAgent(
    event_bus=event_bus,
    blackboard=blackboard,
    scheduler=scheduler,
    skill_registry=skill_registry,
    vector_memory=vector_memory,
    llm_handler=llm_handler
)

print("✅ 主Agent初始化成功")

# 测试任务分解
test_task = "研究人工智能的发展历程和主要技术突破"
print(f"\n测试任务: {test_task}")

try:
    # 直接调用任务分解
    subtasks = main_agent._decompose_task(test_task, {})
    
    print(f"\n分解结果:")
    print(f"  子任务数量: {len(subtasks)}")
    
    for i, subtask in enumerate(subtasks, 1):
        print(f"\n  [{i}] {subtask.get('name')}")
        print(f"      描述: {subtask.get('description')}")
        print(f"      优先级: {subtask.get('priority')}")
        print(f"      代理角色: {subtask.get('agent_role')}")
        if subtask.get('dependencies'):
            print(f"      依赖: {subtask.get('dependencies')}")
        if subtask.get('payload'):
            print(f"      载荷: {subtask.get('payload')}")
    
    if len(subtasks) == 0:
        print("\n❌ 任务分解失败：没有生成子任务")
    else:
        print(f"\n✅ 任务分解成功，生成了 {len(subtasks)} 个子任务")
        
except Exception as e:
    print(f"\n❌ 任务分解失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)