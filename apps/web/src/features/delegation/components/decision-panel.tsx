/**
 * 决策面板组件
 *
 * 展示全权委托运行中的待决策节点列表。
 * 每个决策包含标题、描述、状态标签和备选方案。
 */
"use client";

import { CircleDot, ListChecks } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import type { DecisionItem } from "@/lib/api-client/types";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface DecisionPanelProps {
  /** 待决策列表 */
  decisions: DecisionItem[];
}

/**
 * 根据决策状态返回 Badge 样式
 */
function statusStyle(status: string): string {
  switch (status.toUpperCase()) {
    case "PENDING":
      return "bg-amber-100 text-amber-700 border-amber-200";
    case "ACCEPTED":
      return "bg-emerald-100 text-emerald-700 border-emerald-200";
    case "REJECTED":
      return "bg-red-100 text-red-700 border-red-200";
    default:
      return "bg-gray-100 text-gray-700 border-gray-200";
  }
}

/**
 * 决策状态中文标签
 */
function statusLabel(status: string): string {
  switch (status.toUpperCase()) {
    case "PENDING":
      return "待确认";
    case "ACCEPTED":
      return "已接受";
    case "REJECTED":
      return "已拒绝";
    default:
      return status;
  }
}

/**
 * 决策面板组件
 *
 * 显示待决策节点列表，包含标题、描述、状态标签和备选方案。
 * 空列表时显示"暂无待决策项"。
 */
export function DecisionPanel({ decisions }: DecisionPanelProps) {
  const { locale } = useLocale();

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <ListChecks className="h-4 w-4 text-amber-500" />
          {L(t.approval.decisionTitle, locale)}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {decisions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <CircleDot className="h-8 w-8 text-muted-foreground/30 mb-2" />
            <p className="text-sm text-muted-foreground">
              {L(t.approval.noDecisions, locale)}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {decisions.map((decision) => (
              <div
                key={decision.id}
                className="rounded-lg border border-border p-4 space-y-2"
              >
                {/* 标题行 */}
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-semibold">{decision.title}</h4>
                  <Badge
                    variant="outline"
                    className={`shrink-0 ${statusStyle(decision.status)}`}
                  >
                    {statusLabel(decision.status)}
                  </Badge>
                </div>

                {/* 描述 */}
                <p className="text-sm text-muted-foreground">
                  {decision.description}
                </p>

                {/* 备选方案 */}
                {decision.alternatives && decision.alternatives.length > 0 && (
                  <div className="space-y-1">
                    <p className="text-xs font-medium text-muted-foreground">
                      {L(t.approval.alternatives, locale)}
                    </p>
                    <ul className="space-y-1">
                      {decision.alternatives.map((alt, idx) => (
                        <li
                          key={idx}
                          className="flex items-start gap-2 text-xs text-muted-foreground"
                        >
                          <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-muted-foreground/40 shrink-0" />
                          {alt}
                        </li>
                      ))}
                    </ul>
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
