/**
 * WebContainer 文件系统桥接模块
 *
 * 将 ArtifactResponseV2 数组转换为 WebContainer 可用的 FileSystemTree 结构。
 * 自动补全缺失的 package.json / index.html / vite.config.ts / main.tsx。
 */

import type { FileSystemTree } from "@webcontainer/api";
import type { ArtifactResponseV2 } from "@/lib/api-client/types";

/**
 * 在嵌套的 FileSystemTree 中按路径设置文件内容
 *
 * @param tree - 目标 FileSystemTree 对象
 * @param pathParts - 文件路径分段数组，如 ["src", "App.tsx"]
 * @param content - 文件内容字符串
 */
function setNestedFile(
  tree: FileSystemTree,
  pathParts: string[],
  content: string,
): void {
  if (pathParts.length === 0) return;

  if (pathParts.length === 1) {
    tree[pathParts[0]] = {
      file: { contents: content },
    };
    return;
  }

  // 中间路径段作为目录节点
  const dirName = pathParts[0];
  if (!tree[dirName] || !("directory" in tree[dirName])) {
    tree[dirName] = { directory: {} };
  }
  const dirNode = tree[dirName] as { directory: FileSystemTree };
  setNestedFile(dirNode.directory, pathParts.slice(1), content);
}

/**
 * 从代码中提取 import 的包名
 *
 * 扫描 import 语句，提取非相对路径的包名（第三方依赖）。
 * 例如 `import React from 'react'` 提取出 `react`。
 *
 * @param code - 源代码字符串
 * @returns 去重后的包名数组
 */
function extractImportedPackages(code: string): string[] {
  const packages = new Set<string>();

  // 匹配 import ... from "xxx" 和 import "xxx"
  const importRegex = /import\s+(?:.*?\s+from\s+)?["']([^"'.][^"']*)["']/g;
  let match: RegExpExecArray | null;

  while ((match = importRegex.exec(code)) !== null) {
    const pkg = match[1];
    // 跳过相对路径
    if (pkg.startsWith(".") || pkg.startsWith("/")) continue;
    // 提取包名（支持 @scope/pkg 格式）
    const parts = pkg.split("/");
    const name = parts[0].startsWith("@")
      ? `${parts[0]}/${parts[1]}`
      : parts[0];
    packages.add(name);
  }

  // 匹配 require("xxx")
  const requireRegex = /require\s*\(\s*["']([^"'.][^"']*)["']\s*\)/g;
  while ((match = requireRegex.exec(code)) !== null) {
    const pkg = match[1];
    if (pkg.startsWith(".") || pkg.startsWith("/")) continue;
    const parts = pkg.split("/");
    const name = parts[0].startsWith("@")
      ? `${parts[0]}/${parts[1]}`
      : parts[0];
    packages.add(name);
  }

  return Array.from(packages);
}

/**
 * 生成默认 package.json
 *
 * 扫描所有产物的 import 语句提取依赖，始终包含 react / react-dom / vite / @vitejs/plugin-react。
 *
 * @param artifacts - 产物数组
 * @returns package.json 字符串内容
 */
function generateDefaultPackageJson(artifacts: ArtifactResponseV2[]): string {
  // 基础依赖
  const deps: Record<string, string> = {
    react: "^18.2.0",
    "react-dom": "^18.2.0",
  };
  const devDeps: Record<string, string> = {
    vite: "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
  };

  // 常见第三方包与版本映射
  const knownVersions: Record<string, string> = {
    "lucide-react": "^0.300.0",
    "tailwindcss": "^3.4.0",
    "clsx": "^2.0.0",
    "framer-motion": "^11.0.0",
    "zustand": "^4.4.0",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.0.0",
  };

  // 扫描所有产物的 import 语句
  for (const artifact of artifacts) {
    if (artifact.artifact_type !== "code" || !artifact.content) continue;
    const packages = extractImportedPackages(artifact.content);
    for (const pkg of packages) {
      // 跳过已有的基础依赖和 dev 依赖
      if (deps[pkg] || devDeps[pkg]) continue;
      // 跳过 react/react-dom（已包含）
      if (pkg === "react" || pkg === "react-dom") continue;
      deps[pkg] = knownVersions[pkg] ?? "latest";
    }
  }

  const pkgJson = {
    name: "preview-project",
    private: true,
    version: "0.0.0",
    type: "module",
    scripts: {
      dev: "vite",
      build: "vite build",
    },
    dependencies: deps,
    devDependencies: devDeps,
  };

  return JSON.stringify(pkgJson, null, 2);
}

/**
 * 生成默认 index.html（Vite 入口）
 *
 * @returns index.html 内容字符串
 */
function generateDefaultIndexHtml(): string {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Preview</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
</html>`;
}

/**
 * 生成默认 vite.config.ts
 *
 * @returns vite.config.ts 内容字符串
 */
function generateDefaultViteConfig(): string {
  return `import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})`;
}

/**
 * 生成默认 src/main.tsx 入口
 *
 * 查找产物中可能的 App 组件并渲染到 root 节点。
 *
 * @param artifacts - 产物数组
 * @returns main.tsx 内容字符串
 */
function generateDefaultMainTsx(artifacts: ArtifactResponseV2[]): string {
  // 查找可能的 App 组件文件
  let appImportPath = "./App";

  for (const a of artifacts) {
    if (a.artifact_type !== "code") continue;
    const fp = a.file_path ?? a.title;
    const lower = fp.toLowerCase();
    // 检查是否有 App 组件文件
    if (lower.includes("app.tsx") || lower.includes("app.jsx")) {
      // 去掉 src/ 前缀和扩展名构建相对导入
      const clean = fp
        .replace(/^src\//, "./")
        .replace(/\.(tsx|jsx|ts|js)$/, "");
      appImportPath = clean.startsWith("./") ? clean : `./${clean}`;
      break;
    }
  }

  return `import React from 'react'
import ReactDOM from 'react-dom/client'
import App from '${appImportPath}'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)`;
}

/**
 * 将 ArtifactResponseV2 数组转换为 WebContainer FileSystemTree
 *
 * 核心逻辑：
 * 1. 遍历所有 code 类型的产物
 * 2. 按 file_path 构建嵌套目录结构
 * 3. 自动补全缺失的 package.json / index.html / vite.config.ts / main.tsx
 *
 * @param artifacts - 产物数组（应仅包含 code 类型）
 * @returns WebContainer 可用的文件系统树
 */
export function buildFileSystemTree(
  artifacts: ArtifactResponseV2[],
): FileSystemTree {
  const tree: FileSystemTree = {};

  // 用于检查是否已有关键文件
  let hasPackageJson = false;
  let hasIndexHtml = false;
  let hasViteConfig = false;
  let hasMainEntry = false;

  // 遍历所有 code 类型产物，构建文件树
  for (const artifact of artifacts) {
    if (artifact.artifact_type !== "code") continue;
    if (!artifact.content) continue;

    // 使用 file_path 或 title 作为文件名
    const filePath = artifact.file_path ?? artifact.title;
    if (!filePath) continue;

    // 检查关键文件
    const lower = filePath.toLowerCase();
    if (lower === "package.json") hasPackageJson = true;
    if (lower === "index.html") hasIndexHtml = true;
    if (lower.startsWith("vite.config")) hasViteConfig = true;
    if (
      lower === "src/main.tsx" ||
      lower === "src/main.jsx" ||
      lower === "src/main.ts" ||
      lower === "src/index.tsx" ||
      lower === "src/index.jsx"
    ) {
      hasMainEntry = true;
    }

    // 按路径分段插入文件树
    const parts = filePath.split("/").filter(Boolean);
    setNestedFile(tree, parts, artifact.content);
  }

  // 补全缺失的关键文件
  if (!hasPackageJson) {
    setNestedFile(tree, ["package.json"], generateDefaultPackageJson(artifacts));
  }
  if (!hasIndexHtml) {
    setNestedFile(tree, ["index.html"], generateDefaultIndexHtml());
  }
  if (!hasViteConfig) {
    setNestedFile(tree, ["vite.config.ts"], generateDefaultViteConfig());
  }
  if (!hasMainEntry) {
    setNestedFile(
      tree,
      ["src", "main.tsx"],
      generateDefaultMainTsx(artifacts),
    );
  }

  return tree;
}
