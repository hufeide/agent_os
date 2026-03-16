#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API服务器

实现RESTful API和WebSocket接口。

作者: Agent OS Team
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import asyncio

from core.models import Task, DAG, TaskStatus, TaskPriority, EventType
from core.event_bus import EventBus
from core.blackboard import Blackboard
from core.task_scheduler import TaskDAGScheduler
from core.skill_registry import SkillRegistry
from core.vector_memory import VectorMemoryService
from agents.main_agent import MainAgent
from agents.sub_agent_worker import SubAgentWorker


app = FastAPI(
    title="Agent OS API",
    description="主从分层Agent系统API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskRequest(BaseModel):
    """任务请求模型"""
    description: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None  # 会话ID，用于会话归类


class TaskResponse(BaseModel):
    """任务响应模型"""
    dag_id: str
    status: str
    message: str
    session_id: Optional[str] = None


class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str
    task_count: int
    latest_task: Optional[str] = None
    latest_final_answer: Optional[Dict[str, str]] = None  # 添加最新最终回答
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SessionListResponse(BaseModel):
    """会话列表响应模型"""
    sessions: List[SessionInfo]
    total_count: int


class AgentStatusResponse(BaseModel):
    """Agent状态响应模型"""
    main_agent: Dict[str, Any]
    sub_agents: List[Dict[str, Any]]
    dynamic_stats: Optional[Dict[str, Any]] = None


class DAGStatusResponse(BaseModel):
    """DAG状态响应模型"""
    dag_id: str
    name: str
    description: str = ""
    total_tasks: int
    status_counts: Dict[str, int]
    is_completed: bool
    tasks: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class WebSocketConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = WebSocketConnectionManager()


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Agent OS",
        "version": "2.0.0",
        "description": "主从分层Agent系统"
    }


@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(request: TaskRequest):
    """
    创建任务（异步执行）
    
    Args:
        request: 任务请求
        
    Returns:
        任务响应
    """
    try:
        main_agent = app.state.main_agent
        
        # 生成或使用提供的session_id
        import uuid
        session_id = request.session_id or str(uuid.uuid4())
        
        # 创建空的DAG
        scheduler = app.state.scheduler
        dag = scheduler.create_dag(
            name=f"Task: {request.description[:50]}",
            description=request.description
        )
        
        # 将session_id存储在DAG的metadata中
        dag.metadata = dag.metadata or {}
        dag.metadata['session_id'] = session_id
        
        # 立即保存DAG到黑板
        blackboard = app.state.blackboard
        blackboard.save_dag(dag)
        
        # 在后台异步执行任务分解
        import asyncio
        asyncio.create_task(
            main_agent.plan_task_async(
                dag_id=dag.id,
                task_description=request.description,
                context=request.context
            )
        )
        
        return TaskResponse(
            dag_id=dag.id,
            status="created",
            message=f"Task created successfully and is being planned",
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ReactTaskRequest(BaseModel):
    """ReAct任务请求模型"""
    description: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    max_iterations: Optional[int] = 10


class ReactTaskResponse(BaseModel):
    """ReAct任务响应模型"""
    task_id: Optional[str]
    session_id: str
    status: str
    message: str


@app.post("/api/tasks/react", response_model=ReactTaskResponse)
async def create_react_task(request: ReactTaskRequest):
    """
    创建ReAct任务（主Agent的ReAct循环）
    
    支持串行和并行任务分配，收集结果并判断完成状态
    
    Args:
        request: ReAct任务请求
        
    Returns:
        ReAct任务响应
    """
    try:
        main_agent = app.state.main_agent
        
        # 生成或使用提供的session_id
        import uuid
        session_id = request.session_id or str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        
        # 在后台异步执行ReAct循环
        import asyncio
        
        async def execute_react_loop():
            try:
                # 添加上下文信息
                context = request.context or {}
                context["session_id"] = session_id
                context["task_id"] = task_id
                
                # 执行ReAct循环
                result = main_agent.react_loop(
                    task_description=request.description,
                    context=context,
                    max_iterations=request.max_iterations or 10
                )
                
                # 将结果存储到黑板，使用task_id作为key
                blackboard = app.state.blackboard
                blackboard.write_knowledge(
                    f"react_result_{task_id}",
                    result,
                    "main_agent"
                )
                
                # 发布完成事件
                main_agent.event_bus.publish(
                    EventType.TASK_COMPLETED,
                    {
                        "task_id": task_id,
                        "session_id": session_id,
                        "result": result
                    },
                    "main_agent"
                )
                
                print(f"[ReAct API] 任务完成: {task_id}")
            except Exception as e:
                print(f"[ReAct API] 任务执行失败: {e}")
                import traceback
                traceback.print_exc()
                
                # 发布失败事件
                main_agent.event_bus.publish(
                    EventType.TASK_FAILED,
                    {
                        "task_id": task_id,
                        "session_id": session_id,
                        "error": str(e)
                    },
                    "main_agent"
                )
        
        # 创建后台任务
        asyncio.create_task(execute_react_loop())
        
        return ReactTaskResponse(
            task_id=task_id,
            session_id=session_id,
            status="created",
            message=f"ReAct task created and is being executed"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{dag_id}", response_model=DAGStatusResponse)
async def get_task_status(dag_id: str):
    """
    获取任务状态
    
    Args:
        dag_id: DAG ID
        
    Returns:
        DAG状态响应
    """
    try:
        scheduler = app.state.scheduler
        blackboard = app.state.blackboard
        status = scheduler.get_dag_status(dag_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="DAG not found")
        
        dag = scheduler.get_dag(dag_id)
        
        # 构建详细的任务信息
        tasks_detail = []
        if dag:
            for task in dag.tasks.values():
                task_info = {
                    "task_id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "agent_role": task.agent_role,
                    "agent_id": task.agent_id,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "retry_count": task.retry_count,
                    "max_retries": task.max_retries
                }
                
                # 添加执行结果
                if task.result:
                    task_info["result"] = format_task_result(task.result)
                
                # 添加错误信息
                if task.error:
                    task_info["error"] = task.error
                
                # 添加依赖关系
                if task.dependencies:
                    dependencies_list = []
                    for dep_id in task.dependencies:
                        # 尝试找到对应的任务
                        dep_task = dag.tasks.get(dep_id) if dag else None
                        if dep_task:
                            dependencies_list.append({"task_id": dep_id, "name": dep_task.name})
                        else:
                            dependencies_list.append({"task_id": dep_id, "name": "Unknown"})
                    task_info["dependencies"] = dependencies_list
                
                tasks_detail.append(task_info)
        
        return DAGStatusResponse(
            dag_id=status["dag_id"],
            name=dag.name if dag else "",
            description=dag.description if dag else "",
            total_tasks=status["total_tasks"],
            status_counts=status["status_counts"],
            is_completed=status["is_completed"],
            tasks=tasks_detail,
            created_at=dag.created_at.isoformat() if dag and dag.created_at else None,
            completed_at=None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def format_task_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化任务结果
    
    Args:
        result: 原始结果
        
    Returns:
        格式化后的结果
    """
    formatted = {
        "method": result.get("skill_name", result.get("method", "unknown")),
        "completed_at": result.get("completed_at"),
        "summary": ""
    }
    
    # 根据执行方法提取摘要
    result_data = result.get("result", {})
    
    if isinstance(result_data, dict):
        # 处理steps字段 - 可能是整数（步骤数）或列表（步骤详情）
        if "steps" in result_data:
            steps_value = result_data["steps"]
            formatted["steps"] = steps_value
            if isinstance(steps_value, list):
                formatted["step_count"] = len(steps_value)
            elif isinstance(steps_value, int):
                formatted["step_count"] = steps_value
            else:
                formatted["step_count"] = 0
        
        if "output" in result_data:
            output = result_data["output"]
            formatted["output"] = output
            output_str = str(output) if not isinstance(output, str) else output
            formatted["summary"] = output_str[:200] + "..." if len(output_str) > 200 else output_str
        
        if "findings" in result_data:
            findings = result_data["findings"]
            formatted["findings"] = findings
            if not formatted["summary"]:
                findings_str = str(findings) if not isinstance(findings, str) else findings
                formatted["summary"] = findings_str[:200] + "..." if len(findings_str) > 200 else findings_str
        
        if "metrics" in result_data:
            formatted["metrics"] = result_data["metrics"]
        
        # 处理特定技能的结果
        if "research_result" in result_data:
            research = result_data["research_result"]
            formatted["type"] = "research"
            formatted["topic"] = research.get("topic")
            formatted["original_question"] = research.get("original_question")  # 原始问题
            formatted["answer_to_original_question"] = research.get("answer_to_original_question")  # 直接回答原始问题
            formatted["findings"] = research.get("findings")
            key_points = research.get("key_points")
            if key_points is not None:
                formatted["key_points"] = key_points
            data_sources = research.get("data_sources")
            if data_sources is not None:
                formatted["data_sources"] = data_sources
            data_points = research.get("data_points")
            if data_points is not None:
                formatted["data_points"] = data_points
            formatted["confidence"] = research.get("confidence")
            steps = research.get("steps")
            if steps is not None:
                formatted["steps"] = steps
                if isinstance(steps, list):
                    formatted["step_count"] = len(steps)
                elif isinstance(steps, int):
                    formatted["step_count"] = steps
                else:
                    formatted["step_count"] = 0
            # 优先使用answer_to_original_question作为摘要
            if research.get("answer_to_original_question"):
                answer_value = research["answer_to_original_question"]
                answer_str = str(answer_value) if not isinstance(answer_value, str) else answer_value
                formatted["summary"] = answer_str[:200] + "..." if len(answer_str) > 200 else answer_str
            elif not formatted["summary"]:
                findings_value = research.get("findings", "")
                findings_str = str(findings_value) if not isinstance(findings_value, str) else findings_value
                formatted["summary"] = findings_str[:200] + "..." if len(findings_str) > 200 else findings_str
        
        elif "analysis_result" in result_data:
            analysis = result_data["analysis_result"]
            formatted["type"] = "analysis"
            formatted["data"] = analysis.get("data")
            formatted["original_question"] = analysis.get("original_question")  # 原始问题
            formatted["answer_to_original_question"] = analysis.get("answer_to_original_question")  # 直接回答原始问题
            formatted["insights"] = analysis.get("insights")
            key_findings = analysis.get("key_findings")
            if key_findings is not None:
                formatted["key_findings"] = key_findings
            trends = analysis.get("trends")
            if trends is not None:
                formatted["trends"] = trends
            metrics = analysis.get("metrics")
            if metrics is not None:
                formatted["metrics"] = metrics
            steps = analysis.get("steps")
            if steps is not None:
                formatted["steps"] = steps
                if isinstance(steps, list):
                    formatted["step_count"] = len(steps)
                elif isinstance(steps, int):
                    formatted["step_count"] = steps
                else:
                    formatted["step_count"] = 0
            # 优先使用answer_to_original_question作为摘要
            if analysis.get("answer_to_original_question"):
                answer_value = analysis["answer_to_original_question"]
                answer_str = str(answer_value) if not isinstance(answer_value, str) else answer_value
                formatted["summary"] = answer_str[:200] + "..." if len(answer_str) > 200 else answer_str
            elif not formatted["summary"]:
                insights_value = analysis.get("insights", "")
                insights_str = str(insights_value) if not isinstance(insights_value, str) else insights_value
                formatted["summary"] = insights_str[:200] + "..." if len(insights_str) > 200 else insights_str
        
        elif "writing_result" in result_data:
            writing = result_data["writing_result"]
            formatted["type"] = "writing"
            formatted["content"] = writing.get("content")
            formatted["original_question"] = writing.get("original_question")  # 原始问题
            formatted["answer_to_original_question"] = writing.get("answer_to_original_question")  # 直接回答原始问题
            formatted["output"] = writing.get("output")
            key_points = writing.get("key_points")
            if key_points is not None:
                formatted["key_points"] = key_points
            style = writing.get("style")
            if style is not None:
                formatted["style"] = style
            word_count = writing.get("word_count")
            if word_count is not None:
                formatted["word_count"] = word_count
            readability_score = writing.get("readability_score")
            if readability_score is not None:
                formatted["readability_score"] = readability_score
            steps = writing.get("steps")
            if steps is not None:
                formatted["steps"] = steps
                if isinstance(steps, list):
                    formatted["step_count"] = len(steps)
                elif isinstance(steps, int):
                    formatted["step_count"] = steps
                else:
                    formatted["step_count"] = 0
            # 优先使用answer_to_original_question作为摘要
            if writing.get("answer_to_original_question"):
                answer_value = writing["answer_to_original_question"]
                answer_str = str(answer_value) if not isinstance(answer_value, str) else answer_value
                formatted["summary"] = answer_str[:200] + "..." if len(answer_str) > 200 else answer_str
            elif not formatted["summary"]:
                output_value = writing.get("output", "")
                output_str = str(output_value) if not isinstance(output_value, str) else output_value
                formatted["summary"] = output_str[:200] + "..." if len(output_str) > 200 else output_str
    else:
        # result_data不是字典的情况
        formatted["summary"] = str(result_data)
    
    # 处理错误情况
    if "error" in result:
        formatted["error"] = result["error"]
        formatted["summary"] = f"执行失败: {result['error']}"
    
    return formatted


@app.get("/api/tasks")
async def list_tasks():
    """
    列出所有任务
    
    Returns:
        任务列表
    """
    try:
        scheduler = app.state.scheduler
        dags = scheduler.get_all_dags()
        
        tasks_list = []
        for dag in dags:
            try:
                task_info = {
                    "dag_id": dag.id,
                    "name": dag.name,
                    "description": str(dag.description) if dag.description is not None else "",
                    "total_tasks": len(dag.tasks),
                    "created_at": dag.created_at.isoformat(),
                    "is_completed": dag.is_completed(),
                    "completed_at": None
                }
                
                # 添加任务摘要信息
                if dag.tasks:
                    completed_tasks = [t for t in dag.tasks.values() if t.status == TaskStatus.COMPLETED]
                    failed_tasks = [t for t in dag.tasks.values() if t.status == TaskStatus.FAILED]
                    
                    task_info["completed_count"] = len(completed_tasks)
                    task_info["failed_count"] = len(failed_tasks)
                    pending_tasks = [t for t in dag.tasks.values() if t.status == TaskStatus.PENDING]
                    task_info["pending_count"] = len(pending_tasks)
                    
                    # 添加最新的任务结果摘要
                    if completed_tasks:
                        latest_task = max(completed_tasks, key=lambda t: t.completed_at or t.created_at)
                        if latest_task.result:
                            formatted_result = format_task_result(latest_task.result)
                            task_info["latest_result"] = formatted_result
                            
                            # 添加最终回答字段，更清晰地展示
                            if formatted_result.get("answer_to_original_question"):
                                task_info["final_answer"] = {
                                    "question": formatted_result.get("original_question", ""),
                                    "answer": formatted_result.get("answer_to_original_question", ""),
                                    "summary": formatted_result.get("summary", ""),
                                    "method": formatted_result.get("method", "")
                                }
                    
                    # 添加所有完成的任务结果
                    if completed_tasks:
                        task_info["completed_results"] = []
                        for task in completed_tasks:
                            if task.result:
                                formatted_result = format_task_result(task.result)
                                task_info["completed_results"].append({
                                    "task_id": task.id,
                                    "task_name": task.name,
                                    "result": formatted_result,
                                    # 添加最终回答字段
                                    "final_answer": formatted_result.get("answer_to_original_question", "") if formatted_result.get("answer_to_original_question") else None
                                })
                        
                        # 添加综合最终回答（整合所有子任务的回答）
                        if task_info["completed_results"]:
                            all_answers = []
                            for result in task_info["completed_results"]:
                                answer = result["final_answer"] or result["result"].get("answer_to_original_question", "")
                                if answer:
                                    # 确保答案是字符串
                                    answer_str = str(answer) if not isinstance(answer, str) else answer
                                    all_answers.append(answer_str)
                            
                            if all_answers:
                                # 合并所有回答
                                combined_answer = " ".join(all_answers)
                                first_result = task_info["completed_results"][0]["result"]
                                original_question = first_result.get("original_question", "") if isinstance(first_result, dict) else ""
                                task_info["combined_final_answer"] = {
                                    "question": original_question,
                                    "answer": combined_answer,
                                    "summary": combined_answer[:200] + "..." if len(combined_answer) > 200 else combined_answer,
                                    "task_count": len(task_info["completed_results"])
                                }
                
                tasks_list.append(task_info)
            except Exception as e:
                print(f"处理DAG {dag.id} 时出错: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return {
            "total_count": len(dags),
            "tasks": tasks_list
        }
    except Exception as e:
        print(f"获取任务列表时出错: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents", response_model=AgentStatusResponse)
async def get_agents_status():
    """
    获取所有Agent状态
    
    Returns:
        Agent状态响应
    """
    try:
        blackboard = app.state.blackboard
        main_agent = app.state.main_agent
        dynamic_agent_manager = app.state.dynamic_agent_manager
        
        agents = blackboard.get_all_agents()
        sub_agents = [
            {
                "agent_id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "status": agent.status,
                "current_task_id": agent.current_task_id,
                "capabilities": agent.capabilities
            }
            for agent in agents
            if agent.type == "sub"
        ]
        
        # 如果有动态Agent管理器，添加统计信息
        dynamic_stats = None
        if dynamic_agent_manager:
            dynamic_stats = dynamic_agent_manager.get_agent_stats()
        
        return AgentStatusResponse(
            main_agent=main_agent.get_status(),
            sub_agents=sub_agents,
            dynamic_stats=dynamic_stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/blackboard")
async def get_blackboard():
    """
    获取黑板状态
    
    Returns:
        黑板快照
    """
    try:
        blackboard = app.state.blackboard
        return blackboard.get_snapshot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events")
async def get_events(limit: int = 100, session_id: Optional[str] = None, grouped: bool = True):
    """
    获取事件历史
    
    Args:
        limit: 最大返回数量
        session_id: 会话ID，用于按会话筛选
        grouped: 是否按会话分组显示（默认为True）
        
    Returns:
        事件列表或分组事件列表
    """
    try:
        event_bus = app.state.event_bus
        events = event_bus.get_history(limit=limit)
        
        # 如果指定了session_id，筛选相关事件
        if session_id:
            events = [
                event for event in events 
                if hasattr(event, 'data') and 
                   isinstance(event.data, dict) and 
                   event.data.get('session_id') == session_id
            ]
        
        # 如果要求按会话分组
        if grouped:
            # 过滤掉没有session_id的系统事件
            filtered_events = []
            for event in events:
                event_dict = event.to_dict()
                event_data = event_dict.get('data', {})
                event_session_id = event_data.get('session_id')
                
                # 只保留有session_id的事件
                if event_session_id:
                    filtered_events.append(event_dict)
            
            # 按会话ID分组事件
            session_events = {}
            for event_dict in filtered_events:
                event_data = event_dict.get('data', {})
                event_session_id = event_data.get('session_id')
                
                if event_session_id not in session_events:
                    session_events[event_session_id] = []
                
                session_events[event_session_id].append(event_dict)
            
            # 转换为分组格式
            grouped_events = []
            for session_id_key, session_event_list in session_events.items():
                # 获取会话的第一个任务描述作为会话名称
                session_name = f"会话 {session_id_key[:8]}"
                for event in session_event_list:
                    event_data = event.get('data', {})
                    if event.get('type') == 'TASK_CREATED' and event_data.get('description'):
                        description = event_data['description']
                        description_str = str(description) if not isinstance(description, str) else description
                        session_name = description_str[:30]
                        break
                
                grouped_events.append({
                    "session_id": session_id_key,
                    "session_name": session_name,
                    "event_count": len(session_event_list),
                    "events": session_event_list
                })
            
            # 按时间排序（最新的会话在前）
            grouped_events.sort(key=lambda x: x['events'][0].get('timestamp', ''), reverse=True)
            
            return {
                "total": len(filtered_events),
                "session_count": len(grouped_events),
                "grouped": True,
                "events": grouped_events
            }
        else:
            return {
                "total": len(events),
                "session_id": session_id,
                "grouped": False,
                "events": [event.to_dict() for event in events]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions", response_model=SessionListResponse)
async def get_sessions():
    """
    获取会话列表
    
    Returns:
        会话列表
    """
    try:
        scheduler = app.state.scheduler
        dags = scheduler.get_all_dags()
        
        # 按session_id分组DAG
        sessions = {}
        for dag in dags:
            session_id = dag.metadata.get('session_id') if dag.metadata else None
            if not session_id:
                session_id = "default"
            
            if session_id not in sessions:
                sessions[session_id] = {
                    "session_id": session_id,
                    "task_count": 0,
                    "latest_task": None,
                    "latest_final_answer": None,  # 添加最新最终回答
                    "created_at": dag.created_at,
                    "updated_at": dag.created_at
                }
            
            sessions[session_id]["task_count"] += 1
            
            # 检查是否有完成的任务
            completed_tasks = [t for t in dag.tasks.values() if t.status == TaskStatus.COMPLETED]
            if completed_tasks:
                # 获取最新的最终回答
                for task in completed_tasks:
                    if task.result:
                        formatted_result = format_task_result(task.result)
                        if formatted_result.get("answer_to_original_question"):
                            sessions[session_id]["latest_final_answer"] = {
                                "question": formatted_result.get("original_question", ""),
                                "answer": formatted_result.get("answer_to_original_question", ""),
                                "summary": formatted_result.get("summary", ""),
                                "method": formatted_result.get("method", "")
                            }
                            break
            
            if not sessions[session_id]["latest_task"] or (dag.created_at and sessions[session_id]["updated_at"] and dag.created_at > sessions[session_id]["updated_at"]):
                sessions[session_id]["latest_task"] = dag.name
                sessions[session_id]["updated_at"] = dag.created_at
        
        # 转换为SessionInfo列表
        session_list = [
            SessionInfo(
                session_id=session_data["session_id"],
                task_count=session_data["task_count"],
                latest_task=session_data["latest_task"],
                latest_final_answer=session_data.get("latest_final_answer"),
                created_at=session_data["created_at"].isoformat() if session_data["created_at"] else None,
                updated_at=session_data["updated_at"].isoformat() if session_data["updated_at"] else None
            )
            for session_data in sessions.values()
        ]
        
        # 按更新时间排序
        session_list.sort(key=lambda x: x.updated_at or "", reverse=True)
        
        return SessionListResponse(
            sessions=session_list,
            total_count=len(session_list)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/tasks")
async def get_session_tasks(session_id: str):
    """
    获取指定会话的任务列表
    
    Args:
        session_id: 会话ID
        
    Returns:
        任务列表
    """
    try:
        scheduler = app.state.scheduler
        dags = scheduler.get_all_dags()
        
        # 筛选指定会话的DAG
        session_dags = [
            dag for dag in dags 
            if dag.metadata and dag.metadata.get('session_id') == session_id
        ]
        
        tasks_list = []
        for dag in session_dags:
            task_info = {
                "dag_id": dag.id,
                "name": dag.name,
                "description": str(dag.description) if dag.description is not None else "",
                "total_tasks": len(dag.tasks),
                "created_at": dag.created_at.isoformat() if dag.created_at else None,
                "is_completed": dag.is_completed(),
                "completed_at": None
            }
            
            # 添加任务摘要信息
            if dag.tasks:
                completed_tasks = [t for t in dag.tasks.values() if t.status == TaskStatus.COMPLETED]
                failed_tasks = [t for t in dag.tasks.values() if t.status == TaskStatus.FAILED]
                
                task_info["completed_count"] = len(completed_tasks)
                task_info["failed_count"] = len(failed_tasks)
                pending_tasks = [t for t in dag.tasks.values() if t.status == TaskStatus.PENDING]
                task_info["pending_count"] = len(pending_tasks)
                
                # 添加最新的任务结果摘要
                if completed_tasks:
                    latest_task = max(completed_tasks, key=lambda t: t.completed_at or t.created_at)
                    if latest_task.result:
                        formatted_result = format_task_result(latest_task.result)
                        task_info["latest_result"] = formatted_result
                        
                        # 添加最终回答字段，更清晰地展示
                        if formatted_result.get("answer_to_original_question"):
                            task_info["final_answer"] = {
                                "question": formatted_result.get("original_question", ""),
                                "answer": formatted_result.get("answer_to_original_question", ""),
                                "summary": formatted_result.get("summary", ""),
                                "method": formatted_result.get("method", "")
                            }
                
                # 添加所有完成的任务结果
                if completed_tasks:
                    task_info["completed_results"] = []
                    for task in completed_tasks:
                        if task.result:
                            formatted_result = format_task_result(task.result)
                            task_info["completed_results"].append({
                                "task_id": task.id,
                                "task_name": task.name,
                                "result": formatted_result,
                                # 添加最终回答字段
                                "final_answer": formatted_result.get("answer_to_original_question", "") if formatted_result.get("answer_to_original_question") else None
                            })
                    
                    # 添加综合最终回答（整合所有子任务的回答）
                    if task_info["completed_results"]:
                        all_answers = []
                        for result in task_info["completed_results"]:
                            answer = result["final_answer"] or result["result"].get("answer_to_original_question", "")
                            if answer:
                                # 确保答案是字符串
                                answer_str = str(answer) if not isinstance(answer, str) else answer
                                all_answers.append(answer_str)
                        
                        if all_answers:
                            # 合并所有回答
                            combined_answer = " ".join(all_answers)
                            first_result = task_info["completed_results"][0]["result"]
                            original_question = first_result.get("original_question", "") if isinstance(first_result, dict) else ""
                            task_info["combined_final_answer"] = {
                                "question": original_question,
                                "answer": combined_answer,
                                "summary": combined_answer[:200] + "..." if len(combined_answer) > 200 else combined_answer,
                                "task_count": len(task_info["completed_results"])
                            }
            
            tasks_list.append(task_info)
        
        return {
            "session_id": session_id,
            "total_tasks": len(tasks_list),
            "tasks": tasks_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/react/{task_id}")
async def get_react_task_result(task_id: str):
    """
    获取ReAct任务的结果
    
    Args:
        task_id: ReAct任务ID
        
    Returns:
        ReAct任务结果
    """
    try:
        blackboard = app.state.blackboard
        
        # 从黑板获取ReAct任务结果
        result_key = f"react_result_{task_id}"
        result = blackboard.get_knowledge(result_key)
        
        if result:
            return result
        
        # 如果没有找到结果，返回空结果
        return {
            "task_id": task_id,
            "status": "not_found",
            "message": "ReAct task result not found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/skills")
async def get_skills():
    """
    获取所有技能
    
    Returns:
        技能列表
    """
    try:
        skill_registry = app.state.skill_registry
        skills = skill_registry.get_all_skills()
        
        return {
            "total": len(skills),
            "skills": [
                {
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "type": skill.type.value,
                    "is_active": skill.is_active,
                    "required_capabilities": skill.required_capabilities
                }
                for skill in skills
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/skills")
async def register_skill(skill_data: Dict[str, Any]):
    """
    注册新技能
    
    Args:
        skill_data: 技能数据
        
    Returns:
        注册结果
    """
    try:
        skill_registry = app.state.skill_registry
        
        from core.models import Skill, SkillType
        
        skill = Skill(
            name=skill_data.get("name", ""),
            description=skill_data.get("description", ""),
            type=SkillType(skill_data.get("type", "function")),
            required_capabilities=skill_data.get("capabilities", []),
            config=skill_data.get("config", {})
        )
        
        skill_registry.register(skill)
        
        return {
            "skill_id": skill.id,
            "status": "registered",
            "message": "Skill registered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/skills/{skill_id}")
async def unregister_skill(skill_id: str):
    """
    注销技能
    
    Args:
        skill_id: 技能ID
        
    Returns:
        注销结果
    """
    try:
        skill_registry = app.state.skill_registry
        skill_registry.unregister(skill_id)
        
        return {
            "skill_id": skill_id,
            "status": "unregistered",
            "message": "Skill unregistered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory")
async def get_memory():
    """
    获取向量记忆
    
    Returns:
        记忆列表
    """
    try:
        vector_memory = app.state.vector_memory
        memories = vector_memory.get_all()
        
        return {
            "total": len(memories),
            "memories": [
                {
                    "id": mem.id,
                    "content": mem.content,
                    "metadata": mem.metadata,
                    "created_at": mem.created_at.isoformat(),
                    "access_count": mem.access_count
                }
                for mem in memories
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/search")
async def search_memory(query: str, top_k: int = 5):
    """
    搜索记忆
    
    Args:
        query: 查询内容
        top_k: 返回结果数量
        
    Returns:
        搜索结果
    """
    try:
        vector_memory = app.state.vector_memory
        results = vector_memory.search(query, top_k=top_k)
        
        return {
            "query": query,
            "total": len(results),
            "results": [
                {
                    "id": mem.id,
                    "content": mem.content,
                    "similarity": similarity,
                    "metadata": mem.metadata
                }
                for mem, similarity in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory")
async def add_memory(content: str, metadata: Optional[Dict[str, Any]] = None):
    """
    添加记忆
    
    Args:
        content: 内容
        metadata: 元数据
        
    Returns:
        添加结果
    """
    try:
        vector_memory = app.state.vector_memory
        memory_id = vector_memory.add(content, metadata=metadata)
        
        return {
            "memory_id": memory_id,
            "status": "added",
            "message": "Memory added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket端点
    
    实时推送事件更新
    """
    await manager.connect(websocket)
    
    try:
        event_bus = app.state.event_bus
        
        def event_handler(event):
            asyncio.create_task(websocket.send_json(event.to_dict()))
        
        event_bus.subscribe(EventType.TASK_CREATED, event_handler)
        event_bus.subscribe(EventType.TASK_STARTED, event_handler)
        event_bus.subscribe(EventType.TASK_COMPLETED, event_handler)
        event_bus.subscribe(EventType.TASK_FAILED, event_handler)
        event_bus.subscribe(EventType.DAG_UPDATED, event_handler)
        
        while True:
            await websocket.receive_text()
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.get("/health")
async def health_check():
    """
    健康检查
    
    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "version": "2.0.0"
    }


@app.get("/api/agent-interaction-graph/{dag_id}")
async def get_agent_interaction_graph(dag_id: str):
    """
    获取Agent交互图
    
    Args:
        dag_id: DAG ID
        
    Returns:
        Agent交互图数据
    """
    try:
        blackboard = app.state.blackboard
        scheduler = app.state.scheduler
        dynamic_agent_manager = app.state.dynamic_agent_manager
        
        # 获取DAG信息
        dag = scheduler.get_dag(dag_id)
        if not dag:
            raise HTTPException(status_code=404, detail=f"DAG {dag_id} not found")
        
        # 构建节点和边
        nodes = []
        edges = []
        
        # 添加主Agent节点
        main_agent = app.state.main_agent
        nodes.append({
            "id": "main_agent",
            "name": "Main Agent (Planner)",
            "role": "planner",
            "type": "main",
            "status": "active",
            "position": {"x": 400, "y": 50}
        })
        
        # 获取所有子任务
        tasks = list(dag.tasks.values())
        
        # 按agent角色分组任务
        agent_tasks = {}
        for task in tasks:
            agent_role = task.agent_role or "unknown"
            if agent_role not in agent_tasks:
                agent_tasks[agent_role] = []
            agent_tasks[agent_role].append(task)
        
        # 为每个agent创建节点
        y_position = 150
        x_position = 100
        agent_positions = {}
        
        for agent_role, role_tasks in agent_tasks.items():
            # 获取该角色的agent实例
            agents = dynamic_agent_manager.get_agents_by_role(agent_role) if dynamic_agent_manager else []
            agent = agents[0] if agents else None
            
            agent_id = agent.agent_id if agent else f"{agent_role}_1"
            agent_status = agent.agent.status if agent and hasattr(agent, 'agent') else "unknown"
            
            # 添加agent节点
            nodes.append({
                "id": agent_id,
                "name": agent_id,
                "role": agent_role,
                "type": "sub",
                "status": agent_status,
                "position": {"x": x_position, "y": y_position},
                "task_count": len(role_tasks)
            })
            
            agent_positions[agent_role] = agent_id
            x_position += 200
            
            # 如果x_position超过800，换行
            if x_position > 800:
                x_position = 100
                y_position += 150
        
        # 添加任务节点和边
        task_positions = {}
        for i, task in enumerate(tasks):
            agent_role = task.agent_role or "unknown"
            agent_id = agent_positions.get(agent_role, "unknown")
            
            # 任务节点位置（在agent节点下方）
            task_x = nodes[nodes.index(next(n for n in nodes if n["id"] == agent_id))]["position"]["x"]
            task_y = nodes[nodes.index(next(n for n in nodes if n["id"] == agent_id))]["position"]["y"] + 100 + (i % 3) * 60
            
            nodes.append({
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "type": "task",
                "status": task.status.value if task.status else "pending",
                "agent_role": agent_role,
                "priority": task.priority.value if task.priority else 2,
                "position": {"x": task_x, "y": task_y}
            })
            
            task_positions[i] = task.id
            
            # 添加agent到任务的边
            edges.append({
                "from": agent_id,
                "to": task.id,
                "type": "assignment",
                "label": "执行"
            })
        
        # 添加任务依赖关系的边
        for i, task in enumerate(tasks):
            if hasattr(task, 'dependencies') and task.dependencies:
                for dep_idx in task.dependencies:
                    if dep_idx in task_positions:
                        edges.append({
                            "from": task_positions[dep_idx],
                            "to": task.id,
                            "type": "dependency",
                            "label": "依赖"
                        })
        
        # 添加主Agent到第一个任务的边
        if tasks:
            first_task = tasks[0]
            first_task_agent_role = first_task.agent_role or "unknown"
            first_task_agent_id = agent_positions.get(first_task_agent_role, "unknown")
            
            edges.append({
                "from": "main_agent",
                "to": first_task_agent_id,
                "type": "assignment",
                "label": "分配"
            })
        
        return {
            "dag_id": dag_id,
            "dag_name": dag.name,
            "dag_description": dag.description,
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "total_agents": len(agent_positions),
                "total_tasks": len(tasks),
                "completed_tasks": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
                "failed_tasks": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
                "pending_tasks": sum(1 for t in tasks if t.status == TaskStatus.PENDING)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent-details/{agent_id}")
async def get_agent_details(agent_id: str):
    """
    获取Agent详细信息，包括工具调用和最终结果
    
    Args:
        agent_id: Agent ID
        
    Returns:
        Agent详细信息
    """
    try:
        dynamic_agent_manager = app.state.dynamic_agent_manager
        blackboard = app.state.blackboard
        
        # 获取agent实例
        agent = dynamic_agent_manager.get_agent_by_id(agent_id) if dynamic_agent_manager else None
        if not agent:
            # 尝试从黑板获取
            all_agents = blackboard.get_all_agents()
            agent = next((a for a in all_agents if (a.id if hasattr(a, 'id') else a.agent_id) == agent_id), None)
            
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        # 获取agent的ID（兼容不同的agent对象）
        agent_id_value = agent.id if hasattr(agent, 'id') else agent.agent_id
        agent_name = agent.name if hasattr(agent, 'name') else agent.agent_id
        agent_role = agent.role if hasattr(agent, 'role') else agent.agent_role
        agent_status = agent.status if hasattr(agent, 'status') else 'unknown'
        
        # 获取agent的工作记忆
        working_memory = []
        if hasattr(agent, 'context_manager'):
            context = agent.context_manager._context
            working_memory = context.get('working_memory', [])
        
        # 获取agent的任务历史
        task_history = []
        if hasattr(agent, 'task_history'):
            task_history = agent.task_history
        
        # 获取agent的当前任务
        current_task = None
        if hasattr(agent, 'current_task_id') and agent.current_task_id:
            current_task = blackboard.get_task(agent.current_task_id)
        
        # 获取agent的统计信息
        stats = {
            "total_tasks_executed": len(task_history),
            "successful_tasks": sum(1 for t in task_history if t.get('status') == 'completed'),
            "failed_tasks": sum(1 for t in task_history if t.get('status') == 'failed'),
            "total_tool_calls": sum(len(wm.get('content', '').split('调用工具')) - 1 for wm in working_memory if '调用工具' in wm.get('content', ''))
        }
        
        return {
            "agent_id": agent_id_value,
            "name": agent_name,
            "role": agent_role,
            "status": agent_status,
            "capabilities": agent.capabilities if hasattr(agent, 'capabilities') else [],
            "current_task": {
                "id": current_task.id if current_task else None,
                "name": current_task.name if current_task else None,
                "description": current_task.description if current_task else None,
                "status": current_task.status.value if current_task and current_task.status else None
            } if current_task else None,
            "working_memory": working_memory,
            "task_history": task_history,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/task-details/{task_id}")
async def get_task_details(task_id: str):
    """
    获取任务详细信息，包括工具调用和结果
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务详细信息
    """
    try:
        blackboard = app.state.blackboard
        scheduler = app.state.scheduler
        
        # 获取任务
        task = blackboard.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # 获取任务结果
        result = blackboard.get_task_result(task_id)
        
        # 获取任务的DAG信息
        dag_id = None
        for dag in scheduler.get_all_dags():
            if task_id in [t.id for t in dag.tasks]:
                dag_id = dag.id
                break
        
        return {
            "task_id": task.id,
            "name": task.name,
            "description": task.description,
            "status": task.status.value if task.status else "pending",
            "priority": task.priority.value if task.priority else 2,
            "agent_role": task.agent_role,
            "agent_id": task.agent_id,
            "dag_id": dag_id,
            "result": result,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def create_app(
    event_bus: EventBus,
    blackboard: Blackboard,
    scheduler: TaskDAGScheduler,
    skill_registry: SkillRegistry,
    vector_memory: VectorMemoryService,
    main_agent: MainAgent,
    dynamic_agent_manager: Optional[Any] = None
) -> FastAPI:
    """
    创建应用
    
    Args:
        event_bus: 事件总线
        blackboard: 黑板
        scheduler: 任务调度器
        skill_registry: 技能注册表
        vector_memory: 向量记忆服务
        main_agent: 主Agent
        dynamic_agent_manager: 动态Agent管理器
        
    Returns:
        FastAPI应用
    """
    app.state.event_bus = event_bus
    app.state.blackboard = blackboard
    app.state.scheduler = scheduler
    app.state.skill_registry = skill_registry
    app.state.vector_memory = vector_memory
    app.state.main_agent = main_agent
    app.state.dynamic_agent_manager = dynamic_agent_manager
    
    return app