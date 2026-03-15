#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能执行测试脚本

测试各个技能的详细执行过程。

作者: Agent OS Team
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.skill_registry import SkillRegistry, create_function_skill
import time
import random


def create_enhanced_skills(skill_registry):
    """创建增强的技能"""
    
    def research_skill(**kwargs):
        topic = kwargs.get('topic', 'unknown')
        task_name = kwargs.get('task_name', 'Research Task')
        
        print(f"[Research Skill] 开始研究任务: {task_name}")
        print(f"[Research Skill] 研究主题: {topic}")
        
        # 模拟研究过程
        research_steps = [
            "收集相关信息",
            "分析数据来源", 
            "验证信息准确性",
            "整理研究结果"
        ]
        
        results = []
        for i, step in enumerate(research_steps):
            time.sleep(0.5)  # 模拟处理时间
            print(f"[Research Skill] 步骤{i+1}/{len(research_steps)}: {step}")
            results.append({
                "step": i+1,
                "action": step,
                "status": "completed"
            })
        
        research_result = {
            "topic": topic,
            "findings": f"关于'{topic}'的研究已完成，共执行了{len(research_steps)}个研究步骤",
            "steps": results,
            "data_points": random.randint(5, 15),
            "confidence": round(random.uniform(0.7, 0.95), 2)
        }
        
        print(f"[Research Skill] 研究完成，发现{research_result['data_points']}个数据点，置信度{research_result['confidence']}")
        
        return {"research_result": research_result}
    
    def analysis_skill(**kwargs):
        data = kwargs.get('data', 'unknown')
        task_name = kwargs.get('task_name', 'Analysis Task')
        
        print(f"[Analysis Skill] 开始分析任务: {task_name}")
        print(f"[Analysis Skill] 分析数据: {data}")
        
        # 模拟分析过程
        analysis_steps = [
            "数据预处理",
            "统计分析",
            "模式识别",
            "生成洞察"
        ]
        
        results = []
        for i, step in enumerate(analysis_steps):
            time.sleep(0.5)
            print(f"[Analysis Skill] 步骤{i+1}/{len(analysis_steps)}: {step}")
            results.append({
                "step": i+1,
                "action": step,
                "status": "completed"
            })
        
        analysis_result = {
            "data": data,
            "insights": f"对'{data}'的分析已完成，共执行了{len(analysis_steps)}个分析步骤",
            "steps": results,
            "metrics": {
                "accuracy": round(random.uniform(0.8, 0.98), 2),
                "completeness": round(random.uniform(0.85, 0.99), 2),
                "relevance": round(random.uniform(0.75, 0.95), 2)
            }
        }
        
        print(f"[Analysis Skill] 分析完成，准确率{analysis_result['metrics']['accuracy']}")
        
        return {"analysis_result": analysis_result}
    
    def writing_skill(**kwargs):
        content = kwargs.get('content', 'unknown')
        task_name = kwargs.get('task_name', 'Writing Task')
        
        print(f"[Writing Skill] 开始写作任务: {task_name}")
        print(f"[Writing Skill] 写作内容: {content}")
        
        # 模拟写作过程
        writing_steps = [
            "大纲规划",
            "内容起草",
            "润色修改",
            "最终定稿"
        ]
        
        results = []
        for i, step in enumerate(writing_steps):
            time.sleep(0.5)
            print(f"[Writing Skill] 步骤{i+1}/{len(writing_steps)}: {step}")
            results.append({
                "step": i+1,
                "action": step,
                "status": "completed"
            })
        
        writing_result = {
            "content": content,
            "output": f"基于'{content}'的文档已完成，共执行了{len(writing_steps)}个写作步骤",
            "steps": results,
            "word_count": random.randint(200, 800),
            "readability_score": round(random.uniform(7.0, 9.5), 1)
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


def test_skills():
    """测试各个技能"""
    
    print("=" * 60)
    print("技能执行测试")
    print("=" * 60)
    
    skill_registry = SkillRegistry()
    create_enhanced_skills(skill_registry)
    
    # 获取所有技能
    all_skills = skill_registry.get_all_skills()
    print(f"\n已注册的技能数量: {len(all_skills)}")
    for skill in all_skills:
        print(f"  - {skill.name} (ID: {skill.id[:8]}...)")
    
    print("\n[1/3] 测试Research技能...")
    research_skill = None
    for skill in all_skills:
        if skill.name == "Research":
            research_skill = skill
            break
    
    if research_skill:
        print(f"✓ 找到Research技能: {research_skill.name}")
        print(f"  描述: {research_skill.description}")
        print(f"  能力: {research_skill.required_capabilities}")
        print(f"  类型: {research_skill.type}")
        
        # 调用技能
        result = research_skill.handler(
            topic="人工智能发展趋势",
            task_name="研究AI发展"
        )
        print(f"\n✓ Research技能执行完成")
        print(f"  结果: {result}")
    else:
        print("✗ 未找到Research技能")
    
    print("\n[2/3] 测试Analysis技能...")
    analysis_skill = None
    for skill in all_skills:
        if skill.name == "Analysis":
            analysis_skill = skill
            break
    
    if analysis_skill:
        print(f"✓ 找到Analysis技能: {analysis_skill.name}")
        print(f"  描述: {analysis_skill.description}")
        print(f"  能力: {analysis_skill.required_capabilities}")
        print(f"  类型: {analysis_skill.type}")
        
        result = analysis_skill.handler(
            data="用户行为数据",
            task_name="分析用户行为"
        )
        print(f"\n✓ Analysis技能执行完成")
        print(f"  结果: {result}")
    else:
        print("✗ 未找到Analysis技能")
    
    print("\n[3/3] 测试Writing技能...")
    writing_skill = None
    for skill in all_skills:
        if skill.name == "Writing":
            writing_skill = skill
            break
    
    if writing_skill:
        print(f"✓ 找到Writing技能: {writing_skill.name}")
        print(f"  描述: {writing_skill.description}")
        print(f"  能力: {writing_skill.required_capabilities}")
        print(f"  类型: {writing_skill.type}")
        
        result = writing_skill.handler(
            content="技术报告",
            task_name="撰写技术报告"
        )
        print(f"\n✓ Writing技能执行完成")
        print(f"  结果: {result}")
    else:
        print("✗ 未找到Writing技能")
    
    print("\n" + "=" * 60)
    print("技能测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_skills()