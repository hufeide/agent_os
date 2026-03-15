# 部署文档

## 部署状态 ✅

主从分层Agent系统已成功部署并运行！

## 服务地址

### 后端服务
- **API服务器**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health

### 前端服务
- **Dashboard**: http://localhost:3050 (需要单独启动)

## 系统组件

### 已启动的组件
1. ✅ **主Agent (Planner)** - 负责全局任务拆分和调度
2. ✅ **子Agent Workers** - 3个Worker (researcher, analyst, writer)
3. ✅ **任务调度器** - 管理DAG任务图
4. ✅ **事件总线** - 事件驱动通信
5. ✅ **黑板系统** - 共享状态存储
6. ✅ **技能注册表** - 3个已注册技能
7. ✅ **向量记忆服务** - 语义检索支持

### 已注册的技能
1. **Research** - 信息收集能力
2. **Analysis** - 数据分析能力
3. **Writing** - 内容创作能力

## 测试结果

### API测试
```bash
# 获取Agent状态
curl http://localhost:8001/api/agents

# 创建任务
curl -X POST http://localhost:8001/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "Write a report about AI technology"}'

# 获取任务列表
curl http://localhost:8001/api/tasks

# 获取技能列表
curl http://localhost:8001/api/skills
```

### 测试结果
- ✅ API服务器正常运行
- ✅ Agent状态正常
- ✅ 任务创建成功
- ✅ 技能注册正常
- ✅ 任务执行正常

## 启动Dashboard

### 1. 安装依赖
```bash
cd /home/aixz/data/hxf/bigmodel/ai_code/agentos/agent_os_v1/agent_os_v1/dashboard
npm install
```

### 2. 启动开发服务器
```bash
npm run dev
```

### 3. 访问Dashboard
打开浏览器访问: http://localhost:3050

## Dashboard功能

### 1. 仪表盘
- 系统概览统计
- 任务状态监控
- 实时事件日志

### 2. Agent管理
- 查看主Agent状态
- 管理子Agent Workers
- Agent详情查看

### 3. 任务管理
- 创建新任务
- 查看任务列表
- 监控任务进度
- 查看任务详情

### 4. 事件日志
- 查看所有系统事件
- 事件类型过滤
- 事件内容搜索

### 5. 黑板状态
- 查看任务状态
- 查看知识库
- 查看执行结果
- 查看Agent状态
- 查看DAG状态

### 6. 技能管理
- 查看已注册技能
- 注册新技能
- 注销技能
- 查看技能详情

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                  用户 / API 接口层              │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Main Agent (Planner)                  │
│         LLM驱动的智能决策引擎                      │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼               ▼
   ┌────────┐     ┌────────┐     ┌────────┐
   │Researcher│     │Analyst │     │Writer  │
   │  Agent  │     │ Agent  │     │ Agent  │
   └────┬───┘     └────┬───┘     └────┬───┘
        │               │               │
        └───────────────┼───────────────┘
                        │
┌───────────────────────▼───────────────────────────┐
│         Event Bus (事件驱动)                  │
└───────────────────────┬───────────────────────────┘
                        │
┌───────────────────────▼───────────────────────────┐
│       Blackboard (共享状态)                  │
│  - 任务状态    - 知识库     - 执行结果    │
└───────────────────────┬───────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌────────┐     ┌────────┐     ┌────────┐
   │Skills  │     │Vector  │     │State   │
   │Registry│     │Memory  │     │Store   │
   └────────┘     └────────┘     └────────┘
```

## 停止服务

### 停止后端服务
```bash
# 查找进程
ps aux | grep "python start.py"

# 停止进程
kill <PID>

# 或者使用Ctrl+C如果在前台运行
```

### 停止Dashboard
```bash
# 在Dashboard终端按Ctrl+C
```

## 故障排查

### 端口被占用
```bash
# 查看端口占用
lsof -i:8001
lsof -i:3050

# 停止占用进程
kill -9 <PID>
```

### 查看日志
```bash
# 后端日志
tail -f server.log

# Dashboard日志
# 在Dashboard终端查看输出
```

### 测试API连接
```bash
# 健康检查
curl http://localhost:8001/health

# 查看API文档
# 浏览器访问 http://localhost:8001/docs
```

## 性能监控

### 系统资源
```bash
# CPU使用
top

# 内存使用
free -h

# 磁盘使用
df -h
```

### API性能
```bash
# 响应时间
time curl http://localhost:8001/api/agents

# 并发测试
ab -n 100 -c 10 http://localhost:8001/api/agents
```

## 扩展配置

### 修改端口
编辑 `start.py` 文件：
```python
uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
```

### 修改并发数
编辑 `start.py` 文件：
```python
scheduler.set_max_concurrent_tasks(10)
```

### 添加新Agent
编辑 `start.py` 文件：
```python
new_agent = SubAgentWorker(
    agent_id="new_agent",
    agent_role="custom",
    capabilities=["custom"],
    event_bus=event_bus,
    blackboard=blackboard,
    skill_registry=skill_registry,
    vector_memory=vector_memory
)
new_agent.start()
```

## 生产环境部署

### 使用systemd管理
创建 `/etc/systemd/system/agent-os.service`:
```ini
[Unit]
Description=Agent OS Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/agent_os_v1
ExecStart=/usr/bin/python3 /path/to/agent_os_v1/start.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable agent-os
sudo systemctl start agent-os
sudo systemctl status agent-os
```

### 使用Nginx反向代理
配置 `/etc/nginx/sites-available/agent-os`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        root /path/to/dashboard/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

## 总结

✅ **系统已成功部署**
- 后端服务运行在 http://localhost:8001
- 3个子Agent Workers正常运行
- 3个技能已注册
- API接口完全可用
- 任务创建和执行正常

🎯 **下一步**
- 启动Dashboard查看可视化界面
- 创建更多任务测试系统
- 添加自定义技能扩展功能
- 监控系统性能和日志

📚 **文档**
- API文档: http://localhost:8001/docs
- README: /home/aixz/data/hxf/bigmodel/ai_code/agentos/agent_os_v1/agent_os_v1/README.md