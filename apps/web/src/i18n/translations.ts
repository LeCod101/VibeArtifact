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

  /* ============ 通用 ============ */
  common: {
    loading: { zh: "加载中...", en: "Loading..." },
    error: { zh: "出错了", en: "Something went wrong" },
    retry: { zh: "重试", en: "Retry" },
    back: { zh: "返回", en: "Back" },
    confirm: { zh: "确认", en: "Confirm" },
    cancel: { zh: "取消", en: "Cancel" },
    language: { zh: "语言", en: "Language" },
  },
} as const;

export type TranslationKey = keyof typeof translations;
export default translations;
