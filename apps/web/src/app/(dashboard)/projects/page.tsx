/**
 * 项目列表页 - 浏览所有项目
 *
 * 支持搜索、排序，网格卡片布局展示项目。
 * 点击卡片跳转项目详情，支持新建项目。
 */
"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Plus,
  Search,
  FolderOpen,
  Loader2,
  ArrowUpDown,
} from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useProjectsQuery } from "@/features/project/api";
import { CreateProjectDialog } from "@/features/project/components/create-project-dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 排序类型 */
type SortMode = "newest" | "oldest" | "name";

/** 格式化日期 */
function formatDate(iso: string, locale: Locale) {
  const date = new Date(iso);
  return date.toLocaleDateString(locale === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function ProjectsListPage() {
  const { locale } = useLocale();
  const router = useRouter();
  const { data: projects, isLoading } = useProjectsQuery();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("newest");

  /** 排序切换 */
  function cycleSortMode() {
    const modes: SortMode[] = ["newest", "oldest", "name"];
    const idx = modes.indexOf(sortMode);
    setSortMode(modes[(idx + 1) % modes.length]);
  }

  /** 排序标签 */
  const sortLabel = {
    newest: L(t.common.sortNewest, locale),
    oldest: L(t.common.sortOldest, locale),
    name: L(t.common.sortName, locale),
  }[sortMode];

  /** 过滤和排序后的项目 */
  const filteredProjects = useMemo(() => {
    if (!projects) return [];

    let list = projects.filter((p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()),
    );

    if (sortMode === "newest") {
      list = [...list].sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      );
    } else if (sortMode === "oldest") {
      list = [...list].sort(
        (a, b) =>
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      );
    } else {
      list = [...list].sort((a, b) => a.name.localeCompare(b.name));
    }

    return list;
  }, [projects, searchQuery, sortMode]);

  return (
    <div className="max-w-5xl mx-auto">
      {/* 页面标题栏 */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-heading text-2xl font-bold tracking-tight">
          {L(t.projectList.title, locale)}
        </h1>
        <Button onClick={() => setDialogOpen(true)} className="gap-1.5">
          <Plus size={16} />
          {L(t.dashboard.newProject, locale)}
        </Button>
      </div>

      {/* 搜索 + 排序 */}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
          />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={L(t.projectList.searchPlaceholder, locale)}
            className="pl-9"
          />
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={cycleSortMode}
          className="gap-1.5 shrink-0"
        >
          <ArrowUpDown size={14} />
          {sortLabel}
        </Button>
      </div>

      {/* 内容区 */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProjects.map((project) => (
            <Card
              key={project.id}
              className="cursor-pointer transition-all duration-200 hover:shadow-md hover:border-foreground/15"
              onClick={() => router.push(`/projects/${project.id}`)}
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-sm font-medium truncate flex-1 mr-2">
                    {project.name}
                  </h3>
                  <Badge
                    variant={
                      project.status === "active" ? "default" : "secondary"
                    }
                    className="text-[10px] shrink-0"
                  >
                    {L(
                      t.project.status[
                        project.status as keyof typeof t.project.status
                      ] || { zh: project.status, en: project.status },
                      locale,
                    )}
                  </Badge>
                </div>
                {project.description && (
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                    {project.description}
                  </p>
                )}
                <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                  <span>{formatDate(project.created_at, locale)}</span>
                  <span>
                    {L(t.projectList.lastUpdated, locale)}{" "}
                    {formatDate(project.updated_at, locale)}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        /* 空状态 */
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <FolderOpen size={40} className="text-muted-foreground/40 mb-4" />
          <p className="text-sm font-medium text-muted-foreground mb-1">
            {L(t.projectList.emptyTitle, locale)}
          </p>
          <p className="text-xs text-muted-foreground mb-4">
            {L(t.projectList.emptyDesc, locale)}
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDialogOpen(true)}
            className="gap-1"
          >
            <Plus size={14} />
            {L(t.dashboard.newProject, locale)}
          </Button>
        </div>
      )}

      <CreateProjectDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}
