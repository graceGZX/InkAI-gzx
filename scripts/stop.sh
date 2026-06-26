#!/usr/bin/env bash
# 停止 InkAI Web 服务器
# 用法: bash scripts/stop.sh
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PID_FILE="logs/web.pid"

echo "正在停止 InkAI Web 服务器..."

# 1) 按 PID 文件停（若存在）
if [ -f "$PID_FILE" ]; then
  PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "${PID:-}" ] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
fi

# 2) 兜底：按进程特征 + 端口清理（debug 重载会派生子进程，需一并清掉）
pkill -f "start_web.py" 2>/dev/null || true
if command -v lsof >/dev/null 2>&1; then
  lsof -ti tcp:5000 2>/dev/null | xargs kill 2>/dev/null || true
fi

sleep 1
echo "已停止。"
