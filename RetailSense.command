#!/bin/bash
# ────────────────────────────────────────────
# RetailSense 快捷启动脚本
# 双击此文件即可启动 RetailSense 系统
# ────────────────────────────────────────────

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
APP_URL="http://localhost:8501"

# 切换到项目目录
cd "$PROJECT_DIR" || {
    osascript -e 'display dialog "❌ 找不到项目目录：'"$PROJECT_DIR"'" with title "RetailSense 启动失败" buttons {"确定"} default button 1 with icon stop'
    exit 1
}

# 使用项目自己的虚拟环境启动，避免启动器内部的旧绝对路径
if [ ! -x "$PYTHON_BIN" ]; then
    osascript -e 'display dialog "❌ 未找到项目虚拟环境，请先按 README 安装依赖。" with title "RetailSense 启动失败" buttons {"确定"} default button 1 with icon stop'
    exit 1
fi

"$PYTHON_BIN" -m streamlit run app.py --server.headless true &

STREAMLIT_PID=$!
echo "🚀 Streamlit 启动中... (PID: $STREAMLIT_PID)"

# 等待 Streamlit 服务就绪
echo "⏳ 等待服务就绪..."
for i in $(seq 1 15); do
    if curl -s -o /dev/null -w "%{http_code}" "$APP_URL" 2>/dev/null | grep -q "200\|302"; then
        echo "✅ 服务已就绪！"
        break
    fi
    sleep 1
done

# 打开 Safari 浏览器
open -a Safari "$APP_URL"

echo "🐾 RetailSense 已启动！浏览器已打开 $APP_URL"
echo "按 Ctrl+C 可停止 Streamlit 服务"

# 保持终端窗口打开，等待 Streamlit 进程
wait $STREAMLIT_PID
