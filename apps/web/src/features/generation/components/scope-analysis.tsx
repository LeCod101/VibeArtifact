/**
 * 分析结果展示组件
 *
 * 展示 ScopeDraft 的完整信息：产品概要、功能模块卡片网格、延后项、风险列表。
 */
"use client";

import { AlertTriangle, Clock, Tag } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ScopeDraftData } from "@/features/generation/api";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 优先级 → Badge 样式 */
function getPriorityStyle(priority: string) {
  switch (priority.toLowerCase()) {
    case "high":
      return "bg-red-50 text-red-600";
    case "medium":
      return "bg-amber-50 text-amber-600";
    case "low":
      return "bg-secondary text-muted-foreground";
    default:
      return "bg-secondary text-muted-foreground";
  }
}

/** 优先级翻译 */
function getPriorityLabel(priority: string, locale: Locale) {
  const key = priority.toLowerCase() as keyof typeof t.generation.priority;
  if (t.generation.priority[key]) {
    return L(t.generation.priority[key], locale);
  }
  return priority;
}

interface ScopeAnalysisProps {
  scopeDraft: ScopeDraftData;
  className?: string;
}

export function ScopeAnalysis({ scopeDraft, className }: ScopeAnalysisProps) {
  const { locale } = useLocale();

  return (
    <div className={cn("space-y-6 animate-reveal", className)}>
      {/* 产品概要 */}
      <div>
        <h2 className="font-heading text-2xl font-bold tracking-tight mb-1">
          {scopeDraft.product_name}
        </h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {scopeDraft.product_description}
        </p>
      </div>

      {/* 功能模块卡片网格 */}
      <div>
        <h3 className="text-sm font-medium text-muted-foreground mb-3">
          {L(t.generation.scopeTitle, locale)}
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {scopeDraft.scopes.map((scope) => (
            <Card key={scope.name} size="sm">
              <CardContent className="space-y-2">
                {/* 名称 + 优先级 */}
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-medium leading-snug">
                    {scope.name}
                  </h4>
                  <span
                    className={cn(
                      "inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[10px] font-medium",
                      getPriorityStyle(scope.priority)
                    )}
                  >
                    {getPriorityLabel(scope.priority, locale)}
                  </span>
                </div>
                {/* 描述 */}
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {scope.description}
                </p>
                {/* 标签 */}
                {scope.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {scope.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 text-[10px] text-muted-foreground"
                      >
                        <Tag size={10} />
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* 延后项 */}
      {scopeDraft.deferred_items.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
            <Clock size={14} className="text-amber-600" />
            {L(t.generation.deferredItems, locale)}
          </h3>
          <ul className="space-y-1">
            {scopeDraft.deferred_items.map((item) => (
              <li
                key={item}
                className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 rounded-md px-3 py-1.5"
              >
                <span className="w-1 h-1 rounded-full bg-amber-400 shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 风险列表 */}
      {scopeDraft.risks.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
            <AlertTriangle size={14} className="text-red-600" />
            {L(t.generation.risks, locale)}
          </h3>
          <ul className="space-y-1">
            {scopeDraft.risks.map((risk) => (
              <li
                key={risk}
                className="flex items-center gap-2 text-sm text-red-600 bg-red-50 rounded-md px-3 py-1.5"
              >
                <span className="w-1 h-1 rounded-full bg-red-400 shrink-0" />
                {risk}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
