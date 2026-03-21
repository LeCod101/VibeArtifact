export type Locale = "zh" | "en";

const translations = {
  // Nav
  nav: {
    product: { zh: "产品", en: "Product" },
    docs: { zh: "文档", en: "Docs" },
    pricing: { zh: "定价", en: "Pricing" },
    cta: { zh: "立即构建", en: "Start Building" },
    login: { zh: "登录", en: "Sign In" },
  },

  // Hero
  hero: {
    badge: {
      zh: "VibeArtifact v2.5 已正式发布",
      en: "VibeArtifact v2.5 is now stable",
    },
    title1: { zh: "停止写代码.", en: "Stop Writing Code." },
    title2: { zh: "开始生成系统.", en: "Start Generating Systems." },
    desc: {
      zh: "不再满足于碎片化代码片段。VibeArtifact 结合深度神经网络与确定性系统工程，",
      en: "No more fragmented code snippets. VibeArtifact combines deep neural networks with deterministic systems engineering to ",
    },
    descBold: {
      zh: "只需一句话，自动为您生成并部署具备工业级可靠性的全栈微服务架构。",
      en: "automatically generate and deploy production-grade full-stack microservice architectures from a single sentence.",
    },
    btnPrimary: { zh: "开始免费构建", en: "Start Building Free" },
    btnGithub: { zh: "查看开源核心", en: "View Open Source Core" },
    noCreditCard: { zh: "无需信用卡", en: "No credit card required" },
    deploy: {
      zh: "支持一键部署至 AWS / Vercel",
      en: "One-click deploy to AWS / Vercel",
    },
    trustedBy: {
      zh: "全球工程团队的共同选择",
      en: "Trusted by global engineering teams",
    },
  },

  // Interactive showcase
  interactive: {
    engineTitle: { zh: "合成引擎", en: "Synthesis Engine" },
    engineSub: { zh: "自主工程化", en: "Autonomous Engineering" },
    tabs: {
      zh: ["需求解码", "架构合成", "资产交付"],
      en: ["Decode", "Synthesize", "Deliver"],
    },
    statusLabel: {
      zh: "引擎实时处理中",
      en: "Engine processing live",
    },
    // Step 01
    step01Label: { zh: "解码意图", en: "Decode Intent" },
    step01Input: {
      zh: "构建一个支持 Stripe 支付、RBAC 权限和实时库存推送的跨境电商平台。",
      en: "Build a cross-border e-commerce platform with Stripe payments, RBAC permissions, and real-time inventory push.",
    },
    identifyEntities: { zh: "识别业务实体", en: "Identify Business Entities" },
    identifyServices: { zh: "识别三方服务", en: "Identify Third-party Services" },
    // Step 02
    step02Label: { zh: "架构推演", en: "Architecture Synthesis" },
    archDiagram: { zh: "微服务架构图谱", en: "Microservice Architecture Graph" },
    ermTitle: { zh: "实体关系模型", en: "Entity Relational Model" },
    ermDesc: {
      zh: "正在处理 Schema 关系...",
      en: "Processing Schema relationships...",
    },
    // Step 03
    step03Label: { zh: "系统构建交付", en: "System Build & Delivery" },
  },

  // Capabilities
  capabilities: {
    sectionTitle: {
      zh: "交付所需，一应俱全",
      en: "Everything You Need to Ship",
    },
    sectionDesc: {
      zh: "一站式 AI 产品工程平台，从创意到部署全链路覆盖。",
      en: "A complete AI-powered product engineering platform with everything from ideation to deployment.",
    },
    cards: [
      {
        suffix: { zh: "x", en: "x" },
        title: { zh: "AI 驱动代码生成", en: "AI-Powered Code Generation" },
        desc: {
          zh: "从自然语言生成生产级 Next.js + FastAPI 代码，全栈输出含测试用例。",
          en: "Generate production-ready Next.js + FastAPI code from natural language. Full-stack output with tests.",
        },
      },
      {
        suffix: { zh: "%", en: "%" },
        title: { zh: "智能架构设计", en: "Smart Architecture" },
        desc: {
          zh: "根据产品描述自动生成数据库 Schema、API 路由和系统架构图。",
          en: "Auto-generates database schemas, API routes, and system diagrams from your product description.",
        },
      },
      {
        suffix: { zh: "分钟", en: "min" },
        title: { zh: "极速部署", en: "Instant Deployment" },
        desc: {
          zh: "一键 Docker Compose 部署到生产环境，零配置 CI/CD 管线。",
          en: "One-click deploy to production with Docker Compose. Zero config CI/CD pipeline included.",
        },
      },
      {
        suffix: { zh: "%", en: "%" },
        title: { zh: "可视化文档", en: "Visual Documentation" },
        desc: {
          zh: "自动生成 Mermaid 图表、ER 图和架构文档，始终与代码库同步。",
          en: "Auto-generated Mermaid diagrams, ERDs, and architecture docs. Always in sync with your codebase.",
        },
      },
      {
        suffix: { zh: " 智能体", en: " Agents" },
        title: { zh: "多智能体协作", en: "Multi-Agent Collaboration" },
        desc: {
          zh: "专业 AI 智能体协同工作：规划师、架构师、编码师、测试师和部署师。",
          en: "Specialized AI agents work together: Planner, Architect, Coder, Tester, and Deployer.",
        },
      },
      {
        suffix: { zh: "", en: "" },
        title: { zh: "内置版本控制", en: "Version Control Built-in" },
        desc: {
          zh: "基于快照的版本管理，支持分支与合并，永不丢失工作成果。",
          en: "Snapshot-based versioning with branch and merge. Never lose your work.",
        },
      },
    ],
    items: [
      {
        title: { zh: "意图解码", en: "Intent Decoding" },
        desc: {
          zh: "利用神经网络提取非结构化语言中的核心业务实体，瞬间转化为高维逻辑规约。",
          en: "Leverages neural networks to extract core business entities from unstructured language, instantly converting them into high-dimensional logical specifications.",
        },
        statLabel: { zh: "解码准确率", en: "Decode Accuracy" },
        features: {
          zh: ["支持自然语言输入", "多模态意图识别", "零延迟实时转换"],
          en: [
            "Natural language input",
            "Multi-modal intent recognition",
            "Zero-latency real-time conversion",
          ],
        },
      },
      {
        title: { zh: "全栈合成", en: "Full-Stack Synthesis" },
        desc: {
          zh: "跨层级代码生成。确保 API 定义、数据库 Schema 与 UI 组件实时语义对齐。",
          en: "Cross-layer code generation. Ensures real-time semantic alignment between API definitions, database schemas, and UI components.",
        },
        statLabel: { zh: "合成延迟", en: "Synthesis Latency" },
        features: {
          zh: ["自动对齐 Schema", "前后端无缝对接"],
          en: ["Auto-align schemas", "Seamless frontend-backend integration"],
        },
      },
      {
        title: { zh: "基础设施自动机", en: "Infra Automaton" },
        desc: {
          zh: "深度感知部署环境，自动化配置多云环境下的 K8s 与 Terraform 资源。",
          en: "Deep deployment environment awareness. Automates K8s and Terraform resource configuration across multi-cloud environments.",
        },
        statLabel: { zh: "底层支持", en: "Infrastructure" },
        features: {
          zh: ["Terraform 自动化", "K8s 原生支持"],
          en: ["Terraform automation", "K8s native support"],
        },
      },
      {
        title: { zh: "逻辑强一致性", en: "Strong Consistency" },
        desc: {
          zh: "任何微小的需求变更都会引发全链路传播。拒绝工程断层，确保系统绝对同步。",
          en: "Every requirement change propagates across the entire chain. Zero engineering gaps, absolute system synchronization.",
        },
        statLabel: { zh: "工程断层", en: "Engineering Gaps" },
        features: {
          zh: ["全链路传播", "严格逻辑校验"],
          en: ["Full-chain propagation", "Strict logic validation"],
        },
      },
      {
        title: { zh: "工业级工程文档", en: "Industrial-Grade Docs" },
        desc: {
          zh: "自动生成高保真架构图、时序图及完整的 API 参考手册，无需人工干预。",
          en: "Automatically generates high-fidelity architecture diagrams, sequence diagrams, and complete API reference manuals without manual intervention.",
        },
        statLabel: { zh: "自动同步", en: "Auto Sync" },
        features: {
          zh: ["高保真架构图", "API 参考手册", "Markdown 导出"],
          en: [
            "High-fidelity architecture diagrams",
            "API reference manuals",
            "Markdown export",
          ],
        },
      },
      {
        title: { zh: "架构级逻辑校验", en: "Architecture Validation" },
        desc: {
          zh: "内置静态分析与逻辑校验引擎，确保每一行生成的代码均符合工业级规范与安全策略。",
          en: "Built-in static analysis and logic validation engine ensures every generated line of code meets industrial standards and security policies.",
        },
        statLabel: { zh: "安全合规", en: "Security Compliance" },
        features: {
          zh: ["静态代码分析", "安全漏洞拦截"],
          en: ["Static code analysis", "Security vulnerability interception"],
        },
      },
    ],
  },

  // CTA
  cta: {
    badge: { zh: "生产就绪", en: "Production Ready" },
    title1: { zh: "告别漫长的研发周期.", en: "End the endless dev cycles." },
    title2: { zh: "Just click compile.", en: "Just click compile." },
    btnPrimary: { zh: "进入控制台", en: "Open Console" },
    btnSecondary: { zh: "获取企业版白皮书", en: "Get Enterprise Whitepaper" },
    bottomText: {
      zh: "10 秒内开始生成 API · 开源核心",
      en: "Start generating APIs in 10s · Open Source Core",
    },
  },

  // Footer
  footer: {
    desc: {
      zh: "全球首个真正意义上的由 AI 驱动的全栈系统合成引擎。告别代码搬运，拥抱自动生成式工程。",
      en: "The world's first truly AI-driven full-stack system synthesis engine. Stop moving code, embrace generative engineering.",
    },
    ecosystem: { zh: "产品生态", en: "Ecosystem" },
    ecosystemItems: {
      zh: ["合成引擎 API", "基础设施部署", "企业私有化"],
      en: ["Synthesis Engine API", "Infra Deployment", "Enterprise Private"],
    },
    developers: { zh: "开发者", en: "Developers" },
    developerItems: {
      zh: ["技术文档", "系统状态", "GitHub 开源"],
      en: ["Documentation", "System Status", "GitHub Open Source"],
    },
  },

  /* ============ 认证相关 ============ */
  auth: {
    loginTitle: { zh: "登录", en: "Sign In" },
    registerTitle: { zh: "注册", en: "Sign Up" },
    email: { zh: "邮箱", en: "Email" },
    emailPlaceholder: { zh: "请输入邮箱", en: "Enter your email" },
    password: { zh: "密码", en: "Password" },
    passwordPlaceholder: { zh: "请输入密码", en: "Enter your password" },
    confirmPassword: { zh: "确认密码", en: "Confirm Password" },
    confirmPasswordPlaceholder: { zh: "再次输入密码", en: "Re-enter your password" },
    displayName: { zh: "显示名称", en: "Display Name" },
    displayNamePlaceholder: { zh: "请输入显示名称", en: "Enter your display name" },
    loginBtn: { zh: "登录", en: "Sign In" },
    registerBtn: { zh: "注册", en: "Sign Up" },
    noAccount: { zh: "还没有账号？", en: "Don't have an account?" },
    hasAccount: { zh: "已有账号？", en: "Already have an account?" },
    goRegister: { zh: "注册", en: "Sign Up" },
    goLogin: { zh: "登录", en: "Sign In" },
    loginSuccess: { zh: "登录成功", en: "Login successful" },
    registerSuccess: { zh: "注册成功", en: "Registration successful" },
    passwordMismatch: { zh: "两次密码输入不一致", en: "Passwords do not match" },
    logoutBtn: { zh: "退出登录", en: "Sign Out" },
  },

  /* ============ 仪表盘 ============ */
  dashboard: {
    title: { zh: "我的项目", en: "My Projects" },
    newProject: { zh: "新建项目", en: "New Project" },
    emptyTitle: { zh: "还没有项目", en: "No projects yet" },
    emptyDesc: { zh: "创建你的第一个项目吧", en: "Create your first project" },
    sidebarDashboard: { zh: "仪表盘", en: "Dashboard" },
    sidebarProjects: { zh: "项目", en: "Projects" },
    sidebarTemplates: { zh: "模板", en: "Templates" },
    sidebarSettings: { zh: "设置", en: "Settings" },
    viewAllProjects: { zh: "查看全部项目", en: "View All Projects" },
    fromTemplate: { zh: "从模板开始", en: "Start from Template" },
    browseMore: { zh: "浏览更多模板", en: "Browse More Templates" },
  },

  /* ============ 问候语 ============ */
  greeting: {
    morning: { zh: "早上好", en: "Good morning" },
    afternoon: { zh: "下午好", en: "Good afternoon" },
    evening: { zh: "晚上好", en: "Good evening" },
    inputPlaceholder: { zh: "描述你的想法...", en: "Describe your idea..." },
    recentProjects: { zh: "最近项目", en: "Recent Projects" },
  },

  /* ============ 项目相关 ============ */
  project: {
    createTitle: { zh: "新建项目", en: "Create Project" },
    nameLabel: { zh: "项目名称", en: "Project Name" },
    namePlaceholder: { zh: "请输入项目名称", en: "Enter project name" },
    descLabel: { zh: "项目描述", en: "Description" },
    descPlaceholder: { zh: "简要描述你的项目（可选）", en: "Briefly describe your project (optional)" },
    createBtn: { zh: "创建", en: "Create" },
    cancelBtn: { zh: "取消", en: "Cancel" },
    createSuccess: { zh: "项目创建成功", en: "Project created" },
    status: {
      active: { zh: "进行中", en: "Active" },
      archived: { zh: "已归档", en: "Archived" },
    },
    conversations: { zh: "对话", en: "Conversations" },
    overview: { zh: "概览", en: "Overview" },
    runs: { zh: "运行记录", en: "Runs" },
    artifacts: { zh: "产物", en: "Artifacts" },
    newConversation: { zh: "新建对话", en: "New Conversation" },
    conversationTitle: { zh: "对话标题", en: "Conversation Title" },
    conversationPlaceholder: { zh: "输入对话标题（可选）", en: "Enter conversation title (optional)" },
    noConversations: { zh: "暂无对话", en: "No conversations" },
    noMessages: { zh: "暂无消息，发送第一条消息吧", en: "No messages yet, send the first one" },
    messagePlaceholder: { zh: "输入消息...", en: "Type a message..." },
    sendBtn: { zh: "发送", en: "Send" },
    createConversationSuccess: { zh: "对话创建成功", en: "Conversation created" },
  },

  /* ============ 生成流程 ============ */
  generation: {
    ideationTitle: { zh: "想法阶段", en: "Ideation" },
    inputPlaceholder: {
      zh: "描述你想要构建的产品...",
      en: "Describe the product you want to build...",
    },
    analyzeBtn: { zh: "分析想法", en: "Analyze Idea" },
    analyzing: { zh: "正在分析...", en: "Analyzing..." },
    analysisResult: { zh: "分析结果", en: "Analysis Result" },
    capacityTitle: { zh: "容量预算", en: "Capacity Budget" },
    totalPoints: { zh: "总点数", en: "Total Points" },
    tier: {
      small: { zh: "小型", en: "Small" },
      medium: { zh: "中型", en: "Medium" },
      large: { zh: "大型", en: "Large" },
    },
    overBudget: { zh: "超出预算", en: "Over Budget" },
    withinBudget: { zh: "预算内", en: "Within Budget" },
    needsContraction: { zh: "建议收缩", en: "Contraction Recommended" },
    mustContract: { zh: "必须收缩", en: "Must Contract" },
    noContraction: { zh: "无需收缩", en: "No Contraction Needed" },
    contractBtn: { zh: "开始收缩", en: "Start Contraction" },
    contracting: { zh: "正在收缩...", en: "Contracting..." },
    contractionResult: { zh: "收缩方案", en: "Contraction Result" },
    retained: { zh: "保留功能", en: "Retained Features" },
    deferred: { zh: "延后功能", en: "Deferred Features" },
    risks: { zh: "风险提示", en: "Risks" },
    rationale: { zh: "收缩理由", en: "Rationale" },
    beforeContraction: { zh: "收缩前", en: "Before" },
    afterContraction: { zh: "收缩后", en: "After" },
    scopeLocked: {
      zh: "功能范围已锁定，可以进入下一阶段。",
      en: "Feature scope is locked. Ready for the next phase.",
    },
    scopeLockedTitle: { zh: "Scope 已确认", en: "Scope Confirmed" },
    confirmBtn: { zh: "确认 Scope", en: "Confirm Scope" },
    confirming: { zh: "确认中...", en: "Confirming..." },
    confirmed: { zh: "Scope 已确认", en: "Scope Confirmed" },
    reanalyze: { zh: "重新分析", en: "Re-analyze" },
    backToProject: { zh: "返回项目", en: "Back to Project" },
    startDelegation: { zh: "开始全权委托", en: "Start Full Delegation" },
    startDelegationDesc: {
      zh: "系统将自动为您生成完整的前后端代码、数据库、文档与部署配置。",
      en: "The system will automatically generate complete frontend/backend code, database, documentation, and deployment configs.",
    },
    scopeTitle: { zh: "功能范围", en: "Feature Scope" },
    deferredItems: { zh: "延后项", en: "Deferred Items" },
    steps: {
      input: { zh: "输入想法", en: "Input Idea" },
      analyze: { zh: "分析", en: "Analyze" },
      contract: { zh: "收缩", en: "Contract" },
      confirm: { zh: "确认", en: "Confirm" },
    },
    dimensions: {
      pages: { zh: "页面数", en: "Pages" },
      api_endpoints: { zh: "API 端点", en: "API Endpoints" },
      db_tables: { zh: "数据表", en: "DB Tables" },
      auth_flows: { zh: "认证流程", en: "Auth Flows" },
      integrations: { zh: "第三方集成", en: "Integrations" },
      file_upload: { zh: "文件上传", en: "File Upload" },
      realtime: { zh: "实时功能", en: "Realtime" },
      payment: { zh: "支付功能", en: "Payment" },
    },
    priority: {
      high: { zh: "高", en: "High" },
      medium: { zh: "中", en: "Medium" },
      low: { zh: "低", en: "Low" },
    },
  },

  /* ============ 全权委托 ============ */
  delegation: {
    tab: { zh: "全权委托", en: "Delegation" },
    title: { zh: "全权委托", en: "Full Delegation" },
    triggerTitle: { zh: "启动全权委托", en: "Launch Delegation" },
    triggerDesc: {
      zh: "系统将自动执行完整 Agent 链路，生成前后端代码、数据库、文档与部署配置。",
      en: "The system will execute the full Agent pipeline to generate frontend/backend code, database, documentation, and deployment configs.",
    },
    startBtn: { zh: "开始全权委托", en: "Start Delegation" },
    historyTitle: { zh: "全权委托历史", en: "Delegation History" },
    emptyState: { zh: "暂无运行记录", en: "No runs yet" },
    triggerBtn: { zh: "触发全权委托", en: "Trigger Delegation" },
    statusRunning: { zh: "运行中", en: "Running" },
    statusCompleted: { zh: "已完成", en: "Completed" },
    creating: { zh: "正在创建...", en: "Creating..." },
    conflictError: {
      zh: "已有运行中的任务，请等待完成后再试",
      en: "A run is already in progress. Please wait for it to complete.",
    },
    createError: {
      zh: "创建运行失败，请稍后重试",
      en: "Failed to create run. Please try again later.",
    },
    recentRuns: { zh: "最近运行", en: "Recent Runs" },
    viewAll: { zh: "查看全部", en: "View All" },
    noRuns: { zh: "暂无运行记录", en: "No runs yet" },
    startFirst: {
      zh: "点击上方按钮开始第一次全权委托",
      en: "Click the button above to start your first delegation",
    },
  },

  /* ============ 通用 ============ */
  common: {
    loading: { zh: "加载中...", en: "Loading..." },
    error: { zh: "出错了", en: "Something went wrong" },
    retry: { zh: "重试", en: "Retry" },
    back: { zh: "返回", en: "Back" },
    confirm: { zh: "确认", en: "Confirm" },
    cancel: { zh: "取消", en: "Cancel" },
    language: { zh: "语言", en: "Language" },
    search: { zh: "搜索", en: "Search" },
    sortNewest: { zh: "最新优先", en: "Newest First" },
    sortOldest: { zh: "最早优先", en: "Oldest First" },
    sortName: { zh: "按名称", en: "By Name" },
    noData: { zh: "暂无数据", en: "No data" },
    edit: { zh: "编辑", en: "Edit" },
    save: { zh: "保存", en: "Save" },
    delete: { zh: "删除", en: "Delete" },
  },

  /* ============ 项目列表页 ============ */
  projectList: {
    title: { zh: "所有项目", en: "All Projects" },
    searchPlaceholder: { zh: "按名称搜索项目...", en: "Search projects by name..." },
    emptyTitle: { zh: "还没有项目", en: "No projects yet" },
    emptyDesc: { zh: "创建你的第一个项目，开始你的创意之旅", en: "Create your first project and start your creative journey" },
    lastUpdated: { zh: "最后更新", en: "Last updated" },
  },

  /* ============ 项目概览页 ============ */
  projectOverview: {
    title: { zh: "项目概览", en: "Project Overview" },
    conversations: { zh: "对话", en: "Conversations" },
    snapshots: { zh: "快照", en: "Snapshots" },
    delegationRuns: { zh: "委托运行", en: "Delegation Runs" },
    recentActivity: { zh: "最近活动", en: "Recent Activity" },
    noActivity: { zh: "暂无活动记录", en: "No recent activity" },
    quickActions: { zh: "快捷操作", en: "Quick Actions" },
    newConversation: { zh: "新建对话", en: "New Conversation" },
    startIdeation: { zh: "开始构思", en: "Start Ideation" },
    fullDelegation: { zh: "全权委托", en: "Full Delegation" },
    editProject: { zh: "编辑项目", en: "Edit Project" },
    saveSuccess: { zh: "项目已更新", en: "Project updated" },
  },

  /* ============ 委托运行历史页 ============ */
  runsHistory: {
    title: { zh: "运行历史", en: "Run History" },
    runId: { zh: "运行 ID", en: "Run ID" },
    status: { zh: "状态", en: "Status" },
    created: { zh: "创建时间", en: "Created" },
    completed: { zh: "完成时间", en: "Completed" },
    duration: { zh: "耗时", en: "Duration" },
    emptyTitle: { zh: "还没有运行记录", en: "No runs yet" },
    emptyDesc: { zh: "启动全权委托后，运行记录会出现在这里", en: "Run records will appear here after you start a delegation" },
    statusPending: { zh: "等待中", en: "Pending" },
    statusRunning: { zh: "运行中", en: "Running" },
    statusCompleted: { zh: "已完成", en: "Completed" },
    statusFailed: { zh: "失败", en: "Failed" },
    statusNeedsAttention: { zh: "需要关注", en: "Needs Attention" },
  },

  /* ============ 分支相关 ============ */
  branches: {
    title: { zh: "分支", en: "Branches" },
    selector: { zh: "切换分支", en: "Switch Branch" },
    create: { zh: "新建分支", en: "New Branch" },
    fork: { zh: "Fork 分支", en: "Fork Branch" },
    rollback: { zh: "回滚", en: "Rollback" },
    rollbackConfirm: {
      zh: "确定要回滚到此快照吗？这将创建一个新分支。",
      en: "Are you sure you want to rollback to this snapshot? This will create a new branch.",
    },
    rollbackSuccess: { zh: "回滚成功", en: "Rollback successful" },
    noChange: { zh: "当前已在此快照", en: "Already at this snapshot" },
    forked: { zh: "已创建新分支", en: "New branch created" },
    switched: {
      zh: "已切换到包含此快照的分支",
      en: "Switched to the branch containing this snapshot",
    },
    mainBranch: { zh: "主分支", en: "Main Branch" },
    messageCount: { zh: "{count} 条消息", en: "{count} messages" },
    snapshotUpdated: { zh: "快照已更新", en: "Snapshot updated" },
    rollbackToSnapshot: {
      zh: "回滚到此快照",
      en: "Rollback to this snapshot",
    },
  },

  /* ============ 审批相关 ============ */
  approval: {
    title: { zh: "审批", en: "Approval" },
    requiresApproval: {
      zh: "此运行需要您的审批",
      en: "This run requires your approval",
    },
    riskCount: {
      zh: "{count} 个高风险项",
      en: "{count} high risk item(s)",
    },
    decisionCount: {
      zh: "{count} 个待决策项",
      en: "{count} pending decision(s)",
    },
    approve: { zh: "批准并继续", en: "Approve & Continue" },
    reject: { zh: "拒绝", en: "Reject" },
    adjust: { zh: "要求调整", en: "Request Adjustment" },
    approveConfirm: {
      zh: "确定批准此运行？所有风险和决策将被标记为已接受。",
      en: "Approve this run? All risks and decisions will be marked as accepted.",
    },
    rejectConfirm: {
      zh: "确定拒绝此运行？请填写拒绝理由。",
      en: "Reject this run? Please provide a reason.",
    },
    adjustPrompt: {
      zh: "请描述需要调整的内容：",
      en: "Describe what needs to be adjusted:",
    },
    reason: { zh: "理由（可选）", en: "Reason (optional)" },
    feedback: { zh: "调整反馈", en: "Adjustment Feedback" },
    approved: { zh: "已批准", en: "Approved" },
    rejected: { zh: "已拒绝", en: "Rejected" },
    adjusted: { zh: "已要求调整", en: "Adjustment Requested" },
    noRisks: { zh: "暂无高风险项", en: "No high-risk items" },
    noDecisions: { zh: "暂无待决策项", en: "No pending decisions" },
    riskTitle: { zh: "高风险项", en: "High Risks" },
    decisionTitle: { zh: "待决策项", en: "Pending Decisions" },
    mitigation: { zh: "缓解措施：", en: "Mitigation: " },
    alternatives: { zh: "备选方案：", en: "Alternatives:" },
    history: { zh: "审批历史", en: "Approval History" },
  },

  /* ============ 模板相关 ============ */
  templates: {
    title: { zh: "项目模板", en: "Project Templates" },
    subtitle: { zh: "选择一个模板快速开始", en: "Choose a template to get started quickly" },
    create: { zh: "从模板创建", en: "Create from Template" },
    projectName: { zh: "项目名称", en: "Project Name" },
    confirm: { zh: "创建项目", en: "Create Project" },
    success: { zh: "项目创建成功", en: "Project created successfully" },
    empty: { zh: "暂无可用模板", en: "No templates available" },
    categories: {
      saas: { zh: "SaaS 应用", en: "SaaS App" },
      api: { zh: "API 服务", en: "API Service" },
      landing: { zh: "落地页", en: "Landing Page" },
      dashboard: { zh: "管理后台", en: "Dashboard" },
      other: { zh: "其他", en: "Other" },
    },
  },

  /* ============ 404 页面 ============ */
  notFound: {
    title: { zh: "页面未找到", en: "Page Not Found" },
    description: {
      zh: "您访问的页面不存在或已被移除",
      en: "The page you are looking for does not exist or has been removed",
    },
    backHome: { zh: "返回首页", en: "Back to Home" },
  },

  /* ============ 错误边界 ============ */
  error: {
    title: { zh: "出了点问题", en: "Something went wrong" },
    description: {
      zh: "页面加载时发生了错误",
      en: "An error occurred while loading the page",
    },
    retry: { zh: "重试", en: "Retry" },
    backHome: { zh: "返回首页", en: "Back to Home" },
  },

  /* ============ 用户设置 ============ */
  settings: {
    title: { zh: "设置", en: "Settings" },
    profile: { zh: "个人信息", en: "Profile" },
    username: { zh: "用户名", en: "Username" },
    email: { zh: "邮箱", en: "Email" },
    appearance: { zh: "外观", en: "Appearance" },
    language: { zh: "语言", en: "Language" },
    security: { zh: "安全", en: "Security" },
    changePassword: { zh: "修改密码", en: "Change Password" },
    currentPassword: { zh: "当前密码", en: "Current Password" },
    newPassword: { zh: "新密码", en: "New Password" },
    confirmPassword: { zh: "确认密码", en: "Confirm Password" },
    save: { zh: "保存", en: "Save" },
    comingSoon: { zh: "即将推出", en: "Coming Soon" },
    apiKeys: { zh: "API 密钥", en: "API Keys" },
    apiKeysDesc: { zh: "配置您的第三方 LLM API 密钥", en: "Configure your third-party LLM API keys" },
    addKey: { zh: "添加密钥", en: "Add Key" },
    provider: { zh: "提供商", en: "Provider" },
    apiKey: { zh: "API 密钥", en: "API Key" },
    apiKeyPlaceholder: { zh: "请输入 API 密钥", en: "Enter your API key" },
    label: { zh: "标签（可选）", en: "Label (optional)" },
    labelPlaceholder: { zh: "自定义标签", en: "Custom label" },
    validate: { zh: "验证", en: "Validate" },
    validating: { zh: "验证中...", en: "Validating..." },
    valid: { zh: "有效", en: "Valid" },
    invalid: { zh: "无效", en: "Invalid" },
    notValidated: { zh: "未验证", en: "Not Validated" },
    deleteConfirm: { zh: "确定删除此密钥？", en: "Delete this key?" },
    noKeys: { zh: "暂无 API 密钥，请添加以使用 LLM 功能", en: "No API keys yet. Add one to use LLM features" },
    modelPreference: { zh: "模型偏好", en: "Model Preference" },
    modelPreferenceDesc: { zh: "选择推理和生成任务使用的模型", en: "Choose models for reasoning and generation tasks" },
    reasoningModel: { zh: "推理模型", en: "Reasoning Model" },
    generationModel: { zh: "生成模型", en: "Generation Model" },
    selectModel: { zh: "选择模型", en: "Select model" },
    usage: { zh: "用量统计", en: "Usage" },
    usageDesc: { zh: "最近 30 天的 LLM 使用情况", en: "LLM usage in the last 30 days" },
    totalTokens: { zh: "总 Token", en: "Total Tokens" },
    totalCost: { zh: "总费用", en: "Total Cost" },
    callCount: { zh: "调用次数", en: "Calls" },
    promptTokens: { zh: "输入 Token", en: "Prompt Tokens" },
    completionTokens: { zh: "输出 Token", en: "Completion Tokens" },
    noUsage: { zh: "暂无使用记录", en: "No usage records" },
    credits: { zh: "额度购买", en: "Purchase Credits" },
    creditsDesc: { zh: "购买平台额度以使用 LLM 功能", en: "Purchase platform credits for LLM features" },
    buyCredits: { zh: "购买额度", en: "Buy Credits" },
    usageWarning: { zh: "您的 LLM 用量较高，最近 30 天已消费", en: "High LLM usage — you have spent" },
    saveSuccess: { zh: "保存成功", en: "Saved successfully" },
    deleteSuccess: { zh: "删除成功", en: "Deleted successfully" },
    addSuccess: { zh: "密钥添加成功", en: "Key added successfully" },
  },

  /* ============ 产物页 ============ */
  artifacts: {
    title: { zh: "项目产物", en: "Artifacts" },
    emptyTitle: { zh: "暂无产物", en: "No artifacts yet" },
    emptyDesc: { zh: "运行全权委托后，生成的产物会出现在这里", en: "Generated artifacts will appear here after a delegation run" },
    kind: {
      frontend_code: { zh: "前端代码", en: "Frontend Code" },
      backend_code: { zh: "后端代码", en: "Backend Code" },
      doc: { zh: "文档", en: "Documentation" },
      diagram: { zh: "图表", en: "Diagram" },
      config: { zh: "配置", en: "Config" },
      other: { zh: "其他", en: "Other" },
    },
    version: { zh: "版本", en: "Version" },
  },
} as const;

export type TranslationKey = keyof typeof translations;
export default translations;
