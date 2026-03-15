#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试 - 核心模块

测试核心数据模型、事件总线、黑板等。

作者: Agent OS Team
"""

import unittest
import time
from datetime import datetime

from core.models import Task, DAG, TaskStatus, TaskPriority, EventType, Event, Skill, SkillType, Agent
from core.event_bus import EventBus
from core.blackboard import Blackboard
from core.skill_registry import SkillRegistry, create_function_skill
from core.vector_memory import VectorMemoryService


class TestModels(unittest.TestCase):
    """测试数据模型"""
    
    def test_task_creation(self):
        """测试任务创建"""
        task = Task(
            name="Test Task",
            description="A test task",
            priority=TaskPriority.HIGH
        )
        
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertIsNotNone(task.id)
    
    def test_dag_creation(self):
        """测试DAG创建"""
        dag = DAG(
            name="Test DAG",
            description="A test DAG"
        )
        
        self.assertEqual(dag.name, "Test DAG")
        self.assertEqual(len(dag.tasks), 0)
        self.assertEqual(len(dag.root_tasks), 0)
        self.assertIsNotNone(dag.id)
    
    def test_dag_add_task(self):
        """测试DAG添加任务"""
        dag = DAG(name="Test DAG")
        task = Task(name="Task 1")
        
        dag.add_task(task)
        
        self.assertEqual(len(dag.tasks), 1)
        self.assertEqual(len(dag.root_tasks), 1)
        self.assertIn(task.id, dag.tasks)
    
    def test_dag_add_dependency(self):
        """测试DAG添加依赖"""
        dag = DAG(name="Test DAG")
        task1 = Task(name="Task 1")
        task2 = Task(name="Task 2")
        
        dag.add_task(task1)
        dag.add_task(task2)
        dag.add_dependency(task2.id, task1.id)
        
        self.assertIn(task1.id, task2.dependencies)
        self.assertIn(task2.id, task1.dependents)
        self.assertNotIn(task2.id, dag.root_tasks)
    
    def test_dag_get_ready_tasks(self):
        """测试获取可执行任务"""
        dag = DAG(name="Test DAG")
        task1 = Task(name="Task 1")
        task2 = Task(name="Task 2")
        
        dag.add_task(task1)
        dag.add_task(task2)
        dag.add_dependency(task2.id, task1.id)
        
        ready_tasks = dag.get_ready_tasks()
        
        self.assertEqual(len(ready_tasks), 1)
        self.assertEqual(ready_tasks[0].id, task1.id)
    
    def test_dag_update_task_status(self):
        """测试更新任务状态"""
        dag = DAG(name="Test DAG")
        task = Task(name="Task 1")
        
        dag.add_task(task)
        dag.update_task_status(task.id, TaskStatus.RUNNING)
        
        self.assertEqual(task.status, TaskStatus.RUNNING)
        self.assertIsNotNone(task.started_at)
        
        dag.update_task_status(task.id, TaskStatus.COMPLETED, result={"success": True})
        
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.result, {"success": True})
    
    def test_dag_is_completed(self):
        """测试DAG完成状态"""
        dag = DAG(name="Test DAG")
        task1 = Task(name="Task 1")
        task2 = Task(name="Task 2")
        
        dag.add_task(task1)
        dag.add_task(task2)
        
        self.assertFalse(dag.is_completed())
        
        dag.update_task_status(task1.id, TaskStatus.COMPLETED)
        self.assertFalse(dag.is_completed())
        
        dag.update_task_status(task2.id, TaskStatus.COMPLETED)
        self.assertTrue(dag.is_completed())


class TestEventBus(unittest.TestCase):
    """测试事件总线"""
    
    def setUp(self):
        """设置测试环境"""
        self.event_bus = EventBus()
        self.events_received = []
    
    def test_subscribe_publish(self):
        """测试订阅和发布"""
        def callback(event):
            self.events_received.append(event)
        
        self.event_bus.subscribe(EventType.TASK_CREATED, callback)
        self.event_bus.publish(
            EventType.TASK_CREATED,
            {"task_id": "test"},
            "test_source"
        )
        
        self.assertEqual(len(self.events_received), 1)
        self.assertEqual(self.events_received[0].type, EventType.TASK_CREATED)
        self.assertEqual(self.events_received[0].data["task_id"], "test")
    
    def test_unsubscribe(self):
        """测试取消订阅"""
        def callback(event):
            self.events_received.append(event)
        
        self.event_bus.subscribe(EventType.TASK_CREATED, callback)
        self.event_bus.unsubscribe(EventType.TASK_CREATED, callback)
        self.event_bus.publish(EventType.TASK_CREATED, {}, "test")
        
        self.assertEqual(len(self.events_received), 0)
    
    def test_multiple_subscribers(self):
        """测试多个订阅者"""
        def callback1(event):
            self.events_received.append("callback1")
        
        def callback2(event):
            self.events_received.append("callback2")
        
        self.event_bus.subscribe(EventType.TASK_CREATED, callback1)
        self.event_bus.subscribe(EventType.TASK_CREATED, callback2)
        self.event_bus.publish(EventType.TASK_CREATED, {}, "test")
        
        self.assertEqual(len(self.events_received), 2)
        self.assertIn("callback1", self.events_received)
        self.assertIn("callback2", self.events_received)
    
    def test_event_history(self):
        """测试事件历史"""
        self.event_bus.publish(EventType.TASK_CREATED, {}, "test1")
        self.event_bus.publish(EventType.TASK_STARTED, {}, "test2")
        self.event_bus.publish(EventType.TASK_COMPLETED, {}, "test3")
        
        history = self.event_bus.get_history()
        
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0].type, EventType.TASK_CREATED)
        self.assertEqual(history[1].type, EventType.TASK_STARTED)
        self.assertEqual(history[2].type, EventType.TASK_COMPLETED)
    
    def test_event_history_filter(self):
        """测试事件历史过滤"""
        self.event_bus.publish(EventType.TASK_CREATED, {}, "test1")
        self.event_bus.publish(EventType.TASK_STARTED, {}, "test2")
        self.event_bus.publish(EventType.TASK_CREATED, {}, "test3")
        
        history = self.event_bus.get_history(event_type=EventType.TASK_CREATED)
        
        self.assertEqual(len(history), 2)
        for event in history:
            self.assertEqual(event.type, EventType.TASK_CREATED)


class TestBlackboard(unittest.TestCase):
    """测试黑板系统"""
    
    def setUp(self):
        """设置测试环境"""
        self.blackboard = Blackboard()
    
    def test_write_read_task(self):
        """测试写入和读取任务"""
        task = Task(name="Test Task")
        self.blackboard.write_task(task)
        
        read_task = self.blackboard.read_task(task.id)
        
        self.assertIsNotNone(read_task)
        self.assertEqual(read_task.id, task.id)
        self.assertEqual(read_task.name, "Test Task")
    
    def test_write_read_knowledge(self):
        """测试写入和读取知识"""
        self.blackboard.write_knowledge("test_key", {"value": 123}, "test_agent")
        
        value = self.blackboard.read_knowledge("test_key")
        
        self.assertEqual(value, {"value": 123})
    
    def test_write_read_result(self):
        """测试写入和读取结果"""
        self.blackboard.write_result("task_1", {"result": "success"}, "agent_1")
        
        result = self.blackboard.read_result("task_1")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.task_id, "task_1")
        self.assertEqual(result.agent_id, "agent_1")
        self.assertEqual(result.value, {"result": "success"})
    
    def test_register_unregister_agent(self):
        """测试注册和注销Agent"""
        agent = Agent(id="agent_1", name="Test Agent", role="test")
        
        self.blackboard.register_agent(agent)
        read_agent = self.blackboard.get_agent("agent_1")
        
        self.assertIsNotNone(read_agent)
        self.assertEqual(read_agent.id, "agent_1")
        
        self.blackboard.unregister_agent("agent_1")
        read_agent = self.blackboard.get_agent("agent_1")
        
        self.assertIsNone(read_agent)
    
    def test_save_load_dag(self):
        """测试保存和加载DAG"""
        dag = DAG(name="Test DAG")
        task = Task(name="Task 1")
        dag.add_task(task)
        
        self.blackboard.save_dag(dag)
        loaded_dag = self.blackboard.load_dag(dag.id)
        
        self.assertIsNotNone(loaded_dag)
        self.assertEqual(loaded_dag.id, dag.id)
        self.assertEqual(loaded_dag.name, "Test DAG")
        self.assertEqual(len(loaded_dag.tasks), 1)
    
    def test_version(self):
        """测试版本号"""
        initial_version = self.blackboard.get_version()
        
        task = Task(name="Test Task")
        self.blackboard.write_task(task)
        
        new_version = self.blackboard.get_version()
        
        self.assertEqual(new_version, initial_version + 1)
    
    def test_clear(self):
        """测试清空黑板"""
        task = Task(name="Test Task")
        self.blackboard.write_task(task)
        self.blackboard.write_knowledge("key", "value", "agent")
        
        self.assertEqual(len(self.blackboard.get_all_tasks()), 1)
        self.assertEqual(len(self.blackboard.get_all_knowledge()), 1)
        
        self.blackboard.clear()
        
        self.assertEqual(len(self.blackboard.get_all_tasks()), 0)
        self.assertEqual(len(self.blackboard.get_all_knowledge()), 0)


class TestSkillRegistry(unittest.TestCase):
    """测试技能注册表"""
    
    def setUp(self):
        """设置测试环境"""
        self.skill_registry = SkillRegistry()
    
    def test_register_skill(self):
        """测试注册技能"""
        def test_handler(**kwargs):
            return kwargs
        
        skill = Skill(
            name="Test Skill",
            description="A test skill",
            type=SkillType.FUNCTION,
            handler=test_handler,
            required_capabilities=["test"]
        )
        
        self.skill_registry.register(skill)
        
        retrieved_skill = self.skill_registry.get_skill(skill.id)
        
        self.assertIsNotNone(retrieved_skill)
        self.assertEqual(retrieved_skill.name, "Test Skill")
        self.assertEqual(retrieved_skill.type, SkillType.FUNCTION)
    
    def test_unregister_skill(self):
        """测试注销技能"""
        skill = Skill(name="Test Skill", type=SkillType.FUNCTION)
        self.skill_registry.register(skill)
        
        self.skill_registry.unregister(skill.id)
        
        retrieved_skill = self.skill_registry.get_skill(skill.id)
        
        self.assertIsNone(retrieved_skill)
    
    def test_get_skills_by_type(self):
        """测试按类型获取技能"""
        skill1 = Skill(name="Skill 1", type=SkillType.FUNCTION)
        skill2 = Skill(name="Skill 2", type=SkillType.LLM)
        skill3 = Skill(name="Skill 3", type=SkillType.FUNCTION)
        
        self.skill_registry.register(skill1)
        self.skill_registry.register(skill2)
        self.skill_registry.register(skill3)
        
        function_skills = self.skill_registry.get_skills_by_type(SkillType.FUNCTION)
        
        self.assertEqual(len(function_skills), 2)
    
    def test_execute_skill(self):
        """测试执行技能"""
        def test_handler(**kwargs):
            return kwargs
        
        skill = Skill(
            name="Test Skill",
            type=SkillType.FUNCTION,
            handler=test_handler
        )
        
        self.skill_registry.register(skill)
        
        result = self.skill_registry.execute_skill(skill.id, test_arg="test_value")
        
        self.assertEqual(result, {"test_arg": "test_value"})
    
    def test_activate_deactivate_skill(self):
        """测试激活和停用技能"""
        skill = Skill(name="Test Skill", type=SkillType.FUNCTION)
        self.skill_registry.register(skill)
        
        self.skill_registry.deactivate_skill(skill.id)
        retrieved_skill = self.skill_registry.get_skill(skill.id)
        
        self.assertFalse(retrieved_skill.is_active)
        
        self.skill_registry.activate_skill(skill.id)
        retrieved_skill = self.skill_registry.get_skill(skill.id)
        
        self.assertTrue(retrieved_skill.is_active)


class TestVectorMemory(unittest.TestCase):
    """测试向量记忆服务"""
    
    def setUp(self):
        """设置测试环境"""
        self.vector_memory = VectorMemoryService()
    
    def test_add_memory(self):
        """测试添加记忆"""
        memory_id = self.vector_memory.add(
            content="Test content",
            metadata={"key": "value"}
        )
        
        self.assertIsNotNone(memory_id)
        
        memory = self.vector_memory.get(memory_id)
        
        self.assertIsNotNone(memory)
        self.assertEqual(memory.content, "Test content")
        self.assertEqual(memory.metadata, {"key": "value"})
    
    def test_search_memory(self):
        """测试搜索记忆"""
        self.vector_memory.add(content="Python programming")
        self.vector_memory.add(content="JavaScript development")
        self.vector_memory.add(content="Python data science")
        
        results = self.vector_memory.search("Python", top_k=2)
        
        self.assertLessEqual(len(results), 2)
        self.assertGreater(len(results), 0)
    
    def test_update_memory(self):
        """测试更新记忆"""
        memory_id = self.vector_memory.add(content="Original content")
        
        success = self.vector_memory.update(
            memory_id,
            content="Updated content"
        )
        
        self.assertTrue(success)
        
        memory = self.vector_memory.get(memory_id)
        
        self.assertEqual(memory.content, "Updated content")
    
    def test_delete_memory(self):
        """测试删除记忆"""
        memory_id = self.vector_memory.add(content="Test content")
        
        success = self.vector_memory.delete(memory_id)
        
        self.assertTrue(success)
        
        memory = self.vector_memory.get(memory_id)
        
        self.assertIsNone(memory)
    
    def test_statistics(self):
        """测试统计信息"""
        self.vector_memory.add(content="Content 1")
        self.vector_memory.add(content="Content 2")
        self.vector_memory.add(content="Content 3")
        
        stats = self.vector_memory.get_statistics()
        
        self.assertEqual(stats["total_memories"], 3)
    
    def test_clear(self):
        """测试清空记忆"""
        self.vector_memory.add(content="Content 1")
        self.vector_memory.add(content="Content 2")
        
        self.assertEqual(len(self.vector_memory.get_all()), 2)
        
        self.vector_memory.clear()
        
        self.assertEqual(len(self.vector_memory.get_all()), 0)


if __name__ == '__main__':
    unittest.main()