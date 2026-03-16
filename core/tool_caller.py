#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具调用器

统一的技能和工具调用接口。

作者: Agent OS Team
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    handler: Callable
    parameters: Dict[str, Any]
    category: str = "skill"


class ToolCaller:
    """
    工具调用器
    
    提供统一的技能和工具调用接口。
    """
    
    def __init__(self, skill_registry=None):
        """
        初始化工具调用器
        
        Args:
            skill_registry: 技能注册表
        """
        self.skill_registry = skill_registry
        self._tools: Dict[str, Tool] = {}
        self._tool_categories: Dict[str, List[str]] = {}
        
        if skill_registry:
            self._register_skills()
    
    def _register_skills(self):
        """注册技能为工具"""
        if not self.skill_registry:
            return
        
        skills = self.skill_registry.get_all_skills()
        
        for skill in skills:
            self.register_tool(
                name=skill.name,
                description=skill.description,
                handler=self._create_skill_handler(skill),
                parameters=skill.config or {},
                category="skill"
            )
            
            print(f"[ToolCaller] 注册技能工具: {skill.name}")
    
    def _create_skill_handler(self, skill) -> Callable:
        """
        创建技能处理器
        
        Args:
            skill: 技能对象
            
        Returns:
            处理函数
        """
        def handler(**kwargs):
            try:
                result = skill.handler(**kwargs)
                return {
                    "success": True,
                    "result": result,
                    "tool_name": skill.name
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "tool_name": skill.name
                }
        
        return handler
    
    def register_tool(self, name: str, description: str, 
                   handler: Callable, parameters: Dict[str, Any] = None,
                   category: str = "custom"):
        """
        注册工具
        
        Args:
            name: 工具名称
            description: 工具描述
            handler: 处理函数
            parameters: 参数定义
            category: 工具类别
        """
        tool = Tool(
            name=name,
            description=description,
            handler=handler,
            parameters=parameters or {},
            category=category
        )
        
        self._tools[name] = tool
        
        if category not in self._tool_categories:
            self._tool_categories[category] = []
        self._tool_categories[category].append(name)
        
        print(f"[ToolCaller] 注册工具: {name} (类别: {category})")
    
    def unregister_tool(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功
        """
        if name in self._tools:
            tool = self._tools[name]
            category = tool.category
            
            del self._tools[name]
            
            if category in self._tool_categories and name in self._tool_categories[category]:
                self._tool_categories[category].remove(name)
            
            print(f"[ToolCaller] 注销工具: {name}")
            return True
        
        return False
    
    def call_tool(self, name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        调用工具
        
        Args:
            name: 工具名称
            params: 参数字典
            
        Returns:
            执行结果
        """
        if name not in self._tools:
            return {
                "success": False,
                "error": f"工具不存在: {name}",
                "available_tools": list(self._tools.keys())
            }
        
        tool = self._tools[name]
        
        try:
            print(f"[ToolCaller] 调用工具: {name}")
            print(f"[ToolCaller] 参数: {params}")
            
            result = tool.handler(**(params or {}))
            
            print(f"[ToolCaller] 工具结果: {str(result)[:100]}...")
            
            if isinstance(result, dict) and 'success' in result:
                return result
            else:
                return {
                    "success": True,
                    "result": result,
                    "tool_name": name
                }
                
        except Exception as e:
            print(f"[ToolCaller] 工具调用失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": name
            }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        获取所有可用工具
        
        Returns:
            工具列表
        """
        return [
            {
                "name": name,
                "description": tool.description,
                "parameters": tool.parameters,
                "category": tool.category
            }
            for name, tool in self._tools.items()
        ]
    
    def get_tools_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        按类别获取工具
        
        Args:
            category: 工具类别
            
        Returns:
            工具列表
        """
        tool_names = self._tool_categories.get(category, [])
        
        return [
            {
                "name": name,
                "description": self._tools[name].description,
                "parameters": self._tools[name].parameters,
                "category": category
            }
            for name in tool_names
            if name in self._tools
        ]
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具对象，如果不存在返回None
        """
        return self._tools.get(name)
    
    def has_tool(self, name: str) -> bool:
        """
        检查工具是否存在
        
        Args:
            name: 工具名称
            
        Returns:
            是否存在
        """
        return name in self._tools
    
    def get_categories(self) -> List[str]:
        """
        获取所有工具类别
        
        Returns:
            类别列表
        """
        return list(self._tool_categories.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据
        """
        return {
            "total_tools": len(self._tools),
            "categories": {
                category: len(tools)
                for category, tools in self._tool_categories.items()
            },
            "tool_names": list(self._tools.keys())
        }
    
    def clear_tools(self, category: Optional[str] = None):
        """
        清空工具
        
        Args:
            category: 工具类别，如果为None则清空所有
        """
        if category:
            tool_names = self._tool_categories.get(category, [])
            for name in tool_names:
                if name in self._tools:
                    del self._tools[name]
            self._tool_categories[category] = []
            print(f"[ToolCaller] 清空类别工具: {category}")
        else:
            self._tools.clear()
            self._tool_categories.clear()
            print(f"[ToolCaller] 清空所有工具")
    
    def reload_skills(self):
        """重新加载技能"""
        self._tools.clear()
        self._tool_categories.clear()
        self._register_skills()
        print(f"[ToolCaller] 重新加载技能，共 {len(self._tools)} 个工具")