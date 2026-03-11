# VibeArtifact AI Group - Windows 启动面板 (PowerShell)
# 用法: powershell -ExecutionPolicy Bypass -File panel.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DIR = Join-Path $ScriptDir ".dev-agents"
$MODEL = "claude-sonnet-4-20250514"
$CLAUDE_CMD = "claude --model $MODEL"

# 检查 Windows Terminal
$hasWT = $null -ne (Get-Command wt.exe -ErrorAction SilentlyContinue)

Write-Host ""
Write-Host "=========================================="
Write-Host "  VibeArtifact AI Group - 启动面板"
Write-Host "=========================================="
Write-Host ""
Write-Host "  a) 全员启动 (Max + Ella + Jarvis + Kyle)"
Write-Host "  b) 三人模式 (Max + Ella + Jarvis)"
Write-Host "  c) 仅 Max (项目管理)"
Write-Host "  d) 设计+开发 (Ella + Jarvis)"
Write-Host "  e) 开发+测试 (Jarvis + Kyle)"
Write-Host "  q) 退出"
Write-Host ""
$selection = Read-Host "请选择"

if ($selection -eq 'q' -or $selection -eq 'Q') { exit }

$agents = switch ($selection.ToLower()) {
    'a' { @('max', 'ella', 'jarvis', 'kyle'); break }
    'b' { @('max', 'ella', 'jarvis'); break }
    'c' { @('max'); break }
    'd' { @('ella', 'jarvis'); break }
    'e' { @('jarvis', 'kyle'); break }
    default { Write-Host "无效选择"; exit }
}

$dirs = $agents | ForEach-Object { Join-Path $DIR $_ }

if ($hasWT) {
    # 使用 Windows Terminal 分屏
    switch ($agents.Count) {
        1 {
            & wt -d $dirs[0] cmd /k $CLAUDE_CMD
        }
        2 {
            # 左右分屏
            & wt -d $dirs[0] cmd /k $CLAUDE_CMD `; split-pane -V -d $dirs[1] cmd /k $CLAUDE_CMD
        }
        3 {
            # 左 + 右上/右下
            & wt -d $dirs[0] cmd /k $CLAUDE_CMD `; `
                split-pane -V -d $dirs[1] cmd /k $CLAUDE_CMD `; `
                split-pane -H -d $dirs[2] cmd /k $CLAUDE_CMD
        }
        4 {
            # 四宫格: Max(左上) Ella(右上) Kyle(左下) Jarvis(右下)
            & wt -d $dirs[0] cmd /k $CLAUDE_CMD `; `
                split-pane -V -d $dirs[1] cmd /k $CLAUDE_CMD `; `
                split-pane -H -d $dirs[2] cmd /k $CLAUDE_CMD `; `
                move-focus left `; `
                split-pane -H -d $dirs[3] cmd /k $CLAUDE_CMD
        }
    }
} else {
    # 回退方案: 打开独立窗口
    Write-Host ""
    Write-Host "未检测到 Windows Terminal (wt.exe), 将打开独立窗口..."
    Write-Host "提示: 安装 Windows Terminal 可获得分屏体验"
    Write-Host ""
    foreach ($i in 0..($agents.Count - 1)) {
        $agent = $agents[$i]
        $agentDir = $dirs[$i]
        Write-Host "  启动 [$agent] ..."
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$agentDir'; Write-Host '=== VibeArtifact Agent: $agent ==='; Write-Host ''; $CLAUDE_CMD"
    }
    Write-Host ""
    Write-Host "已启动 $($agents.Count) 个 Agent 窗口"
}
