/**
 * 变更摘要卡片组件
 *
 * 显示在助手消息下方，展示本次对话处理的变更摘要信息。
 * 包含：摘要文本、影响范围、执行的 Agent、操作数量、警告信息。
 *
 * 使用 shadcn/ui Card + Badge 组件，暖色调紧凑布局。
 */
"use client";

import { AlertTriangle, Layers, Bot, Hash } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ChangeSummaryResponse } from "@/lib/api-client/types";

interface ChangeSummaryProps {
  /** 变更摘要数据 */
  summary: ChangeSummaryResponse;
  /** 额外的 CSS 类名 */
  className?: string;
}

/**
 * 变更摘要卡片
 *
 * 紧凑展示对话模式下 AI 处理的变更摘要。
 * 影响范围和执行 Agent 使用 Badge 展示，警告信息使用黄色背景。
 */
export function ChangeSummary({ summary, className }: ChangeSummaryProps) {
  return (
    <Card
      className={cn(
        "border-orange-200/60 bg-orange-50/30 dark:border-orange-900/40 dark:bg-orange-950/20",
        className
      )}
    >
      <CardContent className="px-4 py-3 space-y-2.5">
        {/* 标题行 */}
        <p className="text-xs font-medium text-orange-700 dark:text-orange-400">
          变更摘要
        </p>

        {/* 摘要正文 */}
        <p className="text-sm text-foreground leading-relaxed">
          {summary.summary}
        </p>

        {/* 信息指标区 */}
        <div className="space-y-1.5 text-xs text-muted-foreground">
          {/* 影响范围 */}
          {summary.affected_areas.length > 0 && (
            <div className="flex items-start gap-2">
              <Layers className="h-3.5 w-3.5 mt-0.5 shrink-0 text-orange-500" />
              <div className="flex flex-wrap gap-1">
                {summary.affected_areas.map((area) => (
                  <Badge
                    key={area}
                    variant="secondary"
                    className="text-[10px] h-4 px-1.5"
                  >
                    {area}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 执行 Agent */}
          {summary.agents_executed.length > 0 && (
            <div className="flex items-start gap-2">
              <Bot className="h-3.5 w-3.5 mt-0.5 shrink-0 text-orange-500" />
              <div className="flex flex-wrap gap-1">
                {summary.agents_executed.map((agent) => (
                  <Badge
                    key={agent}
                    variant="outline"
                    className="text-[10px] h-4 px-1.5"
                  >
                    {agent}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 操作数量 */}
          <div className="flex items-center gap-2">
            <Hash className="h-3.5 w-3.5 shrink-0 text-orange-500" />
            <span>{summary.operations_count} 项操作</span>
          </div>
        </div>

        {/* 警告信息 */}
        {summary.warnings.length > 0 && (
          <div className="rounded-md bg-amber-100/80 dark:bg-amber-900/30 px-3 py-2 space-y-1">
            {summary.warnings.map((warning, idx) => (
              <div key={idx} className="flex items-start gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-amber-600 dark:text-amber-400" />
                <p className="text-xs text-amber-800 dark:text-amber-300">
                  {warning}
                </p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
