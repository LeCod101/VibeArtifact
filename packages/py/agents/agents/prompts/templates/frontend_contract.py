"""
Frontend Agent 输出契约。

定义 FrontendPlan 中每个 FileSpec 的字段约束、
必须包含的文件列表、以及命名和路径规范。
此契约会被注入 PromptBuilder 的 contract 层。
"""

FRONTEND_CONTRACT = """## FrontendPlan 输出契约

### 顶层字段

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| files | array[FileSpec] | 是 | 至少 8 个文件，不可为空 |

### FileSpec 字段定义

| 字段 | 类型 | 必填 | 约束 |
|------|------|------|------|
| path | string | 是 | 以 "frontend/" 开头，使用正斜杠分隔，不含 ".." |
| content | string | 是 | 非空字符串，包含完整的文件源码 |
| language | string | 是 | 取值: "typescript" / "css" / "json" / "javascript" / "dockerfile" |

### 必须包含的配置文件

以下文件缺一不可：

1. `frontend/package.json` — 依赖和脚本
2. `frontend/tsconfig.json` — TypeScript 配置
3. `frontend/tailwind.config.ts` — Tailwind 配置
4. `frontend/next.config.mjs` — Next.js 配置
5. `frontend/postcss.config.mjs` — PostCSS 配置
6. `frontend/Dockerfile` — 容器化配置

### 必须包含的应用文件

1. `frontend/app/layout.tsx` — 根布局
2. `frontend/app/page.tsx` — 首页
3. `frontend/app/globals.css` — 全局样式
4. `frontend/lib/api.ts` — API 客户端
5. `frontend/lib/types.ts` — TypeScript 类型

### 每个实体必须生成的文件

对于 SchemaPlan 中的每个核心实体（名为 X），至少生成：

| 文件路径模式 | 说明 |
|-------------|------|
| `frontend/app/{feature}/page.tsx` | 该实体的功能页面（feature 为实体的 kebab-case 复数形式） |

### path 规范

1. 路径以 "frontend/" 开头
2. 使用正斜杠 "/" 分隔
3. app 目录下的页面文件固定为 page.tsx
4. 组件文件使用 PascalCase 命名
5. 不允许包含 ".." 或绝对路径

### content 规范

1. TypeScript 文件必须类型安全
2. 所有注释使用中文
3. 禁止尾行注释
4. 组件必须有默认导出
5. 客户端组件必须有 "use client" 指令

### language 取值

| language 值 | 适用文件 |
|-------------|---------|
| typescript | .tsx / .ts 文件 |
| css | .css 文件 |
| json | .json 文件 |
| javascript | .mjs / .js 文件 |
| dockerfile | Dockerfile |

### 合法性自检

输出前自检：
1. files 列表不为空
2. 每个文件都有 path、content、language 三个字段
3. 所有 path 以 "frontend/" 开头
4. 必须包含所有配置文件和应用文件
5. 每个核心实体都有对应的功能页面
6. content 不为空字符串
7. language 值属于合法集合
8. 无重复 path
9. API 客户端中的路径与 SchemaPlan 中的端点一致
"""
