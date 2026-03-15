#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务调试工具

提供任务创建、监控和调试功能。

作者: Agent OS Team
"""

import requests
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime


class TaskDebugger:
    """
    任务调试器
    
    提供任务调试和监控功能。
    """
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        初始化调试器
        
        Args:
            base_url: API基础URL
        """
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.last_event_count = 0
    
    def create_task(self, description: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建任务
        
        Args:
            description: 任务描述
            context: 任务上下文
            
        Returns:
            创建结果
        """
        if context is None:
            context = {}
        
        try:
            response = requests.post(
                f"{self.api_url}/tasks",
                json={
                    "description": description,
                    "context": context
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 任务创建成功: {result['dag_id']}")
                return result
            else:
                print(f"✗ 任务创建失败: {response.status_code}")
                print(f"  错误信息: {response.text}")
                return {}
        
        except Exception as e:
            print(f"✗ 任务创建异常: {e}")
            return {}
    
    def get_tasks(self) -> Dict[str, Any]:
        """
        获取任务列表
        
        Returns:
            任务列表
        """
        try:
            response = requests.get(f"{self.api_url}/tasks")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"✗ 获取任务失败: {response.status_code}")
                return {}
        
        except Exception as e:
            print(f"✗ 获取任务异常: {e}")
            return {}
    
    def get_events(self, limit: int = 50) -> Dict[str, Any]:
        """
        获取事件列表
        
        Args:
            limit: 事件数量限制
            
        Returns:
            事件列表
        """
        try:
            response = requests.get(f"{self.api_url}/events", params={"limit": limit})
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"✗ 获取事件失败: {response.status_code}")
                return {}
        
        except Exception as e:
            print(f"✗ 获取事件异常: {e}")
            return {}
    
    def get_agents(self) -> Dict[str, Any]:
        """
        获取Agent列表
        
        Returns:
            Agent列表
        """
        try:
            response = requests.get(f"{self.api_url}/agents")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"✗ 获取Agent失败: {response.status_code}")
                return {}
        
        except Exception as e:
            print(f"✗ 获取Agent异常: {e}")
            return {}
    
    def get_skills(self) -> Dict[str, Any]:
        """
        获取技能列表
        
        Returns:
            技能列表
        """
        try:
            response = requests.get(f"{self.api_url}/skills")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"✗ 获取技能失败: {response.status_code}")
                return {}
        
        except Exception as e:
            print(f"✗ 获取技能异常: {e}")
            return {}
    
    def get_blackboard(self) -> Dict[str, Any]:
        """
        获取黑板状态
        
        Returns:
            黑板状态
        """
        try:
            response = requests.get(f"{self.api_url}/blackboard")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"✗ 获取黑板失败: {response.status_code}")
                return {}
        
        except Exception as e:
            print(f"✗ 获取黑板异常: {e}")
            return {}
    
    def monitor_task(self, dag_id: str, timeout: int = 120, interval: int = 5) -> bool:
        """
        监控任务执行
        
        Args:
            dag_id: DAG ID
            timeout: 超时时间（秒）
            interval: 检查间隔（秒）
            
        Returns:
            是否成功完成
        """
        print(f"\n{'='*60}")
        print(f"开始监控任务: {dag_id}")
        print(f"超时时间: {timeout}秒")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        last_event_count = 0
        
        while time.time() - start_time < timeout:
            # 获取任务状态
            tasks = self.get_tasks()
            
            if tasks.get("tasks"):
                for task in tasks["tasks"]:
                    if task.get("dag_id") == dag_id:
                        if task.get("is_completed"):
                            print(f"\n✓ 任务完成: {dag_id}")
                            self._print_task_summary(task)
                            return True
            
            # 获取新事件
            events = self.get_events(limit=100)
            
            if events.get("events"):
                new_events = events["events"][last_event_count:]
                
                for event in new_events:
                    self._print_event(event)
                
                last_event_count = len(events["events"])
            
            # 等待下一次检查
            time.sleep(interval)
        
        print(f"\n✗ 任务超时: {dag_id}")
        return False
    
    def _print_event(self, event: Dict[str, Any]) -> None:
        """
        打印事件信息
        
        Args:
            event: 事件对象
        """
        event_type = event.get("type", "unknown")
        timestamp = event.get("timestamp", "")
        data = event.get("data", {})
        
        # 格式化时间
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%H:%M:%S")
        except:
            time_str = timestamp
        
        # 根据事件类型选择图标
        icons = {
            "task_created": "📝",
            "task_started": "▶️",
            "task_completed": "✅",
            "task_failed": "❌",
            "dag_updated": "📊",
            "new_task_generated": "➕",
            "agent_registered": "🤖",
            "skill_registered": "🔧"
        }
        
        icon = icons.get(event_type, "📌")
        
        # 打印事件
        print(f"[{time_str}] {icon} {event_type}")
        
        if event_type == "task_created":
            print(f"  任务ID: {data.get('task_id')}")
            print(f"  任务名称: {data.get('task_name')}")
        elif event_type == "task_started":
            print(f"  任务ID: {data.get('task_id')}")
            print(f"  开始执行: {data.get('task_name')}")
        elif event_type == "task_completed":
            print(f"  任务ID: {data.get('task_id')}")
            result = data.get('result', {})
            if isinstance(result, dict):
                skill_name = result.get('skill_name', 'unknown')
                print(f"  使用技能: {skill_name}")
        elif event_type == "task_failed":
            print(f"  任务ID: {data.get('task_id')}")
            print(f"  错误信息: {data.get('error', 'unknown')}")
        
        print()
    
    def _print_task_summary(self, task: Dict[str, Any]) -> None:
        """
        打印任务摘要
        
        Args:
            task: 任务对象
        """
        print(f"\n{'='*60}")
        print(f"任务摘要")
        print(f"{'='*60}")
        print(f"DAG ID: {task.get('dag_id')}")
        print(f"任务名称: {task.get('name')}")
        print(f"任务描述: {task.get('description')}")
        print(f"子任务数: {task.get('total_tasks', 0)}")
        print(f"创建时间: {task.get('created_at')}")
        print(f"完成状态: {'✓ 是' if task.get('is_completed') else '✗ 否'}")
        print(f"{'='*60}\n")
    
    def debug_system(self) -> None:
        """
        调试系统状态
        """
        print(f"\n{'='*60}")
        print(f"系统状态调试")
        print(f"{'='*60}\n")
        
        # 检查Agent
        print("🤖 Agent状态:")
        agents = self.get_agents()
        if agents.get("sub_agents"):
            for agent in agents["sub_agents"]:
                status_icon = "🟢" if agent.get("status") == "idle" else "🟡"
                print(f"  {status_icon} {agent.get('agent_id')} ({agent.get('role')}) - {agent.get('status')}")
        
        # 检查技能
        print(f"\n🔧 技能状态:")
        skills = self.get_skills()
        if skills.get("skills"):
            for skill in skills["skills"]:
                active_icon = "✅" if skill.get("is_active") else "❌"
                print(f"  {active_icon} {skill.get('name')} ({skill.get('type')})")
        
        # 检查任务
        print(f"\n📝 任务状态:")
        tasks = self.get_tasks()
        if tasks.get("tasks"):
            for task in tasks["tasks"]:
                completed_icon = "✅" if task.get("is_completed") else "🔄"
                print(f"  {completed_icon} {task.get('name')} - {task.get('total_tasks', 0)}个子任务")
        
        # 检查黑板
        print(f"\n📊 黑板状态:")
        blackboard = self.get_blackboard()
        if blackboard:
            print(f"  任务数: {len(blackboard.get('tasks', []))}")
            print(f"  知识数: {len(blackboard.get('knowledge', []))}")
            print(f"  结果数: {len(blackboard.get('results', []))}")
            print(f"  DAG数: {len(blackboard.get('dags', []))}")
        
        print(f"\n{'='*60}\n")
    
    def run_test_scenario(self, scenario: str) -> bool:
        """
        运行测试场景
        
        Args:
            scenario: 场景名称
            
        Returns:
            是否成功
        """
        scenarios = {
            "simple": "测试任务执行流程",
            "report": "测试报告生成任务",
            "research": "测试研究任务",
            "complex": "测试复杂任务"
        }
        
        description = scenarios.get(scenario, scenario)
        print(f"\n{'='*60}")
        print(f"运行测试场景: {scenario}")
        print(f"场景描述: {description}")
        print(f"{'='*60}\n")
        
        # 创建任务
        result = self.create_task(description)
        
        if not result.get("dag_id"):
            print("✗ 任务创建失败，无法继续测试")
            return False
        
        dag_id = result["dag_id"]
        
        # 监控任务
        return self.monitor_task(dag_id)


def main():
    """主函数"""
    import sys
    
    debugger = TaskDebugger()
    
    if len(sys.argv) < 2:
        print("任务调试工具")
        print("\n使用方法:")
        print("  python debug_task.py create <description>  - 创建任务")
        print("  python debug_task.py monitor <dag_id>    - 监控任务")
        print("  python debug_task.py debug                 - 调试系统状态")
        print("  python debug_task.py test <scenario>        - 运行测试场景")
        print("\n测试场景:")
        print("  simple   - 简单任务测试")
        print("  report   - 报告生成测试")
        print("  research - 研究任务测试")
        print("  complex  - 复杂任务测试")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) < 3:
            print("请提供任务描述")
            return
        
        description = " ".join(sys.argv[2:])
        debugger.create_task(description)
    
    elif command == "monitor":
        if len(sys.argv) < 3:
            print("请提供DAG ID")
            return
        
        dag_id = sys.argv[2]
        debugger.monitor_task(dag_id)
    
    elif command == "debug":
        debugger.debug_system()
    
    elif command == "test":
        if len(sys.argv) < 3:
            print("请提供测试场景")
            return
        
        scenario = sys.argv[2]
        debugger.run_test_scenario(scenario)
    
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()