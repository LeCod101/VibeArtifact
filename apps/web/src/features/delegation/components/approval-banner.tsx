/**
 * 审批横幅组件
 *
 * 在委托结果页顶部显示，提示用户当前运行需要审批。
 * 包含批准、拒绝、调整三个操作按钮。
 */
"use client";

import { AlertTriangle, Check, X, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface ApprovalBannerProps {
  /** 是否需要审批 */
  requiresApproval: boolean;
  /** 高风险项数量 */
  riskCount: number;
  /** 待决策项数量 */
  decisionCount: number;
  /** 点击批准回调 */
  onApprove: () => void;
  /** 点击拒绝回调 */
  onReject: () => void;
  /** 点击调整回调 */
  onAdjust: () => void;
  /** 是否正在执行操作 */
  isLoading?: boolean;
}

/**
 * 审批横幅组件
 *
 * 当运行需要审批时显示琥珀色横幅，包含风险和决策数量统计，
 * 以及批准（绿色）、拒绝（红色）、调整（灰色）三个操作按钮。
 * 不需要审批时不渲染任何内容。
 */
export function ApprovalBanner({
  requiresApproval,
  riskCount,
  decisionCount,
  onApprove,
  onReject,
  onAdjust,
  isLoading = false,
}: ApprovalBannerProps) {
  const { locale } = useLocale();

  // 不需要审批时不显示
  if (!requiresApproval) {
    return null;
  }

  /**
   * 构建统计描述文本
   */
  function buildDescription(): string {
    const parts: string[] = [];
    if (riskCount > 0) {
      parts.push(
        L(t.approval.riskCount, locale).replace("{count}", String(riskCount)),
      );
    }
    if (decisionCount > 0) {
      parts.push(
        L(t.approval.decisionCount, locale).replace(
          "{count}",
          String(decisionCount),
        ),
      );
    }
    if (parts.length === 0) {
      return "";
    }
    return `（${parts.join(", ")}）`;
  }

  return (
    <div className="rounded-lg border border-amber-300 bg-amber-50 px-5 py-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        {/* 左侧：提示信息 */}
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-amber-800">
              {L(t.approval.requiresApproval, locale)}
            </p>
            <p className="text-xs text-amber-700 mt-0.5">
              {buildDescription()}
            </p>
          </div>
        </div>

        {/* 右侧：操作按钮 */}
        <div className="flex items-center gap-2 shrink-0">
          {/* 批准按钮 */}
          <Button
            size="sm"
            onClick={onApprove}
            disabled={isLoading}
            className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            <Check className="h-3.5 w-3.5" />
            {L(t.approval.approve, locale)}
          </Button>

          {/* 拒绝按钮 */}
          <Button
            size="sm"
            variant="outline"
            onClick={onReject}
            disabled={isLoading}
            className="gap-1.5 border-red-300 text-red-600 hover:bg-red-50 hover:text-red-700"
          >
            <X className="h-3.5 w-3.5" />
            {L(t.approval.reject, locale)}
          </Button>

          {/* 调整按钮 */}
          <Button
            size="sm"
            variant="outline"
            onClick={onAdjust}
            disabled={isLoading}
            className="gap-1.5"
          >
            <MessageSquare className="h-3.5 w-3.5" />
            {L(t.approval.adjust, locale)}
          </Button>
        </div>
      </div>
    </div>
  );
}
