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
        if "steps" in result_data:
            formatted["steps"] = result_data["steps"]
            formatted["step_count"] = len(result_data["steps"])
        
        if "output" in result_data:
            output = result_data["output"]
            formatted["output"] = output
            formatted["summary"] = str(output)[:200] + "..." if len(str(output)) > 200 else str(output)
        
        if "findings" in result_data:
            formatted["findings"] = result_data["findings"]
            if not formatted["summary"]:
                formatted["summary"] = str(result_data["findings"])[:200] + "..." if len(str(result_data["findings"])) > 200 else str(result_data["findings"])
        
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
            formatted["key_points"] = research.get("key_points", [])
            formatted["data_sources"] = research.get("data_sources", [])
            formatted["data_points"] = research.get("data_points")
            formatted["confidence"] = research.get("confidence")
            formatted["steps"] = research.get("steps", [])
            formatted["step_count"] = len(research.get("steps", []))
            # 优先使用answer_to_original_question作为摘要
            if research.get("answer_to_original_question"):
                formatted["summary"] = research["answer_to_original_question"][:200] + "..." if len(research["answer_to_original_question"]) > 200 else research["answer_to_original_question"]
            elif not formatted["summary"]:
                formatted["summary"] = research.get("findings", "")[:200] + "..." if len(research.get("findings", "")) > 200 else research.get("findings", "")
        
        elif "analysis_result" in result_data:
            analysis = result_data["analysis_result"]
            formatted["type"] = "analysis"
            formatted["data"] = analysis.get("data")
            formatted["original_question"] = analysis.get("original_question")  # 原始问题
            formatted["answer_to_original_question"] = analysis.get("answer_to_original_question")  # 直接回答原始问题
            formatted["insights"] = analysis.get("insights")
            formatted["key_findings"] = analysis.get("key_findings", [])
            formatted["trends"] = analysis.get("trends", [])
            formatted["metrics"] = analysis.get("metrics", {})
            formatted["steps"] = analysis.get("steps", [])
            formatted["step_count"] = len(analysis.get("steps", []))
            # 优先使用answer_to_original_question作为摘要
            if analysis.get("answer_to_original_question"):
                formatted["summary"] = analysis["answer_to_original_question"][:200] + "..." if len(analysis["answer_to_original_question"]) > 200 else analysis["answer_to_original_question"]
            elif not formatted["summary"]:
                formatted["summary"] = analysis.get("insights", "")[:200] + "..." if len(analysis.get("insights", "")) > 200 else analysis.get("insights", "")
        
        elif "writing_result" in result_data:
            writing = result_data["writing_result"]
            formatted["type"] = "writing"
            formatted["content"] = writing.get("content")
            formatted["original_question"] = writing.get("original_question")  # 原始问题
            formatted["answer_to_original_question"] = writing.get("answer_to_original_question")  # 直接回答原始问题
            formatted["output"] = writing.get("output")
            formatted["key_points"] = writing.get("key_points", [])
            formatted["style"] = writing.get("style", "")
            formatted["word_count"] = writing.get("word_count")
            formatted["readability_score"] = writing.get("readability_score")
            formatted["steps"] = writing.get("steps", [])
            formatted["step_count"] = len(writing.get("steps", []))
            # 优先使用answer_to_original_question作为摘要
            if writing.get("answer_to_original_question"):
                formatted["summary"] = writing["answer_to_original_question"][:200] + "..." if len(writing["answer_to_original_question"]) > 200 else writing["answer_to_original_question"]
            elif not formatted["summary"]:
                formatted["summary"] = writing.get("output", "")[:200] + "..." if len(writing.get("output", "")) > 200 else writing.get("output", "")
    
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
            task_info = {
                "dag_id": dag.id,
                "name": dag.name,
                "description": dag.description,
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
                        all_answers = [
                            result["final_answer"] or result["result"].get("answer_to_original_question", "")
                            for result in task_info["completed_results"]
                            if result["final_answer"] or result["result"].get("answer_to_original_question")
                        ]
                        
                        if all_answers:
                            # 合并所有回答
                            combined_answer = " ".join(all_answers)
                            task_info["combined_final_answer"] = {
                                "question": task_info["completed_results"][0]["result"].get("original_question", ""),
                                "answer": combined_answer,
                                "summary": combined_answer[:200] + "..." if len(combined_answer) > 200 else combined_answer,
                                "task_count": len(task_info["completed_results"])
                            }
            
            tasks_list.append(task_info)
        
        return {
            "total_count": len(dags),
            "tasks": tasks_list
        }
    except Exception as e:
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
                        session_name = event_data['description'][:30]
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
                "description": dag.description,
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
                        all_answers = [
                            result["final_answer"] or result["result"].get("answer_to_original_question", "")
                            for result in task_info["completed_results"]
                            if result["final_answer"] or result["result"].get("answer_to_original_question")
                        ]
                        
                        if all_answers:
                            # 合并所有回答
                            combined_answer = " ".join(all_answers)
                            task_info["combined_final_answer"] = {
                                "question": task_info["completed_results"][0]["result"].get("original_question", ""),
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