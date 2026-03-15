#!/bin/bash
# Agent OS 快速启动脚本

echo "=========================================="
echo "Agent OS - 快速启动"
echo "=========================================="

# 检查后端服务是否运行
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✓ 后端服务已在运行"
else
    echo "✗ 后端服务未运行"
    echo "请先运行: cd /home/aixz/data/hxf/bigmodel/ai_code/agentos/agent_os_v1/agent_os_v1 && python start.py"
    exit 1
fi

# 进入dashboard目录
cd /home/aixz/data/hxf/bigmodel/ai_code/agentos/agent_os_v1/agent_os_v1/dashboard

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo ""
    echo "安装Dashboard依赖..."
    npm install
fi

echo ""
echo "=========================================="
echo "启动Dashboard..."
echo "=========================================="
echo ""
echo "Dashboard地址: http://localhost:3050"
echo "API文档地址: http://localhost:8001/docs"
echo ""
echo "按 Ctrl+C 停止Dashboard"
echo "=========================================="

# 启动Dashboard
npm run dev