/**
 * 项目级预览面板
 *
 * 使用 WebContainer 在浏览器内运行完整的多文件 React/Vite 项目。
 * 结构：工具栏（状态+刷新） + iframe 预览区 + 可折叠终端面板。
 *
 * 核心流程：
 * 1. boot WebContainer
 * 2. mount 文件系统
 * 3. npm install
 * 4. npm run dev
 * 5. 监听 server-ready 获取预览 URL
 * 6. 后续 artifacts 变化 -> 增量写入文件 -> Vite HMR 自动刷新
 */
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Loader2,
  Play,
  RefreshCw,
  Terminal,
} from "lucide-react";
import type { WebContainer, WebContainerProcess } from "@webcontainer/api";
import type { ArtifactResponseV2 } from "@/lib/api-client/types";
import { useWebContainer } from "./use-webcontainer";
import { buildFileSystemTree } from "./file-system-bridge";

/** 预览面板属性 */
export interface PreviewPanelProps {
  /** 项目所有 code 类型产物（含 content） */
  artifacts: ArtifactResponseV2[];
  /** 面板是否可见（避免隐藏时仍运行） */
  visible?: boolean;
}

/** 预览运行状态 */
type PreviewStatus =
  | "idle"
  | "booting"
  | "installing"
  | "starting"
  | "running"
  | "error";

/** 状态显示配置 */
const STATUS_CONFIG: Record<
  PreviewStatus,
  { label: string; colorClass: string; animate: boolean }
> = {
  idle: { label: "等待启动", colorClass: "bg-gray-400", animate: false },
  booting: {
    label: "正在初始化...",
    colorClass: "bg-yellow-400",
    animate: true,
  },
  installing: {
    label: "安装依赖...",
    colorClass: "bg-yellow-400",
    animate: true,
  },
  starting: {
    label: "启动服务...",
    colorClass: "bg-yellow-400",
    animate: true,
  },
  running: { label: "运行中", colorClass: "bg-green-500", animate: false },
  error: { label: "出错", colorClass: "bg-red-500", animate: false },
};

/**
 * 项目级预览面板组件
 *
 * 将多个 code 类型产物在 WebContainer 中运行，展示实时预览。
 *
 * @param props - 组件属性
 * @param props.artifacts - 项目所有 code 类型产物
 * @param props.visible - 面板是否可见
 */
export function PreviewPanel({ artifacts, visible = true }: PreviewPanelProps) {
  const { instance, boot, status: wcStatus, error: wcError } = useWebContainer();

  const [previewStatus, setPreviewStatus] = useState<PreviewStatus>("idle");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
  const [terminalOpen, setTerminalOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 追踪当前进程，防止重复 install
  const devProcessRef = useRef<WebContainerProcess | null>(null);
  // 标记是否已完成首次 install
  const hasInstalledRef = useRef(false);
  // 记录上次 mount 的 artifacts 指纹，用于增量更新
  const prevArtifactsRef = useRef<string>("");
  // 终端日志容器引用，用于自动滚到底
  const terminalEndRef = useRef<HTMLDivElement>(null);

  /**
   * 追加终端日志
   */
  const appendLog = useCallback((line: string) => {
    setTerminalLogs((prev) => {
      // 限制最多保留 500 行日志
      const next = [...prev, line];
      return next.length > 500 ? next.slice(-500) : next;
    });
  }, []);

  /**
   * 终端日志自动滚到底
   */
  useEffect(() => {
    if (terminalOpen) {
      terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [terminalLogs, terminalOpen]);

  /**
   * 执行完整的预览启动流程
   *
   * 包含：boot -> mount -> npm install -> npm run dev -> 监听 URL
   */
  const runPreview = useCallback(
    async (wc: WebContainer) => {
      if (artifacts.length === 0) return;

      try {
        // 构建并 mount 文件系统
        setPreviewStatus("installing");
        appendLog("[系统] 正在构建文件系统...");

        const tree = buildFileSystemTree(artifacts);
        await wc.mount(tree);
        appendLog("[系统] 文件系统已挂载");

        // 记录当前 artifacts 指纹
        prevArtifactsRef.current = JSON.stringify(
          artifacts.map((a) => `${a.id}:${a.updated_at}`),
        );

        // 执行 npm install
        appendLog("[系统] 正在安装依赖 (npm install)...");
        const installProcess = await wc.spawn("npm", ["install"]);

        // 收集 install 输出
        installProcess.output.pipeTo(
          new WritableStream({
            write(data) {
              appendLog(data);
            },
          }),
        );

        const installExitCode = await installProcess.exit;
        if (installExitCode !== 0) {
          setPreviewStatus("error");
          setErrorMsg(`npm install 失败 (exit code: ${installExitCode})`);
          appendLog(`[错误] npm install 失败，退出码: ${installExitCode}`);
          return;
        }

        hasInstalledRef.current = true;
        appendLog("[系统] 依赖安装完成");

        // 启动 dev server
        setPreviewStatus("starting");
        appendLog("[系统] 正在启动开发服务器 (npm run dev)...");

        const devProcess = await wc.spawn("npm", ["run", "dev"]);
        devProcessRef.current = devProcess;

        // 收集 dev server 输出
        devProcess.output.pipeTo(
          new WritableStream({
            write(data) {
              appendLog(data);
            },
          }),
        );

        // 监听 server-ready 事件获取预览 URL
        wc.on("server-ready", (_port, url) => {
          setPreviewUrl(url);
          setPreviewStatus("running");
          appendLog(`[系统] 服务就绪: ${url}`);
        });

        // 监听进程退出
        devProcess.exit.then((code) => {
          if (code !== 0) {
            appendLog(`[警告] 开发服务器退出，退出码: ${code}`);
          }
          devProcessRef.current = null;
        });
      } catch (err) {
        const msg = err instanceof Error ? err.message : "预览启动失败";
        setPreviewStatus("error");
        setErrorMsg(msg);
        appendLog(`[错误] ${msg}`);
      }
    },
    [artifacts, appendLog],
  );

  /**
   * 主启动流程：boot WebContainer 然后运行预览
   */
  const startPreview = useCallback(async () => {
    setPreviewStatus("booting");
    setErrorMsg(null);
    setTerminalLogs([]);
    appendLog("[系统] 正在启动 WebContainer...");

    await boot();
  }, [boot, appendLog]);

  /**
   * WebContainer 就绪后触发预览流程
   */
  useEffect(() => {
    if (wcStatus === "ready" && instance && previewStatus === "booting") {
      appendLog("[系统] WebContainer 就绪");
      void runPreview(instance);
    }
    if (wcStatus === "error" && wcError) {
      setPreviewStatus("error");
      setErrorMsg(wcError);
      appendLog(`[错误] WebContainer 启动失败: ${wcError}`);
    }
  }, [wcStatus, instance, wcError, previewStatus, runPreview, appendLog]);

  /**
   * artifacts 变化时增量更新文件（已有实例且已安装完毕）
   */
  useEffect(() => {
    if (!instance || !hasInstalledRef.current) return;
    if (previewStatus !== "running") return;

    // 计算新指纹
    const newFingerprint = JSON.stringify(
      artifacts.map((a) => `${a.id}:${a.updated_at}`),
    );
    if (newFingerprint === prevArtifactsRef.current) return;
    prevArtifactsRef.current = newFingerprint;

    // 增量写入变化的文件
    appendLog("[系统] 检测到产物变化，正在更新文件...");
    const tree = buildFileSystemTree(artifacts);
    instance.mount(tree).then(() => {
      appendLog("[系统] 文件已更新，等待 HMR 刷新...");
    });
  }, [artifacts, instance, previewStatus, appendLog]);

  /**
   * 面板首次可见且有产物时自动启动
   */
  useEffect(() => {
    if (visible && artifacts.length > 0 && previewStatus === "idle") {
      void startPreview();
    }
  }, [visible, artifacts.length, previewStatus, startPreview]);

  /**
   * 刷新预览：重新 mount 文件并重启 dev server
   */
  const handleRefresh = useCallback(async () => {
    if (!instance) return;

    // 终止现有 dev server
    if (devProcessRef.current) {
      devProcessRef.current.kill();
      devProcessRef.current = null;
    }

    setPreviewUrl(null);
    hasInstalledRef.current = false;
    setPreviewStatus("installing");
    setErrorMsg(null);
    appendLog("[系统] 正在刷新预览...");

    await runPreview(instance);
  }, [instance, runPreview, appendLog]);

  // 获取当前状态配置
  const statusConfig = STATUS_CONFIG[previewStatus];
  // 如果有具体错误信息，显示错误而非通用标签
  const displayLabel =
    previewStatus === "error" && errorMsg
      ? errorMsg
      : statusConfig.label;

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg border border-border bg-background">
      {/* 工具栏 */}
      <div className="flex shrink-0 items-center justify-between border-b border-border bg-muted/50 px-3 py-2">
        <div className="flex items-center gap-2">
          {/* 状态指示器 */}
          <span
            className={`inline-block h-2 w-2 rounded-full ${statusConfig.colorClass} ${
              statusConfig.animate ? "animate-pulse" : ""
            }`}
          />
          <span className="text-xs text-muted-foreground truncate max-w-[200px]">
            {displayLabel}
          </span>
        </div>

        <div className="flex items-center gap-1">
          {/* 终端切换 */}
          <button
            type="button"
            onClick={() => setTerminalOpen((o) => !o)}
            className={`flex items-center gap-1 rounded px-2 py-1 text-xs transition-colors ${
              terminalOpen
                ? "bg-muted text-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
            title="终端日志"
          >
            <Terminal size={12} />
            {terminalOpen ? (
              <ChevronDown size={10} />
            ) : (
              <ChevronUp size={10} />
            )}
          </button>

          {/* 刷新按钮 */}
          <button
            type="button"
            onClick={() => void handleRefresh()}
            disabled={
              previewStatus === "booting" || previewStatus === "installing"
            }
            className="flex items-center gap-1 rounded px-2 py-1 text-xs text-muted-foreground transition-colors hover:text-foreground disabled:opacity-40 disabled:cursor-not-allowed"
            title="刷新预览"
          >
            <RefreshCw size={12} />
          </button>
        </div>
      </div>

      {/* iframe 预览区域 */}
      <div className="min-h-0 flex-1 relative">
        {previewUrl ? (
          <iframe
            src={previewUrl}
            title="项目预览"
            className="h-full w-full border-0 bg-white"
            allow="cross-origin-isolated"
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-muted-foreground">
            {previewStatus === "idle" ? (
              <>
                <Play size={32} className="opacity-40" />
                <p className="text-sm">点击启动项目预览</p>
                <button
                  type="button"
                  onClick={() => void startPreview()}
                  className="rounded-md bg-primary px-4 py-2 text-xs text-primary-foreground transition-colors hover:bg-primary/90"
                >
                  启动预览
                </button>
              </>
            ) : previewStatus === "error" ? (
              <>
                <div className="rounded-md bg-destructive/10 px-4 py-3 text-center">
                  <p className="text-sm text-destructive">{errorMsg}</p>
                </div>
                <button
                  type="button"
                  onClick={() => void handleRefresh()}
                  className="rounded-md bg-primary px-4 py-2 text-xs text-primary-foreground transition-colors hover:bg-primary/90"
                >
                  重试
                </button>
              </>
            ) : (
              <>
                <Loader2 size={24} className="animate-spin" />
                <p className="text-sm">{displayLabel}</p>
              </>
            )}
          </div>
        )}
      </div>

      {/* 终端面板（可折叠） */}
      {terminalOpen ? (
        <div className="shrink-0 border-t border-border">
          <div className="h-[160px] overflow-y-auto bg-[#1e1e2e] p-3 font-mono text-xs text-[#cdd6f4]">
            {terminalLogs.length === 0 ? (
              <span className="text-[#6c7086]">等待输出...</span>
            ) : (
              terminalLogs.map((line, i) => (
                <div key={i} className="whitespace-pre-wrap break-all leading-5">
                  {line}
                </div>
              ))
            )}
            <div ref={terminalEndRef} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
