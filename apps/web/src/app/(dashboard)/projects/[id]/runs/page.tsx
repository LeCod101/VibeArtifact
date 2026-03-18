/**
 * 委托运行历史页 - 展示项目所有全权委托运行记录
 *
 * 表格/列表视图，支持状态徽章、点击跳转结果页。
 */
"use client";

import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  PlayCircle,
  Timer,
} from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useProjectQuery } from "@/features/project/api";
import { useDelegatedRunsQuery } from "@/features/delegation/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ProjectTabs } from "@/features/project/components/project-tabs";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 格式化日期时间 */
function formatDateTime(iso: string | null, locale: Locale) {
  if (!iso) return "—";
  const date = new Date(iso);
  return date.toLocaleString(locale === "zh" ? "zh-CN" : "en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** 计算时长 */
function calcDuration(
  created: string | null,
  completed: string | null,
): string {
  if (!created || !completed) return "—";
  const ms = new Date(completed).getTime() - new Date(created).getTime();
  if (ms < 1000) return `${ms}ms`;
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const remainder = s % 60;
  return `${m}m ${remainder}s`;
}

/** 运行状态配置 */
const statusConfig: Record<
  string,
  {
    label: { zh: string; en: string };
    variant: "default" | "secondary" | "destructive" | "outline";
    className: string;
    icon: typeof Clock;
  }
> = {
  pending: {
    label: t.runsHistory.statusPending,
    variant: "secondary",
    className: "",
    icon: Clock,
  },
  running: {
    label: t.runsHistory.statusRunning,
    variant: "default",
    className: "bg-blue-500/10 text-blue-700 border-blue-200",
    icon: PlayCircle,
  },
  completed: {
    label: t.runsHistory.statusCompleted,
    variant: "default",
    className: "bg-green-500/10 text-green-700 border-green-200",
    icon: CheckCircle2,
  },
  failed: {
    label: t.runsHistory.statusFailed,
    variant: "destructive",
    className: "",
    icon: XCircle,
  },
  needs_attention: {
    label: t.runsHistory.statusNeedsAttention,
    variant: "default",
    className: "bg-amber-500/10 text-amber-700 border-amber-200",
    icon: AlertTriangle,
  },
};

export default function RunsHistoryPage() {
  const params = useParams();
  const router = useRouter();
  const { locale } = useLocale();
  const projectId = params.id as string;

  const { data: project, isLoading: projectLoading } =
    useProjectQuery(projectId);
  const { data: runs, isLoading: runsLoading } =
    useDelegatedRunsQuery(projectId);

  const isLoading = projectLoading || runsLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* 顶部导航 */}
      <div className="flex items-center gap-3 mb-6">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push(`/projects/${projectId}/overview`)}
        >
          <ArrowLeft size={18} />
        </Button>
        <div className="flex-1">
          <h1 className="text-lg font-bold">{project?.name}</h1>
          <p className="text-xs text-muted-foreground">
            {L(t.runsHistory.title, locale)}
          </p>
        </div>
      </div>

      {/* 项目内导航 tab */}
      <ProjectTabs projectId={projectId} />

      {/* 运行列表 */}
      {runs && runs.length > 0 ? (
        <div className="space-y-3 animate-reveal">
          {/* 表头 */}
          <div className="hidden sm:grid grid-cols-5 gap-4 px-5 py-2 text-xs font-medium text-muted-foreground">
            <span>{L(t.runsHistory.runId, locale)}</span>
            <span>{L(t.runsHistory.status, locale)}</span>
            <span>{L(t.runsHistory.created, locale)}</span>
            <span>{L(t.runsHistory.completed, locale)}</span>
            <span>{L(t.runsHistory.duration, locale)}</span>
          </div>

          {runs.map((run) => {
            const config = statusConfig[run.status] || statusConfig.pending;
            const StatusIcon = config.icon;

            return (
              <Card
                key={run.run_id}
                className="cursor-pointer transition-all duration-200 hover:shadow-md hover:border-foreground/15"
                onClick={() =>
                  router.push(
                    `/projects/${projectId}/result?runId=${run.run_id}`,
                  )
                }
              >
                <CardContent className="p-5">
                  {/* 桌面视图 */}
                  <div className="hidden sm:grid grid-cols-5 gap-4 items-center">
                    <span className="text-xs font-mono truncate">
                      {run.run_id.slice(0, 8)}
                    </span>
                    <Badge
                      variant={config.variant}
                      className={`text-[10px] w-fit gap-1 ${config.className}`}
                    >
                      <StatusIcon size={12} />
                      {L(config.label, locale)}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {formatDateTime(run.created_at, locale)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {formatDateTime(run.completed_at, locale)}
                    </span>
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <Timer size={12} />
                      {calcDuration(run.created_at, run.completed_at)}
                    </span>
                  </div>

                  {/* 移动视图 */}
                  <div className="sm:hidden space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono">
                        {run.run_id.slice(0, 8)}
                      </span>
                      <Badge
                        variant={config.variant}
                        className={`text-[10px] gap-1 ${config.className}`}
                      >
                        <StatusIcon size={12} />
                        {L(config.label, locale)}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                      <span>
                        {formatDateTime(run.created_at, locale)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Timer size={10} />
                        {calcDuration(run.created_at, run.completed_at)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        /* 空状态 */
        <div className="flex flex-col items-center justify-center h-64 text-center animate-reveal">
          <FileText size={40} className="text-muted-foreground/40 mb-4" />
          <p className="text-sm font-medium text-muted-foreground mb-1">
            {L(t.runsHistory.emptyTitle, locale)}
          </p>
          <p className="text-xs text-muted-foreground">
            {L(t.runsHistory.emptyDesc, locale)}
          </p>
        </div>
      )}
    </div>
  );
}
