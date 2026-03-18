/**
 * 对话模式 SSE Hook - 实时接收 Agent 执行进度事件
 *
 * 订阅 /conversations/{id}/events 获取对话模式下的 Agent 执行进度。
 * 与全权委托的 useSSE 不同，这里需要外部调用 startListening() 来开始监听，
 * 适配"发送消息 → 等待处理 → 接收结果"的对话交互模式。
 *
 * 支持事件类型：
 * - chat_analysis_start / chat_analysis_done（影响分析）
 * - chat_agent_start / chat_agent_done（Agent 执行）
 * - chat_apply_done（变更应用）
 * - chat_complete（处理完成）
 * - chat_failed（处理失败）
 */
"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useAuthStore } from "@/stores/auth-store";
import type { ChatSSEEvent } from "@/lib/api-client/types";

/** SSE 连接状态 */
interface ChatSSEState {
  /** 接收到的所有事件列表 */
  events: ChatSSEEvent[];
  /** 是否正在处理中（SSE 连接存活期间） */
  isProcessing: boolean;
  /** 当前正在执行的 Agent 标识 */
  currentAgent: string | null;
  /** 连接错误信息 */
  error: string | null;
}

/** SSE Hook 返回值 */
interface ChatSSEReturn extends ChatSSEState {
  /** 开始监听 SSE 事件 */
  startListening: () => void;
  /** 停止监听并关闭连接 */
  stopListening: () => void;
}

/** 最大重试次数 */
const MAX_RETRIES = 3;

/** 退避基准延迟（毫秒） */
const BASE_DELAY_MS = 1000;

/**
 * 对话模式 SSE Hook
 *
 * 连接到 /api/v1/conversations/{id}/events，
 * 实时接收对话处理过程中各 Agent 的执行进度事件。
 *
 * @param conversationId - 对话 UUID（为 null 时无法连接）
 * @returns SSE 状态和控制方法
 */
export function useChatSSE(conversationId: string | null): ChatSSEReturn {
  const [events, setEvents] = useState<ChatSSEEvent[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 使用 ref 记录重试次数，避免闭包陷阱
  const retryCountRef = useRef(0);
  const eventSourceRef = useRef<EventSource | null>(null);
  // 标记是否因终结事件而主动关闭，无需重连
  const terminatedRef = useRef(false);
  // 保持 connect 引用最新
  const connectRef = useRef<(() => void) | null>(null);

  /**
   * 处理收到的 SSE 事件
   *
   * 根据事件类型更新 currentAgent 和 isProcessing 状态。
   */
  const handleEvent = useCallback(
    (parsed: ChatSSEEvent) => {
      setEvents((prev) => [...prev, parsed]);

      switch (parsed.event) {
        case "chat_agent_start":
          // 标记当前正在执行的 Agent
          setCurrentAgent(
            (parsed.data?.agent_id as string) ?? null
          );
          break;

        case "chat_agent_done":
          // Agent 执行完毕，清除当前 Agent
          setCurrentAgent(null);
          break;

        case "chat_complete":
          // 处理完成，关闭连接
          setIsProcessing(false);
          setCurrentAgent(null);
          terminatedRef.current = true;
          eventSourceRef.current?.close();
          break;

        case "chat_failed":
          // 处理失败，记录错误并关闭连接
          setIsProcessing(false);
          setCurrentAgent(null);
          setError(
            (parsed.data?.message as string) ?? "对话处理失败"
          );
          terminatedRef.current = true;
          eventSourceRef.current?.close();
          break;
      }
    },
    []
  );

  /**
   * 创建并连接 EventSource
   *
   * EventSource 不支持自定义 header，
   * 所以通过 URL 查询参数传递 token。
   */
  const connect = useCallback(() => {
    if (!conversationId) return;

    const apiBase =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const token = useAuthStore.getState().accessToken;

    // 构造 SSE URL，通过查询参数传递 token
    let sseUrl = `${apiBase}/api/v1/conversations/${conversationId}/events`;
    if (token) {
      sseUrl += `?token=${encodeURIComponent(token)}`;
    }

    const es = new EventSource(sseUrl);
    eventSourceRef.current = es;

    es.onopen = () => {
      setError(null);
      // 连接成功后重置重试计数
      retryCountRef.current = 0;
    };

    es.onmessage = (messageEvent) => {
      try {
        const parsed: ChatSSEEvent = JSON.parse(messageEvent.data);
        handleEvent(parsed);
      } catch {
        // JSON 解析失败时忽略（可能是心跳注释）
      }
    };

    es.onerror = () => {
      es.close();
      eventSourceRef.current = null;

      // 如果是主动关闭（终结事件），不重试
      if (terminatedRef.current) return;

      // 指数退避重连
      if (retryCountRef.current < MAX_RETRIES) {
        const delay =
          BASE_DELAY_MS * Math.pow(2, retryCountRef.current);
        retryCountRef.current += 1;
        setTimeout(() => {
          connectRef.current?.();
        }, delay);
      } else {
        setIsProcessing(false);
        setError("SSE 连接失败，已达最大重试次数");
      }
    };
  }, [conversationId, handleEvent]);

  // 保持 connectRef 与最新的 connect 同步（必须在 useEffect 中赋值 ref）
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  /**
   * 开始监听 SSE 事件
   *
   * 重置所有状态，建立新的 SSE 连接。
   * 需要在发送消息后手动调用。
   */
  const startListening = useCallback(() => {
    // 关闭已有连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    // 重置状态
    setEvents([]);
    setIsProcessing(true);
    setCurrentAgent(null);
    setError(null);
    retryCountRef.current = 0;
    terminatedRef.current = false;

    connect();
  }, [connect]);

  /**
   * 停止监听，关闭 SSE 连接
   */
  const stopListening = useCallback(() => {
    terminatedRef.current = true;
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsProcessing(false);
    setCurrentAgent(null);
  }, []);

  return {
    events,
    isProcessing,
    currentAgent,
    error,
    startListening,
    stopListening,
  };
}
