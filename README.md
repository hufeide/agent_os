# Agent OS - 主从分层Agent系统

## 项目简介

Agent OS 是一个全新的主从分层Agent系统，实现了事件驱动、动态任务DAG、闭环反馈等先进特性。

## 核心特性

### 1. 主从分层架构
- **主Agent (Planner)**: 负责全局任务拆分、调度、策略、目标管理
- **子Agent (Worker)**: 负责具体任务执行、技能调用、结果上报

### 2. 黑板 + 事件总线
- **Blackboard**: Agent之间通过共享状态协作
- **Event Bus**: 发布订阅事件通知，事件驱动

### 3. 动态任务DAG
- 任务不是静态分配，而是可以根据执行结果动态生成新的任务
- 支持任务依赖关系管理和优先级调度

### 4. 闭环反馈
- Planner根据子Agent执行结果判断任务是否完成或需要拆分重试
- LLM驱动的智能决策

### 5. 可扩展与多模态
- 支持不同类型Agent：LLM、Python函数、API调用、工具调用
- 动态技能注册表，运行时注册新技能

### 6. 事件驱动 + 异步执行
- 不轮询，不阻塞
- DAG自动触发下游任务

## 项目结构

```
agent_os_v1/
├── core/                    # 核心模块
│   ├── models.py           # 数据模型
│   ├── event_bus.py        # 事件总线
│   ├── blackboard.py       # 黑板系统
│   ├── skill_registry.py   # 技能注册表
│   ├── vector_memory.py    # 向量记忆服务
│   └── task_scheduler.py   # 任务调度器
├── agents/                  # Agent模块
│   ├── main_agent.py       # 主Agent (Planner)
│   └── sub_agent_worker.py # 子Agent Worker
├── api/                     # API模块
│   └── server.py           # API服务器
├── dashboard/               # Web Dashboard
│   ├── src/
│   │   ├── pages/         # 页面组件
│   │   ├── App.jsx        # 主应用
│   │   └── main.jsx       # 入口
│   ├── package.json
│   └── vite.config.js
├── tests/                   # 测试
│   ├── test_core.py        # 核心模块测试
│   └── test_integration.py # 集成测试
└── start.py                # 启动脚本
```

## 快速开始

### 1. 安装依赖

```bash
# Python依赖
pip install fastapi uvicorn

# Dashboard依赖
cd dashboard
npm install
cd ..
```

### 2. 启动后端服务

```bash
python start.py
```

服务将在以下地址启动：
- API服务器: http://localhost:8000
- API文档: http://localhost:8000/docs

### 3. 启动Dashboard

```bash
cd dashboard
npm run dev
```

Dashboard将在 http://localhost:3050 启动

### 4. 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行核心模块测试
python -m pytest tests/test_core.py -v

# 运行集成测试
python -m pytest tests/test_integration.py -v
```

## API使用示例

### 创建任务

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Write a report about AI",
    "context": {}
  }'
```

### 获取任务状态

```bash
curl http://localhost:8000/api/tasks/{dag_id}
```

### 获取Agent状态

```bash
curl http://localhost:8000/api/agents
```

### 获取黑板状态

```bash
curl http://localhost:8000/api/blackboard
```

### 注册技能

```bash
curl -X POST http://localhost:8000/api/skills \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Skill",
    "description": "A custom skill",
    "type": "function",
    "capabilities": ["custom"]
  }'
```

## Dashboard功能

### 1. 仪表盘
- 显示系统概览
- 任务状态统计
- 最近事件日志

### 2. Agent管理
- 查看主Agent状态
- 查看子Agent列表
- Agent详情查看

### 3. 任务管理
- 创建新任务
- 查看任务列表
- 任务详情和进度

### 4. 事件日志
- 查看所有事件
- 事件类型过滤
- 事件搜索

### 5. 黑板状态
- 查看任务、知识、结果
- 查看Agent和DAG状态

### 6. 技能管理
- 查看已注册技能
- 注册新技能
- 注销技能

## 核心概念

### 任务DAG
任务以有向无环图（DAG）的形式组织，支持任务依赖关系。

### 事件驱动
所有组件通过事件总线通信，实现松耦合。

### 技能系统
Agent通过调用技能完成任务，技能支持动态注册。

### 向量记忆
提供语义搜索能力，支持知识检索。

## 配置说明

### 环境变量
- `API_HOST`: API服务器地址（默认: 0.0.0.0）
- `API_PORT`: API服务器端口（默认: 8000）
- `MAX_CONCURRENT_TASKS`: 最大并发任务数（默认: 5）

## 扩展开发

### 添加新技能

```python
from core.skill_registry import create_function_skill

def my_skill(**kwargs):
    return {"result": "success"}

skill = create_function_skill(
    name="My Skill",
    description="My custom skill",
    handler=my_skill,
    capabilities=["custom"]
)

skill_registry.register(skill)
```

### 添加新Agent

```python
from agents.sub_agent_worker import SubAgentWorker

agent = SubAgentWorker(
    agent_id="my_agent",
    agent_role="custom",
    capabilities=["custom"],
    event_bus=event_bus,
    blackboard=blackboard,
    skill_registry=skill_registry,
    vector_memory=vector_memory
)

agent.start()
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！# agent_os
