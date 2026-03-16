#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReAct循环

实现推理-行动循环机制。

作者: Agent OS Team
"""

import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum


class ReActActionType(Enum):
    """ReAct动作类型"""
    THINK = "think"
    TOOL_CALL = "tool_call"
    OBSERVE = "observe"
    FINISH = "finish"


@dataclass
class ReActStep:
    """ReAct步骤"""
    step_number: int
    action_type: ReActActionType
    thought: str
    action: Optional[str] = None
    tool_name: Optional[str] = None
    tool_params: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class ReActLoop:
    """
    ReAct循环
    
    实现推理-行动循环，支持Agent自主决策和工具调用。
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_role: str,
        context_manager,
        tool_caller,
        llm_handler: Optional[Callable] = None,
        max_steps: int = 10,
        max_thought_time: float = 30.0
    ):
        """
        初始化ReAct循环
        
        Args:
            agent_id: Agent ID
            agent_role: Agent角色
            context_manager: 上下文管理器
            tool_caller: 工具调用器
            llm_handler: LLM处理函数
            max_steps: 最大步骤数
            max_thought_time: 最大思考时间（秒）
        """
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.context_manager = context_manager
        self.tool_caller = tool_caller
        self.llm_handler = llm_handler
        self.max_steps = max_steps
        self.max_thought_time = max_thought_time
        
        self._steps: List[ReActStep] = []
        self._current_step = 0
        self._is_running = False
        self._final_result: Optional[Dict[str, Any]] = None
    
    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行ReAct循环
        
        Args:
            task: 任务字典
            
        Returns:
            最终结果
        """
        self._is_running = True
        self._steps = []
        self._current_step = 0
        self._final_result = None
        
        context_manager = self.context_manager
        context_manager.set_current_task(task)
        context_manager.update_status("thinking")
        
        print(f"[ReAct] 开始执行任务: {task.get('name', 'Unknown')}")
        print(f"[ReAct] 最大步骤数: {self.max_steps}")
        
        try:
            while self._should_continue():
                step = self._execute_step(task)
                self._steps.append(step)
                self._current_step += 1
                
                self._log_step(step)
                
                if step.action_type == ReActActionType.FINISH:
                    self._final_result = self._extract_final_result(step)
                    break
            
            context_manager.complete_current_task(self._final_result or {"status": "completed", "steps": len(self._steps)})
            context_manager.update_status("idle")
            
            print(f"[ReAct] 任务完成，总步骤: {len(self._steps)}")
            
            return self._final_result or {
                "status": "completed",
                "steps": len(self._steps),
                "agent_id": self.agent_id
            }
            
        except Exception as e:
            print(f"[ReAct] 执行错误: {e}")
            context_manager.fail_current_task(str(e))
            context_manager.update_status("idle")
            return {
                "status": "failed",
                "error": str(e),
                "steps": len(self._steps),
                "agent_id": self.agent_id
            }
        finally:
            self._is_running = False
    
    def _should_continue(self) -> bool:
        """判断是否应该继续循环"""
        if self._current_step >= self.max_steps:
            print(f"[ReAct] 达到最大步骤数: {self.max_steps}")
            return False
        
        if self._final_result is not None:
            return False
        
        return True
    
    def _execute_step(self, task: Dict[str, Any]) -> ReActStep:
        """
        执行单个ReAct步骤
        
        Args:
            task: 任务字典
            
        Returns:
            ReAct步骤
        """
        step = ReActStep(
            step_number=self._current_step + 1,
            action_type=ReActActionType.THINK,
            thought=""
        )
        
        working_context = self.context_manager.get_working_context()
        
        if self.llm_handler:
            step = self._llm_react_step(task, working_context, step)
        else:
            step = self._rule_based_react_step(task, working_context, step)
        
        return step
    
    def _llm_react_step(self, task: Dict[str, Any], 
                       context: Dict[str, Any], step: ReActStep) -> ReActStep:
        """
        使用LLM执行ReAct步骤
        
        Args:
            task: 任务字典
            context: 工作上下文
            step: 当前步骤
            
        Returns:
            更新后的步骤
        """
        available_tools = self.tool_caller.get_available_tools()
        
        prompt = self._build_react_prompt(task, context, available_tools)
        
        try:
            response = self.llm_handler.complete(prompt)
            parsed = self._parse_react_response(response)
            
            step.action_type = parsed.get('action_type', ReActActionType.THINK)
            step.thought = parsed.get('thought', step.thought)
            step.action = parsed.get('action')
            step.tool_name = parsed.get('tool_name')
            step.tool_params = parsed.get('tool_params')
            
            if step.action_type == ReActActionType.TOOL_CALL and step.tool_name:
                print(f"[ReAct] 调用工具: {step.tool_name}")
                result = self.tool_caller.call_tool(
                    step.tool_name, 
                    step.tool_params or {}
                )
                step.observation = str(result)
                print(f"[ReAct] 工具结果: {step.observation[:100]}...")
                
                self.context_manager.add_to_working_memory(
                    f"调用工具 {step.tool_name}: {step.observation}"
                )
            elif step.action_type == ReActActionType.FINISH:
                step.observation = parsed.get('observation', '任务完成')
                print(f"[ReAct] 任务完成")
            
            return step
            
        except Exception as e:
            print(f"[ReAct] LLM执行错误: {e}")
            step.action_type = ReActActionType.FINISH
            step.observation = f"执行错误: {str(e)}"
            return step
    
    def _rule_based_react_step(self, task: Dict[str, Any], 
                              context: Dict[str, Any], step: ReActStep) -> ReActStep:
        """
        基于规则的ReAct步骤（无LLM时的降级方案）
        
        Args:
            task: 任务字典
            context: 工作上下文
            step: 当前步骤
            
        Returns:
            更新后的步骤
        """
        step.thought = f"分析任务: {task.get('description', 'Unknown')}"
        
        available_tools = self.tool_caller.get_available_tools()
        
        if available_tools and self._current_step == 0:
            step.action_type = ReActActionType.TOOL_CALL
            step.tool_name = available_tools[0]['name']
            step.tool_params = task.get('payload', {})
            step.action = f"调用工具 {step.tool_name}"
        else:
            step.action_type = ReActActionType.FINISH
            step.action = "完成任务"
            step.observation = "任务完成"
        
        if step.action_type == ReActActionType.TOOL_CALL:
            result = self.tool_caller.call_tool(step.tool_name, step.tool_params or {})
            step.observation = str(result)
            
            self.context_manager.add_to_working_memory(
                f"调用工具 {step.tool_name}: {step.observation}"
            )
        
        return step
    
    def _build_react_prompt(self, task: Dict[str, Any], 
                          context: Dict[str, Any], 
                          available_tools: List[Dict[str, Any]]) -> str:
        """
        构建ReAct提示词
        
        Args:
            task: 任务字典
            context: 工作上下文
            available_tools: 可用工具列表
            
        Returns:
            提示词
        """
        agent_info = context.get('agent', {})
        current_task = context.get('current_task', {})
        
        prompt = f"""你是{agent_info.get('role', 'Agent')}，负责执行以下任务：

## 当前任务
- 任务名称: {task.get('name', 'Unknown')}
- 任务描述: {task.get('description', 'Unknown')}

## 你的身份
- 角色: {agent_info.get('role', 'Agent')}
- 能力: {', '.join(agent_info.get('capabilities', []))}
- 目标: {agent_info.get('goal', '完成任务')}

## 决策规则
"""
        for i, rule in enumerate(agent_info.get('rules', []), 1):
            prompt += f"{i}. {rule}\n"
        
        prompt += """
## 可用工具
"""
        for i, tool in enumerate(available_tools, 1):
            prompt += f"{i}. **{tool.get('name', 'Unknown')}**: {tool.get('description', 'No description')}\n"
        
        if not available_tools:
            prompt += "暂无可用工具\n"
        
        prompt += """
## 工作记忆
"""
        for i, item in enumerate(context.get('working_memory', [])[-10:], 1):
            content = item.get('content', item) if isinstance(item, dict) else item
            prompt += f"{i}. {content}\n"
        
        if not context.get('working_memory'):
            prompt += "工作记忆为空\n"
        
        prompt += f"""
## 待处理事项
"""
        for i, item in enumerate(context.get('pending_items', []), 1):
            prompt += f"{i}. {item}\n"
        
        if not context.get('pending_items'):
            prompt += "无待处理事项\n"
        
        prompt += f"""
## 执行步骤
你当前是第{self._current_step + 1}步，最多执行{self.max_steps}步。

**重要指示**：
1. 仔细分析任务需求，确定需要哪些信息或操作
2. 如果需要收集信息，调用相应的工具
3. 获得足够信息后，应该尽快完成任务，不要重复调用工具
4. 当你已经获得了完成任务所需的信息时，立即使用"finish"动作
5. 不要无限循环，每步都要有明确的进展

**何时使用finish**：
- 已经收集到足够的信息来回答任务
- 工具调用已经返回了有用的结果
- 已经完成了任务的主要目标
- 达到了最大步骤数的一半时，应该考虑完成

请按照以下格式思考和行动：

**思考**: 分析当前情况，决定下一步行动
**行动**: 选择行动类型 (think/tool_call/finish)
**工具**: 如果选择tool_call，指定工具名称和参数
**观察**: 描述行动的结果

请用JSON格式返回你的决策（只返回一个JSON对象，不要包含其他文本）：
{{
  "action_type": "think" | "tool_call" | "finish",
  "thought": "你的思考过程",
  "action": "具体行动描述",
  "tool_name": "工具名称（如果action_type为tool_call）",
  "tool_params": {{"参数名": "参数值"}},
  "observation": "观察结果（如果action_type为finish）"
}}

**示例1 - 需要收集信息时**：
{{
  "action_type": "tool_call",
  "thought": "我需要收集关于Python编程的信息",
  "action": "调用Research工具",
  "tool_name": "Research",
  "tool_params": {{"topic": "Python编程"}}
}}

**示例2 - 完成任务时**：
{{
  "action_type": "finish",
  "thought": "我已经收集到了足够的信息，可以完成任务了",
  "action": "完成任务",
  "observation": "任务完成，获得了Python编程的相关信息"
}}

重要要求：
1. 必须真正执行任务，不能只是描述步骤
2. 如果需要收集信息，应该主动调用相应的工具
3. 每次工具调用后都要观察结果并更新工作记忆
4. 当获得足够信息时，应该立即选择finish，不要重复调用工具
5. 工具参数必须完整和准确
6. 避免无限循环，每步都要有明确的进展
7. 最多执行{self.max_steps}步，建议在{self.max_steps // 2}步内完成任务
"""
        
        return prompt
    
    def _parse_react_response(self, response: str) -> Dict[str, Any]:
        """
        解析ReAct响应
        
        Args:
            response: LLM响应
            
        Returns:
            解析后的字典
        """
        try:
            cleaned = self._clean_json_response(response)
            parsed = json.loads(cleaned)
            
            action_type_str = parsed.get('action_type', 'think')
            try:
                parsed['action_type'] = ReActActionType(action_type_str)
            except ValueError:
                parsed['action_type'] = ReActActionType.THINK
            
            return parsed
            
        except json.JSONDecodeError as e:
            print(f"[ReAct] JSON解析失败: {e}")
            return {
                'action_type': ReActActionType.THINK,
                'thought': '解析响应失败，继续思考',
                'action': '继续思考'
            }
    
    def _clean_json_response(self, response: str) -> str:
        """清理JSON响应"""
        response = response.strip()
        
        # 移除markdown代码块标记
        if response.startswith('```json'):
            response = response[7:]
        if response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()
        
        # 查找第一个完整的JSON对象
        start_idx = response.find('{')
        if start_idx == -1:
            return "{}"
        
        # 找到匹配的结束括号
        brace_count = 0
        end_idx = start_idx
        for i in range(start_idx, len(response)):
            if response[i] == '{':
                brace_count += 1
            elif response[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        if end_idx > start_idx:
            response = response[start_idx:end_idx + 1]
        
        return response
    
    def _extract_final_result(self, step: ReActStep) -> Dict[str, Any]:
        """
        提取最终结果
        
        Args:
            step: 最后一个步骤
            
        Returns:
            结果字典
        """
        result = {
            "status": "completed",
            "agent_id": self.agent_id,
            "agent_role": self.agent_role,
            "steps": len(self._steps),
            "final_observation": step.observation,
            "thought_process": [s.thought for s in self._steps],
            "tool_calls": [
                {
                    "step": s.step_number,
                    "tool": s.tool_name,
                    "params": s.tool_params,
                    "result": s.observation
                }
                for s in self._steps if s.tool_name
            ]
        }
        
        if step.observation:
            result["result"] = step.observation
        
        return result
    
    def _log_step(self, step: ReActStep):
        """记录步骤"""
        print(f"[ReAct Step {step.step_number}]")
        print(f"  类型: {step.action_type.value}")
        print(f"  思考: {step.thought[:100]}...")
        if step.tool_name:
            print(f"  工具: {step.tool_name}")
        if step.observation:
            print(f"  观察: {step.observation[:100]}...")
        print()
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        获取执行摘要
        
        Returns:
            执行摘要
        """
        return {
            "total_steps": len(self._steps),
            "tool_calls": sum(1 for s in self._steps if s.tool_name),
            "finish_reason": self._final_result.get('status', 'unknown') if self._final_result else 'incomplete',
            "execution_time": sum(
                s.timestamp for s in self._steps
            ) - self._steps[0].timestamp if self._steps else 0
        }