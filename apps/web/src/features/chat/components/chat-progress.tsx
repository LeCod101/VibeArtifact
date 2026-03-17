/**
 * 对话模式内联进度指示器
 *
 * 显示在消息输入框上方，实时展示 AI 处理各阶段的执行状态。
 * 从 SSE 事件流中解析各阶段状态并渲染对应的状态图标和文本。
 *
 * 阶段状态：pending → running → completed / failed
 * 处理完成后组件渐隐消失。
 */
"use client";

import { useMemo } from "react";
import {
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatSSEEvent } from "@/lib/api-client/types";

interface ChatProgressProps {
  /** SSE 事件流 */
  events: ChatSSEEvent[];
  /** 是否正在处理中 */
  isProcessing: boolean;
}

/** 阶段状态类型 */
type StageStatus = "pending" | "running" | "completed" | "failed";

/** 单个阶段的渲染数据 */
interface StageInfo {
  /** 阶段唯一标识 */
  id: string;
  /** 中文标签 */
  label: string;
  /** 当前状态 */
  status: StageStatus;
}

/**
 * 从 SSE 事件流中解析各阶段状态
 *
 * @param events - 收到的 SSE 事件列表
 * @returns 各阶段的渲染数据
 */
function deriveStages(events: ChatSSEEvent[]): StageInfo[] {
  // 影响分析阶段状态
  let analysisStatus: StageStatus = "pending";
  // Agent 阶段状态映射
  const agentStatusMap: Record<string, StageStatus> = {};
  // Agent 发现顺序
  const agentOrder: string[] = [];
  // 是否整体完成或失败
  let isComplete = false;
  let isFailed = false;

  for (const evt of events) {
    switch (evt.event) {
      case "chat_analysis_start":
        analysisStatus = "running";
        break;

      case "chat_analysis_done":
        analysisStatus = "completed";
        break;

      case "chat_agent_start": {
        const agentId = evt.data?.agent_id as string;
        if (agentId) {
          if (!agentOrder.includes(agentId)) {
            agentOrder.push(agentId);
          }
          agentStatusMap[agentId] = "running";
        }
        break;
      }

      case "chat_agent_done": {
        const agentId = evt.data?.agent_id as string;
        if (agentId) {
          agentStatusMap[agentId] = "completed";
        }
        break;
      }

      case "chat_complete":
        isComplete = true;
        break;

      case "chat_failed":
        isFailed = true;
        break;
    }
  }

  // 构建阶段列表
  const stages: StageInfo[] = [];

  // 影响分析阶段（只要有事件就展示）
  if (analysisStatus !== "pending" || events.length > 0) {
    stages.push({
      id: "analysis",
      label: "影响分析",
      status: analysisStatus,
    });
  }

  // 各 Agent 阶段
  for (const agentId of agentOrder) {
    stages.push({
      id: agentId,
      label: agentId,
      status: agentStatusMap[agentId] || "pending",
    });
  }

  // 整体失败时，把未完成阶段标记为 failed
  if (isFailed) {
    for (const stage of stages) {
      if (stage.status === "running") {
        stage.status = "failed";
      }
    }
  }

  // 整体完成时，确保所有阶段都标记为 completed
  if (isComplete) {
    for (const stage of stages) {
      if (stage.status === "running" || stage.status === "pending") {
        stage.status = "completed";
      }
    }
  }

  return stages;
}

/**
 * 状态图标组件
 *
 * 根据阶段状态渲染对应的 Lucide 图标。
 */
function StageIcon({ status }: { status: StageStatus }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />;
    case "running":
      return <Loader2 className="h-4 w-4 text-blue-500 animate-spin shrink-0" />;
    case "failed":
      return <XCircle className="h-4 w-4 text-red-500 shrink-0" />;
    case "pending":
    default:
      return <Circle className="h-4 w-4 text-muted-foreground/40 shrink-0" />;
  }
}

/**
 * 对话模式内联进度指示器
 *
 * 在消息输入框上方显示 AI 处理的实时进度。
 * 处理完成后自动渐隐。不在处理中且无事件时不渲染。
 */
export function ChatProgress({ events, isProcessing }: ChatProgressProps) {
  const stages = useMemo(() => deriveStages(events), [events]);

  // 不在处理中且没有事件时不显示
  if (!isProcessing && events.length === 0) {
    return null;
  }

  return (
    <div
      className={cn(
        "mx-4 mb-2 rounded-xl border border-border bg-muted/30 px-4 py-3 transition-opacity duration-500",
        !isProcessing && "opacity-0 pointer-events-none"
      )}
    >
      {/* 总标题 */}
      <div className="flex items-center gap-2 mb-2">
        <Loader2
          className={cn(
            "h-4 w-4 text-blue-500",
            isProcessing && "animate-spin"
          )}
        />
        <span className="text-sm font-medium text-foreground">
          AI 正在处理...
        </span>
      </div>

      {/* 阶段列表 */}
      {stages.length > 0 && (
        <div className="space-y-1.5">
          {stages.map((stage) => (
            <div
              key={stage.id}
              className="flex items-center gap-2"
            >
              <StageIcon status={stage.status} />
              <span
                className={cn(
                  "text-xs",
                  stage.status === "completed" && "text-emerald-600",
                  stage.status === "running" && "text-blue-600 font-medium",
                  stage.status === "failed" && "text-red-600",
                  stage.status === "pending" && "text-muted-foreground"
                )}
              >
                {stage.status === "running" && `执行 ${stage.label}...`}
                {stage.status === "completed" && `${stage.label}完成`}
                {stage.status === "failed" && `${stage.label}失败`}
                {stage.status === "pending" && stage.label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
