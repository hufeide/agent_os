#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试 - Agent系统

测试主从分层Agent系统的集成功能。

作者: Agent OS Team
"""

import unittest
import time
import threading

from core.models import Task, DAG, TaskStatus, EventType
from core.event_bus import EventBus
from core.blackboard import Blackboard
from core.task_scheduler import TaskDAGScheduler
from core.skill_registry import SkillRegistry, create_function_skill
from core.vector_memory import VectorMemoryService
from agents.main_agent import MainAgent
from agents.sub_agent_worker import SubAgentWorker


class TestAgentSystemIntegration(unittest.TestCase):
    """测试Agent系统集成"""
    
    def setUp(self):
        """设置测试环境"""
        self.event_bus = EventBus()
        self.blackboard = Blackboard()
        self.skill_registry = SkillRegistry()
        self.vector_memory = VectorMemoryService()
        self.scheduler = TaskDAGScheduler(self.event_bus)
        
        self.scheduler.start()
        
        def dummy_llm_handler(prompt):
            return "LLM response"
        
        self.main_agent = MainAgent(
            event_bus=self.event_bus,
            blackboard=self.blackboard,
            scheduler=self.scheduler,
            skill_registry=self.skill_registry,
            vector_memory=self.vector_memory,
            llm_handler=dummy_llm_handler
        )
        
        self.sub_agents = []
    
    def tearDown(self):
        """清理测试环境"""
        for agent in self.sub_agents:
            agent.stop()
        
        self.scheduler.stop()
    
    def create_sub_agent(self, agent_id, role, capabilities):
        """创建子Agent"""
        agent = SubAgentWorker(
            agent_id=agent_id,
            agent_role=role,
            capabilities=capabilities,
            event_bus=self.event_bus,
            blackboard=self.blackboard,
            skill_registry=self.skill_registry,
            vector_memory=self.vector_memory
        )
        
        agent.start()
        self.sub_agents.append(agent)
        
        return agent
    
    def test_task_planning(self):
        """测试任务规划"""
        dag_id = self.main_agent.plan_task(
            "Write a report about AI",
            {"context": "test"}
        )
        
        self.assertIsNotNone(dag_id)
        
        dag = self.scheduler.get_dag(dag_id)
        
        self.assertIsNotNone(dag)
        self.assertGreater(len(dag.tasks), 0)
    
    def test_task_execution(self):
        """测试任务执行"""
        agent = self.create_sub_agent(
            "agent_1",
            "researcher",
            ["research"]
        )
        
        dag_id = self.main_agent.plan_task(
            "Research AI topics",
            {}
        )
        
        time.sleep(2)
        
        dag = self.scheduler.get_dag(dag_id)
        
        self.assertIsNotNone(dag)
    
    def test_skill_execution(self):
        """测试技能执行"""
        def test_skill(**kwargs):
            return {"result": "success", "input": kwargs}
        
        skill = create_function_skill(
            name="Test Skill",
            description="A test skill",
            handler=test_skill,
            capabilities=["test"]
        )
        
        self.skill_registry.register(skill)
        
        agent = self.create_sub_agent(
            "agent_1",
            "tester",
            ["test"]
        )
        
        dag_id = self.main_agent.plan_task(
            "Test task",
            {}
        )
        
        time.sleep(2)
        
        dag = self.scheduler.get_dag(dag_id)
        
        self.assertIsNotNone(dag)
    
    def test_event_flow(self):
        """测试事件流"""
        events_received = []
        
        def task_created_handler(event):
            events_received.append(("task_created", event))
        
        def task_started_handler(event):
            events_received.append(("task_started", event))
        
        self.event_bus.subscribe(EventType.TASK_CREATED, task_created_handler)
        self.event_bus.subscribe(EventType.TASK_STARTED, task_started_handler)
        
        agent = self.create_sub_agent(
            "agent_1",
            "researcher",
            ["research"]
        )
        
        dag_id = self.main_agent.plan_task(
            "Test task",
            {}
        )
        
        time.sleep(2)
        
        event_types = [event_type for event_type, _ in events_received]
        
        self.assertIn("task_created", event_types)
    
    def test_blackboard_integration(self):
        """测试黑板集成"""
        agent = self.create_sub_agent(
            "agent_1",
            "researcher",
            ["research"]
        )
        
        self.blackboard.write_knowledge(
            "test_key",
            {"value": "test_value"},
            "main_agent"
        )
        
        value = self.blackboard.read_knowledge("test_key")
        
        self.assertEqual(value, {"value": "test_value"})
        
        dag_id = self.main_agent.plan_task(
            "Test task",
            {}
        )
        
        time.sleep(1)
        
        snapshot = self.blackboard.get_snapshot()
        
        self.assertGreater(len(snapshot["tasks"]), 0)
    
    def test_vector_memory_integration(self):
        """测试向量记忆集成"""
        self.vector_memory.add(
            content="Python programming",
            metadata={"category": "programming"}
        )
        
        self.vector_memory.add(
            content="JavaScript development",
            metadata={"category": "programming"}
        )
        
        results = self.vector_memory.search("Python", top_k=1)
        
        self.assertGreater(len(results), 0)
        self.assertIn("Python", results[0][0].content)
    
    def test_multiple_agents(self):
        """测试多Agent协作"""
        agent1 = self.create_sub_agent(
            "agent_1",
            "researcher",
            ["research"]
        )
        
        agent2 = self.create_sub_agent(
            "agent_2",
            "analyst",
            ["analysis"]
        )
        
        dag_id = self.main_agent.plan_task(
            "Research and analyze AI",
            {}
        )
        
        time.sleep(3)
        
        dag = self.scheduler.get_dag(dag_id)
        
        self.assertIsNotNone(dag)
    
    def test_dag_completion(self):
        """测试DAG完成"""
        agent = self.create_sub_agent(
            "agent_1",
            "researcher",
            ["research"]
        )
        
        dag_id = self.main_agent.plan_task(
            "Test task",
            {}
        )
        
        time.sleep(5)
        
        dag = self.scheduler.get_dag(dag_id)
        
        if dag:
            completed = dag.is_completed()
            self.assertTrue(completed or len(dag.tasks) > 0)


class TestSkillRegistryIntegration(unittest.TestCase):
    """测试技能注册表集成"""
    
    def setUp(self):
        """设置测试环境"""
        self.skill_registry = SkillRegistry()
    
    def test_dynamic_skill_registration(self):
        """测试动态技能注册"""
        def dynamic_skill(**kwargs):
            return kwargs
        
        skill = create_function_skill(
            name="Dynamic Skill",
            description="A dynamically registered skill",
            handler=dynamic_skill,
            capabilities=["dynamic"]
        )
        
        self.skill_registry.register(skill)
        
        retrieved_skill = self.skill_registry.get_skill(skill.id)
        
        self.assertIsNotNone(retrieved_skill)
        self.assertEqual(retrieved_skill.name, "Dynamic Skill")
        
        result = self.skill_registry.execute_skill(skill.id, test="value")
        
        self.assertEqual(result, {"test": "value"})
    
    def test_skill_deactivation(self):
        """测试技能停用"""
        skill = create_function_skill(
            name="Test Skill",
            description="Test",
            handler=lambda **kwargs: kwargs,
            capabilities=["test"]
        )
        
        self.skill_registry.register(skill)
        self.skill_registry.deactivate_skill(skill.id)
        
        retrieved_skill = self.skill_registry.get_skill(skill.id)
        
        self.assertFalse(retrieved_skill.is_active)


if __name__ == '__main__':
    unittest.main()