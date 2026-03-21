/**
 * 风险面板组件
 *
 * 展示全权委托运行中的高风险节点列表。
 * 每个风险条目包含标题、描述、严重等级和缓解措施。
 */
"use client";

import { AlertTriangle, ShieldAlert } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import type { RiskItem } from "@/lib/api-client/types";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface RiskPanelProps {
  /** 风险列表 */
  risks: RiskItem[];
}

/**
 * 根据严重等级返回 Badge 颜色样式
 */
function severityStyle(severity: string): string {
  switch (severity.toUpperCase()) {
    case "HIGH":
    case "CRITICAL":
      return "bg-red-100 text-red-700 border-red-200";
    case "MEDIUM":
      return "bg-amber-100 text-amber-700 border-amber-200";
    case "LOW":
      return "bg-blue-100 text-blue-700 border-blue-200";
    default:
      return "bg-gray-100 text-gray-700 border-gray-200";
  }
}

/**
 * 严重等级中文标签
 */
function severityLabel(severity: string): string {
  switch (severity.toUpperCase()) {
    case "CRITICAL":
      return "严重";
    case "HIGH":
      return "高";
    case "MEDIUM":
      return "中";
    case "LOW":
      return "低";
    default:
      return severity;
  }
}

/**
 * 风险面板组件
 *
 * 显示高风险节点列表，包含标题、描述、严重等级标签和缓解措施。
 * 空列表时显示"暂无高风险项"。
 */
export function RiskPanel({ risks }: RiskPanelProps) {
  const { locale } = useLocale();

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <ShieldAlert className="h-4 w-4 text-red-500" />
          {L(t.approval.riskTitle, locale)}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {risks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <AlertTriangle className="h-8 w-8 text-muted-foreground/30 mb-2" />
            <p className="text-sm text-muted-foreground">
              {L(t.approval.noRisks, locale)}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {risks.map((risk) => (
              <div
                key={risk.id}
                className="rounded-lg border border-border p-4 space-y-2"
              >
                {/* 标题行 */}
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-semibold">{risk.title}</h4>
                  <Badge
                    variant="outline"
                    className={`shrink-0 ${severityStyle(risk.severity)}`}
                  >
                    {severityLabel(risk.severity)}
                  </Badge>
                </div>

                {/* 描述 */}
                <p className="text-sm text-muted-foreground">
                  {risk.description}
                </p>

                {/* 缓解措施 */}
                {risk.mitigation && (
                  <div className="rounded-md bg-muted/50 px-3 py-2">
                    <p className="text-xs text-muted-foreground">
                      <span className="font-medium">
                        {L(t.approval.mitigation, locale)}
                      </span>
                      {risk.mitigation}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
