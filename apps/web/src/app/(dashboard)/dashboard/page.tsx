/**
 * 仪表盘页面 - 项目列表
 *
 * 展示用户所有项目的卡片网格，支持新建项目。
 * 空状态显示引导文案。
 */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, FolderOpen, Loader2 } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useProjectsQuery } from "@/features/project/api";
import { CreateProjectDialog } from "@/features/project/components/create-project-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 格式化日期为简短格式 */
function formatDate(iso: string, locale: Locale) {
  const date = new Date(iso);
  return date.toLocaleDateString(locale === "zh" ? "zh-CN" : "en-US", {
    month: "short",
    day: "numeric",
  });
}

export default function DashboardPage() {
  const { locale } = useLocale();
  const router = useRouter();
  const { data: projects, isLoading } = useProjectsQuery();
  const [dialogOpen, setDialogOpen] = useState(false);

  // 加载中
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div>
      {/* 页面头部 */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-extrabold">
          {L(t.dashboard.title, locale)}
        </h1>
        <Button onClick={() => setDialogOpen(true)} className="gap-2">
          <Plus size={16} />
          {L(t.dashboard.newProject, locale)}
        </Button>
      </div>

      {/* 项目网格 */}
      {projects && projects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => (
            <Card
              key={project.id}
              className="cursor-pointer transition-all duration-300 hover:-translate-y-1 hover:border-foreground/20"
              onClick={() => router.push(`/projects/${project.id}`)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-lg">{project.name}</CardTitle>
                  <Badge
                    variant={project.status === "active" ? "default" : "secondary"}
                  >
                    {L(
                      t.project.status[
                        project.status as keyof typeof t.project.status
                      ] || { zh: project.status, en: project.status },
                      locale
                    )}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                {project.description && (
                  <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                    {project.description}
                  </p>
                )}
                <p className="text-xs text-muted-foreground">
                  {formatDate(project.created_at, locale)}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        /* 空状态 */
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <FolderOpen size={48} className="text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">
            {L(t.dashboard.emptyTitle, locale)}
          </h3>
          <p className="text-sm text-muted-foreground mb-6">
            {L(t.dashboard.emptyDesc, locale)}
          </p>
          <Button onClick={() => setDialogOpen(true)} className="gap-2">
            <Plus size={16} />
            {L(t.dashboard.newProject, locale)}
          </Button>
        </div>
      )}

      <CreateProjectDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}
