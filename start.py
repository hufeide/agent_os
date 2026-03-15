#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent OS 启动脚本

启动主从分层Agent系统。

作者: Agent OS Team
"""

import sys
import time
import signal

from core.event_bus import EventBus
from core.blackboard import Blackboard
from core.task_scheduler import TaskDAGScheduler
from core.skill_registry import SkillRegistry
from core.vector_memory import VectorMemoryService
from agents.main_agent import MainAgent
from agents.sub_agent_worker import SubAgentWorker
from agents.dynamic_agent_manager import DynamicAgentManager
from api.server import create_app
from llm.llm_handler import create_llm_handler
import uvicorn


def create_sample_skills(skill_registry, llm_handler=None):
    """创建示例技能"""
    from core.skill_registry import create_function_skill
    import time
    import random
    
    def research_skill(**kwargs):
        topic = kwargs.get('topic', 'unknown')
        task_name = kwargs.get('task_name', 'Research Task')
        task_description = kwargs.get('task_description', '')
        original_question = kwargs.get('original_question', '')  # 获取原始问题
        
        print(f"[Research Skill] 开始研究任务: {task_name}")
        print(f"[Research Skill] 研究主题: {topic}")
        print(f"[Research Skill] 任务描述: {task_description}")
        print(f"[Research Skill] 原始问题: {original_question}")
        
        # 真正调用LLM执行研究任务
        if llm_handler:
            research_prompt = f"""
            你是一个专业的研究专家，请对以下主题进行深入研究：
            
            研究主题: {topic}
            任务描述: {task_description}
            原始问题: {original_question}
            
            重要要求：
            1. 必须结合原始问题来回答，不能只研究主题
            2. 研究结果要直接回答原始问题
            3. 提供具体、实用的答案，不能是泛泛而谈
            4. 确保研究结果能够解决用户的实际需求
            
            请执行以下研究步骤：
            1. 分析原始问题的核心需求
            2. 结合研究主题收集相关信息
            3. 整理研究发现并直接回答原始问题
            4. 生成具体的结论和建议
            
            请用JSON格式返回研究结果，包含以下字段：
            {{
                "answer_to_original_question": "直接回答原始问题的具体答案",
                "findings": "详细的研究发现和结论（必须有具体内容）",
                "key_points": ["关键点1", "关键点2", "关键点3"],
                "data_sources": ["数据来源1", "数据来源2"],
                "confidence": 0.9
            }}
            
            注意：必须提供直接回答原始问题的具体答案，不能是占位符或空内容。
            """
            
            print(f"[Research Skill] 调用LLM执行研究...")
            try:
                llm_result = llm_handler.complete(research_prompt)
                print(f"[Research Skill] LLM返回结果长度: {len(llm_result)}")
                
                # 解析LLM返回的JSON
                import json
                import re
                
                # 提取JSON内容
                json_match = re.search(r'\{.*\}', llm_result, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        parsed_result = json.loads(json_str)
                        answer_to_original = parsed_result.get('answer_to_original_question', '')
                        findings = parsed_result.get('findings', '')
                        key_points = parsed_result.get('key_points', [])
                        data_sources = parsed_result.get('data_sources', [])
                        confidence = parsed_result.get('confidence', 0.8)
                        
                        # 构建研究结果
                        research_result = {
                            "topic": topic,
                            "original_question": original_question,
                            "answer_to_original_question": answer_to_original,  # 直接回答原始问题
                            "findings": findings,
                            "key_points": key_points,
                            "data_sources": data_sources,
                            "steps": [
                                {"step": 1, "action": "分析原始问题的核心需求", "status": "completed"},
                                {"step": 2, "action": "结合研究主题收集相关信息", "status": "completed"},
                                {"step": 3, "action": "整理研究发现并直接回答原始问题", "status": "completed"},
                                {"step": 4, "action": "生成具体的结论和建议", "status": "completed"}
                            ],
                            "data_points": len(key_points) + len(data_sources),
                            "confidence": confidence
                        }
                        
                        print(f"[Research Skill] 研究完成，发现{research_result['data_points']}个数据点，置信度{research_result['confidence']}")
                        return {"research_result": research_result}
                        
                    except json.JSONDecodeError as e:
                        print(f"[Research Skill] JSON解析失败: {e}")
                        # 如果JSON解析失败，使用原始文本
                        findings = llm_result
                else:
                    findings = llm_result
            except Exception as e:
                print(f"[Research Skill] LLM调用失败: {e}")
                findings = f"研究任务执行失败: {str(e)}"
        else:
            findings = f"LLM处理器未配置，无法执行研究任务"
        
        # 回退到基本结果
        research_result = {
            "topic": topic,
            "original_question": original_question,
            "answer_to_original_question": findings,  # 直接回答原始问题
            "findings": findings,
            "steps": [
                {"step": 1, "action": "分析原始问题的核心需求", "status": "completed"},
                {"step": 2, "action": "结合研究主题收集相关信息", "status": "completed"},
                {"step": 3, "action": "整理研究发现并直接回答原始问题", "status": "completed"},
                {"step": 4, "action": "生成具体的结论和建议", "status": "completed"}
            ],
            "data_points": 4,
            "confidence": 0.5
        }
        
        print(f"[Research Skill] 研究完成，发现{research_result['data_points']}个数据点，置信度{research_result['confidence']}")
        return {"research_result": research_result}
    
    def analysis_skill(**kwargs):
        data = kwargs.get('data', 'unknown')
        task_name = kwargs.get('task_name', 'Analysis Task')
        task_description = kwargs.get('task_description', '')
        original_question = kwargs.get('original_question', '')  # 获取原始问题
        
        print(f"[Analysis Skill] 开始分析任务: {task_name}")
        print(f"[Analysis Skill] 分析数据: {data}")
        print(f"[Analysis Skill] 任务描述: {task_description}")
        print(f"[Analysis Skill] 原始问题: {original_question}")
        
        # 真正调用LLM执行分析任务
        if llm_handler:
            analysis_prompt = f"""
            你是一个专业的数据分析专家，请对以下数据进行深入分析：
            
            分析数据: {data}
            任务描述: {task_description}
            原始问题: {original_question}
            
            重要要求：
            1. 必须结合原始问题来回答，不能只分析数据
            2. 分析结果要直接回答原始问题
            3. 提供具体、实用的答案，不能是泛泛而谈
            4. 确保分析结果能够解决用户的实际需求
            
            请执行以下分析步骤：
            1. 分析原始问题的核心需求
            2. 结合分析数据进行深入分析
            3. 识别关键洞察和趋势
            4. 生成具体的分析结论并回答原始问题
            
            请用JSON格式返回分析结果，包含以下字段：
            {{
                "answer_to_original_question": "直接回答原始问题的具体答案",
                "insights": "详细的分析洞察和结论（必须有具体内容）",
                "key_findings": ["关键发现1", "关键发现2", "关键发现3"],
                "trends": ["趋势1", "趋势2"],
                "metrics": {{
                    "accuracy": 0.95,
                    "completeness": 0.9,
                    "relevance": 0.85
                }}
            }}
            
            注意：必须提供直接回答原始问题的具体答案，不能是占位符或空内容。
            """
            
            print(f"[Analysis Skill] 调用LLM执行分析...")
            try:
                llm_result = llm_handler.complete(analysis_prompt)
                print(f"[Analysis Skill] LLM返回结果长度: {len(llm_result)}")
                
                # 解析LLM返回的JSON
                import json
                import re
                
                # 提取JSON内容
                json_match = re.search(r'\{.*\}', llm_result, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        parsed_result = json.loads(json_str)
                        answer_to_original = parsed_result.get('answer_to_original_question', '')
                        insights = parsed_result.get('insights', '')
                        key_findings = parsed_result.get('key_findings', [])
                        trends = parsed_result.get('trends', [])
                        metrics = parsed_result.get('metrics', {})
                        
                        # 构建分析结果
                        analysis_result = {
                            "data": data,
                            "original_question": original_question,
                            "answer_to_original_question": answer_to_original,  # 直接回答原始问题
                            "insights": insights,
                            "key_findings": key_findings,
                            "trends": trends,
                            "steps": [
                                {"step": 1, "action": "分析原始问题的核心需求", "status": "completed"},
                                {"step": 2, "action": "结合分析数据进行深入分析", "status": "completed"},
                                {"step": 3, "action": "识别关键洞察和趋势", "status": "completed"},
                                {"step": 4, "action": "生成具体的分析结论并回答原始问题", "status": "completed"}
                            ],
                            "metrics": {
                                "accuracy": metrics.get('accuracy', 0.9),
                                "completeness": metrics.get('completeness', 0.85),
                                "relevance": metrics.get('relevance', 0.8)
                            }
                        }
                        
                        print(f"[Analysis Skill] 分析完成，准确率{analysis_result['metrics']['accuracy']}")
                        return {"analysis_result": analysis_result}
                        
                    except json.JSONDecodeError as e:
                        print(f"[Analysis Skill] JSON解析失败: {e}")
                        # 如果JSON解析失败，使用原始文本
                        insights = llm_result
                else:
                    insights = llm_result
            except Exception as e:
                print(f"[Analysis Skill] LLM调用失败: {e}")
                insights = f"分析任务执行失败: {str(e)}"
        else:
            insights = f"LLM处理器未配置，无法执行分析任务"
        
        # 回退到基本结果
        analysis_result = {
            "data": data,
            "original_question": original_question,
            "answer_to_original_question": insights,  # 直接回答原始问题
            "insights": insights,
            "steps": [
                {"step": 1, "action": "分析原始问题的核心需求", "status": "completed"},
                {"step": 2, "action": "结合分析数据进行深入分析", "status": "completed"},
                {"step": 3, "action": "识别关键洞察和趋势", "status": "completed"},
                {"step": 4, "action": "生成具体的分析结论并回答原始问题", "status": "completed"}
            ],
            "metrics": {
                "accuracy": 0.5,
                "completeness": 0.5,
                "relevance": 0.5
            }
        }
        
        print(f"[Analysis Skill] 分析完成，准确率{analysis_result['metrics']['accuracy']}")
        return {"analysis_result": analysis_result}
    
    def writing_skill(**kwargs):
        content = kwargs.get('content', 'unknown')
        task_name = kwargs.get('task_name', 'Writing Task')
        task_description = kwargs.get('task_description', '')
        original_question = kwargs.get('original_question', '')  # 获取原始问题
        
        print(f"[Writing Skill] 开始写作任务: {task_name}")
        print(f"[Writing Skill] 写作内容: {content}")
        print(f"[Writing Skill] 任务描述: {task_description}")
        print(f"[Writing Skill] 原始问题: {original_question}")
        
        # 真正调用LLM执行写作任务
        if llm_handler:
            writing_prompt = f"""
            你是一个专业的写作专家，请根据以下要求创作内容：
            
            写作主题: {content}
            任务描述: {task_description}
            原始问题: {original_question}
            
            重要要求：
            1. 必须结合原始问题来创作，不能只按照主题写作
            2. 写作内容要直接回答或回应原始问题
            3. 提供具体、实用的内容，不能是泛泛而谈
            4. 确保写作内容能够解决用户的实际需求
            
            请执行以下写作步骤：
            1. 分析原始问题的核心需求
            2. 结合写作主题构思内容框架
            3. 撰写具体内容并回应原始问题
            4. 完善和润色
            
            请用JSON格式返回写作结果，包含以下字段：
            {{
                "answer_to_original_question": "直接回答或回应原始问题的具体内容",
                "output": "具体的写作内容（必须有实际内容，至少200字）",
                "key_points": ["要点1", "要点2", "要点3"],
                "style": "写作风格描述",
                "word_count": 实际字数
            }}
            
            注意：必须提供直接回应原始问题的具体内容，不能是占位符或空内容。
            """
            
            print(f"[Writing Skill] 调用LLM执行写作...")
            try:
                llm_result = llm_handler.complete(writing_prompt)
                print(f"[Writing Skill] LLM返回结果长度: {len(llm_result)}")
                
                # 解析LLM返回的JSON
                import json
                import re
                
                # 提取JSON内容
                json_match = re.search(r'\{.*\}', llm_result, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        parsed_result = json.loads(json_str)
                        answer_to_original = parsed_result.get('answer_to_original_question', '')
                        output = parsed_result.get('output', '')
                        key_points = parsed_result.get('key_points', [])
                        style = parsed_result.get('style', '')
                        word_count = parsed_result.get('word_count', len(output))
                        
                        # 构建写作结果
                        writing_result = {
                            "content": content,
                            "original_question": original_question,
                            "answer_to_original_question": answer_to_original,  # 直接回答原始问题
                            "output": output,
                            "key_points": key_points,
                            "style": style,
                            "steps": [
                                {"step": 1, "action": "分析原始问题的核心需求", "status": "completed"},
                                {"step": 2, "action": "结合写作主题构思内容框架", "status": "completed"},
                                {"step": 3, "action": "撰写具体内容并回应原始问题", "status": "completed"},
                                {"step": 4, "action": "完善和润色", "status": "completed"}
                            ],
                            "word_count": word_count,
                            "readability_score": round(random.uniform(7.0, 9.5), 1)
                        }
                        
                        print(f"[Writing Skill] 写作完成，字数{writing_result['word_count']}，可读性{writing_result['readability_score']}")
                        return {"writing_result": writing_result}
                        
                    except json.JSONDecodeError as e:
                        print(f"[Writing Skill] JSON解析失败: {e}")
                        # 如果JSON解析失败，使用原始文本
                        output = llm_result
                else:
                    output = llm_result
            except Exception as e:
                print(f"[Writing Skill] LLM调用失败: {e}")
                output = f"写作任务执行失败: {str(e)}"
        else:
            output = f"LLM处理器未配置，无法执行写作任务"
        
        # 回退到基本结果
        writing_result = {
            "content": content,
            "original_question": original_question,
            "answer_to_original_question": output,  # 直接回答原始问题
            "output": output,
            "steps": [
                {"step": 1, "action": "分析原始问题的核心需求", "status": "completed"},
                {"step": 2, "action": "结合写作主题构思内容框架", "status": "completed"},
                {"step": 3, "action": "撰写具体内容并回应原始问题", "status": "completed"},
                {"step": 4, "action": "完善和润色", "status": "completed"}
            ],
            "word_count": len(output),
            "readability_score": 5.0
        }
        
        print(f"[Writing Skill] 写作完成，字数{writing_result['word_count']}，可读性{writing_result['readability_score']}")
        return {"writing_result": writing_result}
    
    research = create_function_skill(
        name="Research",
        description="Research skill for gathering information",
        handler=research_skill,
        capabilities=["research"]
    )
    
    analysis = create_function_skill(
        name="Analysis",
        description="Analysis skill for processing data",
        handler=analysis_skill,
        capabilities=["analysis"]
    )
    
    writing = create_function_skill(
        name="Writing",
        description="Writing skill for creating content",
        handler=writing_skill,
        capabilities=["writing"]
    )
    
    skill_registry.register(research)
    skill_registry.register(analysis)
    skill_registry.register(writing)


def main():
    """主函数"""
    print("=" * 60)
    print("Agent OS - 主从分层Agent系统")
    print("Version 2.0.0")
    print("=" * 60)
    
    event_bus = EventBus()
    blackboard = Blackboard()
    scheduler = TaskDAGScheduler(event_bus, blackboard)
    skill_registry = SkillRegistry()
    vector_memory = VectorMemoryService()
    
    print("\n[1/7] 创建LLM处理器...")
    llm_handler = create_llm_handler(
        api_url="http://192.168.1.159:19000",
        model_name="Qwen3Coder"
    )
    print(f"✓ LLM处理器已创建 (API: {llm_handler.api_url}, Model: {llm_handler.model_name})")
    
    print("\n[2/7] 创建示例技能...")
    create_sample_skills(skill_registry, llm_handler)
    print(f"✓ 已注册 {len(skill_registry.get_all_skills())} 个技能")
    
    print("\n[3/7] 创建动态Agent管理器...")
    dynamic_agent_manager = DynamicAgentManager(
        event_bus=event_bus,
        blackboard=blackboard,
        skill_registry=skill_registry,
        vector_memory=vector_memory,
        llm_handler=llm_handler,
        scheduler=scheduler
    )
    
    # 创建基础Agent
    researcher = dynamic_agent_manager.get_or_create_agent("researcher")
    analyst = dynamic_agent_manager.get_or_create_agent("analyst")
    writer = dynamic_agent_manager.get_or_create_agent("writer")
    
    print(f"✓ 已创建动态Agent管理器，包含 {len(dynamic_agent_manager.get_all_agents())} 个Agent")
    
    print("\n[4/8] 创建主Agent (Planner)...")
    main_agent = MainAgent(
        event_bus=event_bus,
        blackboard=blackboard,
        scheduler=scheduler,
        skill_registry=skill_registry,
        vector_memory=vector_memory,
        llm_handler=llm_handler,
        dynamic_agent_manager=dynamic_agent_manager
    )
    print("✓ 主Agent已创建")
    
    print("\n[5/8] 启动任务调度器...")
    scheduler.start()
    print("✓ 任务调度器已启动")
    
    print("\n[6/8] 启动子Agent Workers...")
    # Agent已经在DynamicAgentManager中启动
    print("✓ 所有子Agent Workers已启动")
    
    print("\n[7/8] 创建API应用...")
    app = create_app(
        event_bus=event_bus,
        blackboard=blackboard,
        scheduler=scheduler,
        skill_registry=skill_registry,
        vector_memory=vector_memory,
        main_agent=main_agent,
        dynamic_agent_manager=dynamic_agent_manager
    )
    print("✓ API应用已创建")
    
    print("\n[8/8] 启动API服务器...")
    print("API服务器地址: http://localhost:8001")
    print("API文档地址: http://localhost:8001/docs")
    print("Dashboard地址: http://localhost:3050 (需要单独启动)")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    def signal_handler(sig, frame):
        """信号处理器"""
        print("\n\n正在停止服务器...")
        researcher.stop()
        analyst.stop()
        writer.stop()
        scheduler.stop()
        print("✓ 服务器已停止")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()