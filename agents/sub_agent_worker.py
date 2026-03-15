#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
子Agent Worker

实现事件驱动的子Agent，负责具体任务执行。

作者: Agent OS Team
"""

import threading
import time
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from core.models import Task, Agent, EventType, TaskStatus
from core.event_bus import EventBus
from core.blackboard import Blackboard
from core.skill_registry import SkillRegistry
from core.vector_memory import VectorMemoryService


class SubAgentWorker:
    """
    子Agent Worker
    
    负责具体任务执行、技能调用、结果上报。
    事件驱动，不轮询，不阻塞。
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_role: str,
        capabilities: List[str],
        event_bus: EventBus,
        blackboard: Blackboard,
        skill_registry: SkillRegistry,
        vector_memory: VectorMemoryService,
        llm_handler: Optional[Callable] = None,
        scheduler: Optional[Any] = None
    ):
        """
        初始化子Agent Worker
        
        Args:
            agent_id: Agent ID
            agent_role: Agent角色
            capabilities: 能力列表
            event_bus: 事件总线
            blackboard: 黑板
            skill_registry: 技能注册表
            vector_memory: 向量记忆服务
            llm_handler: LLM处理函数
            scheduler: 任务调度器（可选）
        """
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.capabilities = capabilities
        
        self.event_bus = event_bus
        self.blackboard = blackboard
        self.skill_registry = skill_registry
        self.vector_memory = vector_memory
        self.llm_handler = llm_handler
        self.scheduler = scheduler
        
        self.agent = Agent(
            id=agent_id,
            name=f"Sub Agent {agent_role}",
            role=agent_role,
            type="sub",
            capabilities=capabilities,
            status="idle"
        )
        
        self._lock = threading.RLock()
        self._current_task: Optional[Task] = None
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._task_queue: List[Task] = []
        
        self._setup_event_subscriptions()
        self.blackboard.register_agent(self.agent)
    
    def _setup_event_subscriptions(self) -> None:
        """设置事件订阅"""
        self.event_bus.subscribe(EventType.TASK_STARTED, self._on_task_started)
        self.event_bus.subscribe(EventType.NEW_TASK_GENERATED, self._on_new_task_generated)
    
    def start(self) -> None:
        """启动Worker"""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self._worker_thread.start()
        
        self.event_bus.publish(
            EventType.AGENT_REGISTERED,
            {"agent_id": self.agent_id, "agent_role": self.agent_role},
            self.agent_id
        )
        
        print(f"SubAgentWorker started: {self.agent_id} ({self.agent_role})")
    
    def stop(self) -> None:
        """停止Worker"""
        if not self._running:
            return
        
        self._running = False
        
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        
        self.event_bus.publish(
            EventType.AGENT_UNREGISTERED,
            {"agent_id": self.agent_id},
            self.agent_id
        )
        
        print(f"SubAgentWorker stopped: {self.agent_id}")
    
    def _run_worker(self) -> None:
        """运行Worker循环"""
        while self._running:
            try:
                if self._current_task is None and self._task_queue:
                    task = self._task_queue.pop(0)
                    self._execute_task(task)
                
                threading.Event().wait(0.1)
            except Exception as e:
                print(f"Worker error: {e}")
    
    def _on_task_started(self, event) -> None:
        """
        任务启动事件处理
        
        Args:
            event: 事件对象
        """
        task_id = event.data.get("task_id")
        dag_id = event.data.get("dag_id")
        task_name = event.data.get("task_name")
        
        if not task_id:
            return
        
        # 尝试从调度器获取任务
        task = None
        if self.scheduler:
            dag = self.scheduler.get_dag(dag_id)
            if dag:
                task = dag.get_task(task_id)
        
        # 如果调度器中没有，尝试从黑板获取
        if not task and dag_id:
            dag = self.blackboard.load_dag(dag_id)
            if dag:
                task = dag.get_task(task_id)
        
        if not task:
            print(f"Task not found: {task_id}")
            return
        
        if self._can_execute_task(task):
            with self._lock:
                # 将dag_id存储在任务元数据中，以便后续执行时使用
                if dag_id:
                    task.metadata['dag_id'] = dag_id
                self._task_queue.append(task)
                print(f"Task queued for {self.agent_id}: {task_name}")
    
    def _on_new_task_generated(self, event) -> None:
        """
        新任务生成事件处理
        
        Args:
            event: 事件对象
        """
        dag_id = event.data.get("dag_id")
        task_data = event.data.get("task")
        
        if not dag_id or not task_data:
            return
        
        task = Task(**task_data)
        
        if self._can_execute_task(task):
            with self._lock:
                self._task_queue.append(task)
                print(f"New task queued for {self.agent_id}: {task.name}")
    
    def _can_execute_task(self, task: Task) -> bool:
        """
        检查是否可以执行任务
        
        Args:
            task: 任务对象
            
        Returns:
            是否可以执行
        """
        if not self.agent.is_available():
            return False
        
        if task.agent_role and task.agent_role != self.agent_role:
            return False
        
        if task.agent_id and task.agent_id != self.agent_id:
            return False
        
        return True
    
    def _execute_task(self, task: Task) -> None:
        """
        执行任务
        
        Args:
            task: 任务对象
        """
        with self._lock:
            if not self.agent.is_available():
                return
            
            self._current_task = task
            self.agent.status = "busy"
            self.agent.current_task_id = task.id
            # 设置任务的agent_id
            task.agent_id = self.agent_id
        
        print(f"Executing task: {task.name} ({task.id})")
        
        try:
            result = self._run_task(task)
            
            # 获取session_id
            session_id = None
            dag_id = task.metadata.get('dag_id') if task.metadata else None
            if dag_id and self.scheduler:
                dag = self.scheduler.get_dag(dag_id)
                if dag and dag.metadata and 'session_id' in dag.metadata:
                    session_id = dag.metadata['session_id']
            
            # 发布事件，包含session_id（如果有）
            event_data = {
                "task_id": task.id,
                "result": result,
                "agent_id": self.agent_id
            }
            if session_id:
                event_data['session_id'] = session_id
            
            self.event_bus.publish(
                EventType.TASK_COMPLETED,
                event_data,
                self.agent_id
            )
            
            self.blackboard.write_result(task.id, result, self.agent_id)
            
        except Exception as e:
            error = str(e)
            print(f"Task execution error: {error}")
            
            # 获取session_id
            session_id = None
            dag_id = task.metadata.get('dag_id') if task.metadata else None
            if dag_id and self.scheduler:
                dag = self.scheduler.get_dag(dag_id)
                if dag and dag.metadata and 'session_id' in dag.metadata:
                    session_id = dag.metadata['session_id']
            
            # 发布事件，包含session_id（如果有）
            event_data = {
                "task_id": task.id,
                "error": error,
                "agent_id": self.agent_id
            }
            if session_id:
                event_data['session_id'] = session_id
            
            self.event_bus.publish(
                EventType.TASK_FAILED,
                event_data,
                self.agent_id
            )
        
        finally:
            with self._lock:
                self._current_task = None
                self.agent.status = "idle"
                self.agent.current_task_id = None
    
    def _run_task(self, task: Task) -> Dict[str, Any]:
        """
        运行任务
        
        Args:
            task: 任务对象
            
        Returns:
            执行结果
        """
        skill = self._select_skill(task)
        
        if skill:
            return self._execute_skill(skill, task)
        else:
            return self._execute_with_llm(task)
    
    def _select_skill(self, task: Task) -> Optional[Any]:
        """
        选择技能
        
        Args:
            task: 任务对象
            
        Returns:
            技能对象
        """
        # 首先分析任务描述，判断是否真的需要特定技能
        task_keywords = self._extract_task_keywords(task)
        
        # 获取所有技能
        all_skills = self.skill_registry.get_all_skills()
        
        # 检查是否有技能与任务关键词匹配
        matched_skills = []
        for skill in all_skills:
            skill_name_lower = skill.name.lower()
            skill_desc_lower = skill.description.lower()
            
            # 检查技能名称是否在任务关键词中
            if any(keyword in skill_name_lower for keyword in task_keywords):
                matched_skills.append((skill, "name_match"))
            # 检查技能描述是否与任务相关
            elif any(keyword in skill_desc_lower for keyword in task_keywords):
                matched_skills.append((skill, "desc_match"))
        
        if matched_skills:
            # 选择最匹配的技能
            best_skill, match_type = matched_skills[0]
            print(f"[技能选择] 找到匹配技能: {best_skill.name} for task: {task.name} (匹配类型: {match_type})")
            return best_skill
        
        # 如果没有明确匹配，尝试根据Agent能力选择
        skill = self.skill_registry.find_best_skill(
            self.capabilities,
            preferred_type=None
        )
        
        if skill:
            print(f"[技能选择] 根据Agent能力找到技能: {skill.name} for task: {task.name}")
            return skill
        
        print(f"[技能选择] 未找到匹配技能 for task: {task.name}, 将使用LLM直接执行")
        return None
    
    def _extract_task_keywords(self, task: Task) -> List[str]:
        """
        从任务中提取关键词
        
        Args:
            task: 任务对象
            
        Returns:
            关键词列表
        """
        keywords = []
        
        # 从任务名称提取关键词
        task_name_lower = task.name.lower()
        keywords.extend(task_name_lower.split())
        
        # 从任务描述提取关键词
        task_desc_lower = task.description.lower()
        keywords.extend(task_desc_lower.split())
        
        # 添加一些常见的任务类型关键词
        common_keywords = ["研究", "分析", "写作", "设计", "开发", "测试", "部署", "优化", "维护",
                          "research", "analysis", "writing", "design", "develop", "test", "deploy", "optimize", "maintain"]
        
        for keyword in common_keywords:
            if keyword in task_name_lower or keyword in task_desc_lower:
                keywords.append(keyword)
        
        return list(set(keywords))  # 去重
    
    def _execute_skill(self, skill: Any, task: Task) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            skill: 技能对象
            task: 任务对象
            
        Returns:
            执行结果
        """
        print(f"Executing skill: {skill.name}")
        print(f"[技能执行] 任务名称: {task.name}")
        print(f"[技能执行] 任务描述: {task.description}")
        print(f"[技能执行] 任务载荷: {task.payload}")
        
        # 根据技能类型和任务内容构建参数
        skill_params = self._build_skill_params(skill, task)
        print(f"[技能执行] 技能参数: {skill_params}")
        
        result = skill.execute(**skill_params)
        
        return {
            "task_id": task.id,
            "skill_name": skill.name,
            "result": result,
            "completed_at": datetime.now().isoformat()
        }
    
    def _build_skill_params(self, skill: Any, task: Task) -> Dict[str, Any]:
        """
        根据技能和任务构建技能参数
        
        Args:
            skill: 技能对象
            task: 任务对象
            
        Returns:
            技能参数字典
        """
        params = task.payload.copy() if task.payload else {}
        
        # 添加任务名称和描述
        params['task_name'] = task.name
        params['task_description'] = task.description
        
        # 添加原始问题 - 从任务描述或载荷中提取
        original_question = params.get('original_question', '')
        if not original_question:
            # 如果载荷中没有原始问题，尝试从任务描述中提取
            original_question = task.description
        params['original_question'] = original_question
        print(f"[参数构建] 原始问题: {original_question}")
        
        # 根据技能类型添加特定参数
        if skill.name.lower() == 'research':
            # 研究技能需要topic参数
            if 'topic' not in params:
                params['topic'] = task.description  # 使用任务描述作为研究主题
            print(f"[参数构建] Research技能，主题: {params.get('topic')}")
            # 确保topic不是unknown
            if params.get('topic') == 'unknown' or not params.get('topic'):
                params['topic'] = task.name if task.name else task.description
                print(f"[参数构建] 修正Research主题为: {params.get('topic')}")
        
        elif skill.name.lower() == 'analysis':
            # 分析技能需要data参数
            if 'data' not in params:
                params['data'] = task.description  # 使用任务描述作为分析数据
            print(f"[参数构建] Analysis技能，数据: {params.get('data')}")
            # 确保data不是unknown
            if params.get('data') == 'unknown' or not params.get('data'):
                params['data'] = task.name if task.name else task.description
                print(f"[参数构建] 修正Analysis数据为: {params.get('data')}")
        
        elif skill.name.lower() == 'writing':
            # 写作技能需要content参数
            if 'content' not in params:
                params['content'] = task.description  # 使用任务描述作为写作内容
            print(f"[参数构建] Writing技能，内容: {params.get('content')}")
            # 确保content不是unknown
            if params.get('content') == 'unknown' or not params.get('content'):
                params['content'] = task.name if task.name else task.description
                print(f"[参数构建] 修正Writing内容为: {params.get('content')}")
        
        return params
    
    def _execute_with_llm(self, task: Task) -> Dict[str, Any]:
        """
        使用LLM执行任务
        
        Args:
            task: 任务对象
            
        Returns:
            执行结果
        """
        print(f"[LLM执行] 使用LLM执行任务: {task.name}")
        print(f"[LLM执行] 任务描述: {task.description}")
        
        context = self._build_context(task)
        
        if self.llm_handler:
            prompt = self._build_prompt(task, context)
            print(f"[LLM执行] 提示词长度: {len(prompt)}")
            
            try:
                llm_result = self.llm_handler.complete(prompt)
                print(f"[LLM执行] LLM原始响应长度: {len(llm_result)}")
                print(f"[LLM执行] LLM原始响应前200字符: {llm_result[:200]}")
                
                # 清理JSON响应
                cleaned_result = self._clean_json_response(llm_result)
                print(f"[LLM执行] 清理后的JSON长度: {len(cleaned_result)}")
                
                # 尝试解析LLM返回的JSON
                try:
                    parsed_result = json.loads(cleaned_result)
                    print(f"[LLM执行] 成功解析JSON结果")
                    return {
                        "task_id": task.id,
                        "method": "llm",
                        "result": parsed_result,
                        "completed_at": datetime.now().isoformat()
                    }
                except json.JSONDecodeError as e:
                    print(f"[LLM执行] JSON解析失败: {e}")
                    print(f"[LLM执行] 清理后的内容: {cleaned_result}")
                    # 如果JSON解析失败，将原始文本作为结果
                    return {
                        "task_id": task.id,
                        "method": "llm",
                        "result": {
                            "output": llm_result,
                            "findings": "LLM执行完成，但返回格式不是标准JSON"
                        },
                        "completed_at": datetime.now().isoformat()
                    }
            except Exception as e:
                print(f"[LLM执行] LLM调用失败: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "task_id": task.id,
                    "method": "llm_error",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                }
        else:
            return self._execute_default(task, context)
    
    def _clean_json_response(self, response: str) -> str:
        """
        清理LLM响应中的JSON内容
        
        Args:
            response: LLM原始响应
            
        Returns:
            清理后的JSON字符串
        """
        # 移除markdown代码块标记
        response = response.strip()
        if response.startswith('```json'):
            response = response[7:]
        elif response.startswith('```'):
            response = response[3:]
        if response.endswith('```'):
            response = response[:-3]
        response = response.strip()
        
        # 找到第一个{和最后一个}
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            response = response[start_idx:end_idx + 1]
        
        return response
    
    def _build_context(self, task: Task) -> Dict[str, Any]:
        """
        构建上下文
        
        Args:
            task: 任务对象
            
        Returns:
            上下文字典
        """
        context = {
            "task": {
                "name": task.name,
                "description": task.description,
                "payload": task.payload
            },
            "agent": {
                "id": self.agent_id,
                "role": self.agent_role,
                "capabilities": self.capabilities
            }
        }
        
        relevant_knowledge = self.vector_memory.search(
            task.description,
            top_k=3
        )
        
        if relevant_knowledge:
            context["knowledge"] = [
                {
                    "content": mem[0].content,
                    "similarity": mem[1]
                }
                for mem in relevant_knowledge
            ]
        
        return context
    
    def _build_prompt(self, task: Task, context: Dict[str, Any]) -> str:
        """
        构建LLM提示
        
        Args:
            task: 任务对象
            context: 上下文
            
        Returns:
            提示字符串
        """
        prompt = f"""
        你是一个{self.agent_role}，负责执行以下任务：
        
        任务名称: {task.name}
        任务描述: {task.description}
        
        你的能力: {', '.join(self.capabilities)}
        
        重要要求：
        1. 必须真正执行任务，不能只是描述步骤
        2. 必须产生具体的输出、数据或结论
        3. 必须返回明确的执行结果，不能是"unknown"或空值
        4. 每个步骤都必须实际执行，不能只是计划
        
        请直接执行这个任务，并返回详细的执行结果。
        结果应该包含：
        1. 执行的具体步骤（每个步骤都要实际执行）
        2. 产生的具体输出或数据（不能是占位符）
        3. 执行的明确结论或发现（必须有实际内容）
        4. 相关的指标或统计数据（如适用）
        
        请用JSON格式返回结果，不要添加任何其他文字说明：
        {{
          "steps": ["步骤1", "步骤2", ...],
          "output": "具体输出内容（必须有实际内容）",
          "findings": "执行发现或结论（必须有明确结论）",
          "metrics": {{"指标名": "数值", ...}}
        }}
        
        相关知识:
        """
        
        if "knowledge" in context:
            for i, knowledge in enumerate(context["knowledge"]):
                prompt += f"\n{i+1}. {knowledge['content']} (相似度: {knowledge['similarity']:.2f})"
        
        if task.payload:
            prompt += f"\n\n任务参数: {task.payload}"
        
        return prompt
    
    def _execute_default(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        默认执行逻辑
        
        Args:
            task: 任务对象
            context: 上下文
            
        Returns:
            执行结果
        """
        result = {
            "task_id": task.id,
            "method": "default",
            "message": f"Task {task.name} executed by {self.agent_role}",
            "completed_at": datetime.now().isoformat()
        }
        
        if task.payload:
            result.update(task.payload)
        
        return result
    
    def request_new_task(self, task_description: str, 
                        context: Optional[Dict[str, Any]] = None) -> None:
        """
        请求生成新任务
        
        Args:
            task_description: 任务描述
            context: 上下文
        """
        print(f"Requesting new task: {task_description}")
        
        self.event_bus.publish(
            EventType.NEW_TASK_GENERATED,
            {
                "task_description": task_description,
                "context": context,
                "requested_by": self.agent_id
            },
            self.agent_id
        )
    
    def learn(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        学习新知识
        
        Args:
            content: 内容
            metadata: 元数据
        """
        memory_id = self.vector_memory.add(
            content,
            metadata=metadata or {}
        )
        
        print(f"Learned new knowledge: {memory_id}")
        
        self.event_bus.publish(
            EventType.KNOWLEDGE_UPDATED,
            {
                "memory_id": memory_id,
                "agent_id": self.agent_id
            },
            self.agent_id
        )
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取状态
        
        Returns:
            状态字典
        """
        with self._lock:
            return {
                "agent_id": self.agent_id,
                "agent_role": self.agent_role,
                "status": self.agent.status,
                "current_task_id": self.agent.current_task_id,
                "queued_tasks": len(self._task_queue),
                "capabilities": self.capabilities
            }