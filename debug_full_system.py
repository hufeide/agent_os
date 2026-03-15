#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整系统调试工具

调试整个Agent OS系统的运行状态。

作者: Agent OS Team
"""

import sys
import os
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.event_bus import EventBus
from core.blackboard import Blackboard
from core.task_scheduler import TaskDAGScheduler
from core.skill_registry import SkillRegistry
from core.vector_memory import VectorMemoryService
from core.models import Task, TaskPriority, TaskStatus, EventType
from llm.llm_handler import create_llm_handler
from agents.sub_agent_worker import SubAgentWorker


def create_sample_skills(skill_registry):
    """创建示例技能"""
    from core.skill_registry import create_function_skill
    
    def research_skill(**kwargs):
        return {"research_result": f"Research completed: {kwargs.get('topic', 'unknown')}"}
    
    research = create_function_skill(
        name="Research",
        description="Research skill for gathering information",
        handler=research_skill,
        capabilities=["research"]
    )
    
    skill_registry.register(research)


def debug_full_system():
    """调试完整系统"""
    
    print("=" * 60)
    print("完整系统调试")
    print("=" * 60)
    
    event_bus = EventBus()
    blackboard = Blackboard()
    scheduler = TaskDAGScheduler(event_bus, blackboard)
    skill_registry = SkillRegistry()
    vector_memory = VectorMemoryService()
    
    print("\n[1/8] 创建示例技能...")
    create_sample_skills(skill_registry)
    print(f"✓ 已注册 {len(skill_registry.get_all_skills())} 个技能")
    
    print("\n[2/8] 创建LLM处理器...")
    llm_handler = create_llm_handler(
        api_url="http://192.168.1.159:21000",
        model_name="Qwen3Coder"
    )
    print(f"✓ LLM处理器已创建")
    
    print("\n[3/8] 创建子Agent Worker...")
    researcher = SubAgentWorker(
        agent_id="researcher_1",
        agent_role="researcher",
        capabilities=["research"],
        event_bus=event_bus,
        blackboard=blackboard,
        skill_registry=skill_registry,
        vector_memory=vector_memory,
        llm_handler=llm_handler
    )
    print("✓ 子Agent Worker已创建")
    
    print("\n[4/8] 启动任务调度器...")
    scheduler.start()
    print("✓ 任务调度器已启动")
    
    print("\n[5/8] 启动子Agent Worker...")
    researcher.start()
    print("✓ 子Agent Worker已启动")
    
    print("\n[6/8] 订阅事件...")
    events_log = []
    
    def log_event(event_type_name):
        def handler(event):
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            events_log.append((timestamp, event_type_name, event.data))
            print(f"[{timestamp}] {event_type_name}: {event.data}")
        return handler
    
    event_bus.subscribe(EventType.DAG_UPDATED, log_event("DAG_UPDATED"))
    event_bus.subscribe(EventType.TASK_CREATED, log_event("TASK_CREATED"))
    event_bus.subscribe(EventType.TASK_STARTED, log_event("TASK_STARTED"))
    event_bus.subscribe(EventType.TASK_COMPLETED, log_event("TASK_COMPLETED"))
    event_bus.subscribe(EventType.AGENT_REGISTERED, log_event("AGENT_REGISTERED"))
    
    print("✓ 已订阅事件")
    
    print("\n[7/8] 创建测试DAG和任务...")
    dag = scheduler.create_dag("测试DAG", "用于完整系统测试")
    task = Task(
        name="测试任务",
        description="测试任务执行流程",
        priority=TaskPriority.MEDIUM,
        agent_role="researcher"
    )
    
    scheduler.add_task(dag.id, task)
    print(f"✓ DAG和任务已创建: {dag.id}")
    
    print("\n[8/8] 监控任务执行...")
    print("等待任务执行...")
    
    for i in range(20):
        time.sleep(1)
        
        dag_status = scheduler.get_dag_status(dag.id)
        print(f"[{i+1}s] 就绪: {dag_status['ready_tasks']}, 运行中: {dag_status['running_tasks']}, 完成: {dag_status['completed_tasks']}")
        
        if dag_status['completed_tasks'] > 0:
            print("\n✓ 任务已完成！")
            break
        
        if i == 10 and dag_status['ready_tasks'] > 0:
            print("\n⚠ 警告: 任务就绪但未执行")
            print("检查调度器状态...")
            print(f"调度器运行中: {scheduler._running}")
            print(f"运行中任务数: {len(scheduler._running_tasks)}")
            print(f"最大并发任务数: {scheduler._max_concurrent_tasks}")
    
    print("\n" + "=" * 60)
    print("事件日志:")
    print("=" * 60)
    for timestamp, event_type, data in events_log:
        print(f"[{timestamp}] {event_type}")
        for key, value in data.items():
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("最终DAG状态:")
    print("=" * 60)
    dag_status = scheduler.get_dag_status(dag.id)
    for key, value in dag_status.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 60)
    print("Agent状态:")
    print("=" * 60)
    print(f"Agent ID: {researcher.agent_id}")
    print(f"Agent角色: {researcher.agent_role}")
    print(f"Agent状态: {researcher.agent.status}")
    print(f"当前任务: {researcher.agent.current_task_id}")
    print(f"任务队列: {len(researcher._task_queue)}")
    
    print("\n停止系统...")
    researcher.stop()
    scheduler.stop()
    print("✓ 系统已停止")


if __name__ == "__main__":
    from datetime import datetime
    
    success = debug_full_system()
    sys.exit(0 if success else 1)