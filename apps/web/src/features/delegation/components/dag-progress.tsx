/**
 * DAG 进度面板
 *
 * 展示全权委托运行中各 agent 阶段的执行状态。
 * 数据来源：SSE 实时更新 + useDelegatedRun polling 兜底。
 * 每个阶段展示 agent 名称、状态图标、耗时信息。
 */
"use client";

import { useMemo } from "react";
import {
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
  Clock,
  AlertTriangle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type {
  DelegatedRunData,
  DelegatedStepData,
  SSEEventData,
} from "@/features/delegation/api";

/* ============ DAG 阶段配置 ============ */

/** 单个 DAG 阶段的元信息 */
interface DagStage {
  /** agent 标识（与后端 agent_id 对应） */
  agentId: string;
  /** 中文展示名称 */
  label: string;
  /** 阶段序号（用于排序和展示） */
  order: number;
}

/**
 * DAG 阶段列表
 *
 * 按执行顺序排列，order 3-6 为并行阶段。
 */
const DAG_STAGES: DagStage[] = [
  { agentId: "planner", label: "规划", order: 1 },
  { agentId: "schema", label: "数据建模", order: 2 },
  { agentId: "backend", label: "后端开发", order: 3 },
  { agentId: "frontend", label: "前端开发", order: 4 },
  { agentId: "doc", label: "文档编写", order: 5 },
  { agentId: "diagram", label: "图表设计", order: 6 },
  { agentId: "qa", label: "质量检查", order: 7 },
  { agentId: "export", label: "打包导出", order: 8 },
];

/* ============ 工具函数 ============ */

/** 步骤状态类型 */
type StepStatus = "pending" | "running" | "completed" | "failed" | "needs_attention";

/**
 * 从 SSE 事件流中提取各 agent 的最新状态
 *
 * SSE 事件类型映射：
 * - step_start → running
 * - step_complete → completed
 * - step_failed → failed
 */
function deriveStatusFromEvents(
  events: SSEEventData[],
): Record<string, StepStatus> {
  const statusMap: Record<string, StepStatus> = {};

  for (const evt of events) {
    const agentId = evt.data?.agent_id;
    if (!agentId) continue;

    switch (evt.event) {
      case "step_start":
        statusMap[agentId] = "running";
        break;
      case "step_complete":
        statusMap[agentId] = "completed";
        break;
      case "step_failed":
        statusMap[agentId] = "failed";
        break;
    }
  }

  return statusMap;
}

/**
 * 从 polling 数据中提取各 agent 的状态
 */
function deriveStatusFromRun(
  steps: DelegatedStepData[],
): Record<string, StepStatus> {
  const statusMap: Record<string, StepStatus> = {};
  for (const step of steps) {
    statusMap[step.agent_id] = step.status as StepStatus;
  }
  return statusMap;
}

/**
 * 格式化耗时（毫秒 → 可读文本）
 */
function formatDuration(ms: number | null | undefined): string {
  if (ms == null) return "";
  if (ms < 1000) return `${ms}ms`;
  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainSeconds = seconds % 60;
  return `${minutes}m ${remainSeconds}s`;
}

/* ============ 子组件 ============ */

/**
 * 状态图标 - 根据步骤状态渲染对应图标
 */
function StatusIcon({ status }: { status: StepStatus }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
    case "running":
      return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
    case "failed":
      return <XCircle className="h-5 w-5 text-red-500" />;
    case "needs_attention":
      return <AlertTriangle className="h-5 w-5 text-amber-500" />;
    case "pending":
    default:
      return <Circle className="h-5 w-5 text-muted-foreground/40" />;
  }
}

/**
 * 状态文本标签
 */
function statusLabel(status: StepStatus): string {
  switch (status) {
    case "completed":
      return "已完成";
    case "running":
      return "执行中";
    case "failed":
      return "失败";
    case "needs_attention":
      return "需要介入";
    case "pending":
    default:
      return "等待中";
  }
}

/* ============ 主组件 ============ */

interface DagProgressProps {
  /** polling 获取的运行数据 */
  runData?: DelegatedRunData | null;
  /** SSE 事件流 */
  sseEvents: SSEEventData[];
  /** 额外的 CSS 类名 */
  className?: string;
  /** Gate 失败详情（needs_attention 时有值） */
  gateResult?: Record<string, unknown> | null;
}

/**
 * DAG 进度面板组件
 *
 * 合并 SSE 实时数据和 polling 兜底数据，
 * 展示 8 个 DAG 阶段的执行状态。
 * 并行阶段（backend/frontend/doc/diagram）以网格布局展示。
 */
export function DagProgress({
  runData,
  sseEvents,
  className,
  gateResult,
}: DagProgressProps) {
  // 合并 SSE 和 polling 的状态数据
  // SSE 优先（更实时），polling 兜底
  const mergedStatus = useMemo(() => {
    const pollingStatus = runData?.steps
      ? deriveStatusFromRun(runData.steps)
      : {};
    const sseStatus = deriveStatusFromEvents(sseEvents);
    return { ...pollingStatus, ...sseStatus };
  }, [runData, sseEvents]);

  // 从 polling 数据中获取耗时
  const durationMap = useMemo(() => {
    const map: Record<string, number | null> = {};
    if (runData?.steps) {
      for (const step of runData.steps) {
        map[step.agent_id] = step.duration_ms;
      }
    }
    return map;
  }, [runData]);

  // 拆分阶段：串行阶段和并行阶段
  const serialBefore = DAG_STAGES.filter((s) => s.order <= 2);
  const parallel = DAG_STAGES.filter((s) => s.order >= 3 && s.order <= 6);
  const serialAfter = DAG_STAGES.filter((s) => s.order >= 7);

  /**
   * 渲染单个阶段卡片
   */
  function renderStageCard(stage: DagStage) {
    const status = (mergedStatus[stage.agentId] || "pending") as StepStatus;
    const duration = durationMap[stage.agentId];

    return (
      <div
        key={stage.agentId}
        className={cn(
          "flex items-center gap-3 rounded-lg border px-4 py-3 transition-all",
          status === "running" && "border-blue-200 bg-blue-50/50",
          status === "completed" && "border-emerald-200 bg-emerald-50/50",
          status === "failed" && "border-red-200 bg-red-50/50",
          status === "needs_attention" && "border-amber-200 bg-amber-50/50",
          status === "pending" && "border-border bg-muted/30",
        )}
      >
        <StatusIcon status={status} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{stage.label}</p>
          <p
            className={cn(
              "text-xs",
              status === "running" && "text-blue-600",
              status === "completed" && "text-emerald-600",
              status === "failed" && "text-red-600",
              status === "needs_attention" && "text-amber-600",
              status === "pending" && "text-muted-foreground",
            )}
          >
            {statusLabel(status)}
          </p>
        </div>
        {/* 耗时信息 */}
        {duration != null && (
          <span className="flex items-center gap-1 text-xs text-muted-foreground shrink-0">
            <Clock className="h-3 w-3" />
            {formatDuration(duration)}
          </span>
        )}
      </div>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>执行进度</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* 串行阶段（规划、数据建模） */}
        {serialBefore.map(renderStageCard)}

        {/* 并行阶段（后端、前端、文档、图表）— 2×2 网格 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {parallel.map(renderStageCard)}
        </div>

        {/* 串行阶段（质量检查、打包导出） */}
        {serialAfter.map(renderStageCard)}

        {/* needs_attention 横幅：Gate 失败需要人工介入 */}
        {gateResult && (
          <div className="mt-2 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
              <div className="text-sm">
                <p className="font-medium text-amber-800">编译门禁未通过，需要人工介入</p>
                <p className="text-amber-700 mt-0.5 text-xs">
                  系统已自动尝试修复 1 次，问题仍然存在。请检查生成代码后重新提交。
                </p>
                {Array.isArray((gateResult as Record<string, unknown>).all_issues) && (
                  <ul className="mt-2 space-y-0.5">
                    {((gateResult as Record<string, unknown>).all_issues as string[])
                      .slice(0, 5)
                      .map((issue, i) => (
                        <li key={i} className="text-xs text-amber-700 font-mono">
                          {issue}
                        </li>
                      ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
