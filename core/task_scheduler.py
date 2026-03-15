#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务DAG调度器

实现动态任务图管理和调度。

作者: Agent OS Team
"""

import threading
import asyncio
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from collections import deque

from core.models import Task, DAG, TaskStatus, TaskPriority, EventType
from core.event_bus import EventBus


class TaskDAGScheduler:
    """
    任务DAG调度器
    
    管理任务之间的依赖关系，控制并行/顺序执行。
    """
    
    def __init__(self, event_bus: EventBus, blackboard=None):
        """
        初始化调度器
        
        Args:
            event_bus: 事件总线
            blackboard: 黑板（可选）
        """
        self.event_bus = event_bus
        self.blackboard = blackboard
        self._dags: Dict[str, DAG] = {}
        self._task_queue: deque = deque()
        self._running_tasks: Dict[str, Task] = {}
        self._lock = threading.RLock()
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._max_concurrent_tasks = 5
        self._task_callbacks: Dict[str, List[Callable]] = {}
        
        self._setup_event_handlers()
    
    def create_dag(self, name: str, description: str = "") -> DAG:
        """
        创建DAG
        
        Args:
            name: DAG名称
            description: 描述
            
        Returns:
            DAG对象
        """
        dag = DAG(name=name, description=description)
        
        with self._lock:
            self._dags[dag.id] = dag
        
        # 发布事件，包含session_id（如果有）
        event_data = {"dag_id": dag.id, "action": "created"}
        if dag.metadata and 'session_id' in dag.metadata:
            event_data['session_id'] = dag.metadata['session_id']
        
        self.event_bus.publish(
            EventType.DAG_UPDATED,
            event_data,
            "scheduler"
        )
        
        return dag
    
    def get_dag(self, dag_id: str) -> Optional[DAG]:
        """
        获取DAG
        
        Args:
            dag_id: DAG ID
            
        Returns:
            DAG对象，如果不存在返回None
        """
        with self._lock:
            return self._dags.get(dag_id)
    
    def add_task(self, dag_id: str, task: Task) -> bool:
        """
        添加任务到DAG
        
        Args:
            dag_id: DAG ID
            task: 任务对象
            
        Returns:
            是否成功
        """
        with self._lock:
            if dag_id not in self._dags:
                return False
            
            dag = self._dags[dag_id]
            dag.add_task(task)
            
            # 发布事件，包含session_id（如果有）
            event_data = {"dag_id": dag_id, "task_id": task.id, "task_name": task.name}
            if dag.metadata and 'session_id' in dag.metadata:
                event_data['session_id'] = dag.metadata['session_id']
            
            self.event_bus.publish(
                EventType.TASK_CREATED,
                event_data,
                "scheduler"
            )
            
            # 更新黑板上的DAG
            if self.blackboard:
                self.blackboard.save_dag(dag)
            
            return True
    
    def add_dependency(self, dag_id: str, task_id: str, depends_on: str) -> bool:
        """
        添加任务依赖关系
        
        Args:
            dag_id: DAG ID
            task_id: 任务ID
            depends_on: 依赖的任务ID
            
        Returns:
            是否成功
        """
        with self._lock:
            if dag_id not in self._dags:
                return False
            
            dag = self._dags[dag_id]
            dag.add_dependency(task_id, depends_on)
            
            # 发布事件，包含session_id（如果有）
            event_data = {"dag_id": dag_id, "action": "dependency_added", 
                        "task_id": task_id, "depends_on": depends_on}
            if dag.metadata and 'session_id' in dag.metadata:
                event_data['session_id'] = dag.metadata['session_id']
            
            self.event_bus.publish(
                EventType.DAG_UPDATED,
                event_data,
                "scheduler"
            )
            
            return True
    
    def start(self) -> None:
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._scheduler_thread.start()
        
        print("TaskDAGScheduler started")
    
    def stop(self) -> None:
        """停止调度器"""
        if not self._running:
            return
        
        self._running = False
        
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        
        print("TaskDAGScheduler stopped")
    
    def _run_scheduler(self) -> None:
        """运行调度器循环"""
        while self._running:
            try:
                self._schedule_tasks()
                self._check_completed_tasks()
                threading.Event().wait(0.1)
            except Exception as e:
                print(f"Scheduler error: {e}")
    
    def _schedule_tasks(self) -> None:
        """调度任务"""
        with self._lock:
            if len(self._running_tasks) >= self._max_concurrent_tasks:
                return
            
            for dag_id, dag in self._dags.items():
                if dag.is_completed():
                    continue
                
                ready_tasks = dag.get_ready_tasks()
                
                for task in ready_tasks:
                    if len(self._running_tasks) >= self._max_concurrent_tasks:
                        break
                    
                    if task.id not in self._running_tasks:
                        self._start_task(dag_id, task)
    
    def _start_task(self, dag_id: str, task: Task) -> None:
        """
        启动任务
        
        Args:
            dag_id: DAG ID
            task: 任务对象
        """
        dag = self._dags[dag_id]
        dag.update_task_status(task.id, TaskStatus.RUNNING)
        
        self._running_tasks[task.id] = task
        
        # 发布事件，包含session_id（如果有）
        event_data = {"dag_id": dag_id, "task_id": task.id, "task_name": task.name}
        if dag.metadata and 'session_id' in dag.metadata:
            event_data['session_id'] = dag.metadata['session_id']
        
        self.event_bus.publish(
            EventType.TASK_STARTED,
            event_data,
            "scheduler"
        )
        
        print(f"Task started: {task.name} ({task.id})")
    
    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None,
                     error: Optional[str] = None) -> None:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            result: 执行结果
            error: 错误信息
        """
        with self._lock:
            if task_id not in self._running_tasks:
                return
            
            task = self._running_tasks[task_id]
            del self._running_tasks[task_id]
            
            for dag_id, dag in self._dags.items():
                if task_id in dag.tasks:
                    if error:
                        dag.update_task_status(task_id, TaskStatus.FAILED, error=error)
                        
                        # 发布事件，包含session_id（如果有）
                        event_data = {"dag_id": dag_id, "task_id": task_id, "error": error}
                        if dag.metadata and 'session_id' in dag.metadata:
                            event_data['session_id'] = dag.metadata['session_id']
                        
                        self.event_bus.publish(
                            EventType.TASK_FAILED,
                            event_data,
                            "scheduler"
                        )
                    else:
                        dag.update_task_status(task_id, TaskStatus.COMPLETED, result=result)
                        
                        # 发布事件，包含session_id（如果有）
                        event_data = {"dag_id": dag_id, "task_id": task_id, "result": result}
                        if dag.metadata and 'session_id' in dag.metadata:
                            event_data['session_id'] = dag.metadata['session_id']
                        
                        self.event_bus.publish(
                            EventType.TASK_COMPLETED,
                            event_data,
                            "scheduler"
                        )
                    
                    if dag.is_completed():
                        print(f"DAG completed: {dag.name} ({dag_id})")
                    
                    break
            
            self._execute_callbacks(task_id, result, error)
    
    def _check_completed_tasks(self) -> None:
        """检查已完成的任务"""
        pass
    
    def register_task_callback(self, task_id: str, callback: Callable) -> None:
        """
        注册任务回调
        
        Args:
            task_id: 任务ID
            callback: 回调函数
        """
        with self._lock:
            if task_id not in self._task_callbacks:
                self._task_callbacks[task_id] = []
            self._task_callbacks[task_id].append(callback)
    
    def _execute_callbacks(self, task_id: str, result: Optional[Dict[str, Any]],
                          error: Optional[str]) -> None:
        """
        执行任务回调
        
        Args:
            task_id: 任务ID
            result: 执行结果
            error: 错误信息
        """
        if task_id not in self._task_callbacks:
            return
        
        for callback in self._task_callbacks[task_id]:
            try:
                callback(task_id, result, error)
            except Exception as e:
                print(f"Task callback error: {e}")
        
        del self._task_callbacks[task_id]
    
    def get_running_tasks(self) -> List[Task]:
        """
        获取正在运行的任务
        
        Returns:
            任务列表
        """
        with self._lock:
            return list(self._running_tasks.values())
    
    def get_dag_status(self, dag_id: str) -> Optional[Dict[str, Any]]:
        """
        获取DAG状态
        
        Args:
            dag_id: DAG ID
            
        Returns:
            状态字典
        """
        with self._lock:
            if dag_id not in self._dags:
                return None
            
            dag = self._dags[dag_id]
            
            ready_tasks = dag.get_ready_tasks()
            running_tasks = list(self._running_tasks.keys())
            
            status_counts = {}
            completed_count = 0
            for task in dag.tasks.values():
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
                if task.status == TaskStatus.COMPLETED:
                    completed_count += 1
            
            return {
                "dag_id": dag_id,
                "name": dag.name,
                "total_tasks": len(dag.tasks),
                "ready_tasks": len(ready_tasks),
                "running_tasks": len(running_tasks),
                "completed_tasks": completed_count,
                "status_counts": status_counts,
                "is_completed": dag.is_completed(),
                "failed_tasks": [t.id for t in dag.get_failed_tasks()]
            }
    
    def set_max_concurrent_tasks(self, max_tasks: int) -> None:
        """
        设置最大并发任务数
        
        Args:
            max_tasks: 最大并发任务数
        """
        with self._lock:
            self._max_concurrent_tasks = max_tasks
    
    def get_all_dags(self) -> List[DAG]:
        """
        获取所有DAG
        
        Returns:
            DAG列表
        """
        with self._lock:
            return list(self._dags.values())
    
    def _setup_event_handlers(self) -> None:
        """设置事件处理器"""
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        self.event_bus.subscribe(EventType.TASK_FAILED, self._on_task_failed)
    
    def _on_task_completed(self, event) -> None:
        """
        任务完成事件处理
        
        Args:
            event: 事件对象
        """
        task_id = event.data.get("task_id")
        result = event.data.get("result")
        
        if task_id:
            self.complete_task(task_id, result=result)
    
    def _on_task_failed(self, event) -> None:
        """
        任务失败事件处理
        
        Args:
            event: 事件对象
        """
        task_id = event.data.get("task_id")
        error = event.data.get("error")
        
        if task_id:
            self.complete_task(task_id, error=error)
    
    def clear(self) -> None:
        """清空所有DAG"""
        with self._lock:
            self._dags.clear()
            self._task_queue.clear()
            self._running_tasks.clear()
            self._task_callbacks.clear()