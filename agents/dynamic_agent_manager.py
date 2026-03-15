#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态Agent管理器

根据任务需求动态创建和管理Agent。

作者: Agent OS Team
"""

import threading
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.event_bus import EventBus
from core.blackboard import Blackboard
from core.skill_registry import SkillRegistry
from core.vector_memory import VectorMemoryService
from agents.sub_agent_worker import SubAgentWorker
from llm.llm_handler import LLMHandler


class DynamicAgentManager:
    """
    动态Agent管理器
    
    根据任务需求动态创建和管理Agent，支持任意角色的Agent。
    """
    
    def __init__(self, event_bus: EventBus, blackboard: Blackboard,
                 skill_registry: SkillRegistry, vector_memory: VectorMemoryService,
                 llm_handler: LLMHandler, scheduler):
        """
        初始化Agent管理器
        
        Args:
            event_bus: 事件总线
            blackboard: 黑板
            skill_registry: 技能注册表
            vector_memory: 向量记忆服务
            llm_handler: LLM处理器
            scheduler: 任务调度器
        """
        self.event_bus = event_bus
        self.blackboard = blackboard
        self.skill_registry = skill_registry
        self.vector_memory = vector_memory
        self.llm_handler = llm_handler
        self.scheduler = scheduler
        
        self._agents: Dict[str, SubAgentWorker] = {}
        self._lock = threading.RLock()
        
        # 角色能力映射
        self._role_capabilities = {
            "researcher": ["research"],
            "analyst": ["analysis"],
            "writer": ["writing"],
            "developer": ["development", "coding", "programming"],
            "devops": ["deployment", "operations", "infrastructure"],
            "tester": ["testing", "quality_assurance"],
            "designer": ["design", "ui_ux"],
            "manager": ["management", "planning"],
            "architect": ["architecture", "system_design"]
        }
    
    def create_agent(self, agent_role: str, agent_id: Optional[str] = None) -> SubAgentWorker:
        """
        创建指定角色的Agent
        
        Args:
            agent_role: Agent角色
            agent_id: Agent ID（可选，自动生成）
            
        Returns:
            创建的Agent
        """
        if agent_id is None:
            agent_id = f"{agent_role}_{len([a for a in self._agents.values() if a.agent_role == agent_role]) + 1}"
        
        # 获取角色对应的能力
        capabilities = self._role_capabilities.get(agent_role.lower(), [agent_role.lower()])
        
        # 创建Agent
        agent = SubAgentWorker(
            agent_id=agent_id,
            agent_role=agent_role,
            capabilities=capabilities,
            event_bus=self.event_bus,
            blackboard=self.blackboard,
            skill_registry=self.skill_registry,
            vector_memory=self.vector_memory,
            llm_handler=self.llm_handler,
            scheduler=self.scheduler
        )
        
        # 启动Agent
        agent.start()
        
        with self._lock:
            self._agents[agent_id] = agent
        
        print(f"[动态Agent] 创建新Agent: {agent_id} (角色: {agent_role}, 能力: {capabilities})")
        
        return agent
    
    def get_or_create_agent(self, agent_role: str) -> SubAgentWorker:
        """
        获取或创建指定角色的Agent
        
        Args:
            agent_role: Agent角色
            
        Returns:
            Agent对象
        """
        with self._lock:
            # 查找现有的Agent
            for agent_id, agent in self._agents.items():
                if agent.agent_role.lower() == agent_role.lower():
                    return agent
            
            # 如果没有找到，创建新的
            return self.create_agent(agent_role)
    
    def get_agent_by_id(self, agent_id: str) -> Optional[SubAgentWorker]:
        """
        根据ID获取Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent对象，如果不存在返回None
        """
        with self._lock:
            return self._agents.get(agent_id)
    
    def get_agents_by_role(self, agent_role: str) -> List[SubAgentWorker]:
        """
        根据角色获取所有Agent
        
        Args:
            agent_role: Agent角色
            
        Returns:
            Agent列表
        """
        with self._lock:
            return [
                agent for agent_id, agent in self._agents.items()
                if agent.agent_role.lower() == agent_role.lower()
            ]
    
    def get_all_agents(self) -> List[SubAgentWorker]:
        """
        获取所有Agent
        
        Returns:
            Agent列表
        """
        with self._lock:
            return list(self._agents.values())
    
    def remove_agent(self, agent_id: str) -> bool:
        """
        移除Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if agent_id in self._agents:
                agent = self._agents[agent_id]
                agent.stop()
                del self._agents[agent_id]
                print(f"[动态Agent] 移除Agent: {agent_id}")
                return True
            return False
    
    def stop_all_agents(self):
        """停止所有Agent"""
        with self._lock:
            for agent_id, agent in self._agents.items():
                agent.stop()
            self._agents.clear()
            print(f"[动态Agent] 停止所有Agent")
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """
        获取Agent统计信息
        
        Returns:
            统计信息字典
        """
        with self._lock:
            role_counts = {}
            for agent in self._agents.values():
                role = agent.agent_role
                role_counts[role] = role_counts.get(role, 0) + 1
            
            return {
                "total_agents": len(self._agents),
                "role_counts": role_counts,
                "agent_ids": list(self._agents.keys())
            }