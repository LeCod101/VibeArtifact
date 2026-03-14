/**
 * SSE Hook - 实时接收全权委托运行事件
 *
 * 使用浏览器原生 EventSource API 连接后端 SSE 端点。
 * 支持自动重连（3 次重试，指数退避），组件卸载时自动清理。
 */
"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useAuthStore } from "@/stores/auth-store";
import type { SSEEventData } from "@/features/delegation/api";

/** SSE 连接状态 */
interface SSEState {
  /** 接收到的所有事件列表 */
  events: SSEEventData[];
  /** 是否已成功连接 */
  isConnected: boolean;
  /** 连接错误信息 */
  error: string | null;
  /** 最新收到的事件 */
  lastEvent: SSEEventData | null;
}

/** 最大重试次数 */
const MAX_RETRIES = 3;

/** 退避基准延迟（毫秒） */
const BASE_DELAY_MS = 1000;

/**
 * SSE 实时事件 Hook
 *
 * 连接到 /api/v1/projects/{projectId}/delegated-runs/{runId}/events，
 * 实时接收 step_start / step_complete / step_failed / run_complete / run_failed 事件。
 *
 * @param runId - 运行 UUID（为空时不连接）
 * @param projectId - 项目 UUID
 * @returns SSE 连接状态和事件数据
 */
export function useSSE(
  runId: string | null | undefined,
  projectId: string,
): SSEState {
  const [events, setEvents] = useState<SSEEventData[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastEvent, setLastEvent] = useState<SSEEventData | null>(null);

  // 使用 ref 记录重试次数，避免闭包陷阱
  const retryCountRef = useRef(0);
  const eventSourceRef = useRef<EventSource | null>(null);
  // 标记是否因终结事件而主动关闭，无需重连
  const terminatedRef = useRef(false);

  /**
   * 创建并连接 EventSource
   *
   * EventSource 不支持自定义 header，
   * 所以通过 URL 查询参数传递 token。
   */
  const connect = useCallback(() => {
    if (!runId || !projectId) return;

    const apiBase =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const token = useAuthStore.getState().accessToken;

    // 构造 SSE URL，通过查询参数传递 token
    let sseUrl = `${apiBase}/api/v1/projects/${projectId}/delegated-runs/${runId}/events`;
    if (token) {
      sseUrl += `?token=${encodeURIComponent(token)}`;
    }

    const es = new EventSource(sseUrl);
    eventSourceRef.current = es;

    es.onopen = () => {
      setIsConnected(true);
      setError(null);
      // 连接成功后重置重试计数
      retryCountRef.current = 0;
    };

    es.onmessage = (messageEvent) => {
      try {
        const parsed: SSEEventData = JSON.parse(messageEvent.data);
        setEvents((prev) => [...prev, parsed]);
        setLastEvent(parsed);

        // 检测终结事件：run_complete 或 run_failed
        if (
          parsed.event === "run_complete" ||
          parsed.event === "run_failed"
        ) {
          terminatedRef.current = true;
          es.close();
          setIsConnected(false);
        }
      } catch {
        // JSON 解析失败时忽略（可能是心跳注释）
      }
    };

    es.onerror = () => {
      es.close();
      setIsConnected(false);

      // 如果是主动关闭（终结事件），不重试
      if (terminatedRef.current) return;

      // 指数退避重连
      if (retryCountRef.current < MAX_RETRIES) {
        const delay =
          BASE_DELAY_MS * Math.pow(2, retryCountRef.current);
        retryCountRef.current += 1;
        setTimeout(() => {
          connect();
        }, delay);
      } else {
        setError("SSE 连接失败，已达最大重试次数");
      }
    };
  }, [runId, projectId]);

  useEffect(() => {
    // 重置状态
    setEvents([]);
    setIsConnected(false);
    setError(null);
    setLastEvent(null);
    retryCountRef.current = 0;
    terminatedRef.current = false;

    connect();

    // 清理：组件卸载时关闭 EventSource
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [connect]);

  return { events, isConnected, error, lastEvent };
}
