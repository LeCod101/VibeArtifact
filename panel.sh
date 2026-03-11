#!/bin/bash
# VibeArtifact AI Group - 交互式启动面板
# Windows 用户: 在 Git Bash 或 WSL 中运行（需要安装 tmux）

SESSION="vibeartifact-agents"
DIR="$(cd "$(dirname "$0")/.dev-agents" && pwd)"

# 检查tmux
if ! command -v tmux &> /dev/null; then
    echo "错误: 需要安装tmux"
    echo ""
    echo "安装命令:"
    echo "  macOS:   brew install tmux"
    echo "  Ubuntu:  sudo apt install tmux"
    echo "  Windows: 建议使用 WSL 后安装 tmux"
    exit 1
fi

# 如果session已存在
if tmux has-session -t $SESSION 2>/dev/null; then
    echo "VibeArtifact Agent 会话已存在"
    echo ""
    echo "  1) 连接到现有会话"
    echo "  2) 关闭并重新启动"
    echo "  3) 退出"
    echo ""
    read -p "请选择 [1-3]: " choice

    case $choice in
        1) tmux attach-session -t $SESSION; exit 0 ;;
        2) tmux kill-session -t $SESSION ;;
        *) exit 0 ;;
    esac
fi

echo "=========================================="
echo "  VibeArtifact AI Group - 启动面板"
echo "=========================================="
echo ""
echo "  a) 全员启动 (Max + Ella + Jarvis + Kyle)"
echo "  b) 三人模式 (Max + Ella + Jarvis)"
echo "  c) 仅 Max (项目管理)"
echo "  d) 设计+开发 (Ella + Jarvis)"
echo "  e) 开发+测试 (Jarvis + Kyle)"
echo "  q) 退出"
echo ""
read -p "请选择: " selection

MODEL="claude-sonnet-4-20250514"

case $selection in
    a|A)
        # 全员: 四宫格
        tmux new-session -d -s $SESSION -c "$DIR/max" -n "AI Group"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m

        tmux split-window -h -t $SESSION -c "$DIR/ella"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m

        tmux split-window -v -t $SESSION.1 -c "$DIR/jarvis"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m

        tmux split-window -v -t $SESSION.0 -c "$DIR/kyle"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m

        tmux select-pane -t $SESSION:0.0
        tmux attach-session -t $SESSION
        ;;
    b|B)
        # 三人: Max左 + 右两栏
        tmux new-session -d -s $SESSION -c "$DIR/max" -n "AI Group"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m

        tmux split-window -h -t $SESSION -c "$DIR/ella"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m

        tmux split-window -v -t $SESSION -c "$DIR/jarvis"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m

        tmux select-pane -t $SESSION:0.0
        tmux attach-session -t $SESSION
        ;;
    c|C)
        # 仅Max
        tmux new-session -d -s $SESSION -c "$DIR/max" -n "AI Group"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m
        tmux attach-session -t $SESSION
        ;;
    d|D)
        # 设计+开发: Ella左 + Jarvis右
        tmux new-session -d -s $SESSION -c "$DIR/ella" -n "设计+开发"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m

        tmux split-window -h -t $SESSION -c "$DIR/jarvis"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m

        tmux attach-session -t $SESSION
        ;;
    e|E)
        # 开发+测试: Jarvis左 + Kyle右
        tmux new-session -d -s $SESSION -c "$DIR/jarvis" -n "开发+测试"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m

        tmux split-window -h -t $SESSION -c "$DIR/kyle"
        tmux send-keys -t $SESSION "claude --model $MODEL -c 2>/dev/null || claude --model $MODEL" C-m

        tmux attach-session -t $SESSION
        ;;
    *)
        exit 0
        ;;
esac
