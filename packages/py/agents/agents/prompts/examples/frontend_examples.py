"""
Frontend Agent Few-Shot 示例。

提供 Todo 应用前端完整示例，帮助 LLM 理解 FrontendPlan 的输出格式。
每个文件包含 path、content、language，代码结构完整但精简。
"""

# noqa: E501 — few-shot 示例中的代码字符串行长度受限于真实代码格式

FRONTEND_EXAMPLES = (  # noqa: E501
    """## 示例

### 示例（Todo 应用前端）

输入（SchemaPlan 摘要）：
实体：Todo（id, title, description, status）
端点：GET /api/todos, POST /api/todos, PUT /api/todos/{id}, DELETE /api/todos/{id}

输出：
{
  "files": [
    {
      "path": "frontend/app/layout.tsx",
      "language": "typescript",
      "content": "import type { Metadata } from 'next'\\nimport './globals.css'\\n\\n/** 站点元数据 */\\nexport const metadata: Metadata = {\\n  title: '效率清单',\\n  description: 'Todo 待办事项管理应用',\\n}\\n\\n/** 根布局组件 */\\nexport default function RootLayout({\\n  children,\\n}: {\\n  children: React.ReactNode\\n}) {\\n  return (\\n    <html lang=\\"zh-CN\\">\\n      <body className=\\"min-h-screen bg-gray-50\\">{children}</body>\\n    </html>\\n  )\\n}\\n"
    },
    {
      "path": "frontend/app/page.tsx",
      "language": "typescript",
      "content": "import Link from 'next/link'\\n\\n/** 首页 - 功能导航入口 */\\nexport default function HomePage() {\\n  return (\\n    <main className=\\"max-w-2xl mx-auto py-12 px-4\\">\\n      <h1 className=\\"text-3xl font-bold mb-8\\">效率清单</h1>\\n      <div className=\\"space-y-4\\">\\n        <Link href=\\"/todos\\" className=\\"block p-4 bg-white rounded shadow hover:shadow-md\\">\\n          <h2 className=\\"text-xl font-semibold\\">待办事项管理</h2>\\n          <p className=\\"text-gray-600\\">创建、编辑和管理你的待办事项</p>\\n        </Link>\\n      </div>\\n    </main>\\n  )\\n}\\n"
    },
    {
      "path": "frontend/app/globals.css",
      "language": "css",
      "content": "@tailwind base;\\n@tailwind components;\\n@tailwind utilities;\\n"
    },
    {
      "path": "frontend/app/todos/page.tsx",
      "language": "typescript",
      "content": "'use client'\\n\\nimport { useEffect, useState } from 'react'\\nimport { type Todo, fetchTodos, createTodo, deleteTodo } from '@/lib/api'\\n\\n/** 待办事项管理页面 */\\nexport default function TodosPage() {\\n  const [todos, setTodos] = useState<Todo[]>([])\\n  const [title, setTitle] = useState('')\\n\\n  /** 加载待办列表 */\\n  useEffect(() => {\\n    fetchTodos().then(setTodos)\\n  }, [])\\n\\n  /** 处理创建 */\\n  const handleCreate = async () => {\\n    if (!title.trim()) return\\n    const todo = await createTodo({ title, status: 'pending' })\\n    setTodos([...todos, todo])\\n    setTitle('')\\n  }\\n\\n  /** 处理删除 */\\n  const handleDelete = async (id: string) => {\\n    await deleteTodo(id)\\n    setTodos(todos.filter(t => t.id !== id))\\n  }\\n\\n  return (\\n    <main className=\\"max-w-2xl mx-auto py-8 px-4\\">\\n      <h1 className=\\"text-2xl font-bold mb-6\\">待办事项</h1>\\n      <div className=\\"flex gap-2 mb-6\\">\\n        <input\\n          value={title}\\n          onChange={e => setTitle(e.target.value)}\\n          placeholder=\\"输入待办事项...\\"\\n          className=\\"flex-1 px-3 py-2 border rounded\\"\\n        />\\n        <button onClick={handleCreate} className=\\"px-4 py-2 bg-blue-500 text-white rounded\\">\\n          添加\\n        </button>\\n      </div>\\n      <ul className=\\"space-y-2\\">\\n        {todos.map(todo => (\\n          <li key={todo.id} className=\\"flex items-center justify-between p-3 bg-white rounded shadow\\">\\n            <span>{todo.title}</span>\\n            <button onClick={() => handleDelete(todo.id)} className=\\"text-red-500\\">删除</button>\\n          </li>\\n        ))}\\n      </ul>\\n    </main>\\n  )\\n}\\n"
    },
    {
      "path": "frontend/lib/api.ts",
      "language": "typescript",
      "content": "/** API 客户端模块 */\\n\\n/** API 基础地址 */\\nconst API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'\\n\\n/** Todo 数据类型 */\\nexport interface Todo {\\n  id: string\\n  title: string\\n  description: string | null\\n  status: string\\n  created_at: string\\n  updated_at: string\\n}\\n\\n/** 创建 Todo 请求体 */\\nexport interface TodoCreate {\\n  title: string\\n  description?: string\\n  status?: string\\n}\\n\\n/** 获取 Todo 列表 */\\nexport async function fetchTodos(): Promise<Todo[]> {\\n  const res = await fetch(`${API_BASE}/api/todos`)\\n  return res.json()\\n}\\n\\n/** 创建 Todo */\\nexport async function createTodo(data: TodoCreate): Promise<Todo> {\\n  const res = await fetch(`${API_BASE}/api/todos`, {\\n    method: 'POST',\\n    headers: { 'Content-Type': 'application/json' },\\n    body: JSON.stringify(data),\\n  })\\n  return res.json()\\n}\\n\\n/** 删除 Todo */\\nexport async function deleteTodo(id: string): Promise<void> {\\n  await fetch(`${API_BASE}/api/todos/${id}`, { method: 'DELETE' })\\n}\\n"
    },
    {
      "path": "frontend/lib/types.ts",
      "language": "typescript",
      "content": "/** 全局类型定义模块 */\\n\\n/** Todo 实体类型 */\\nexport interface Todo {\\n  id: string\\n  title: string\\n  description: string | null\\n  status: string\\n  created_at: string\\n  updated_at: string\\n}\\n\\n/** 创建 Todo 请求体 */\\nexport interface TodoCreate {\\n  title: string\\n  description?: string\\n  status?: string\\n}\\n\\n/** 更新 Todo 请求体 */\\nexport interface TodoUpdate {\\n  title?: string\\n  description?: string\\n  status?: string\\n}\\n"
    },
    {
      "path": "frontend/package.json",
      "language": "json",
      "content": "{\\n  \\"name\\": \\"todo-frontend\\",\\n  \\"version\\": \\"0.1.0\\",\\n  \\"private\\": true,\\n  \\"scripts\\": {\\n    \\"dev\\": \\"next dev\\",\\n    \\"build\\": \\"next build\\",\\n    \\"start\\": \\"next start\\"\\n  },\\n  \\"dependencies\\": {\\n    \\"next\\": \\"15.0.0\\",\\n    \\"react\\": \\"19.0.0\\",\\n    \\"react-dom\\": \\"19.0.0\\"\\n  },\\n  \\"devDependencies\\": {\\n    \\"@types/node\\": \\"^20.0.0\\",\\n    \\"@types/react\\": \\"^19.0.0\\",\\n    \\"autoprefixer\\": \\"^10.4.0\\",\\n    \\"postcss\\": \\"^8.4.0\\",\\n    \\"tailwindcss\\": \\"^3.4.0\\",\\n    \\"typescript\\": \\"^5.6.0\\"\\n  }\\n}\\n"
    },
    {
      "path": "frontend/tailwind.config.ts",
      "language": "typescript",
      "content": "import type { Config } from 'tailwindcss'\\n\\nconst config: Config = {\\n  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],\\n  theme: { extend: {} },\\n  plugins: [],\\n}\\n\\nexport default config\\n"
    },
    {
      "path": "frontend/tsconfig.json",
      "language": "json",
      "content": "{\\n  \\"compilerOptions\\": {\\n    \\"target\\": \\"es2017\\",\\n    \\"lib\\": [\\"dom\\", \\"dom.iterable\\", \\"esnext\\"],\\n    \\"allowJs\\": true,\\n    \\"skipLibCheck\\": true,\\n    \\"strict\\": true,\\n    \\"noEmit\\": true,\\n    \\"esModuleInterop\\": true,\\n    \\"module\\": \\"esnext\\",\\n    \\"moduleResolution\\": \\"bundler\\",\\n    \\"resolveJsonModule\\": true,\\n    \\"isolatedModules\\": true,\\n    \\"jsx\\": \\"preserve\\",\\n    \\"incremental\\": true,\\n    \\"plugins\\": [{ \\"name\\": \\"next\\" }],\\n    \\"paths\\": { \\"@/*\\": [\\"./*\\"] }\\n  },\\n  \\"include\\": [\\"next-env.d.ts\\", \\"**/*.ts\\", \\"**/*.tsx\\", \\".next/types/**/*.ts\\"],\\n  \\"exclude\\": [\\"node_modules\\"]\\n}\\n"
    },
    {
      "path": "frontend/next.config.mjs",
      "language": "javascript",
      "content": "/** @type {import('next').NextConfig} */\\nconst nextConfig = {}\\n\\nexport default nextConfig\\n"
    },
    {
      "path": "frontend/postcss.config.mjs",
      "language": "javascript",
      "content": "/** @type {import('postcss-load-config').Config} */\\nconst config = {\\n  plugins: {\\n    tailwindcss: {},\\n    autoprefixer: {},\\n  },\\n}\\n\\nexport default config\\n"
    },
    {
      "path": "frontend/Dockerfile",
      "language": "dockerfile",
      "content": "FROM node:20-slim AS deps\\nWORKDIR /app\\nCOPY package.json package-lock.json* ./\\nRUN npm ci\\n\\nFROM node:20-slim AS builder\\nWORKDIR /app\\nCOPY --from=deps /app/node_modules ./node_modules\\nCOPY . .\\nRUN npm run build\\n\\nFROM node:20-slim AS runner\\nWORKDIR /app\\nCOPY --from=builder /app/.next ./.next\\nCOPY --from=builder /app/node_modules ./node_modules\\nCOPY --from=builder /app/package.json ./\\n\\nEXPOSE 3000\\nCMD [\\"npm\\", \\"start\\"]\\n"
    }
  ]
}
"""
)
