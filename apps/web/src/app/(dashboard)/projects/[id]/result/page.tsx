/**
 * 全权委托结果页
 *
 * URL: /projects/{id}/result?runId={runId}
 *
 * 页面组合：
 * - 运行中：DAG 进度面板（SSE 实时 + polling 兜底）
 * - 完成后：DAG 进度面板 + 下载面板
 * - 失败时：DAG 进度面板 + 错误信息
 */
"use client";

import { useParams, useSearchParams, useRouter } from "next/navigation";
import { ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProjectTabs } from "@/features/project/components/project-tabs";
import { useProjectQuery } from "@/features/project/api";
import { useSSE } from "@/features/delegation/hooks/use-sse";
import { useDelegatedRun } from "@/features/delegation/hooks/use-delegated";
import { DagProgress } from "@/features/delegation/components/dag-progress";
import { DownloadPanel } from "@/features/delegation/components/download-panel";

/**
 * 运行状态中文标签
 */
function runStatusLabel(status: string | undefined): string {
  switch (status) {
    case "pending":
      return "准备中";
    case "running":
      return "执行中";
    case "completed":
      return "已完成";
    case "failed":
      return "执行失败";
    case "needs_attention":
      return "需要介入";
    default:
      return "加载中";
  }
}

/**
 * 运行状态对应的样式
 */
function runStatusStyle(status: string | undefined): string {
  switch (status) {
    case "running":
    case "pending":
      return "text-blue-600 bg-blue-50";
    case "completed":
      return "text-emerald-600 bg-emerald-50";
    case "failed":
      return "text-red-600 bg-red-50";
    case "needs_attention":
      return "text-amber-600 bg-amber-50";
    default:
      return "text-muted-foreground bg-muted";
  }
}

export default function DelegatedResultPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const projectId = params.id as string;
  const runId = searchParams.get("runId");

  // 查询项目信息（用于面包屑/标题）
  const { data: project, isLoading: projectLoading } =
    useProjectQuery(projectId);

  // SSE 实时事件
  const { events: sseEvents, isConnected, error: sseError } = useSSE(
    runId,
    projectId,
  );

  // Polling 兜底查询
  const { data: runData, isLoading: runLoading } = useDelegatedRun(
    projectId,
    runId,
  );

  // 缺少 runId 参数
  if (!runId) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-muted-foreground">
        缺少运行 ID 参数
      </div>
    );
  }

  // 项目加载中
  if (projectLoading || runLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 顶部导航 */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push(`/projects/${projectId}`)}
        >
          <ArrowLeft size={18} />
        </Button>
        <div className="flex-1">
          <h1 className="text-lg font-bold">
            {project?.name ?? "项目"} — 全权委托
          </h1>
          <p className="text-xs text-muted-foreground">
            运行 ID: {runId}
          </p>
        </div>
        {/* 运行状态标签 */}
        <span
          className={`text-xs font-medium px-3 py-1 rounded-full ${runStatusStyle(runData?.status)}`}
        >
          {runStatusLabel(runData?.status)}
        </span>
      </div>

      {/* 项目内导航 tab */}
      <ProjectTabs projectId={projectId} />

      {/* SSE 连接状态提示 */}
      {sseError && (
        <div className="text-xs text-amber-600 bg-amber-50 rounded-lg px-4 py-2">
          实时连接断开，数据通过轮询更新：{sseError}
        </div>
      )}

      {/* SSE 连接指示器 */}
      {isConnected && (
        <div className="flex items-center gap-2 text-xs text-emerald-600">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          实时连接中
        </div>
      )}

      {/* DAG 进度面板 */}
      <DagProgress
        runData={runData}
        sseEvents={sseEvents}
        gateResult={
          runData?.status === "needs_attention"
            ? (runData.output_payload?.gate_result as Record<string, unknown> ?? null)
            : null
        }
      />

      {/* 运行失败提示 */}
      {runData?.status === "failed" && runData.error_message && (
        <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50/50 px-4 py-3">
          <span className="text-sm text-red-600">
            运行失败: {runData.error_message}
          </span>
        </div>
      )}

      {/* 下载面板（仅在完成时显示） */}
      <DownloadPanel
        projectId={projectId}
        runId={runId}
        runData={runData}
      />
    </div>
  );
}
