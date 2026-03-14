/**
 * 容量仪表盘组件
 *
 * 展示容量报告：总点数、分档标签、进度条、各维度明细。
 * 颜色随 tier（small / medium / large）变化，保持暖色调。
 */
"use client";

import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { CapacityReportData } from "@/features/generation/api";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 维度 key → 翻译映射 */
const DIMENSION_KEYS: Record<string, { zh: string; en: string }> = {
  pages: { zh: "页面数", en: "Pages" },
  api_endpoints: { zh: "API 端点", en: "API Endpoints" },
  db_tables: { zh: "数据表", en: "DB Tables" },
  auth_flows: { zh: "认证流程", en: "Auth Flows" },
  integrations: { zh: "第三方集成", en: "Integrations" },
  file_upload: { zh: "文件上传", en: "File Upload" },
  realtime: { zh: "实时功能", en: "Realtime" },
  payment: { zh: "支付功能", en: "Payment" },
};

/** 根据 tier 返回对应样式 */
function getTierStyles(tier: string) {
  switch (tier) {
    case "small":
      return {
        badge: "bg-emerald-100 text-emerald-700",
        bar: "bg-emerald-500/70",
        label: t.generation.tier.small,
      };
    case "medium":
      return {
        badge: "bg-amber-100 text-amber-700",
        bar: "bg-amber-500/70",
        label: t.generation.tier.medium,
      };
    case "large":
      return {
        badge: "bg-red-100 text-red-700",
        bar: "bg-red-500/70",
        label: t.generation.tier.large,
      };
    default:
      return {
        badge: "bg-secondary text-secondary-foreground",
        bar: "bg-muted-foreground/50",
        label: { zh: tier, en: tier },
      };
  }
}

interface CapacityDashboardProps {
  report: CapacityReportData;
  className?: string;
}

export function CapacityDashboard({ report, className }: CapacityDashboardProps) {
  const { locale } = useLocale();
  const tierStyles = getTierStyles(report.tier);

  // 进度条百分比：budget <= 0 时（如 large 档 -1 或异常 0）直接视为 100%
  const progressPercent = report.budget > 0
    ? Math.min((report.total_points / report.budget) * 100, 100)
    : 100;

  return (
    <Card className={cn("animate-reveal", className)}>
      <CardHeader>
        <CardTitle>{L(t.generation.capacityTitle, locale)}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* 总点数 + 分档标签 */}
        <div className="flex items-end gap-3">
          <span className="font-heading text-4xl font-bold tracking-tight">
            {report.total_points}
          </span>
          <span className="text-sm text-muted-foreground mb-1">
            / {report.budget} {L(t.generation.totalPoints, locale)}
          </span>
          <span
            className={cn(
              "ml-auto mb-1 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
              tierStyles.badge
            )}
          >
            {L(tierStyles.label, locale)}
          </span>
        </div>

        {/* 进度条 */}
        <div className="h-2.5 w-full rounded-full bg-secondary overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-500", tierStyles.bar)}
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* 预算状态提示 */}
        <div className="flex items-center gap-2 text-sm">
          {report.must_contract ? (
            <span className="text-red-600 font-medium">
              {L(t.generation.mustContract, locale)}
            </span>
          ) : report.needs_contraction ? (
            <span className="text-amber-600 font-medium">
              {L(t.generation.needsContraction, locale)}
            </span>
          ) : report.over_budget ? (
            <span className="text-amber-600 font-medium">
              {L(t.generation.overBudget, locale)}
            </span>
          ) : (
            <span className="text-emerald-600 font-medium">
              {L(t.generation.noContraction, locale)}
            </span>
          )}
        </div>

        {/* 各维度明细 */}
        <div className="space-y-1.5">
          {report.dimensions.map((dim) => {
            // 尝试用翻译字典映射维度名
            const dimLabel = DIMENSION_KEYS[dim.dimension]
              ? L(DIMENSION_KEYS[dim.dimension], locale)
              : dim.dimension;
            return (
              <div
                key={dim.dimension}
                className="flex items-center justify-between py-1.5 border-b border-border/50 last:border-0"
              >
                <span className="text-sm text-foreground">{dimLabel}</span>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-muted-foreground tabular-nums">
                    x{dim.count}
                  </span>
                  <span className="text-sm font-medium tabular-nums w-10 text-right">
                    {dim.points}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
