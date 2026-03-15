#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主Agent（Planner）

实现LLM驱动的智能决策引擎。

作者: Agent OS Team
"""

import threading
from typing import Dict, List, Optional, Any
from datetime import datetime

from core.models import Task, DAG, TaskStatus, TaskPriority, EventType, Agent
from core.event_bus import EventBus
from core.blackboard import Blackboard
from core.task_scheduler import TaskDAGScheduler
from core.skill_registry import SkillRegistry
from core.vector_memory import VectorMemoryService


class MainAgent:
    """
    主Agent（Planner）
    
    负责全局任务拆分、调度、策略、目标管理。
    使用LLM进行智能决策。
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        blackboard: Blackboard,
        scheduler: TaskDAGScheduler,
        skill_registry: SkillRegistry,
        vector_memory: VectorMemoryService,
        llm_handler: Optional[callable] = None,
        dynamic_agent_manager: Optional[Any] = None
    ):
        """
        初始化主Agent
        
        Args:
            event_bus: 事件总线
            blackboard: 黑板
            scheduler: 任务调度器
            skill_registry: 技能注册表
            vector_memory: 向量记忆服务
            llm_handler: LLM处理函数
            dynamic_agent_manager: 动态Agent管理器
        """
        self.event_bus = event_bus
        self.blackboard = blackboard
        self.scheduler = scheduler
        self.skill_registry = skill_registry
        self.vector_memory = vector_memory
        self.llm_handler = llm_handler
        self.dynamic_agent_manager = dynamic_agent_manager
        
        self.agent_id = "main_agent"
        self.agent = Agent(
            id=self.agent_id,
            name="Main Agent (Planner)",
            role="planner",
            type="main",
            capabilities=["planning", "scheduling", "decision_making"],
            status="idle"
        )
        
        self._lock = threading.RLock()
        self._active_dags: Dict[str, DAG] = {}
        
        self._setup_event_subscriptions()
        self.blackboard.register_agent(self.agent)
    
    def _setup_event_subscriptions(self) -> None:
        """设置事件订阅"""
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        self.event_bus.subscribe(EventType.TASK_FAILED, self._on_task_failed)
        self.event_bus.subscribe(EventType.NEW_TASK_GENERATED, self._on_new_task_generated)
    
    def _clean_json_response(self, response: str) -> str:
        """
        清理LLM返回的JSON响应
        
        Args:
            response: LLM返回的原始响应
            
        Returns:
            清理后的JSON字符串
        """
        import json
        
        cleaned = response.strip()
        
        # 移除markdown代码块标记
        if cleaned.startswith("```"):
            # 找到第一个换行符
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                # 移除开头的 ```json 或 ```
                cleaned = cleaned[first_newline:].strip()
                
                # 移除结尾的 ```
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3].strip()
        
        # 查找JSON对象的开始和结束
        json_start = -1
        json_end = -1
        
        # 查找第一个 {
        for i, char in enumerate(cleaned):
            if char == '{':
                json_start = i
                break
        
        # 查找最后一个 }
        if json_start != -1:
            brace_count = 0
            for i in range(json_start, len(cleaned)):
                if cleaned[i] == '{':
                    brace_count += 1
                elif cleaned[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
        
        # 如果找到完整的JSON对象
        if json_start != -1 and json_end > json_start:
            return cleaned[json_start:json_end]
        
        # 如果找不到JSON对象，尝试JSON数组
        array_start = -1
        array_end = -1
        
        # 查找第一个 [
        for i, char in enumerate(cleaned):
            if char == '[':
                array_start = i
                break
        
        # 查找最后一个 ]
        if array_start != -1:
            bracket_count = 0
            for i in range(array_start, len(cleaned)):
                if cleaned[i] == '[':
                    bracket_count += 1
                elif cleaned[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        array_end = i + 1
                        break
        
        # 如果找到完整的JSON数组
        if array_start != -1 and array_end > array_start:
            return cleaned[array_start:array_end]
        
        return cleaned
    
    def plan_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        规划任务（同步版本）
        
        Args:
            task_description: 任务描述
            context: 上下文信息
            
        Returns:
            DAG ID
        """
        print(f"Planning task: {task_description}")
        
        dag = self.scheduler.create_dag(
            name=f"Task: {task_description[:50]}",
            description=task_description
        )
        
        # 立即保存DAG到黑板，确保Agent可以访问
        self.blackboard.save_dag(dag)
        
        subtasks = self._decompose_task(task_description, context or {})
        
        task_map = {}
        for i, subtask in enumerate(subtasks):
            # 构建任务payload，包含原始问题
            payload = subtask.get("payload", {})
            
            # 确保原始问题被传递到子任务
            if context and "original_question" in context:
                payload["original_question"] = context["original_question"]
            elif "original_question" not in payload:
                # 如果没有明确的原始问题，使用任务描述作为原始问题
                payload["original_question"] = task_description
            
            task = Task(
                name=subtask["name"],
                description=subtask["description"],
                priority=TaskPriority(subtask.get("priority", 2)),
                agent_role=subtask.get("agent_role"),
                payload=payload
            )
            
            # 动态创建Agent（如果需要）
            if self.dynamic_agent_manager and task.agent_role:
                self.dynamic_agent_manager.get_or_create_agent(task.agent_role)
            
            self.scheduler.add_task(dag.id, task)
            task_map[i] = task.id
        
        for i, subtask in enumerate(subtasks):
            if "dependencies" in subtask:
                for dep_idx in subtask["dependencies"]:
                    self.scheduler.add_dependency(dag.id, task_map[i], task_map[dep_idx])
        
        with self._lock:
            self._active_dags[dag.id] = dag
        
        print(f"Task planned: {dag.id} with {len(subtasks)} subtasks")
        
        return dag.id
    
    async def plan_task_async(self, dag_id: str, task_description: str, 
                          context: Optional[Dict[str, Any]] = None) -> None:
        """
        异步规划任务
        
        Args:
            dag_id: DAG ID
            task_description: 任务描述
            context: 上下文信息
        """
        try:
            print(f"[异步规划] 开始规划任务: {task_description}")
            
            # 获取已创建的DAG
            dag = self.scheduler.get_dag(dag_id)
            if not dag:
                print(f"[异步规划] DAG不存在: {dag_id}")
                return
            
            # 异步分解任务
            import asyncio
            subtasks = await asyncio.to_thread(
                self._decompose_task, 
                task_description, 
                context or {}
            )
            
            print(f"[异步规划] 任务分解完成，子任务数量: {len(subtasks)}")
            
            # 添加子任务到DAG
            task_map = {}
            for i, subtask in enumerate(subtasks):
                # 构建任务payload，包含原始问题
                payload = subtask.get("payload", {})
                
                # 确保原始问题被传递到子任务
                if context and "original_question" in context:
                    payload["original_question"] = context["original_question"]
                elif "original_question" not in payload:
                    # 如果没有明确的原始问题，使用任务描述作为原始问题
                    payload["original_question"] = task_description
                
                task = Task(
                    name=subtask["name"],
                    description=subtask["description"],
                    priority=TaskPriority(subtask.get("priority", 2)),
                    agent_role=subtask.get("agent_role"),
                    payload=payload
                )
                
                # 动态创建Agent（如果需要）
                if self.dynamic_agent_manager and task.agent_role:
                    self.dynamic_agent_manager.get_or_create_agent(task.agent_role)
                
                self.scheduler.add_task(dag.id, task)
                task_map[i] = task.id
            
            # 添加任务依赖关系
            for i, subtask in enumerate(subtasks):
                if "dependencies" in subtask:
                    for dep_idx in subtask["dependencies"]:
                        self.scheduler.add_dependency(dag.id, task_map[i], task_map[dep_idx])
            
            with self._lock:
                self._active_dags[dag.id] = dag
            
            print(f"[异步规划] 任务规划完成: {dag_id} with {len(subtasks)} subtasks")
            
        except Exception as e:
            print(f"[异步规划] 任务规划失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _decompose_task(self, task_description: str, 
                       context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        分解任务
        
        Args:
            task_description: 任务描述
            context: 上下文
            
        Returns:
            子任务列表
        """
        if self.llm_handler:
            return self._llm_decompose(task_description, context)
        else:
            return self._rule_based_decompose(task_description, context)
    
    def _llm_decompose(self, task_description: str, 
                      context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        使用LLM分解任务
        
        Args:
            task_description: 任务描述
            context: 上下文
            
        Returns:
            子任务列表
        """
        prompt = f"""
        请将以下任务分解为多个子任务：
        
        任务描述: {task_description}
        上下文: {context}
        
        请直接返回JSON格式的子任务列表，不要添加任何其他文字说明。
        JSON必须包含以下结构：
        {{
          "subtasks": [
            {{
              "name": "子任务名称",
              "description": "子任务描述",
              "priority": 1,
              "agent_role": "researcher",
              "dependencies": [0],
              "payload": {{}}
            }}
          ]
        }}
        
        或者直接返回子任务数组：
        [
          {{
            "name": "子任务名称",
            "description": "子任务描述",
            "priority": 1,
            "agent_role": "researcher"
          }}
        ]
        """
        
        try:
            print(f"[LLM调试] 开始调用LLM进行任务分解...")
            print(f"[LLM调试] 任务描述: {task_description}")
            print(f"[LLM调试] 上下文: {context}")
            
            result = self.llm_handler.complete(prompt)
            
            print(f"[LLM调试] LLM原始响应:")
            print(f"[LLM调试] {result}")
            print(f"[LLM调试] 响应长度: {len(result)}")
            
            import json
            
            cleaned_result = self._clean_json_response(result)
            print(f"[LLM调试] 清理后的JSON:")
            print(f"[LLM调试] {cleaned_result}")
            
            parsed = json.loads(cleaned_result)
            print(f"[LLM调试] 解析结果: {parsed}")
            
            if "subtasks" in parsed:
                subtasks = parsed["subtasks"]
                print(f"[LLM调试] 返回subtasks，数量: {len(subtasks)}")
                return subtasks
            elif isinstance(parsed, list):
                print(f"[LLM调试] 返回列表，数量: {len(parsed)}")
                return parsed
            elif isinstance(parsed, dict) and "name" in parsed and "description" in parsed:
                print(f"[LLM调试] 返回单个任务对象，转换为列表")
                return [parsed]
            else:
                print(f"[LLM调试] LLM返回格式不符合预期: {parsed}")
                print(f"[LLM调试] 回退到规则分解")
                return self._rule_based_decompose(task_description, context)
                
        except Exception as e:
            print(f"[LLM调试] LLM decomposition error: {e}")
            import traceback
            traceback.print_exc()
            print(f"[LLM调试] 回退到规则分解")
            return self._rule_based_decompose(task_description, context)
    
    def _rule_based_decompose(self, task_description: str,
                             context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        基于规则分解任务
        
        Args:
            task_description: 任务描述
            context: 上下文
            
        Returns:
            子任务列表
        """
        task_lower = task_description.lower()
        
        if "report" in task_lower:
            return [
                {
                    "name": "Gather Information",
                    "description": "Collect relevant information for the report",
                    "priority": 3,
                    "agent_role": "researcher"
                },
                {
                    "name": "Analyze Data",
                    "description": "Analyze the collected data",
                    "priority": 3,
                    "agent_role": "analyst",
                    "dependencies": [0]
                },
                {
                    "name": "Write Report",
                    "description": "Write the final report",
                    "priority": 2,
                    "agent_role": "writer",
                    "dependencies": [1]
                }
            ]
        elif "research" in task_lower:
            return [
                {
                    "name": "Define Research Questions",
                    "description": "Define the research questions and objectives",
                    "priority": 3,
                    "agent_role": "researcher"
                },
                {
                    "name": "Collect Data",
                    "description": "Collect relevant data and information",
                    "priority": 3,
                    "agent_role": "researcher",
                    "dependencies": [0]
                },
                {
                    "name": "Analyze Findings",
                    "description": "Analyze the research findings",
                    "priority": 2,
                    "agent_role": "analyst",
                    "dependencies": [1]
                }
            ]
        else:
            return [
                {
                    "name": "Execute Task",
                    "description": task_description,
                    "priority": 2,
                    "agent_role": "researcher"
                }
            ]
    
    def _on_task_completed(self, event) -> None:
        """
        任务完成事件处理
        
        Args:
            event: 事件对象
        """
        task_id = event.data.get("task_id")
        dag_id = event.data.get("dag_id")
        result = event.data.get("result")
        
        print(f"Task completed: {task_id} in DAG {dag_id}")
        
        decision = self._analyze_result(task_id, result, dag_id)
        
        if decision["action"] == "continue":
            print(f"Continuing with next tasks")
        elif decision["action"] == "retry":
            print(f"Retrying task: {task_id}")
            self._retry_task(dag_id, task_id)
        elif decision["action"] == "split":
            print(f"Splitting task: {task_id}")
            self._split_task(dag_id, task_id, decision["new_tasks"])
        elif decision["action"] == "complete":
            print(f"DAG {dag_id} completed")
            self._complete_dag(dag_id)
    
    def _on_task_failed(self, event) -> None:
        """
        任务失败事件处理
        
        Args:
            event: 事件对象
        """
        task_id = event.data.get("task_id")
        dag_id = event.data.get("dag_id")
        error = event.data.get("error")
        
        print(f"Task failed: {task_id} in DAG {dag_id}, error: {error}")
        
        dag = self.scheduler.get_dag(dag_id)
        if dag:
            task = dag.get_task(task_id)
            if task and task.retry_count < task.max_retries:
                print(f"Retrying task {task_id} (attempt {task.retry_count + 1})")
                self._retry_task(dag_id, task_id)
            else:
                print(f"Task {task_id} exceeded max retries, marking as failed")
    
    def _on_new_task_generated(self, event) -> None:
        """
        新任务生成事件处理
        
        Args:
            event: 事件对象
        """
        dag_id = event.data.get("dag_id")
        task_data = event.data.get("task")
        
        if dag_id and task_data:
            task = Task(**task_data)
            self.scheduler.add_task(dag_id, task)
            print(f"New task generated: {task.name} in DAG {dag_id}")
    
    def _analyze_result(self, task_id: str, result: Optional[Dict[str, Any]],
                       dag_id: str) -> Dict[str, Any]:
        """
        分析执行结果
        
        Args:
            task_id: 任务ID
            result: 执行结果
            dag_id: DAG ID
            
        Returns:
            决策字典
        """
        if self.llm_handler:
            return self._llm_analyze_result(task_id, result, dag_id)
        else:
            return self._rule_based_analyze_result(task_id, result, dag_id)
    
    def _llm_analyze_result(self, task_id: str, result: Optional[Dict[str, Any]],
                           dag_id: str) -> Dict[str, Any]:
        """
        使用LLM分析结果
        
        Args:
            task_id: 任务ID
            result: 执行结果
            dag_id: DAG ID
            
        Returns:
            决策字典
        """
        dag = self.scheduler.get_dag(dag_id)
        task = dag.get_task(task_id) if dag else None
        
        prompt = f"""
        分析以下任务执行结果，决定下一步行动：
        
        任务: {task.name if task else task_id}
        描述: {task.description if task else ''}
        结果: {result}
        
        请直接返回JSON格式的决策，不要添加任何其他文字说明。
        JSON必须包含以下字段：
        - action: 行动类型（continue, retry, split, complete）
        - reason: 决策原因
        
        决策规则：
        1. 如果任务成功执行完成（没有错误信息），使用"continue"
        2. 只有在任务执行失败或出现明确错误时才使用"retry"
        3. 如果结果中包含具体的输出内容（即使是"unknown"），说明任务已成功执行，应该使用"continue"
        4. 如果DAG中所有任务都已完成，使用"complete"
        
        示例格式：
        {{
          "action": "continue",
          "reason": "任务成功完成"
        }}
        """
        
        try:
            print(f"[LLM调试] 开始分析任务结果...")
            print(f"[LLM调试] 任务ID: {task_id}")
            print(f"[LLM调试] DAG ID: {dag_id}")
            print(f"[LLM调试] 结果: {result}")
            
            llm_result = self.llm_handler.complete(prompt)
            
            print(f"[LLM调试] LLM分析原始响应:")
            print(f"[LLM调试] {llm_result}")
            
            import json
            cleaned_result = self._clean_json_response(llm_result)
            print(f"[LLM调试] 清理后的JSON:")
            print(f"[LLM调试] {cleaned_result}")
            
            decision = json.loads(cleaned_result)
            print(f"[LLM调试] 解析的决策: {decision}")
            return decision
        except Exception as e:
            print(f"[LLM调试] LLM analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {"action": "continue", "reason": "default"}
    
    def _rule_based_analyze_result(self, task_id: str, result: Optional[Dict[str, Any]],
                                  dag_id: str) -> Dict[str, Any]:
        """
        基于规则分析结果
        
        Args:
            task_id: 任务ID
            result: 执行结果
            dag_id: DAG ID
            
        Returns:
            决策字典
        """
        if result and "error" in result:
            return {"action": "retry", "reason": "Error in result"}
        
        dag = self.scheduler.get_dag(dag_id)
        if dag and dag.is_completed():
            return {"action": "complete", "reason": "All tasks completed"}
        
        return {"action": "continue", "reason": "Normal completion"}
    
    def _retry_task(self, dag_id: str, task_id: str) -> None:
        """
        重试任务
        
        Args:
            dag_id: DAG ID
            task_id: 任务ID
        """
        dag = self.scheduler.get_dag(dag_id)
        if not dag:
            return
        
        task = dag.get_task(task_id)
        if not task:
            return
        
        task.retry_count += 1
        task.status = TaskStatus.PENDING
        
        # 发布事件，包含session_id（如果有）
        event_data = {"dag_id": dag_id, "task_id": task.id, "task_name": task.name}
        if dag.metadata and 'session_id' in dag.metadata:
            event_data['session_id'] = dag.metadata['session_id']
        
        self.event_bus.publish(
            EventType.TASK_CREATED,
            event_data,
            "main_agent"
        )
    
    def _split_task(self, dag_id: str, task_id: str, 
                   new_tasks: List[Dict[str, Any]]) -> None:
        """
        拆分任务
        
        Args:
            dag_id: DAG ID
            task_id: 任务ID
            new_tasks: 新任务列表
        """
        dag = self.scheduler.get_dag(dag_id)
        if not dag:
            return
        
        original_task = dag.get_task(task_id)
        if not original_task:
            return
        
        original_task.status = TaskStatus.COMPLETED
        
        for task_data in new_tasks:
            task = Task(
                name=task_data.get("name", "Split Task"),
                description=task_data.get("description", ""),
                priority=TaskPriority(task_data.get("priority", 2)),
                agent_role=task_data.get("agent_role"),
                payload=task_data.get("payload", {})
            )
            
            self.scheduler.add_task(dag_id, task)
            self.scheduler.add_dependency(dag_id, task.id, task_id)
    
    def _complete_dag(self, dag_id: str) -> None:
        """
        完成DAG
        
        Args:
            dag_id: DAG ID
        """
        dag = self.scheduler.get_dag(dag_id)
        if not dag:
            return
        
        results = []
        for task in dag.tasks.values():
            if task.result:
                results.append({
                    "task_id": task.id,
                    "task_name": task.name,
                    "result": task.result
                })
        
        final_result = {
            "dag_id": dag_id,
            "dag_name": dag.name,
            "completed_at": datetime.now().isoformat(),
            "results": results
        }
        
        self.blackboard.write_knowledge(
            f"dag_result_{dag_id}",
            final_result,
            self.agent_id
        )
        
        with self._lock:
            if dag_id in self._active_dags:
                del self._active_dags[dag_id]
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取状态
        
        Returns:
            状态字典
        """
        with self._lock:
            return {
                "agent_id": self.agent_id,
                "agent_name": self.agent.name,
                "active_dags": len(self._active_dags),
                "dag_ids": list(self._active_dags.keys())
            }