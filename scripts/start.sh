#!/usr/bin/env bash
# 启动 InkAI Web 服务器（后台运行，日志输出到 logs/web.log）
# 用法: bash scripts/start.sh
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

mkdir -p logs
LOG_FILE="logs/web.log"
PID_FILE="logs/web.pid"

# 已在运行则直接返回
if [ -f "$PID_FILE" ]; then
  PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
    echo "server already running, pid=${PID}, url=http://localhost:5000"
    exit 0
  fi
fi

# 选择 Python 解释器：优先 .venv，其次系统 python3
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi

echo "starting InkAI web server, python=${PY} ..."
nohup "${PY}" start_web.py >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
sleep 2
echo "started, pid=$(cat "$PID_FILE")"
echo "frontend: http://localhost:5000   log: ${LOG_FILE}"
