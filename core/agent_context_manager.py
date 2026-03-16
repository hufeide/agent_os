#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent上下文管理器

管理Agent的身份MD文件和上下文状态。

作者: Agent OS Team
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class AgentContextManager:
    """
    Agent上下文管理器
    
    负责管理Agent的MD文件和上下文状态。
    """
    
    def __init__(self, agent_id: str, agent_role: str, 
                 capabilities: List[str], context_dir: str = "agent_contexts"):
        """
        初始化上下文管理器
        
        Args:
            agent_id: Agent ID
            agent_role: Agent角色
            capabilities: 能力列表
            context_dir: 上下文文件目录
        """
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.capabilities = capabilities
        self.context_dir = Path(context_dir)
        self.context_dir.mkdir(exist_ok=True)
        
        self.md_file_path = self.context_dir / f"{agent_id}.md"
        self.json_file_path = self.context_dir / f"{agent_id}.json"
        
        self._context: Dict[str, Any] = {
            "agent_id": agent_id,
            "agent_role": agent_role,
            "capabilities": capabilities,
            "created_at": datetime.now().isoformat(),
            "status": "idle",
            "primary_goal": self._get_default_goal(agent_role),
            "decision_rules": self._get_default_rules(agent_role),
            "constraints": [],
            "success_criteria": self._get_default_criteria(agent_role),
            "skills": [],
            "tools": [],
            "task_history": [],
            "experience_summary": "",
            "current_task": None,
            "working_memory": [],
            "pending_items": []
        }
        
        self._initialize_context_files()
    
    def _get_default_goal(self, role: str) -> str:
        """获取角色的默认目标"""
        goals = {
            "researcher": "收集和分析信息，提供准确的研究结果",
            "analyst": "分析数据和问题，提供有价值的洞察",
            "writer": "创作高质量的内容，满足用户需求",
            "developer": "开发和维护代码，确保功能正确",
            "tester": "测试系统，发现和报告问题",
            "designer": "设计用户界面和用户体验",
            "manager": "协调资源，确保项目成功",
            "architect": "设计系统架构，确保可扩展性"
        }
        return goals.get(role.lower(), f"作为{role}角色，完成相关任务")
    
    def _get_default_rules(self, role: str) -> List[str]:
        """获取角色的默认决策规则"""
        rules = {
            "researcher": [
                "优先使用可靠的信息源",
                "验证信息的准确性",
                "提供具体的数据和证据",
                "避免主观臆断"
            ],
            "analyst": [
                "基于数据进行分析",
                "识别关键模式和趋势",
                "提供可操作的建议",
                "考虑多种可能性"
            ],
            "writer": [
                "确保内容清晰易懂",
                "符合目标受众的需求",
                "保持逻辑连贯",
                "使用恰当的语气和风格"
            ],
            "developer": [
                "遵循最佳实践",
                "确保代码质量",
                "考虑性能和可维护性",
                "进行适当的测试"
            ]
        }
        return rules.get(role.lower(), [
            "基于角色能力执行任务",
            "确保结果质量",
            "及时完成任务",
            "主动沟通问题"
        ])
    
    def _get_default_criteria(self, role: str) -> List[str]:
        """获取角色的默认成功标准"""
        criteria = {
            "researcher": [
                "信息准确可靠",
                "覆盖了所有关键方面",
                "提供了有价值的洞察",
                "格式清晰易读"
            ],
            "analyst": [
                "分析深入透彻",
                "发现了重要模式",
                "建议切实可行",
                "结论有数据支持"
            ],
            "writer": [
                "内容完整准确",
                "语言流畅自然",
                "结构清晰合理",
                "满足用户需求"
            ],
            "developer": [
                "功能正确实现",
                "代码质量良好",
                "性能满足要求",
                "通过相关测试"
            ]
        }
        return criteria.get(role.lower(), [
            "任务完成",
            "结果质量良好",
            "符合预期要求",
            "按时交付"
        ])
    
    def _initialize_context_files(self):
        """初始化上下文文件"""
        if not self.md_file_path.exists():
            self._write_md_file()
        
        if not self.json_file_path.exists():
            self._write_json_file()
    
    def _write_md_file(self):
        """写入MD文件"""
        content = self._generate_md_content()
        with open(self.md_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _write_json_file(self):
        """写入JSON文件"""
        with open(self.json_file_path, 'w', encoding='utf-8') as f:
            json.dump(self._context, f, ensure_ascii=False, indent=2)
    
    def _generate_md_content(self) -> str:
        """生成MD文件内容"""
        ctx = self._context
        
        content = f"""# Agent: {ctx['agent_id']}

## 基本信息
- **Agent ID**: {ctx['agent_id']}
- **角色**: {ctx['agent_role']}
- **能力**: {', '.join(ctx['capabilities'])}
- **创建时间**: {ctx['created_at']}
- **状态**: {ctx['status']}

## 目标和约束
- **主要目标**: {ctx['primary_goal']}

### 决策规则
"""
        for i, rule in enumerate(ctx['decision_rules'], 1):
            content += f"{i}. {rule}\n"
        
        content += """
### 约束条件
"""
        for i, constraint in enumerate(ctx['constraints'], 1):
            content += f"{i}. {constraint}\n"
        
        if not ctx['constraints']:
            content += "无特殊约束\n"
        
        content += """
### 成功标准
"""
        for i, criteria in enumerate(ctx['success_criteria'], 1):
            content += f"{i}. {criteria}\n"
        
        content += """
## 技能和工具清单
### 可用技能
"""
        for skill in ctx['skills']:
            content += f"- **{skill.get('name', 'Unknown')}**: {skill.get('description', 'No description')}\n"
        
        if not ctx['skills']:
            content += "暂无注册技能\n"
        
        content += """
### 可用工具
"""
        for tool in ctx['tools']:
            content += f"- **{tool.get('name', 'Unknown')}**: {tool.get('description', 'No description')}\n"
        
        if not ctx['tools']:
            content += "暂无可用工具\n"
        
        content += """
## 执行历史
### 最近任务
"""
        if ctx['task_history']:
            for i, task in enumerate(ctx['task_history'][-10:], 1):
                content += f"{i}. [{task.get('timestamp', 'Unknown')}] {task.get('task_name', 'Unknown')} - {task.get('status', 'Unknown')}\n"
        else:
            content += "暂无任务历史\n"
        
        content += """
### 经验总结
"""
        content += ctx['experience_summary'] or "暂无经验总结\n"
        
        content += """
## 上下文状态
### 当前任务
"""
        if ctx['current_task']:
            task = ctx['current_task']
            content += f"""- **任务名称**: {task.get('name', 'Unknown')}
- **任务描述**: {task.get('description', 'Unknown')}
- **开始时间**: {task.get('started_at', 'Unknown')}
- **状态**: {task.get('status', 'Unknown')}
"""
        else:
            content += "当前无任务\n"
        
        content += """
### 工作记忆
"""
        for i, item in enumerate(ctx['working_memory'][-10:], 1):
            content += f"{i}. {item}\n"
        
        if not ctx['working_memory']:
            content += "工作记忆为空\n"
        
        content += """
### 待处理事项
"""
        for i, item in enumerate(ctx['pending_items'], 1):
            content += f"{i}. {item}\n"
        
        if not ctx['pending_items']:
            content += "无待处理事项\n"
        
        content += f"""
---
*最后更新: {datetime.now().isoformat()}*
"""
        
        return content
    
    def update_status(self, status: str):
        """更新Agent状态"""
        self._context['status'] = status
        self._save_context()
    
    def set_current_task(self, task: Dict[str, Any]):
        """设置当前任务"""
        self._context['current_task'] = {
            **task,
            'started_at': datetime.now().isoformat(),
            'status': 'in_progress'
        }
        self._save_context()
    
    def complete_current_task(self, result: Dict[str, Any]):
        """完成当前任务"""
        if self._context['current_task']:
            task_name = self._context['current_task'].get('name', 'Unknown')
            self._context['task_history'].append({
                'task_name': task_name,
                'timestamp': datetime.now().isoformat(),
                'status': 'completed',
                'result_summary': str(result)[:500]  # 增加到500个字符
            })
            
            self._context['current_task'] = None
            self._save_context()
    
    def fail_current_task(self, error: str):
        """当前任务失败"""
        if self._context['current_task']:
            task_name = self._context['current_task'].get('name', 'Unknown')
            self._context['task_history'].append({
                'task_name': task_name,
                'timestamp': datetime.now().isoformat(),
                'status': 'failed',
                'error': error
            })
            
            self._context['current_task'] = None
            self._save_context()
    
    def add_to_working_memory(self, item: str):
        """添加到工作记忆"""
        self._context['working_memory'].append({
            'content': item,
            'timestamp': datetime.now().isoformat()
        })
        self._save_context()
    
    def add_pending_item(self, item: str):
        """添加待处理事项"""
        self._context['pending_items'].append(item)
        self._save_context()
    
    def remove_pending_item(self, item: str):
        """移除待处理事项"""
        if item in self._context['pending_items']:
            self._context['pending_items'].remove(item)
            self._save_context()
    
    def update_experience(self, experience: str):
        """更新经验总结"""
        self._context['experience_summary'] = experience
        self._save_context()
    
    def add_skill(self, skill: Dict[str, Any]):
        """添加技能"""
        skill_names = [s.get('name') for s in self._context['skills']]
        if skill.get('name') not in skill_names:
            self._context['skills'].append(skill)
            self._save_context()
    
    def add_tool(self, tool: Dict[str, Any]):
        """添加工具"""
        tool_names = [t.get('name') for t in self._context['tools']]
        if tool.get('name') not in tool_names:
            self._context['tools'].append(tool)
            self._save_context()
    
    def get_context(self) -> Dict[str, Any]:
        """获取完整上下文"""
        return self._context.copy()
    
    def get_working_context(self) -> Dict[str, Any]:
        """获取工作上下文（用于ReAct循环）"""
        return {
            "agent": {
                "id": self._context['agent_id'],
                "role": self._context['agent_role'],
                "capabilities": self._context['capabilities'],
                "goal": self._context['primary_goal'],
                "rules": self._context['decision_rules'],
                "constraints": self._context['constraints']
            },
            "current_task": self._context['current_task'],
            "working_memory": self._context['working_memory'][-20:],  # 增加到20个项目
            "pending_items": self._context['pending_items'],
            "experience": self._context['experience_summary']
        }
    
    def _save_context(self):
        """保存上下文到文件"""
        self._write_md_file()
        self._write_json_file()
    
    def reload_context(self):
        """从文件重新加载上下文"""
        if self.json_file_path.exists():
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self._context = json.load(f)
    
    def clear_working_memory(self):
        """清空工作记忆"""
        self._context['working_memory'] = []
        self._save_context()
    
    def get_md_file_path(self) -> str:
        """获取MD文件路径"""
        return str(self.md_file_path)