# .dev-agents - AI 多角色协作框架

基于 agentGroup 的多 Agent 协作开发框架，4 个 AI Agent 各司其职，通过共享工作区协同完成 VibeArtifact 的开发任务。

## 团队成员

| Agent | 角色 | 职责 | 启动命令 |
|-------|------|------|----------|
| **Max (麦克斯)** | 项目经理 | 进度监控、风险识别、产品建议、团队协调 | `./start-max.sh` |
| **Ella (艾拉)** | UI/UX 设计师 | 界面设计、交互原型、设计规范输出 | `./start-ella.sh` |
| **Jarvis (贾维斯)** | 全栈开发 | 前后端编码、技术方案、Bug 修复 | `./start-jarvis.sh` |
| **Kyle (凯尔)** | 质量保障 | 代码审查、功能验收、测试报告 | `./start-kyle.sh` |

## 快速开始

### 前提条件

- 已安装 [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- 在 Git Bash、WSL 或 macOS/Linux 终端中运行

### 启动单个 Agent

```bash
# 在项目根目录执行（默认使用 Sonnet 模型）
./start-max.sh          # 启动 Max
./start-ella.sh         # 启动 Ella
./start-jarvis.sh       # 启动 Jarvis
./start-kyle.sh         # 启动 Kyle

# 使用 Opus 模型（更强但更贵）
./start-jarvis.sh opus
```

每个启动脚本会 `cd` 到对应的 Agent 目录（如 `.dev-agents/max/`），然后以该目录为工作目录启动 Claude Code 会话。Agent 会自动读取自己的 `CLAUDE.md` 获取项目指令和角色定义。

### 启动多 Agent 面板（tmux）

```bash
# 需要安装 tmux
# macOS:  brew install tmux
# Ubuntu: sudo apt install tmux
# Windows: 在 WSL 中安装

./panel.sh
```

面板提供 5 种启动模式：

| 选项 | 模式 | 说明 |
|------|------|------|
| a | 全员启动 | Max + Ella + Jarvis + Kyle 四宫格 |
| b | 三人模式 | Max + Ella + Jarvis |
| c | 仅 Max | 项目管理 |
| d | 设计+开发 | Ella + Jarvis |
| e | 开发+测试 | Jarvis + Kyle |

## 目录结构

```
.dev-agents/
├── max/                        # Max 的工作目录
│   ├── CLAUDE.md               # 项目指令（含 VibeArtifact 上下文）
│   ├── PERSONA.md              # 人设定义
│   └── .claude/commands/       # Slash 命令
│       ├── status.md           #   /status - 查看团队状态
│       ├── meeting.md          #   /meeting - 记录会议
│       ├── report.md           #   /report - 生成项目报告
│       ├── todo.md             #   /todo - 管理待办
│       └── suggest.md          #   /suggest - 产品建议
├── ella/
│   ├── CLAUDE.md
│   ├── PERSONA.md
│   └── .claude/commands/
│       ├── design.md           #   /design - UI 设计
│       ├── prototype.md        #   /prototype - 交互原型
│       ├── spec.md             #   /spec - 设计规范
│       ├── style.md            #   /style - 风格提取
│       └── handoff.md          #   /handoff - 设计交付
├── jarvis/
│   ├── CLAUDE.md
│   ├── PERSONA.md
│   └── .claude/commands/
│       ├── dev.md              #   /dev - 开始开发
│       ├── plan.md             #   /plan - 技术方案
│       ├── bug.md              #   /bug - 记录 Bug
│       ├── project.md          #   /project - 项目 AI 说明
│       ├── status.md           #   /status - 查看状态
│       └── notify-kyle.md      #   /notify-kyle - 通知凯尔
├── kyle/
│   ├── CLAUDE.md
│   ├── PERSONA.md
│   └── .claude/commands/
│       ├── review.md           #   /review - 代码审查
│       ├── test.md             #   /test - 执行测试
│       ├── report.md           #   /report - 审查报告
│       ├── status.md           #   /status - 查看状态
│       └── notify-jarvis.md    #   /notify-jarvis - 通知贾维斯
└── shared/                     # 共享协作区
    ├── status.json             # 团队实时状态
    ├── notifications.json      # 通知系统
    ├── scripts/
    │   ├── check_notifications_simple.sh  # 轻量通知检查
    │   └── check_notifications.sh         # 完整通知检查（需 jq）
    ├── templates/              # 文档模板
    │   ├── prd.md              #   PRD 模板
    │   ├── ui.md               #   UI 设计模板
    │   ├── api.md              #   API 文档模板
    │   ├── bug.md              #   Bug 报告模板
    │   └── meeting.md          #   会议纪要模板
    ├── tasks/                  # 任务文档（运行时生成）
    ├── docs/                   # PRD 文档（运行时生成）
    ├── designs/                # 设计稿（运行时生成）
    ├── reviews/                # 审查报告（运行时生成）
    └── .cache/                 # 通知检查缓存
```

## 协作流程

### 典型开发流程

```
用户提需求
    │
    ▼
Max 分析需求 ──→ 拆解任务、排优先级
    │
    ▼
Ella 设计 UI ──→ 输出设计稿到 shared/designs/
    │
    ▼
Ella /handoff ──→ 通知 Jarvis 开发
    │
    ▼
Jarvis /dev ──→ 编码实现
    │
    ▼
Jarvis /notify-kyle ──→ 通知 Kyle 验收
    │
    ▼
Kyle /review + /test ──→ 输出审查报告到 shared/reviews/
    │
    ├─ 通过 → 完成
    └─ 不通过 → Kyle /notify-jarvis → Jarvis 修复 → 重新验收
```

### Agent 间通信机制

Agent 之间通过 `shared/` 目录进行异步通信：

1. **通知系统**：Agent 写入 `notifications.json`，其他 Agent 启动时通过 `check_notifications_simple.sh` 检查
2. **状态共享**：各 Agent 更新 `status.json` 中自己的状态（idle/working、当前任务）
3. **产物交接**：设计稿放 `designs/`，审查报告放 `reviews/`，任务文档放 `tasks/`

通知发送需要用户确认（Agent 会先询问"需要通知 XX 吗？"），不会自动跨 Agent 通信。

## 常用场景

### 场景 1：让 Jarvis 开发一个功能

```bash
./start-jarvis.sh

# 在 Jarvis 会话中：
> /plan 实现用户登录 API
> /dev 按照技术方案开发登录功能
> /notify-kyle 登录功能开发完成，请验收
```

### 场景 2：让 Ella 设计页面

```bash
./start-ella.sh

# 在 Ella 会话中：
> /design 根据 PRD 设计登录页面
> /spec 输出设计规范
> /handoff 交付给贾维斯
```

### 场景 3：让 Kyle 做代码审查

```bash
./start-kyle.sh

# 在 Kyle 会话中：
> /status                          # 查看是否有待审查通知
> /review ../../services/api/      # 审查 API 代码
> /test 用户登录功能               # 功能测试
> /report 用户登录                 # 生成综合报告
```

### 场景 4：让 Max 了解项目全貌

```bash
./start-max.sh

# 在 Max 会话中：
> /status                          # 查看团队状态
> /report weekly                   # 生成周报
> /suggest priorities              # 建议优先级调整
```

## 注意事项

- **Git 安全**：所有 Agent 禁止自动 commit/push，必须用户明确授权
- **职责边界**：每个 Agent 只做自己职责内的事，跨职责操作会提醒用户转交
- **运行时产物**：`shared/` 下的 status.json、notifications.json 及各子目录中的 .md 文件已在 `.gitignore` 中排除，不会被提交
- **框架文件**：Agent 的 CLAUDE.md、PERSONA.md、commands、templates、scripts 是框架的一部分，会被提交到代码仓库
- **Windows 用户**：启动脚本需要在 Git Bash 或 WSL 中运行；tmux 面板需要 WSL
