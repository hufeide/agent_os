#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心数据模型

定义主从分层Agent系统的核心数据模型。

作者: Agent OS Team
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import uuid


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class EventType(Enum):
    """事件类型枚举"""
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    DAG_UPDATED = "dag_updated"
    NEW_TASK_GENERATED = "new_task_generated"
    AGENT_REGISTERED = "agent_registered"
    AGENT_UNREGISTERED = "agent_unregistered"
    SKILL_REGISTERED = "skill_registered"
    SKILL_UNREGISTERED = "skill_unregistered"
    KNOWLEDGE_UPDATED = "knowledge_updated"
    RESULT_UPDATED = "result_updated"


class SkillType(Enum):
    """技能类型枚举"""
    LLM = "llm"
    FUNCTION = "function"
    API = "api"
    TOOL = "tool"


@dataclass
class Task:
    """
    任务模型

    表示系统中的一个任务，支持动态DAG。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    
    agent_role: Optional[str] = None
    agent_id: Optional[str] = None
    
    payload: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    retry_count: int = 0
    max_retries: int = 3
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DAG:
    """
    动态任务DAG

    管理任务之间的依赖关系，支持动态修改。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    tasks: Dict[str, Task] = field(default_factory=dict)
    root_tasks: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据，用于存储session_id等信息
    
    def add_task(self, task: Task) -> None:
        """
        添加任务到DAG
        
        Args:
            task: 要添加的任务
        """
        self.tasks[task.id] = task
        
        if not task.dependencies:
            self.root_tasks.append(task.id)
        
        self.updated_at = datetime.now()
    
    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """
        添加任务依赖关系
        
        Args:
            task_id: 任务ID
            depends_on: 依赖的任务ID
        """
        if task_id not in self.tasks or depends_on not in self.tasks:
            return
        
        task = self.tasks[task_id]
        if depends_on not in task.dependencies:
            task.dependencies.append(depends_on)
        
        dependent_task = self.tasks[depends_on]
        if task_id not in dependent_task.dependents:
            dependent_task.dependents.append(task_id)
        
        if task_id in self.root_tasks:
            self.root_tasks.remove(task_id)
        
        self.updated_at = datetime.now()
    
    def get_ready_tasks(self) -> List[Task]:
        """
        获取可以执行的任务（所有依赖都已完成）
        
        Returns:
            可执行的任务列表
        """
        ready_tasks = []
        
        print(f"[DAG] Checking ready tasks in DAG {self.name}")
        print(f"[DAG] Total tasks: {len(self.tasks)}")
        
        for task_id, task in self.tasks.items():
            print(f"[DAG] Task {task.name} (ID: {task_id}): status={task.status}, deps={len(task.dependencies)}")
            if task.status == TaskStatus.PENDING:
                all_deps_completed = all(
                    self.tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                    if dep_id in self.tasks
                )
                print(f"[DAG] Task {task.name}: all_deps_completed={all_deps_completed}")
                if all_deps_completed:
                    ready_tasks.append(task)
        
        print(f"[DAG] Ready tasks count: {len(ready_tasks)}")
        return ready_tasks
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取指定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在返回None
        """
        return self.tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                        result: Optional[Dict[str, Any]] = None,
                        error: Optional[str] = None) -> None:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            result: 执行结果
            error: 错误信息
        """
        if task_id not in self.tasks:
            print(f"[DAG] update_task_status: Task {task_id} not found in DAG")
            return
        
        task = self.tasks[task_id]
        print(f"[DAG] update_task_status: Task {task.name} ({task_id}): {task.status} -> {status}")
        task.status = status
        
        if status == TaskStatus.RUNNING:
            task.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now()
        
        if result is not None:
            task.result = result
        if error is not None:
            task.error = error
        
        self.updated_at = datetime.now()
    
    def is_completed(self) -> bool:
        """
        检查DAG是否全部完成
        
        Returns:
            是否所有任务都已完成
        """
        # 如果没有任务，则不算完成
        if not self.tasks:
            return False
        
        # 只有当有任务且所有任务都完成时才算完成
        return all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            for task in self.tasks.values()
        )
    
    def get_failed_tasks(self) -> List[Task]:
        """
        获取失败的任务
        
        Returns:
            失败的任务列表
        """
        return [
            task for task in self.tasks.values()
            if task.status == TaskStatus.FAILED
        ]


@dataclass
class Event:
    """
    事件模型
    
    用于事件总线通信。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.TASK_CREATED
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        timestamp_str = None
        if self.timestamp:
            try:
                timestamp_str = self.timestamp.isoformat()
            except Exception as e:
                print(f"时间格式化错误: {e}")
                timestamp_str = None
        
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "source": self.source,
            "timestamp": timestamp_str
        }


@dataclass
class Skill:
    """
    技能模型
    
    表示Agent可以调用的技能。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    type: SkillType = SkillType.FUNCTION
    
    handler: Optional[Callable] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    required_capabilities: List[str] = field(default_factory=list)
    output_schema: Optional[Dict[str, Any]] = None
    
    registered_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def execute(self, **kwargs) -> Any:
        """
        执行技能
        
        Args:
            **kwargs: 执行参数
            
        Returns:
            执行结果
        """
        if self.handler is None:
            raise RuntimeError(f"Skill {self.name} has no handler")
        
        return self.handler(**kwargs)


@dataclass
class Agent:
    """
    Agent模型
    
    表示系统中的Agent。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    role: str = ""
    type: str = "sub"  # "main" or "sub"
    
    capabilities: List[str] = field(default_factory=list)
    registered_skills: List[str] = field(default_factory=list)
    
    status: str = "idle"  # idle, busy, error
    current_task_id: Optional[str] = None
    
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: Optional[datetime] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_available(self) -> bool:
        """
        检查Agent是否可用
        
        Returns:
            是否可用
        """
        return self.status == "idle"
    
    def can_execute_task(self, task: Task) -> bool:
        """
        检查Agent是否可以执行任务
        
        Args:
            task: 任务对象
            
        Returns:
            是否可以执行
        """
        if not self.is_available():
            return False
        
        if task.agent_role and task.agent_role != self.role:
            return False
        
        if task.agent_id and task.agent_id != self.id:
            return False
        
        return True


@dataclass
class Knowledge:
    """
    知识模型
    
    存储在黑板中的知识。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    value: Any = None
    agent: str = ""
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Result:
    """
    结果模型
    
    存储任务执行结果。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    agent_id: str = ""
    value: Any = None
    
    created_at: datetime = field(default_factory=datetime.now)
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """
    会话模型
    
    跟踪Agent执行会话。
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    task_id: str = ""
    
    status: str = "pending"
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    llm_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)