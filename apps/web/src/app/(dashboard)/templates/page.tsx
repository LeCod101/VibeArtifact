/**
 * 模板浏览页 - 展示所有可用项目模板
 *
 * 提供类别筛选标签和模板卡片网格。
 * 点击模板弹出创建对话框，输入项目名后创建并跳转。
 */
"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Loader2, LayoutTemplate } from "lucide-react";
import { toast } from "sonner";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import {
  useTemplatesQuery,
  useCreateFromTemplateMutation,
} from "@/features/templates/api";
import type { TemplateResponse } from "@/features/templates/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ApiError } from "@/lib/api-client/errors";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 类别筛选项定义 */
const categoryFilters = [
  { key: "all", label: { zh: "全部", en: "All" } },
  { key: "saas", label: { zh: "SaaS", en: "SaaS" } },
  { key: "api", label: { zh: "API", en: "API" } },
  { key: "landing", label: { zh: "落地页", en: "Landing" } },
  { key: "dashboard", label: { zh: "管理后台", en: "Dashboard" } },
] as const;

/** 类别标签颜色映射 */
const categoryColors: Record<string, string> = {
  saas: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  api: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  landing:
    "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  dashboard:
    "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
  other: "bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-300",
};

export default function TemplatesPage() {
  const { locale } = useLocale();
  const router = useRouter();

  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [selectedTemplate, setSelectedTemplate] =
    useState<TemplateResponse | null>(null);
  const [projectName, setProjectName] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  /** 获取模板列表，根据类别筛选 */
  const categoryParam =
    activeCategory === "all" ? undefined : activeCategory;
  const { data: templates, isLoading } = useTemplatesQuery(categoryParam);
  const createMutation = useCreateFromTemplateMutation();

  /** 点击模板卡片，打开确认对话框 */
  function handleSelectTemplate(template: TemplateResponse) {
    setSelectedTemplate(template);
    setProjectName(template.name);
    setDialogOpen(true);
  }

  /** 确认创建项目 */
  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!selectedTemplate) return;

    try {
      const result = await createMutation.mutateAsync({
        template_id: selectedTemplate.id,
        project_name: projectName,
      });
      toast.success(L(t.templates.success, locale));
      setDialogOpen(false);
      setProjectName("");
      setSelectedTemplate(null);
      router.push(`/projects/${result.project_id}`);
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  /** 获取类别的本地化名称 */
  function getCategoryLabel(category: string): string {
    const categories = t.templates.categories;
    const key = category as keyof typeof categories;
    if (key in categories) {
      return L(categories[key], locale);
    }
    return category;
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* 页面标题 */}
      <div className="mb-8 animate-reveal">
        <div className="flex items-center gap-3 mb-2">
          <LayoutTemplate size={24} className="text-foreground/70" />
          <h1 className="font-heading text-2xl font-bold tracking-tight">
            {L(t.templates.title, locale)}
          </h1>
        </div>
        <p className="text-sm text-muted-foreground">
          {L(t.templates.subtitle, locale)}
        </p>
      </div>

      {/* 类别筛选标签 */}
      <div
        className="flex flex-wrap gap-2 mb-6 animate-reveal"
        style={{ animationDelay: "0.05s" }}
      >
        {categoryFilters.map((filter) => (
          <button
            key={filter.key}
            onClick={() => setActiveCategory(filter.key)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              activeCategory === filter.key
                ? "bg-primary text-primary-foreground"
                : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
            }`}
          >
            {L(filter.label, locale)}
          </button>
        ))}
      </div>

      {/* 模板卡片网格 */}
      <div
        className="animate-reveal"
        style={{ animationDelay: "0.1s" }}
      >
        {isLoading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : !templates || templates.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <LayoutTemplate
              size={40}
              className="text-muted-foreground/40 mb-4"
            />
            <p className="text-sm text-muted-foreground">
              {L(t.templates.empty, locale)}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <Card
                key={template.id}
                className="p-5 cursor-pointer hover:shadow-md transition-all duration-200 border hover:border-primary/50"
                onClick={() => handleSelectTemplate(template)}
              >
                <div className="flex items-start gap-3">
                  {/* 图标 */}
                  <span className="text-3xl">
                    {template.icon || "📦"}
                  </span>
                  <div className="flex-1 min-w-0">
                    {/* 模板名称 */}
                    <h3 className="font-semibold text-base truncate">
                      {template.name}
                    </h3>
                    {/* 类别标签 */}
                    <Badge
                      variant="secondary"
                      className={`mt-1 text-xs ${categoryColors[template.category] || categoryColors.other}`}
                    >
                      {getCategoryLabel(template.category)}
                    </Badge>
                  </div>
                </div>
                {/* 描述 */}
                <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
                  {template.description}
                </p>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* 确认创建对话框 */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {L(t.templates.create, locale)}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            {/* 显示选中模板信息 */}
            {selectedTemplate && (
              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <span className="text-2xl">
                  {selectedTemplate.icon || "📦"}
                </span>
                <div>
                  <p className="font-medium">{selectedTemplate.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {selectedTemplate.description}
                  </p>
                </div>
              </div>
            )}
            {/* 项目名称输入 */}
            <div className="space-y-2">
              <Label htmlFor="templateProjectName">
                {L(t.templates.projectName, locale)}
              </Label>
              <Input
                id="templateProjectName"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                required
              />
            </div>
            {/* 操作按钮 */}
            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => setDialogOpen(false)}
              >
                {L(t.common.cancel, locale)}
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {L(t.templates.confirm, locale)}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
