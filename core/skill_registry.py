#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能注册表

实现动态技能注册和管理。

作者: Agent OS Team
"""

import threading
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

from core.models import Skill, SkillType


class SkillRegistry:
    """
    技能注册表
    
    支持运行时动态注册新技能，无需重启系统。
    """
    
    def __init__(self):
        """初始化技能注册表"""
        self._skills: Dict[str, Skill] = {}
        self._skills_by_type: Dict[SkillType, List[str]] = {
            SkillType.LLM: [],
            SkillType.FUNCTION: [],
            SkillType.API: [],
            SkillType.TOOL: []
        }
        self._skills_by_capability: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
    
    def register(self, skill: Skill) -> None:
        """
        注册技能
        
        Args:
            skill: 技能对象
        """
        with self._lock:
            if skill.id in self._skills:
                raise ValueError(f"Skill {skill.id} already registered")
            
            self._skills[skill.id] = skill
            self._skills_by_type[skill.type].append(skill.id)
            
            for capability in skill.required_capabilities:
                if capability not in self._skills_by_capability:
                    self._skills_by_capability[capability] = []
                self._skills_by_capability[capability].append(skill.id)
            
            print(f"Skill registered: {skill.name} ({skill.type.value})")
    
    def unregister(self, skill_id: str) -> None:
        """
        注销技能
        
        Args:
            skill_id: 技能ID
        """
        with self._lock:
            if skill_id not in self._skills:
                raise ValueError(f"Skill {skill_id} not found")
            
            skill = self._skills[skill_id]
            
            del self._skills[skill_id]
            self._skills_by_type[skill.type].remove(skill_id)
            
            for capability in skill.required_capabilities:
                if capability in self._skills_by_capability:
                    if skill_id in self._skills_by_capability[capability]:
                        self._skills_by_capability[capability].remove(skill_id)
            
            print(f"Skill unregistered: {skill.name}")
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """
        获取技能
        
        Args:
            skill_id: 技能ID
            
        Returns:
            技能对象，如果不存在返回None
        """
        with self._lock:
            return self._skills.get(skill_id)
    
    def get_all_skills(self) -> List[Skill]:
        """
        获取所有技能
        
        Returns:
            技能列表
        """
        with self._lock:
            return list(self._skills.values())
    
    def get_skills_by_type(self, skill_type: SkillType) -> List[Skill]:
        """
        按类型获取技能
        
        Args:
            skill_type: 技能类型
            
        Returns:
            技能列表
        """
        with self._lock:
            skill_ids = self._skills_by_type.get(skill_type, [])
            return [self._skills[sid] for sid in skill_ids if sid in self._skills]
    
    def get_skills_by_capability(self, capability: str) -> List[Skill]:
        """
        按能力获取技能
        
        Args:
            capability: 能力名称
            
        Returns:
            技能列表
        """
        with self._lock:
            skill_ids = self._skills_by_capability.get(capability, [])
            return [self._skills[sid] for sid in skill_ids if sid in self._skills]
    
    def find_best_skill(self, required_capabilities: List[str], 
                      preferred_type: Optional[SkillType] = None) -> Optional[Skill]:
        """
        查找最佳技能
        
        Args:
            required_capabilities: 需要的能力列表
            preferred_type: 偏好的技能类型
            
        Returns:
            最佳技能，如果找不到返回None
        """
        with self._lock:
            candidates = []
            
            for skill_id, skill in self._skills.items():
                if not skill.is_active:
                    continue
                
                has_all_capabilities = all(
                    cap in skill.required_capabilities
                    for cap in required_capabilities
                )
                
                if has_all_capabilities:
                    if preferred_type is None or skill.type == preferred_type:
                        candidates.append(skill)
            
            if not candidates:
                return None
            
            candidates.sort(key=lambda s: len(s.required_capabilities))
            
            return candidates[0] if candidates else None
    
    def execute_skill(self, skill_id: str, **kwargs) -> Any:
        """
        执行技能
        
        Args:
            skill_id: 技能ID
            **kwargs: 执行参数
            
        Returns:
            执行结果
        """
        skill = self.get_skill(skill_id)
        if skill is None:
            raise ValueError(f"Skill {skill_id} not found")
        
        return skill.execute(**kwargs)
    
    def activate_skill(self, skill_id: str) -> None:
        """
        激活技能
        
        Args:
            skill_id: 技能ID
        """
        with self._lock:
            if skill_id in self._skills:
                self._skills[skill_id].is_active = True
    
    def deactivate_skill(self, skill_id: str) -> None:
        """
        停用技能
        
        Args:
            skill_id: 技能ID
        """
        with self._lock:
            if skill_id in self._skills:
                self._skills[skill_id].is_active = False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据
        """
        with self._lock:
            return {
                "total_skills": len(self._skills),
                "active_skills": sum(1 for s in self._skills.values() if s.is_active),
                "by_type": {
                    stype.value: len(self._skills_by_type[stype])
                    for stype in SkillType
                },
                "by_capability": {
                    cap: len(sids)
                    for cap, sids in self._skills_by_capability.items()
                }
            }
    
    def clear(self) -> None:
        """清空技能注册表"""
        with self._lock:
            self._skills.clear()
            for stype in self._skills_by_type:
                self._skills_by_type[stype].clear()
            self._skills_by_capability.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        with self._lock:
            return {
                "skills": [skill.__dict__ for skill in self._skills.values()],
                "statistics": self.get_statistics()
            }


def create_llm_skill(name: str, description: str, model: str,
                   handler: Callable, capabilities: List[str]) -> Skill:
    """
    创建LLM技能
    
    Args:
        name: 技能名称
        description: 描述
        model: 模型名称
        handler: 处理函数
        capabilities: 能力列表
        
    Returns:
        技能对象
    """
    return Skill(
        name=name,
        description=description,
        type=SkillType.LLM,
        handler=handler,
        required_capabilities=capabilities,
        config={"model": model}
    )


def create_function_skill(name: str, description: str, handler: Callable,
                       capabilities: List[str]) -> Skill:
    """
    创建函数技能
    
    Args:
        name: 技能名称
        description: 描述
        handler: 处理函数
        capabilities: 能力列表
        
    Returns:
        技能对象
    """
    return Skill(
        name=name,
        description=description,
        type=SkillType.FUNCTION,
        handler=handler,
        required_capabilities=capabilities
    )


def create_api_skill(name: str, description: str, endpoint: str,
                  method: str = "POST", capabilities: List[str] = None) -> Skill:
    """
    创建API技能
    
    Args:
        name: 技能名称
        description: 描述
        endpoint: API端点
        method: HTTP方法
        capabilities: 能力列表
        
    Returns:
        技能对象
    """
    import requests
    
    def api_handler(**kwargs):
        """API处理函数"""
        url = endpoint
        response = requests.request(method, url, json=kwargs)
        return response.json()
    
    return Skill(
        name=name,
        description=description,
        type=SkillType.API,
        handler=api_handler,
        required_capabilities=capabilities or [],
        config={"endpoint": endpoint, "method": method}
    )


def create_tool_skill(name: str, description: str, tool_path: str,
                   capabilities: List[str]) -> Skill:
    """
    创建工具技能
    
    Args:
        name: 技能名称
        description: 描述
        tool_path: 工具路径
        capabilities: 能力列表
        
    Returns:
        技能对象
    """
    import importlib.util
    
    def tool_handler(**kwargs):
        """工具处理函数"""
        spec = importlib.util.spec_from_file_location("tool", tool_path)
        tool_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool_module)
        
        if hasattr(tool_module, "execute"):
            return tool_module.execute(**kwargs)
        else:
            raise AttributeError(f"Tool {tool_path} has no execute function")
    
    return Skill(
        name=name,
        description=description,
        type=SkillType.TOOL,
        handler=tool_handler,
        required_capabilities=capabilities,
        config={"tool_path": tool_path}
    )