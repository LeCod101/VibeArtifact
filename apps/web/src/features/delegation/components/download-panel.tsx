/**
 * 下载面板
 *
 * 全权委托运行完成后展示：
 * - ZIP 产物下载按钮
 * - QA 报告摘要（passed/failed + issue 数量）
 * - QA 失败时显示警告但仍允许下载
 */
"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  Loader2,
  XCircle,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useDownloadZip } from "@/features/delegation/hooks/use-delegated";
import type { DelegatedRunData, DelegatedStepData } from "@/features/delegation/api";

interface DownloadPanelProps {
  /** 项目 UUID */
  projectId: string;
  /** 运行 UUID */
  runId: string;
  /** 运行数据 */
  runData?: DelegatedRunData | null;
  /** 额外的 CSS 类名 */
  className?: string;
}

/**
 * 从步骤列表中找到 QA 步骤
 */
function findQaStep(steps: DelegatedStepData[]): DelegatedStepData | null {
  return steps.find((s) => s.agent_id === "qa") ?? null;
}

/**
 * 下载面板组件
 *
 * 仅在运行完成（completed）时展示。
 * 提供 ZIP 下载和 QA 报告摘要。
 */
export function DownloadPanel({
  projectId,
  runId,
  runData,
  className,
}: DownloadPanelProps) {
  const { download } = useDownloadZip(projectId, runId);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // 运行未完成时不渲染
  if (!runData || runData.status !== "completed") {
    return null;
  }

  const qaStep = findQaStep(runData.steps);
  const qaFailed = qaStep?.status === "failed";

  /** 处理下载点击 */
  async function handleDownload() {
    setIsDownloading(true);
    setDownloadError(null);
    try {
      await download();
    } catch (err) {
      setDownloadError(
        err instanceof Error ? err.message : "下载失败"
      );
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>产物下载</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* QA 报告摘要 */}
        <div
          className={cn(
            "flex items-center gap-3 rounded-lg border px-4 py-3",
            qaFailed
              ? "border-amber-200 bg-amber-50/50"
              : "border-emerald-200 bg-emerald-50/50",
          )}
        >
          {qaFailed ? (
            <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0" />
          ) : (
            <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0" />
          )}
          <div className="flex-1">
            <p className="text-sm font-medium">
              {qaFailed ? "QA 检查发现问题" : "QA 检查通过"}
            </p>
            <p className="text-xs text-muted-foreground">
              {qaFailed
                ? "产物中可能存在质量问题，建议检查后使用"
                : "所有质量检查项已通过"}
            </p>
          </div>
          {qaStep && (
            <span
              className={cn(
                "text-xs font-medium px-2 py-1 rounded-full shrink-0",
                qaFailed
                  ? "bg-amber-100 text-amber-700"
                  : "bg-emerald-100 text-emerald-700",
              )}
            >
              {qaFailed ? "FAILED" : "PASSED"}
            </span>
          )}
        </div>

        {/* QA 失败警告 */}
        {qaFailed && (
          <div className="flex items-start gap-2 text-xs text-amber-600 bg-amber-50 rounded-lg px-3 py-2">
            <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
            <span>
              QA 检查未通过，但您仍可以下载产物。建议在使用前手动检查代码质量。
            </span>
          </div>
        )}

        {/* 运行失败信息 */}
        {runData.error_message && (
          <div className="flex items-start gap-2 text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">
            <XCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
            <span>{runData.error_message}</span>
          </div>
        )}

        {/* 下载按钮 */}
        <Button
          className="w-full gap-2"
          size="lg"
          onClick={handleDownload}
          disabled={isDownloading}
        >
          {isDownloading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          {isDownloading ? "正在下载..." : "下载 ZIP 产物"}
        </Button>

        {/* 下载错误提示 */}
        {downloadError && (
          <p className="text-sm text-red-600 bg-red-50 rounded-lg px-4 py-2">
            {downloadError}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
