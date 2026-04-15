/**
 * iframe 沙箱预览组件
 *
 * 将 code 类型的 Artifact（HTML/CSS/JS/JSX/TSX）在安全的 iframe 中实时渲染。
 * 安全策略：sandbox 仅开放 allow-scripts allow-modals，禁止 allow-same-origin。
 */
"use client";

import { useCallback, useMemo, useState } from "react";
import { AlertTriangle, Eye, RefreshCw } from "lucide-react";

export interface PreviewIframeProps {
  /** 源代码内容 */
  code: string;
  /** 语言标识，如 html / css / javascript / typescript / jsx / tsx */
  language: string | null;
  /** 文件路径，用于辅助判断预览类型 */
  filePath?: string | null;
}

/**
 * 判断文件扩展名
 */
function getExtension(filePath: string | null | undefined): string {
  if (!filePath) return "";
  const dot = filePath.lastIndexOf(".");
  if (dot === -1) return "";
  return filePath.slice(dot + 1).toLowerCase();
}

/**
 * 判断是否为 HTML 类型
 */
function isHtmlType(language: string | null, filePath: string | null | undefined): boolean {
  if (language?.toLowerCase() === "html") return true;
  if (getExtension(filePath) === "html") return true;
  return false;
}

/**
 * 判断是否为 CSS 类型
 */
function isCssType(language: string | null, filePath: string | null | undefined): boolean {
  if (language?.toLowerCase() === "css") return true;
  if (getExtension(filePath) === "css") return true;
  return false;
}

/**
 * 判断是否为 JavaScript 类型（不含 JSX）
 */
function isJsType(language: string | null, filePath: string | null | undefined): boolean {
  const lang = language?.toLowerCase() ?? "";
  if (lang === "javascript" || lang === "js") return true;
  const ext = getExtension(filePath);
  if (ext === "js" || ext === "mjs") return true;
  return false;
}

/**
 * 判断是否为 TypeScript 类型（不含 TSX）
 */
function isTsType(language: string | null, filePath: string | null | undefined): boolean {
  const lang = language?.toLowerCase() ?? "";
  if (lang === "typescript" || lang === "ts") return true;
  const ext = getExtension(filePath);
  if (ext === "ts" || ext === "mts") return true;
  return false;
}

/**
 * 判断是否为 React 组件类型（JSX/TSX）
 */
function isReactType(language: string | null, filePath: string | null | undefined): boolean {
  const lang = language?.toLowerCase() ?? "";
  if (lang === "jsx" || lang === "tsx" || lang === "react") return true;
  const ext = getExtension(filePath);
  if (ext === "jsx" || ext === "tsx") return true;
  return false;
}

/**
 * 从 React 组件代码中提取默认导出的组件名
 *
 * 支持以下模式：
 * - export default function ComponentName
 * - export default class ComponentName
 * - export default ComponentName
 */
function extractDefaultExportName(code: string): string | null {
  // export default function/class ComponentName
  const funcMatch = code.match(
    /export\s+default\s+(?:function|class)\s+([A-Z][A-Za-z0-9_]*)/
  );
  if (funcMatch) return funcMatch[1];

  // export default ComponentName (标识符以大写开头)
  const identMatch = code.match(
    /export\s+default\s+([A-Z][A-Za-z0-9_]*)\s*;?/
  );
  if (identMatch) return identMatch[1];

  return null;
}

/**
 * 构建预览用 HTML 文档
 *
 * @param code - 源代码
 * @param language - 语言标识
 * @param filePath - 文件路径
 * @returns 可在 srcdoc 中使用的完整 HTML 字符串，不可预览时返回 null
 */
function buildPreviewHtml(
  code: string,
  language: string | null,
  filePath: string | null | undefined
): string | null {
  // HTML 文件：直接使用源码
  if (isHtmlType(language, filePath)) {
    return code;
  }

  // CSS 文件：包裹在 HTML 模板中展示样式效果
  if (isCssType(language, filePath)) {
    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      padding: 24px;
      margin: 0;
      color: #333;
    }
    .preview-hint {
      margin-bottom: 16px;
      padding: 8px 12px;
      background: #f0f4ff;
      border-radius: 6px;
      font-size: 12px;
      color: #666;
    }
  </style>
  <style>${code}</style>
</head>
<body>
  <div class="preview-hint">CSS 样式预览 - 以下为示例元素</div>
  <h1>Heading 1</h1>
  <h2>Heading 2</h2>
  <h3>Heading 3</h3>
  <p>This is a paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
  <ul>
    <li>List item 1</li>
    <li>List item 2</li>
    <li>List item 3</li>
  </ul>
  <button>Button</button>
  <input type="text" placeholder="Input field" />
  <div class="container">
    <div class="box">Box 1</div>
    <div class="box">Box 2</div>
    <div class="box">Box 3</div>
  </div>
</body>
</html>`;
  }

  // JavaScript 文件：包裹在 HTML 中，提供 root 节点和 console 输出
  if (isJsType(language, filePath) || isTsType(language, filePath)) {
    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      padding: 16px;
      margin: 0;
      color: #333;
    }
    #root { min-height: 50px; }
    #console-output {
      margin-top: 16px;
      padding: 12px;
      background: #1e1e2e;
      color: #cdd6f4;
      border-radius: 6px;
      font-family: "Fira Code", "Cascadia Code", Consolas, monospace;
      font-size: 13px;
      white-space: pre-wrap;
      word-break: break-all;
      max-height: 300px;
      overflow-y: auto;
    }
    #console-output:empty { display: none; }
    .console-label {
      margin-top: 16px;
      font-size: 11px;
      color: #888;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .console-label:has(+ #console-output:empty) { display: none; }
  </style>
</head>
<body>
  <div id="root"></div>
  <div class="console-label">Console Output</div>
  <div id="console-output"></div>
  <script>
    // 劫持 console 方法，将输出显示在页面中
    (function() {
      var output = document.getElementById('console-output');
      var origLog = console.log;
      var origError = console.error;
      var origWarn = console.warn;
      function append(prefix, args) {
        var line = prefix + Array.from(args).map(function(a) {
          try { return typeof a === 'object' ? JSON.stringify(a, null, 2) : String(a); }
          catch(e) { return String(a); }
        }).join(' ') + '\\n';
        output.textContent += line;
      }
      console.log = function() { append('', arguments); origLog.apply(console, arguments); };
      console.error = function() { append('[ERROR] ', arguments); origError.apply(console, arguments); };
      console.warn = function() { append('[WARN] ', arguments); origWarn.apply(console, arguments); };
      window.onerror = function(msg, src, line, col, err) {
        append('[ERROR] ', [msg + ' (line ' + line + ')']);
      };
    })();
  </script>
  <script>${code}</script>
</body>
</html>`;
  }

  // React 组件（JSX/TSX）：加载 React UMD + Babel standalone 编译渲染
  if (isReactType(language, filePath)) {
    const componentName = extractDefaultExportName(code);
    // 自动渲染脚本：找到导出的组件并挂载到 root
    const renderScript = componentName
      ? `\n      try {
        const root = ReactDOM.createRoot(document.getElementById('root'));
        root.render(React.createElement(${componentName}));
      } catch(e) {
        document.getElementById('error-output').textContent = e.message + '\\n' + (e.stack || '');
        document.getElementById('error-output').style.display = 'block';
      }`
      : `\n      // 未检测到 export default 组件，请确保代码导出了默认组件
      document.getElementById('error-output').textContent = '未检测到 export default 组件。请确保代码中有 export default 声明。';
      document.getElementById('error-output').style.display = 'block';`;

    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      padding: 16px;
      margin: 0;
      color: #333;
    }
    #error-output {
      display: none;
      margin-top: 12px;
      padding: 12px;
      background: #fef2f2;
      color: #dc2626;
      border: 1px solid #fecaca;
      border-radius: 6px;
      font-family: monospace;
      font-size: 13px;
      white-space: pre-wrap;
      word-break: break-all;
    }
  </style>
  <script src="https://unpkg.com/react@18/umd/react.development.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head>
<body>
  <div id="root"></div>
  <div id="error-output"></div>
  <script>
    window.onerror = function(msg, src, line, col, err) {
      var el = document.getElementById('error-output');
      el.textContent = msg + '\\n' + (err && err.stack || '');
      el.style.display = 'block';
    };
  </script>
  <script type="text/babel" data-presets="react,typescript">
    ${code}
    ${renderScript}
  </script>
</body>
</html>`;
  }

  // 其他语言不支持预览
  return null;
}

/**
 * iframe 沙箱预览组件
 *
 * 根据代码语言/文件类型构建可预览的 HTML，在沙箱 iframe 中安全渲染。
 */
export function PreviewIframe({ code, language, filePath }: PreviewIframeProps) {
  // 用于强制刷新 iframe 的计数器
  const [refreshKey, setRefreshKey] = useState(0);

  const previewHtml = useMemo(
    () => buildPreviewHtml(code, language, filePath),
    [code, language, filePath]
  );

  /** 刷新预览 */
  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  // 不可预览时显示提示
  if (previewHtml === null) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 text-muted-foreground">
        <AlertTriangle size={32} className="opacity-40" />
        <p className="text-sm">此类型暂不支持预览</p>
        <p className="text-xs opacity-70">
          仅支持 HTML、CSS、JavaScript、JSX/TSX 文件的实时预览
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg border border-border bg-background">
      {/* 工具栏 */}
      <div className="flex shrink-0 items-center justify-between border-b border-border bg-muted/50 px-4 py-2">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Eye size={12} className="opacity-70" />
          <span>实时预览</span>
        </div>
        <button
          type="button"
          onClick={handleRefresh}
          className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
          title="刷新预览"
        >
          <RefreshCw size={12} />
          刷新
        </button>
      </div>

      {/* iframe 预览区域 */}
      <div className="min-h-0 flex-1">
        <iframe
          key={refreshKey}
          srcDoc={previewHtml}
          sandbox="allow-scripts allow-modals"
          title="Artifact 预览"
          className="h-full w-full border-0 bg-white"
        />
      </div>
    </div>
  );
}
