#!/usr/bin/env bash
# 重启 InkAI Web 服务器（停止后再启动）
# 用法: bash scripts/restart.sh
set -uo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

bash scripts/stop.sh
bash scripts/start.sh
