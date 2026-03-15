#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务事件顺序分析

展示一个任务从创建到完成的完整事件顺序。

作者: Agent OS Team
"""

# 任务事件顺序分析
# ====================

# 阶段1: 任务创建
# ================
# 1. API接收请求
#    POST /api/tasks
#    { "description": "写一份关于AI的报告", "context": {} }

# 2. 主Agent规划任务
#    main_agent.plan_task()

# 3. 创建DAG
#    scheduler.create_dag()
#    → 事件: DAG_UPDATED
#    {
#      "dag_id": "dag_123",
#      "action": "created"
#    }

# 4. 分解任务
#    main_agent._decompose_task()
#    → 生成子任务列表

# 5. 添加任务到DAG
#    scheduler.add_task(dag_id, task)
#    → 事件: TASK_CREATED (每个子任务)
#    {
#      "dag_id": "dag_123",
#      "task_id": "task_1",
#      "task_name": "Execute Task"
#    }

# 6. 添加依赖关系
#    scheduler.add_dependency(dag_id, task_id, depends_on)
#    → 事件: DAG_UPDATED (每个依赖关系)
#    {
#      "dag_id": "dag_123",
#      "action": "dependency_added",
#      "task_id": "task_2",
#      "depends_on": "task_1"
#    }

# 7. 保存到黑板
#    blackboard.save_dag(dag)

# 阶段2: 任务调度
# ================
# 8. 调度器检查就绪任务
#    scheduler._schedule_tasks()
#    → 找到就绪任务 (依赖已满足)

# 9. 启动任务
#    scheduler._start_task(dag_id, task)
#    → 事件: TASK_STARTED
#    {
#      "dag_id": "dag_123",
#      "task_id": "task_1",
#      "task_name": "Execute Task"
#    }

# 阶段3: 任务执行
# ================
# 10. SubAgent接收任务
#     sub_agent_worker._on_task_started(event)
#     → 检查是否可以执行任务

# 11. 任务加入队列
#     sub_agent_worker._task_queue.append(task)

# 12. Agent开始执行
#     sub_agent_worker._execute_task(task)
#     → agent.status = "busy"

# 13. 选择技能
#     sub_agent_worker._select_skill(task)
#     → 找到合适的技能

# 14. 执行技能
#     sub_agent_worker._execute_skill(skill, task)
#     → 调用技能函数

# 15. 生成新任务 (可选)
#     如果技能需要生成子任务
#     → 事件: NEW_TASK_GENERATED
#     {
#       "dag_id": "dag_123",
#       "task": {...}
#     }

# 阶段4: 任务完成
# ================
# 16. 任务执行完成
#     sub_agent_worker._run_task(task)
#     → 返回执行结果

# 17. 发布完成事件
#     sub_agent_worker.event_bus.publish(TASK_COMPLETED)
#     → 事件: TASK_COMPLETED
#     {
#       "task_id": "task_1",
#       "result": {...},
#       "agent_id": "researcher_1"
#     }

# 18. 写入结果到黑板
#     blackboard.write_result(task_id, result, agent_id)
#     → 事件: RESULT_UPDATED
#     {
#       "task_id": "task_1",
#       "agent_id": "researcher_1",
#       "value": {...}
#     }

# 19. 更新知识 (可选)
#     blackboard.write_knowledge(key, value, agent)
#     → 事件: KNOWLEDGE_UPDATED
#     {
#       "key": "research_result",
#       "value": {...},
#       "agent": "researcher_1"
#     }

# 20. 调度器标记任务完成
#     scheduler.complete_task(task_id, result)
#     → 更新DAG状态

# 21. 检查下一个就绪任务
#     scheduler._schedule_tasks()
#     → 如果有就绪任务，重复阶段2-4

# 阶段5: DAG完成 (所有任务完成)
# =============================
# 22. DAG完成
#     dag.is_completed() == True
#     → 所有任务都已完成

# 23. 最终事件
#     → 事件: DAG_UPDATED
#     {
#       "dag_id": "dag_123",
#       "action": "completed"
#     }

# ====================
# 完整事件顺序示例
# ====================

# 假设创建一个包含3个依赖任务的任务：
# task_1 → task_2 → task_3

# 事件时间线:
# ============

# T1: DAG_UPDATED (action: "created")
# T2: TASK_CREATED (task_1)
# T3: TASK_CREATED (task_2)
# T4: TASK_CREATED (task_3)
# T5: DAG_UPDATED (dependency: task_2 depends on task_1)
# T6: DAG_UPDATED (dependency: task_3 depends on task_2)
# T7: TASK_STARTED (task_1)
# T8: TASK_COMPLETED (task_1)
# T9: RESULT_UPDATED (task_1)
# T10: TASK_STARTED (task_2)
# T11: TASK_COMPLETED (task_2)
# T12: RESULT_UPDATED (task_2)
# T13: TASK_STARTED (task_3)
# T14: TASK_COMPLETED (task_3)
# T15: RESULT_UPDATED (task_3)
# T16: DAG_UPDATED (action: "completed")

# ====================
# 错误处理事件
# ====================

# 如果任务执行失败:
# T7: TASK_STARTED (task_1)
# T8: TASK_FAILED (task_1)
# {
#   "task_id": "task_1",
#   "error": "Execution failed: ...",
#   "agent_id": "researcher_1"
# }
# T9: DAG_UPDATED (action: "failed")

# ====================
# 事件订阅者
# ====================

# 订阅TASK_STARTED:
# - SubAgentWorker (接收任务并执行)

# 订阅TASK_COMPLETED:
# - TaskDAGScheduler (标记任务完成，调度下一个任务)
# - Blackboard (更新结果)

# 订阅TASK_FAILED:
# - TaskDAGScheduler (标记任务失败)
# - Blackboard (记录错误)

# 订阅DAG_UPDATED:
# - API Server (通知前端)
# - Dashboard (更新UI)

# 订阅NEW_TASK_GENERATED:
# - SubAgentWorker (接收新任务)

# ====================
# 调试建议
# ====================

# 1. 在事件总线设置断点
#    core/event_bus.py line 82
#    callback(event)

# 2. 使用调试工具
#    python debug_task.py test simple

# 3. 在VSCode中调试
#    - 打开 core/event_bus.py
#    - 在 publish() 方法设置断点
#    - 按 F5 启动调试
#    - 创建任务触发断点

# 4. 查看事件日志
#    curl http://localhost:8001/api/events?limit=100

# 5. 在Dashboard中查看实时事件
#    http://localhost:3050/events

if __name__ == "__main__":
    print("任务事件顺序分析")
    print("=" * 50)
    print("\n查看代码中的详细注释了解完整事件流程")
    print("\n快速开始:")
    print("  python debug_task.py test simple")
    print("  python debug_task.py monitor <dag_id>")
    print("  curl http://localhost:8001/api/events?limit=100")