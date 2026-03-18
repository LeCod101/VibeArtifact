/**
 * 全权委托页 - 启动 AI 全权委托 + 查看历史运行记录
 *
 * 页面结构：
 * - 项目标题栏 + 导航 tab（对话 / 想法 / 全权委托）
 * - 触发区：使用 DelegatedTrigger 组件
 * - 历史运行记录列表（暂用空状态占位）
 */
"use client";

import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  Rocket,
  Clock,
  FileText,
} from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useProjectQuery } from "@/features/project/api";
import { DelegatedTrigger } from "@/features/delegation/components/delegated-trigger";
import { Button } from "@/components/ui/button";
import { ProjectTabs } from "@/features/project/components/project-tabs";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

export default function DelegationPage() {
  const params = useParams();
  const router = useRouter();
  const { locale } = useLocale();
  const projectId = params.id as string;

  // 项目信息
  const { data: project, isLoading: projectLoading } =
    useProjectQuery(projectId);

  // 项目加载中
  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

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

        {/* 历史运行记录区 */}
        <div
          className="rounded-xl border border-border bg-card p-6 animate-reveal"
          style={{ animationDelay: "0.1s" }}
        >
          <div className="flex items-center gap-3 mb-4">
            <Clock size={20} className="text-foreground/70" />
            <h3 className="text-base font-bold">
              {L(t.delegation.historyTitle, locale)}
            </h3>
          </div>

          {/* 空状态占位 */}
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileText
              size={40}
              className="text-muted-foreground/40 mb-4"
            />
            <p className="text-sm text-muted-foreground">
              {L(t.delegation.emptyState, locale)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
