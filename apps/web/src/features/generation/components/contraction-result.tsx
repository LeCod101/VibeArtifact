/**
 * 收缩方案展示组件
 *
 * 三栏对比展示：保留功能 / 延后功能 / 风险列表。
 * 底部展示收缩理由和收缩前后容量点数对比。
 */
"use client";

import { Check, Clock, AlertTriangle, ArrowRight } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type {
  ContractionDecisionData,
  CapacityReportData,
} from "@/features/generation/api";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface ContractionResultProps {
  decision: ContractionDecisionData;
  capacityBefore: CapacityReportData;
  capacityAfter: CapacityReportData;
  className?: string;
}

export function ContractionResult({
  decision,
  capacityBefore,
  capacityAfter,
  className,
}: ContractionResultProps) {
  const { locale } = useLocale();

  return (
    <div className={cn("space-y-6 animate-reveal", className)}>
      {/* 标题 */}
      <h2 className="font-heading text-xl font-bold tracking-tight">
        {L(t.generation.contractionResult, locale)}
      </h2>

      {/* 三栏对比 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* 左栏：保留的功能 */}
        <Card size="sm">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-1.5 text-emerald-600">
              <Check size={16} />
              {L(t.generation.retained, locale)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1.5">
              {decision.retained_features.map((feature) => (
                <li
                  key={feature}
                  className="flex items-center gap-2 text-sm bg-emerald-50 text-emerald-600 rounded-md px-3 py-1.5"
                >
                  <Check size={14} className="shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        {/* 中栏：延后的功能及理由 */}
        <Card size="sm">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-1.5 text-amber-600">
              <Clock size={16} />
              {L(t.generation.deferred, locale)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {decision.deferred_features.map((item) => (
                <li
                  key={item.name}
                  className="bg-amber-50 rounded-md px-3 py-2"
                >
                  <span className="flex items-center gap-2 text-sm font-medium text-amber-600">
                    <Clock size={14} className="shrink-0" />
                    {item.name}
                  </span>
                  <p className="text-xs text-amber-600/80 mt-0.5 ml-[22px]">
                    {item.reason}
                  </p>
                </li>
              ))}
              {decision.deferred_features.length === 0 && (
                <li className="text-xs text-muted-foreground py-2">--</li>
              )}
            </ul>
          </CardContent>
        </Card>

        {/* 右栏：风险列表 */}
        <Card size="sm">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-1.5 text-red-600">
              <AlertTriangle size={16} />
              {L(t.generation.risks, locale)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1.5">
              {decision.risks.map((risk) => (
                <li
                  key={risk}
                  className="flex items-center gap-2 text-sm bg-red-50 text-red-600 rounded-md px-3 py-1.5"
                >
                  <AlertTriangle size={14} className="shrink-0" />
                  {risk}
                </li>
              ))}
              {decision.risks.length === 0 && (
                <li className="text-xs text-muted-foreground py-2">--</li>
              )}
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* 收缩理由 */}
      <Card size="sm">
        <CardHeader className="pb-1">
          <CardTitle className="text-sm">
            {L(t.generation.rationale, locale)}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {decision.rationale}
          </p>
        </CardContent>
      </Card>

      {/* 容量对比：收缩前 → 收缩后 */}
      <div className="flex items-center justify-center gap-4 py-2">
        <div className="text-center">
          <p className="text-xs text-muted-foreground mb-1">
            {L(t.generation.beforeContraction, locale)}
          </p>
          <span className="font-heading text-2xl font-bold text-red-600">
            {capacityBefore.total_points}
          </span>
          <span className="text-xs text-muted-foreground ml-1">
            / {capacityBefore.budget}
          </span>
        </div>

        <ArrowRight size={20} className="text-muted-foreground" />

        <div className="text-center">
          <p className="text-xs text-muted-foreground mb-1">
            {L(t.generation.afterContraction, locale)}
          </p>
          <span className="font-heading text-2xl font-bold text-emerald-600">
            {capacityAfter.total_points}
          </span>
          <span className="text-xs text-muted-foreground ml-1">
            / {capacityAfter.budget}
          </span>
        </div>
      </div>
    </div>
  );
}
