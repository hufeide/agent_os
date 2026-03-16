#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查DAG对象

测试DAG对象的属性。

作者: Agent OS Team
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.models import DAG, Task, TaskStatus


def test_dag_object():
    """测试DAG对象"""
    print("=" * 60)
    print("测试DAG对象")
    print("=" * 60)
    
    # 创建一个DAG
    dag = DAG(
        name="测试DAG",
        description="这是一个测试DAG"
    )
    
    print(f"\nDAG ID: {dag.id}")
    print(f"DAG名称: {dag.name}")
    print(f"DAG描述: {dag.description}")
    
    # 添加一个任务
    task = Task(
        name="测试任务",
        description="这是一个测试任务"
    )
    dag.add_task(task)
    
    print(f"\n任务数量: {len(dag.tasks)}")
    print(f"任务列表: {dag.tasks}")
    
    # 检查tasks属性
    print(f"\ntasks类型: {type(dag.tasks)}")
    print(f"tasks值: {dag.tasks}")
    
    # 测试len()
    try:
        tasks_len = len(dag.tasks)
        print(f"len(dag.tasks) = {tasks_len}")
    except Exception as e:
        print(f"len(dag.tasks) 失败: {e}")
    
    # 测试迭代
    try:
        for task_id, task in dag.tasks.items():
            print(f"  任务ID: {task_id}, 任务名: {task.name}")
    except Exception as e:
        print(f"迭代tasks失败: {e}")
    
    # 测试values()
    try:
        tasks_values = list(dag.tasks.values())
        print(f"\ntasks.values() 类型: {type(tasks_values)}")
        print(f"tasks.values() 长度: {len(tasks_values)}")
    except Exception as e:
        print(f"tasks.values() 失败: {e}")
    
    print("\n✅ DAG对象测试完成")


if __name__ == "__main__":
    try:
        test_dag_object()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)