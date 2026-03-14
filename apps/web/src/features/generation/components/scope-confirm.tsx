/**
 * 确认 Scope 交互组件
 *
 * 让用户确认或微调收缩方案：每个功能可切换 "保留/延后"，
 * 提供 "确认 Scope" 和 "重新分析" 按钮。
 */
"use client";

import { useState } from "react";
import { Loader2, RotateCcw, Check } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ScopeDraftData } from "@/features/generation/api";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface ScopeConfirmProps {
  scopeDraft: ScopeDraftData;
  onConfirm: (restore: string[], defer: string[]) => void;
  onReanalyze: () => void;
  isPending: boolean;
  className?: string;
}

export function ScopeConfirm({
  scopeDraft,
  onConfirm,
  onReanalyze,
  isPending,
  className,
}: ScopeConfirmProps) {
  const { locale } = useLocale();

  // 初始化：scope 中的功能默认"保留"，deferred_items 默认"延后"
  const allFeatureNames = scopeDraft.scopes.map((s) => s.name);
  const initialDeferred = new Set(scopeDraft.deferred_items);

  const [deferredSet, setDeferredSet] = useState<Set<string>>(initialDeferred);

  /** 切换某个功能的保留/延后状态 */
  function toggleFeature(name: string) {
    setDeferredSet((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  }

  /** 确认时计算 restore 和 defer 列表 */
  function handleConfirm() {
    // 从初始延后中被恢复的
    const restore = scopeDraft.deferred_items.filter(
      (name) => !deferredSet.has(name)
    );
    // 所有当前标记为延后的
    const defer = Array.from(deferredSet);
    onConfirm(restore, defer);
  }

  return (
    <div className={cn("space-y-6 animate-reveal", className)}>
      <h2 className="font-heading text-xl font-bold tracking-tight">
        {L(t.generation.scopeTitle, locale)}
      </h2>

      {/* 功能列表，可切换 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">
            {locale === "zh"
              ? "点击切换功能的保留/延后状态"
              : "Click to toggle retain/defer status"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {allFeatureNames.map((name) => {
            const isDeferred = deferredSet.has(name);
            return (
              <button
                key={name}
                type="button"
                onClick={() => toggleFeature(name)}
                disabled={isPending}
                className={cn(
                  "flex items-center gap-3 w-full text-left rounded-lg px-4 py-3 transition-colors",
                  "border border-border hover:border-foreground/15",
                  isDeferred
                    ? "bg-amber-50 border-amber-200"
                    : "bg-emerald-50 border-emerald-200"
                )}
              >
                {/* 状态指示 */}
                <span
                  className={cn(
                    "flex items-center justify-center w-5 h-5 rounded-full shrink-0",
                    isDeferred
                      ? "bg-amber-100 text-amber-600"
                      : "bg-emerald-100 text-emerald-600"
                  )}
                >
                  {isDeferred ? (
                    <span className="text-xs font-bold">-</span>
                  ) : (
                    <Check size={12} />
                  )}
                </span>

                {/* 功能名 */}
                <span
                  className={cn(
                    "text-sm font-medium flex-1",
                    isDeferred ? "text-amber-700" : "text-emerald-700"
                  )}
                >
                  {name}
                </span>

                {/* 状态标签 */}
                <span
                  className={cn(
                    "text-[10px] font-medium px-2 py-0.5 rounded-full",
                    isDeferred
                      ? "bg-amber-100 text-amber-600"
                      : "bg-emerald-100 text-emerald-600"
                  )}
                >
                  {isDeferred
                    ? L(t.generation.deferred, locale)
                    : L(t.generation.retained, locale)}
                </span>
              </button>
            );
          })}

          {/* 原始延后项中不在 scopes 里的项 */}
          {scopeDraft.deferred_items
            .filter((name) => !allFeatureNames.includes(name))
            .map((name) => {
              const isDeferred = deferredSet.has(name);
              return (
                <button
                  key={name}
                  type="button"
                  onClick={() => toggleFeature(name)}
                  disabled={isPending}
                  className={cn(
                    "flex items-center gap-3 w-full text-left rounded-lg px-4 py-3 transition-colors",
                    "border border-border hover:border-foreground/15",
                    isDeferred
                      ? "bg-amber-50 border-amber-200"
                      : "bg-emerald-50 border-emerald-200"
                  )}
                >
                  <span
                    className={cn(
                      "flex items-center justify-center w-5 h-5 rounded-full shrink-0",
                      isDeferred
                        ? "bg-amber-100 text-amber-600"
                        : "bg-emerald-100 text-emerald-600"
                    )}
                  >
                    {isDeferred ? (
                      <span className="text-xs font-bold">-</span>
                    ) : (
                      <Check size={12} />
                    )}
                  </span>
                  <span
                    className={cn(
                      "text-sm font-medium flex-1",
                      isDeferred ? "text-amber-700" : "text-emerald-700"
                    )}
                  >
                    {name}
                  </span>
                  <span
                    className={cn(
                      "text-[10px] font-medium px-2 py-0.5 rounded-full",
                      isDeferred
                        ? "bg-amber-100 text-amber-600"
                        : "bg-emerald-100 text-emerald-600"
                    )}
                  >
                    {isDeferred
                      ? L(t.generation.deferred, locale)
                      : L(t.generation.retained, locale)}
                  </span>
                </button>
              );
            })}
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex items-center justify-end gap-3">
        <Button
          variant="outline"
          onClick={onReanalyze}
          disabled={isPending}
        >
          <RotateCcw size={14} className="mr-1.5" />
          {L(t.generation.reanalyze, locale)}
        </Button>
        <Button onClick={handleConfirm} disabled={isPending}>
          {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {L(t.generation.confirmBtn, locale)}
        </Button>
      </div>
    </div>
  );
}
