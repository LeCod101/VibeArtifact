/**
 * WebContainer 生命周期管理 Hook
 *
 * 核心职责：
 * - 单例模式 boot WebContainer（整个应用只需一个实例）
 * - 提供实例引用和启动状态
 * - 管理状态：idle / booting / ready / error
 *
 * 注意：WebContainer.boot() 只能在浏览器环境调用，且全局只能调用一次。
 * 实例在页面生命周期内保持活跃，不在组件 unmount 时 teardown（boot 开销大）。
 */

import { useCallback, useState } from "react";
import type { WebContainer } from "@webcontainer/api";

/** WebContainer 状态类型 */
export type WebContainerStatus = "idle" | "booting" | "ready" | "error";

/** Hook 返回值类型 */
export interface UseWebContainerReturn {
  /** WebContainer 实例（ready 后可用） */
  instance: WebContainer | null;
  /** 当前状态 */
  status: WebContainerStatus;
  /** 错误信息 */
  error: string | null;
  /** 启动 WebContainer */
  boot: () => Promise<void>;
}

// 模块级单例：WebContainer 只能 boot 一次
let _instance: WebContainer | null = null;
let _bootPromise: Promise<WebContainer> | null = null;

/**
 * WebContainer 生命周期管理 Hook
 *
 * 提供 WebContainer 实例的启动、状态管理和错误处理。
 * 使用模块级单例确保全局只有一个 WebContainer 实例。
 *
 * @returns WebContainer 实例、状态、错误和启动方法
 */
export function useWebContainer(): UseWebContainerReturn {
  const [status, setStatus] = useState<WebContainerStatus>(
    _instance ? "ready" : "idle",
  );
  const [error, setError] = useState<string | null>(null);
  const [instance, setInstance] = useState<WebContainer | null>(_instance);

  const boot = useCallback(async () => {
    // 已经有实例，直接返回
    if (_instance) {
      setInstance(_instance);
      setStatus("ready");
      return;
    }

    // 只在浏览器环境执行
    if (typeof window === "undefined") {
      setError("WebContainer 仅支持浏览器环境");
      setStatus("error");
      return;
    }

    setStatus("booting");
    setError(null);

    try {
      // 如果已有进行中的 boot 请求，复用
      if (!_bootPromise) {
        // 动态导入 WebContainer，避免 SSR 问题
        const { WebContainer: WC } = await import("@webcontainer/api");
        _bootPromise = WC.boot();
      }

      const wc = await _bootPromise;
      _instance = wc;
      setInstance(wc);
      setStatus("ready");
    } catch (err) {
      _bootPromise = null;
      const message =
        err instanceof Error ? err.message : "WebContainer 启动失败";
      setError(message);
      setStatus("error");
    }
  }, []);

  return { instance, status, error, boot };
}
