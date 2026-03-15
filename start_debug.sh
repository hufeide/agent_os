#!/bin/bash
# 前端调试启动脚本

echo "=========================================="
echo "Agent OS Dashboard - 调试模式启动"
echo "=========================================="

# 检查是否在正确的目录
if [ ! -d "dashboard" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

cd dashboard

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo ""
    echo "安装依赖..."
    npm install
fi

echo ""
echo "选择调试模式:"
echo "1. 普通模式 (npm run dev)"
echo "2. VSCode调试模式"
echo "3. Chrome调试模式"
echo "4. React DevTools模式"
echo ""
read -p "请选择 (1-4): " choice

case $choice in
  1)
    echo ""
    echo "启动普通开发服务器..."
    echo "访问地址: http://localhost:3050"
    echo ""
    echo "调试方法:"
    echo "1. 打开浏览器访问 http://localhost:3050"
    echo "2. 按F12打开开发者工具"
    echo "3. 在Sources标签中设置断点"
    echo ""
    npm run dev
    ;;
    
  2)
    echo ""
    echo "VSCode调试模式"
    echo "=========================================="
    echo ""
    echo "使用方法:"
    echo "1. 在VSCode中按F5或点击'运行和调试'"
    echo "2. 选择'Launch Chrome'配置"
    echo "3. 在代码中设置断点"
    echo "4. 使用调试控制台控制执行"
    echo ""
    echo "调试快捷键:"
    echo "  F5 - 继续"
    echo "  F10 - 单步跳过"
    echo "  F11 - 单步进入"
    echo "  Shift+F11 - 单步跳出"
    echo "  F9 - 切换断点"
    echo ""
    echo "启动开发服务器..."
    npm run dev
    ;;
    
  3)
    echo ""
    echo "Chrome调试模式"
    echo "=========================================="
    echo ""
    echo "使用方法:"
    echo "1. 启动Chrome并使用调试端口"
    echo "2. 访问 http://localhost:3050"
    echo "3. 在Chrome DevTools中设置断点"
    echo ""
    echo "Chrome调试端口: 9222"
    echo ""
    echo "启动Chrome调试:"
    echo "  google-chrome --remote-debugging-port=9222"
    echo ""
    echo "启动开发服务器..."
    npm run dev
    ;;
    
  4)
    echo ""
    echo "React DevTools模式"
    echo "=========================================="
    echo ""
    echo "检查React DevTools..."
    if ! npm list react-devtools &> /dev/null; then
      echo "安装React DevTools..."
      npm install --save-dev react-devtools
    else
      echo "✓ React DevTools已安装"
    fi
    echo ""
    echo "使用方法:"
    echo "1. 安装Chrome扩展: React Developer Tools"
    echo "2. 访问 http://localhost:3050"
    echo "3. 在Chrome DevTools中查看React组件"
    echo "4. 使用React DevTools检查组件状态"
    echo ""
    echo "启动开发服务器..."
    npm run dev
    ;;
    
  *)
    echo "无效选择"
    exit 1
    ;;
esac