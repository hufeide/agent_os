#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务调度调试工具

调试任务调度和执行问题。

作者: Agent OS Team
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.event_bus import EventBus
from core.blackboard import Blackboard
from core.task_scheduler import TaskDAGScheduler
from core.skill_registry import SkillRegistry
from core.vector_memory import VectorMemoryService
from core.models import Task, TaskPriority, TaskStatus
from llm.llm_handler import create_llm_handler


def debug_scheduler():
    """调试调度器"""
    
    print("=" * 60)
    print("任务调度调试")
    print("=" * 60)
    
    event_bus = EventBus()
    blackboard = Blackboard()
    scheduler = TaskDAGScheduler(event_bus)
    
    print("\n[1/5] 创建测试DAG...")
    dag = scheduler.create_dag("测试DAG", "用于调试的DAG")
    print(f"✓ DAG创建成功: {dag.id}")
    
    print("\n[2/5] 添加测试任务...")
    task1 = Task(
        name="任务1",
        description="第一个测试任务",
        priority=TaskPriority.MEDIUM,
        agent_role="researcher"
    )
    
    task2 = Task(
        name="任务2", 
        description="第二个测试任务",
        priority=TaskPriority.MEDIUM,
        agent_role="analyst"
    )
    
    scheduler.add_task(dag.id, task1)
    scheduler.add_task(dag.id, task2)
    print(f"✓ 已添加2个任务")
    
    print("\n[3/5] 检查DAG状态...")
    dag_status = scheduler.get_dag_status(dag.id)
    print(f"DAG ID: {dag_status['dag_id']}")
    print(f"总任务数: {dag_status['total_tasks']}")
    print(f"就绪任务数: {dag_status['ready_tasks']}")
    print(f"运行中任务数: {dag_status['running_tasks']}")
    print(f"已完成任务数: {dag_status['completed_tasks']}")
    
    print("\n[4/5] 检查就绪任务...")
    ready_tasks = dag.get_ready_tasks()
    print(f"就绪任务: {len(ready_tasks)}")
    for task in ready_tasks:
        print(f"  - {task.name} ({task.id})")
        print(f"    状态: {task.status.value}")
        print(f"    依赖: {task.dependencies}")
        print(f"    Agent角色: {task.agent_role}")
    
    print("\n[5/5] 启动调度器...")
    scheduler.start()
    print("✓ 调度器已启动")
    
    print("\n等待任务调度...")
    for i in range(10):
        time.sleep(1)
        dag_status = scheduler.get_dag_status(dag.id)
        print(f"[{i+1}s] 就绪: {dag_status['ready_tasks']}, 运行中: {dag_status['running_tasks']}, 完成: {dag_status['completed_tasks']}")
        
        if dag_status['completed_tasks'] > 0:
            print("\n✓ 任务已开始执行！")
            break
    
    print("\n最终状态:")
    dag_status = scheduler.get_dag_status(dag.id)
    print(f"就绪任务数: {dag_status['ready_tasks']}")
    print(f"运行中任务数: {dag_status['running_tasks']}")
    print(f"已完成任务数: {dag_status['completed_tasks']}")
    
    scheduler.stop()
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)


def debug_task_creation():
    """调试任务创建流程"""
    
    print("=" * 60)
    print("任务创建流程调试")
    print("=" * 60)
    
    event_bus = EventBus()
    blackboard = Blackboard()
    scheduler = TaskDAGScheduler(event_bus)
    
    print("\n[1/4] 订阅事件...")
    events_received = []
    
    def on_task_created(event):
        events_received.append(("TASK_CREATED", event.data))
        print(f"  ✓ TASK_CREATED: {event.data.get('task_name')}")
    
    def on_task_started(event):
        events_received.append(("TASK_STARTED", event.data))
        print(f"  ✓ TASK_STARTED: {event.data.get('task_name')}")
    
    def on_dag_updated(event):
        events_received.append(("DAG_UPDATED", event.data))
        print(f"  ✓ DAG_UPDATED: {event.data.get('action')}")
    
    event_bus.subscribe("task_created", on_task_created)
    event_bus.subscribe("task_started", on_task_started)
    event_bus.subscribe("dag_updated", on_dag_updated)
    
    print("✓ 已订阅事件")
    
    print("\n[2/4] 创建DAG和任务...")
    dag = scheduler.create_dag("测试DAG", "用于调试的DAG")
    task = Task(
        name="测试任务",
        description="测试任务描述",
        priority=TaskPriority.MEDIUM,
        agent_role="researcher"
    )
    scheduler.add_task(dag.id, task)
    print("✓ DAG和任务已创建")
    
    print("\n[3/4] 检查事件...")
    print(f"接收到的事件数: {len(events_received)}")
    for event_type, event_data in events_received:
        print(f"  - {event_type}: {event_data}")
    
    print("\n[4/4] 检查任务状态...")
    dag_obj = scheduler.get_dag(dag.id)
    if dag_obj:
        task_obj = dag_obj.get_task(task.id)
        if task_obj:
            print(f"任务ID: {task_obj.id}")
            print(f"任务名称: {task_obj.name}")
            print(f"任务状态: {task_obj.status.value}")
            print(f"任务依赖: {task_obj.dependencies}")
            print(f"任务Agent角色: {task_obj.agent_role}")
        else:
            print("✗ 任务未找到")
    else:
        print("✗ DAG未找到")
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "scheduler":
            debug_scheduler()
        elif command == "creation":
            debug_task_creation()
        else:
            print(f"未知命令: {command}")
            print("可用命令: scheduler, creation")
    else:
        print("任务调度调试工具")
        print("\n使用方法:")
        print("  python debug_scheduler.py scheduler  - 调试调度器")
        print("  python debug_scheduler.py creation  - 调试任务创建")