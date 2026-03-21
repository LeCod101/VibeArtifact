/**
 * 全权委托页 - 启动 AI 全权委托 + 查看历史运行记录
 *
 * 页面结构：
 * - 项目标题栏 + 导航 tab（对话 / 想法 / 全权委托）
 * - 触发区：使用 DelegatedTrigger 组件
 * - 最近运行记录列表（最多显示 5 条 + "查看全部" 链接）
 */
"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Loader2,
  Rocket,
  Clock,
  FileText,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  PlayCircle,
  ArrowRight,
} from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useProjectQuery } from "@/features/project/api";
import { useDelegatedRunsQuery } from "@/features/delegation/api";
import { DelegatedTrigger } from "@/features/delegation/components/delegated-trigger";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ProjectTabs } from "@/features/project/components/project-tabs";

/** 多语言取值辅助函数 */
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

/** 运行状态图标映射 */
const statusIcons: Record<string, typeof Clock> = {
  pending: Clock,
  running: PlayCircle,
  completed: CheckCircle2,
  failed: XCircle,
  needs_attention: AlertTriangle,
};

/** 运行状态样式映射 */
const statusStyles: Record<
  string,
  { variant: "default" | "secondary" | "destructive"; className: string }
> = {
  pending: { variant: "secondary", className: "" },
  running: {
    variant: "default",
    className: "bg-blue-500/10 text-blue-700 border-blue-200",
  },
  completed: {
    variant: "default",
    className: "bg-green-500/10 text-green-700 border-green-200",
  },
  failed: { variant: "destructive", className: "" },
  needs_attention: {
    variant: "default",
    className: "bg-amber-500/10 text-amber-700 border-amber-200",
  },
};

/** 运行状态文本映射 */
const statusLabels: Record<string, { zh: string; en: string }> = {
  pending: { zh: "等待中", en: "Pending" },
  running: { zh: "运行中", en: "Running" },
  completed: { zh: "已完成", en: "Completed" },
  failed: { zh: "失败", en: "Failed" },
  needs_attention: { zh: "需要关注", en: "Needs Attention" },
};

export default function DelegationPage() {
  const params = useParams();
  const router = useRouter();
  const { locale } = useLocale();
  const projectId = params.id as string;

  // 项目信息
  const { data: project, isLoading: projectLoading } =
    useProjectQuery(projectId);

  // 运行列表
  const { data: runs, isLoading: runsLoading } =
    useDelegatedRunsQuery(projectId);

  // 项目加载中
  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  /** 最近 5 条运行记录 */
  const recentRuns = runs?.slice(0, 5) ?? [];
  const hasMoreRuns = (runs?.length ?? 0) > 5;

  return (
    <div className="flex flex-col items-center pb-12">
      {/* 项目标题栏 */}
      <div className="w-full max-w-4xl flex items-center gap-3 mb-6">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push("/dashboard")}
        >
          <ArrowLeft size={18} />
        </Button>
        <div className="flex-1">
          <h2 className="text-lg font-bold">{project?.name}</h2>
        </div>
        {/* 项目内导航 tab */}
        <ProjectTabs projectId={projectId} />
      </div>

      {/* 主内容区 */}
      <div className="w-full max-w-4xl space-y-8">
        {/* 标题区 */}
        <div className="animate-reveal">
          <h1 className="font-heading text-2xl font-bold tracking-tight mb-2">
            {L(t.delegation.title, locale)}
          </h1>
          <p className="text-sm text-muted-foreground">
            {L(t.delegation.triggerDesc, locale)}
          </p>
        </div>

        {/* 触发区 */}
        <div
          className="rounded-xl border border-border bg-card p-6 animate-reveal"
          style={{ animationDelay: "0.05s" }}
        >
          <div className="flex items-center gap-3 mb-4">
            <Rocket size={20} className="text-foreground/70" />
            <h3 className="text-base font-bold">
              {L(t.delegation.triggerTitle, locale)}
            </h3>
          </div>
          <DelegatedTrigger projectId={projectId} className="max-w-sm" />
        </div>

        {/* 最近运行记录区 */}
        <div
          className="rounded-xl border border-border bg-card p-6 animate-reveal"
          style={{ animationDelay: "0.1s" }}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Clock size={20} className="text-foreground/70" />
              <h3 className="text-base font-bold">
                {L(t.delegation.recentRuns, locale)}
              </h3>
            </div>
            {hasMoreRuns && (
              <Link href={`/projects/${projectId}/runs`}>
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-1 text-muted-foreground"
                >
                  {L(t.delegation.viewAll, locale)}
                  <ArrowRight size={14} />
                </Button>
              </Link>
            )}
          </div>

          {runsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : recentRuns.length > 0 ? (
            <div className="space-y-2">
              {recentRuns.map((run) => {
                const style =
                  statusStyles[run.status] || statusStyles.pending;
                const StatusIcon =
                  statusIcons[run.status] || Clock;
                const label =
                  statusLabels[run.status] || statusLabels.pending;

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
                    <CardContent className="px-4 py-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-mono text-muted-foreground">
                            {run.run_id.slice(0, 8)}
                          </span>
                          <Badge
                            variant={style.variant}
                            className={`text-[10px] gap-1 ${style.className}`}
                          >
                            <StatusIcon size={12} />
                            {L(label, locale)}
                          </Badge>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {formatDateTime(run.created_at, locale)}
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            /* 空状态 */
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText
                size={40}
                className="text-muted-foreground/40 mb-4"
              />
              <p className="text-sm text-muted-foreground mb-1">
                {L(t.delegation.noRuns, locale)}
              </p>
              <p className="text-xs text-muted-foreground">
                {L(t.delegation.startFirst, locale)}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
