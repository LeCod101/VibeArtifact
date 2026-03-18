/**
 * 产物页 - 浏览项目生成的产物
 *
 * 按种类分组展示产物，支持网格/列表布局。
 * Phase 1 展示空状态或占位。
 */
"use client";

import { useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Loader2,
  Package,
  Code2,
  FileText,
  GitBranch,
  Settings,
  File,
} from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useProjectQuery } from "@/features/project/api";
import { useArtifactsQuery } from "@/features/artifact/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ProjectTabs } from "@/features/project/components/project-tabs";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 格式化日期 */
function formatDate(iso: string, locale: Locale) {
  const date = new Date(iso);
  return date.toLocaleDateString(locale === "zh" ? "zh-CN" : "en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** 产物种类图标映射 */
const kindIcons: Record<string, typeof Code2> = {
  frontend_code: Code2,
  backend_code: Code2,
  doc: FileText,
  diagram: GitBranch,
  config: Settings,
};

/** 获取产物种类的国际化标签 */
function getKindLabel(kind: string, locale: Locale): string {
  const key = kind as keyof typeof t.artifacts.kind;
  if (t.artifacts.kind[key]) {
    return L(t.artifacts.kind[key], locale);
  }
  return L(t.artifacts.kind.other, locale);
}

export default function ArtifactsPage() {
  const params = useParams();
  const router = useRouter();
  const { locale } = useLocale();
  const projectId = params.id as string;

  const { data: project, isLoading: projectLoading } =
    useProjectQuery(projectId);
  const { data: artifacts, isLoading: artifactsLoading } =
    useArtifactsQuery(projectId);

  const isLoading = projectLoading || artifactsLoading;

  /** 按种类分组的产物 */
  const groupedArtifacts = useMemo(() => {
    const map = new Map<string, NonNullable<typeof artifacts>>();
    if (!artifacts) return map;
    for (const a of artifacts) {
      const group = map.get(a.kind) || [];
      group.push(a);
      map.set(a.kind, group);
    }
    return map;
  }, [artifacts]);

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
            {L(t.artifacts.title, locale)}
          </p>
        </div>
      </div>

      {/* 项目内导航 tab */}
      <ProjectTabs projectId={projectId} />

      {/* 产物列表 */}
      {artifacts && artifacts.length > 0 ? (
        <div className="space-y-8 animate-reveal">
          {Array.from(groupedArtifacts.entries()).map(([kind, items]) => {
            const KindIcon = kindIcons[kind] || File;

            return (
              <div key={kind}>
                {/* 分组标题 */}
                <div className="flex items-center gap-2 mb-3">
                  <KindIcon size={16} className="text-muted-foreground" />
                  <h2 className="text-sm font-medium">
                    {getKindLabel(kind, locale)}
                  </h2>
                  <Badge variant="secondary" className="text-[10px]">
                    {items.length}
                  </Badge>
                </div>

                {/* 产物卡片网格 */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {items.map((artifact) => (
                    <Card
                      key={artifact.id}
                      className="transition-all duration-200 hover:shadow-md hover:border-foreground/15"
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="text-sm font-medium truncate flex-1 mr-2">
                            {artifact.name}
                          </h3>
                          <Badge
                            variant="outline"
                            className="text-[10px] shrink-0"
                          >
                            {getKindLabel(artifact.kind, locale)}
                          </Badge>
                        </div>
                        <p className="text-[10px] text-muted-foreground">
                          {formatDate(artifact.created_at, locale)}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* 空状态 */
        <div className="flex flex-col items-center justify-center h-64 text-center animate-reveal">
          <Package size={40} className="text-muted-foreground/40 mb-4" />
          <p className="text-sm font-medium text-muted-foreground mb-1">
            {L(t.artifacts.emptyTitle, locale)}
          </p>
          <p className="text-xs text-muted-foreground">
            {L(t.artifacts.emptyDesc, locale)}
          </p>
        </div>
      )}
    </div>
  );
}
