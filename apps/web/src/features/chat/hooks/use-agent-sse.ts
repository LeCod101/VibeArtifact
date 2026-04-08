/**
 * Agent SSE Hook - 通过 fetch + ReadableStream 接收 SSE 流
 *
 * 对接 Phase 2 的 POST /projects/{id}/chat 端点。
 * 使用 fetch 而非 EventSource，因为需要 POST 与自定义请求头。
 *
 * 事件类型：thinking | tool_call | tool_result | content | error | done
 */
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuthStore } from "@/stores/auth-store";
import type { AgentMode, AgentSSEEvent } from "@/lib/api-client/types";

/** SSE 流在 Hook 中的聚合状态 */
export interface AgentSSEState {
  isStreaming: boolean;
  thinkingText: string;
  contentText: string;
  activeToolCalls: ToolCallEvent[];
  completedToolCalls: ToolCallEvent[];
  events: AgentSSEEvent[];
  error: string | null;
}

/** 单条工具调用的 UI 状态（与 tool_call / tool_result 对齐） */
export interface ToolCallEvent {
  tool: string;
  arguments: Record<string, unknown>;
  result?: unknown;
  status: "calling" | "done" | "error";
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * 从 SSE data 中读取文本增量（兼容后端的 content 与计划中的 text）
 */
function pickTextChunk(data: Record<string, unknown>): string {
  const content = data.content;
  const text = data.text;
  if (typeof content === "string") return content;
  if (typeof text === "string") return text;
  return "";
}

/**
 * 从 SSE data 中读取工具参数（兼容 args 与 arguments）
 */
function pickToolArgs(data: Record<string, unknown>): Record<string, unknown> {
  const args = data.args;
  const arguments_ = data.arguments;
  if (args && typeof args === "object" && !Array.isArray(args)) {
    return args as Record<string, unknown>;
  }
  if (
    arguments_ &&
    typeof arguments_ === "object" &&
    !Array.isArray(arguments_)
  ) {
    return arguments_ as Record<string, unknown>;
  }
  return {};
}

/**
 * 根据工具返回结构判断是否为失败（后端序列化为 { success, error? }）
 */
function inferToolStatus(result: unknown): "done" | "error" {
  if (result && typeof result === "object" && !Array.isArray(result)) {
    const r = result as Record<string, unknown>;
    if (r.success === false) return "error";
  }
  return "done";
}

/**
 * 解析单个 SSE 事件块（event: + data:，以 \\n\\n 分隔）
 */
function parseSSEEvent(raw: string): AgentSSEEvent | null {
  let eventType = "";
  const dataLines: string[] = [];

  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  const dataStr = dataLines.join("\n");
  if (!eventType || !dataStr) return null;

  try {
    const data = JSON.parse(dataStr) as Record<string, unknown>;
    return { event: eventType as AgentSSEEvent["event"], data };
  } catch {
    return null;
  }
}

/**
 * 将单条 SSE 事件合并进状态（纯函数，便于单测与调试）
 */
export function applyEvent(
  prev: AgentSSEState,
  event: AgentSSEEvent
): AgentSSEState {
  const next: AgentSSEState = {
    ...prev,
    events: [...prev.events, event],
  };

  switch (event.event) {
    case "thinking":
      next.thinkingText = prev.thinkingText + pickTextChunk(event.data);
      break;

    case "tool_call": {
      const tc: ToolCallEvent = {
        tool: (event.data.tool as string) || "",
        arguments: pickToolArgs(event.data),
        status: "calling",
      };
      next.activeToolCalls = [...prev.activeToolCalls, tc];
      break;
    }

    case "tool_result": {
      const toolName = (event.data.tool as string) || "";
      const result = event.data.result;
      const idx = prev.activeToolCalls.findIndex((tc) => tc.tool === toolName);
      let args: Record<string, unknown> = pickToolArgs(event.data);

      if (idx >= 0) {
        args = { ...prev.activeToolCalls[idx].arguments, ...args };
        next.activeToolCalls = prev.activeToolCalls.filter((_, i) => i !== idx);
      } else {
        next.activeToolCalls = [...prev.activeToolCalls];
      }

      const status = inferToolStatus(result);
      const completed: ToolCallEvent = {
        tool: toolName,
        arguments: args,
        result,
        status,
      };
      next.completedToolCalls = [...prev.completedToolCalls, completed];
      break;
    }

    case "content":
      next.contentText = prev.contentText + pickTextChunk(event.data);
      break;

    case "error":
      next.error = (event.data.message as string) || "未知错误";
      next.isStreaming = false;
      break;

    case "done":
      next.isStreaming = false;
      break;

    default:
      break;
  }

  return next;
}

/**
 * Agent SSE Hook
 *
 * @param projectId - 项目 UUID
 */
export function useAgentSSE(projectId: string) {
  const [state, setState] = useState<AgentSSEState>({
    isStreaming: false,
    thinkingText: "",
    contentText: "",
    activeToolCalls: [],
    completedToolCalls: [],
    events: [],
    error: null,
  });

  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (
      message: string,
      mode: AgentMode = "auto",
      conversationId?: string
    ) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setState({
        isStreaming: true,
        thinkingText: "",
        contentText: "",
        activeToolCalls: [],
        completedToolCalls: [],
        events: [],
        error: null,
      });

      try {
        const token = useAuthStore.getState().accessToken;
        const res = await fetch(
          `${API_BASE}/api/v1/projects/${projectId}/chat`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
              message,
              mode,
              conversation_id: conversationId,
            }),
            signal: controller.signal,
          }
        );

        if (!res.ok) {
          const errText = await res.text();
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            error: `HTTP ${res.status}: ${errText}`,
          }));
          return;
        }

        const reader = res.body?.getReader();
        if (!reader) {
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            error: "无法读取响应流",
          }));
          return;
        }

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const parts = buffer.split("\n\n");
          buffer = parts.pop() || "";

          for (const part of parts) {
            const parsed = parseSSEEvent(part);
            if (!parsed) continue;
            setState((prev) => applyEvent(prev, parsed));
          }
        }

        if (buffer.trim()) {
          const parsed = parseSSEEvent(buffer);
          if (parsed) {
            setState((prev) => applyEvent(prev, parsed));
          }
        }

        setState((prev) => ({ ...prev, isStreaming: false }));
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: (err as Error).message,
        }));
      }
    },
    [projectId]
  );

  const abort = useCallback(() => {
    abortRef.current?.abort();
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  // 组件卸载时中止正在进行的 SSE 流，防止内存泄漏和 setState 警告
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  return { ...state, sendMessage, abort };
}
