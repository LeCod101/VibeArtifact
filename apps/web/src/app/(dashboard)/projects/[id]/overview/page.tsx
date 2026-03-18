/**
 * 项目概览页 - 项目仪表盘视图
 *
 * 展示项目基本信息、统计卡片、最近活动和快捷操作。
 * 支持内联编辑项目名称和描述。
 */
"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  MessageSquare,
  Camera,
  Rocket,
  Lightbulb,
  Activity,
  Pencil,
  Check,
  X,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useProjectQuery, useUpdateProjectMutation } from "@/features/project/api";
import { useConversationsQuery } from "@/features/chat/api";
import { useSnapshotsQuery } from "@/features/snapshot/api";
import { useDelegatedRunsQuery } from "@/features/delegation/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api-client/errors";
import { ProjectTabs } from "@/features/project/components/project-tabs";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

export default function ProjectOverviewPage() {
  const params = useParams();
  const router = useRouter();
  const { locale } = useLocale();
  const projectId = params.id as string;

  const { data: project, isLoading } = useProjectQuery(projectId);
  const { data: conversations } = useConversationsQuery(projectId);
  const { data: snapshots } = useSnapshotsQuery(projectId);
  const { data: runs } = useDelegatedRunsQuery(projectId);
  const updateMutation = useUpdateProjectMutation(projectId);

  // 编辑模式状态
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");

  /** 进入编辑模式 */
  function startEdit() {
    setEditName(project?.name || "");
    setEditDesc(project?.description || "");
    setEditing(true);
  }

  /** 保存编辑 */
  async function saveEdit() {
    try {
      await updateMutation.mutateAsync({
        name: editName.trim() || project?.name,
        description: editDesc.trim(),
      });
      setEditing(false);
      toast.success(L(t.projectOverview.saveSuccess, locale));
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  /** 统计数据 */
  const stats = [
    {
      label: L(t.projectOverview.conversations, locale),
      value: conversations?.length ?? 0,
      icon: MessageSquare,
    },
    {
      label: L(t.projectOverview.snapshots, locale),
      value: snapshots?.length ?? 0,
      icon: Camera,
    },
    {
      label: L(t.projectOverview.delegationRuns, locale),
      value: runs?.length ?? 0,
      icon: Rocket,
    },
  ];

  return (
    <div className="max-w-4xl mx-auto">
      {/* 顶部导航 */}
      <div className="flex items-center gap-3 mb-6">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push("/projects")}
        >
          <ArrowLeft size={18} />
        </Button>
        <div className="flex-1">
          {editing ? (
            <div className="space-y-2">
              <Input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="text-lg font-bold h-9"
              />
              <Input
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                placeholder={L(t.project.descPlaceholder, locale)}
                className="text-xs h-8"
              />
            </div>
          ) : (
            <>
              <h1 className="text-lg font-bold">{project?.name}</h1>
              {project?.description && (
                <p className="text-xs text-muted-foreground">
                  {project.description}
                </p>
              )}
            </>
          )}
        </div>
        <Badge
          variant={project?.status === "active" ? "default" : "secondary"}
          className="shrink-0"
        >
          {L(
            t.project.status[
              project?.status as keyof typeof t.project.status
            ] || { zh: project?.status, en: project?.status },
            locale,
          )}
        </Badge>
        {editing ? (
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={saveEdit}
              disabled={updateMutation.isPending}
            >
              <Check size={16} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setEditing(false)}
            >
              <X size={16} />
            </Button>
          </div>
        ) : (
          <Button variant="ghost" size="icon" onClick={startEdit}>
            <Pencil size={16} />
          </Button>
        )}
      </div>

      {/* 项目内导航 tab */}
      <ProjectTabs projectId={projectId} />

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8 animate-reveal">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-5 flex items-center gap-4">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-secondary">
                <stat.icon size={20} className="text-foreground/70" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stat.value}</p>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 快捷操作 */}
      <div
        className="mb-8 animate-reveal"
        style={{ animationDelay: "0.05s" }}
      >
        <h2 className="text-sm font-medium text-muted-foreground mb-3">
          {L(t.projectOverview.quickActions, locale)}
        </h2>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => router.push(`/projects/${projectId}`)}
          >
            <MessageSquare size={14} />
            {L(t.projectOverview.newConversation, locale)}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => router.push(`/projects/${projectId}/ideation`)}
          >
            <Lightbulb size={14} />
            {L(t.projectOverview.startIdeation, locale)}
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => router.push(`/projects/${projectId}/delegation`)}
          >
            <Rocket size={14} />
            {L(t.projectOverview.fullDelegation, locale)}
          </Button>
        </div>
      </div>

      {/* 最近活动 */}
      <div
        className="animate-reveal"
        style={{ animationDelay: "0.1s" }}
      >
        <h2 className="text-sm font-medium text-muted-foreground mb-3">
          {L(t.projectOverview.recentActivity, locale)}
        </h2>
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Activity
                size={32}
                className="text-muted-foreground/40 mb-3"
              />
              <p className="text-sm text-muted-foreground">
                {L(t.projectOverview.noActivity, locale)}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
