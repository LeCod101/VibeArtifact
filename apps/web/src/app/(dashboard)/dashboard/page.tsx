/**
 * 仪表盘页面 - Claude 风格问候 + 输入 + 最近项目
 *
 * 页面上半部分：时间问候语 + 创意输入框
 * 页面下半部分：最近项目卡片网格
 */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Plus,
  ArrowUp,
  Mic,
  FolderOpen,
  Loader2,
  ChevronDown,
  ArrowRight,
  LayoutTemplate,
} from "lucide-react";
import { toast } from "sonner";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useProjectsQuery, useCreateProjectMutation } from "@/features/project/api";
import { useTemplatesQuery } from "@/features/templates/api";
import { useAuthStore } from "@/stores/auth-store";
import { CreateProjectDialog } from "@/features/project/components/create-project-dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client/errors";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 根据当前时间返回问候语 key */
function getGreetingKey(): "morning" | "afternoon" | "evening" {
  const hour = new Date().getHours();
  if (hour < 12) return "morning";
  if (hour < 18) return "afternoon";
  return "evening";
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
  const { user } = useAuthStore();
  const { data: projects, isLoading } = useProjectsQuery();
  const { data: templates } = useTemplatesQuery();
  const createMutation = useCreateProjectMutation();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");

  /** 通过输入框快速创建项目 */
  async function handleQuickCreate() {
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    try {
      const project = await createMutation.mutateAsync({
        name: trimmed,
        description: "",
      });
      setInputValue("");
      toast.success(L(t.project.createSuccess, locale));
      router.push(`/projects/${project.id}`);
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  /** 键盘事件：Enter 提交 */
  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleQuickCreate();
    }
  }

  /** 问候语文本 */
  const greetingKey = getGreetingKey();
  const greetingText = L(t.greeting[greetingKey], locale);
  const displayName = user?.display_name || user?.email?.split("@")[0] || "";

  return (
    <div className="flex flex-col items-center pt-16 md:pt-24 lg:pt-32 px-4">
      {/* 问候语 */}
      <h1 className="font-serif-display text-3xl md:text-4xl lg:text-5xl font-medium text-foreground mb-10 text-center animate-reveal">
        {greetingText}
        {displayName && (
          <span className="text-muted-foreground">
            &#xFF0C;{displayName}
          </span>
        )}
      </h1>

      {/* 输入框卡片 */}
      <div className="w-full max-w-2xl mb-16 animate-reveal" style={{ animationDelay: "0.1s" }}>
        <div className="flex items-center gap-2 bg-card rounded-2xl border border-border shadow-sm px-4 py-3">
          {/* 附件按钮（占位） */}
          <button
            type="button"
            className="flex items-center justify-center w-8 h-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors shrink-0"
            title={L({ zh: "附件", en: "Attach" }, locale)}
          >
            <Plus size={18} />
          </button>

          {/* 文本输入 */}
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={L(t.greeting.inputPlaceholder, locale)}
            className="flex-1 bg-transparent border-none outline-none text-sm text-foreground placeholder:text-muted-foreground"
          />

          {/* 模型标签（静态占位） */}
          <button
            type="button"
            className="hidden sm:flex items-center gap-1 h-7 px-3 rounded-full bg-secondary text-xs font-medium text-secondary-foreground shrink-0"
          >
            Pro
            <ChevronDown size={12} />
          </button>

          {/* 麦克风按钮（占位） */}
          <button
            type="button"
            className="flex items-center justify-center w-8 h-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors shrink-0"
            title={L({ zh: "语音输入", en: "Voice input" }, locale)}
          >
            <Mic size={16} />
          </button>

          {/* 发送按钮 */}
          <button
            type="button"
            onClick={handleQuickCreate}
            disabled={!inputValue.trim() || createMutation.isPending}
            className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground disabled:opacity-30 transition-opacity shrink-0"
          >
            {createMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowUp size={16} />
            )}
          </button>
        </div>
      </div>

      {/* 最近项目区域 */}
      <div className="w-full max-w-4xl animate-reveal" style={{ animationDelay: "0.2s" }}>
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : projects && projects.length > 0 ? (
          <>
            {/* 区域标题 */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium text-muted-foreground">
                {L(t.greeting.recentProjects, locale)}
              </h2>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setDialogOpen(true)}
                  className="gap-1 text-muted-foreground"
                >
                  <Plus size={14} />
                  {L(t.dashboard.newProject, locale)}
                </Button>
                <Link href="/projects">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="gap-1 text-muted-foreground"
                  >
                    {L(t.dashboard.viewAllProjects, locale)}
                    <ArrowRight size={14} />
                  </Button>
                </Link>
              </div>
            </div>

            {/* 项目卡片网格 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {projects.slice(0, 6).map((project) => (
                <Card
                  key={project.id}
                  className="cursor-pointer transition-all duration-200 hover:shadow-md hover:border-foreground/15"
                  onClick={() => router.push(`/projects/${project.id}`)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-sm font-medium truncate flex-1 mr-2">
                        {project.name}
                      </h3>
                      <Badge
                        variant={project.status === "active" ? "default" : "secondary"}
                        className="text-[10px] shrink-0"
                      >
                        {L(
                          t.project.status[
                            project.status as keyof typeof t.project.status
                          ] || { zh: project.status, en: project.status },
                          locale
                        )}
                      </Badge>
                    </div>
                    {project.description && (
                      <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                        {project.description}
                      </p>
                    )}
                    <p className="text-[10px] text-muted-foreground">
                      {formatDate(project.created_at, locale)}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        ) : (
          /* 空状态 */
          <div className="flex flex-col items-center justify-center h-32 text-center">
            <FolderOpen size={32} className="text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground mb-3">
              {L(t.dashboard.emptyTitle, locale)}
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
      </div>

      {/* 从模板开始区域 */}
      {templates && templates.length > 0 && (
        <div
          className="w-full max-w-4xl mt-8 animate-reveal"
          style={{ animationDelay: "0.3s" }}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <LayoutTemplate size={14} />
              {L(t.dashboard.fromTemplate, locale)}
            </h2>
            <Link href="/templates">
              <Button
                variant="ghost"
                size="sm"
                className="gap-1 text-muted-foreground"
              >
                {L(t.dashboard.browseMore, locale)}
                <ArrowRight size={14} />
              </Button>
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {templates.slice(0, 3).map((tpl) => (
              <Card
                key={tpl.id}
                className="cursor-pointer transition-all duration-200 hover:shadow-md hover:border-foreground/15"
                onClick={() => router.push("/templates")}
              >
                <CardContent className="p-4 flex items-center gap-3">
                  <span className="text-2xl">{tpl.icon || "📦"}</span>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium truncate">
                      {tpl.name}
                    </h3>
                    <p className="text-xs text-muted-foreground truncate">
                      {tpl.description}
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      <CreateProjectDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}
