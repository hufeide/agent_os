#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黑板系统

实现共享状态存储，支持多Agent协作。

作者: Agent OS Team
"""

import threading
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.models import Task, DAG, Knowledge, Result, Session, Agent


class Blackboard:
    """
    黑板系统
    
    提供共享状态存储，支持多Agent协作。
    """
    
    def __init__(self):
        """初始化黑板"""
        self._tasks: Dict[str, Task] = {}
        self._knowledge: Dict[str, Knowledge] = {}
        self._results: Dict[str, Result] = {}
        self._sessions: Dict[str, Session] = {}
        self._agents: Dict[str, Agent] = {}
        self._dags: Dict[str, DAG] = {}
        
        self._lock = threading.RLock()
        self._version = 0
    
    def write_task(self, task: Task) -> None:
        """
        写入任务
        
        Args:
            task: 任务对象
        """
        with self._lock:
            self._tasks[task.id] = task
            self._version += 1
    
    def read_task(self, task_id: str) -> Optional[Task]:
        """
        读取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在返回None
        """
        with self._lock:
            return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """
        获取所有任务
        
        Returns:
            任务列表
        """
        with self._lock:
            return list(self._tasks.values())
    
    def write_knowledge(self, key: str, value: Any, agent: str = "system") -> None:
        """
        写入知识
        
        Args:
            key: 知识键
            value: 知识值
            agent: Agent标识
        """
        with self._lock:
            knowledge = Knowledge(
                key=key,
                value=value,
                agent=agent
            )
            self._knowledge[key] = knowledge
            self._version += 1
    
    def read_knowledge(self, key: str) -> Optional[Any]:
        """
        读取知识
        
        Args:
            key: 知识键
            
        Returns:
            知识值，如果不存在返回None
        """
        with self._lock:
            knowledge = self._knowledge.get(key)
            return knowledge.value if knowledge else None
    
    def get_all_knowledge(self) -> List[Knowledge]:
        """
        获取所有知识
        
        Returns:
            知识列表
        """
        with self._lock:
            return list(self._knowledge.values())
    
    def write_result(self, task_id: str, value: Any, agent_id: str) -> None:
        """
        写入结果
        
        Args:
            task_id: 任务ID
            value: 结果值
            agent_id: Agent ID
        """
        with self._lock:
            result = Result(
                task_id=task_id,
                agent_id=agent_id,
                value=value
            )
            self._results[task_id] = result
            self._version += 1
    
    def read_result(self, task_id: str) -> Optional[Result]:
        """
        读取结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            结果对象，如果不存在返回None
        """
        with self._lock:
            return self._results.get(task_id)
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """
        获取任务结果值
        
        Args:
            task_id: 任务ID
            
        Returns:
            结果值，如果不存在返回None
        """
        with self._lock:
            result = self._results.get(task_id)
            return result.value if result else None
    
    def get_all_results(self) -> List[Result]:
        """
        获取所有结果
        
        Returns:
            结果列表
        """
        with self._lock:
            return list(self._results.values())
    
    def create_session(self, session: Session) -> None:
        """
        创建会话
        
        Args:
            session: 会话对象
        """
        with self._lock:
            self._sessions[session.id] = session
            self._version += 1
    
    def read_session(self, session_id: str) -> Optional[Session]:
        """
        读取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话对象，如果不存在返回None
        """
        with self._lock:
            return self._sessions.get(session_id)
    
    def get_all_sessions(self) -> List[Session]:
        """
        获取所有会话
        
        Returns:
            会话列表
        """
        with self._lock:
            return list(self._sessions.values())
    
    def update_session(self, session_id: str, **kwargs) -> None:
        """
        更新会话
        
        Args:
            session_id: 会话ID
            **kwargs: 要更新的字段
        """
        with self._lock:
            if session_id not in self._sessions:
                return
            
            session = self._sessions[session_id]
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            self._version += 1
    
    def register_agent(self, agent: Agent) -> None:
        """
        注册Agent
        
        Args:
            agent: Agent对象
        """
        with self._lock:
            self._agents[agent.id] = agent
            self._version += 1
    
    def unregister_agent(self, agent_id: str) -> None:
        """
        注销Agent
        
        Args:
            agent_id: Agent ID
        """
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                self._version += 1
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        获取Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent对象，如果不存在返回None
        """
        with self._lock:
            return self._agents.get(agent_id)
    
    def get_all_agents(self) -> List[Agent]:
        """
        获取所有Agent
        
        Returns:
            Agent列表
        """
        with self._lock:
            return list(self._agents.values())
    
    def save_dag(self, dag: DAG) -> None:
        """
        保存DAG
        
        Args:
            dag: DAG对象
        """
        with self._lock:
            self._dags[dag.id] = dag
            self._version += 1
    
    def load_dag(self, dag_id: str) -> Optional[DAG]:
        """
        加载DAG
        
        Args:
            dag_id: DAG ID
            
        Returns:
            DAG对象，如果不存在返回None
        """
        with self._lock:
            return self._dags.get(dag_id)
    
    def get_all_dags(self) -> List[DAG]:
        """
        获取所有DAG
        
        Returns:
            DAG列表
        """
        with self._lock:
            return list(self._dags.values())
    
    def get_version(self) -> int:
        """
        获取黑板版本
        
        Returns:
            版本号
        """
        with self._lock:
            return self._version
    
    def clear(self) -> None:
        """清空黑板"""
        with self._lock:
            self._tasks.clear()
            self._knowledge.clear()
            self._results.clear()
            self._sessions.clear()
            self._agents.clear()
            self._dags.clear()
            self._version += 1
    
    def get_snapshot(self) -> Dict[str, Any]:
        """
        获取黑板快照
        
        Returns:
            快照数据
        """
        with self._lock:
            return {
                "version": self._version,
                "tasks": [task.__dict__ for task in self._tasks.values()],
                "knowledge": [
                    {
                        "key": k.key,
                        "value": k.value,
                        "agent": k.agent,
                        "created_at": k.created_at.isoformat()
                    }
                    for k in self._knowledge.values()
                ],
                "results": [
                    {
                        "task_id": r.task_id,
                        "agent_id": r.agent_id,
                        "value": r.value,
                        "created_at": r.created_at.isoformat()
                    }
                    for r in self._results.values()
                ],
                "sessions": [s.__dict__ for s in self._sessions.values()],
                "agents": [a.__dict__ for a in self._agents.values()],
                "dags": [
                    {
                        "id": d.id,
                        "name": d.name,
                        "description": d.description,
                        "task_count": len(d.tasks),
                        "created_at": d.created_at.isoformat()
                    }
                    for d in self._dags.values()
                ],
                "timestamp": datetime.now().isoformat()
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return self.get_snapshot()
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"Blackboard(v={self._version}, tasks={len(self._tasks)}, " \
               f"knowledge={len(self._knowledge)}, agents={len(self._agents)})"