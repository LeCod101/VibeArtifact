#!/bin/bash
# 启动麦克斯 (Max) - 项目管理/产品顾问
# 用法: ./start-max.sh [opus]
# Windows 用户: 在 Git Bash 或 WSL 中运行

cd "$(dirname "$0")/.dev-agents/max"

# 模型选择
if [ "$1" = "opus" ]; then
  MODEL="claude-opus-4-6"
  MODEL_NAME="Opus 4.6"
else
  MODEL="claude-sonnet-4-20250514"
  MODEL_NAME="Sonnet 4"
fi

echo "=========================================="
echo "  启动麦克斯 (Max) - 项目管理"
echo "  项目: VibeArtifact"
echo "  模型: Claude $MODEL_NAME"
echo "=========================================="
echo ""

# 默认继承上次会话，如果没有历史则新建
claude --model $MODEL -c 2>/dev/null || claude --model $MODEL
