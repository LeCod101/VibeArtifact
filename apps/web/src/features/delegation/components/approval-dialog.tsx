/**
 * 审批对话框组件
 *
 * 通用的确认对话框，用于 approve / reject / adjust 三种审批操作。
 * approve：可选填理由；reject：必填理由；adjust：必填调整反馈。
 */
"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 审批操作类型 */
type ApprovalAction = "approve" | "reject" | "adjust";

interface ApprovalDialogProps {
  /** 对话框是否打开 */
  open: boolean;
  /** 控制对话框开关 */
  onOpenChange: (open: boolean) => void;
  /** 审批操作类型 */
  action: ApprovalAction;
  /** 确认回调，传递理由和/或反馈 */
  onConfirm: (reason?: string, feedback?: string) => void;
  /** 是否正在执行 */
  isLoading?: boolean;
}

/**
 * 根据操作类型返回对话框标题
 */
function getTitle(action: ApprovalAction, locale: Locale): string {
  switch (action) {
    case "approve":
      return L(t.approval.approve, locale);
    case "reject":
      return L(t.approval.reject, locale);
    case "adjust":
      return L(t.approval.adjust, locale);
  }
}

/**
 * 根据操作类型返回描述文本
 */
function getDescription(action: ApprovalAction, locale: Locale): string {
  switch (action) {
    case "approve":
      return L(t.approval.approveConfirm, locale);
    case "reject":
      return L(t.approval.rejectConfirm, locale);
    case "adjust":
      return L(t.approval.adjustPrompt, locale);
  }
}

/**
 * 根据操作类型返回确认按钮样式
 */
function getButtonStyle(action: ApprovalAction): string {
  switch (action) {
    case "approve":
      return "bg-emerald-600 hover:bg-emerald-700 text-white";
    case "reject":
      return "bg-red-600 hover:bg-red-700 text-white";
    case "adjust":
      return "";
  }
}

/**
 * 审批对话框组件
 *
 * 根据操作类型（approve/reject/adjust）展示不同的表单内容：
 * - approve：确认提示 + 可选理由
 * - reject：确认提示 + 必填理由
 * - adjust：提示 + 必填调整反馈
 */
export function ApprovalDialog({
  open,
  onOpenChange,
  action,
  onConfirm,
  isLoading = false,
}: ApprovalDialogProps) {
  const { locale } = useLocale();
  const [reason, setReason] = useState("");
  const [feedback, setFeedback] = useState("");

  /**
   * 判断确认按钮是否可用
   * reject 需要填写理由，adjust 需要填写反馈
   */
  function canConfirm(): boolean {
    if (action === "reject" && !reason.trim()) return false;
    if (action === "adjust" && !feedback.trim()) return false;
    return true;
  }

  /**
   * 处理确认操作
   */
  function handleConfirm() {
    if (action === "adjust") {
      onConfirm(reason.trim() || undefined, feedback.trim());
    } else {
      onConfirm(reason.trim() || undefined);
    }
    // 重置表单
    setReason("");
    setFeedback("");
  }

  /**
   * 处理对话框关闭
   */
  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      // 关闭时重置表单
      setReason("");
      setFeedback("");
    }
    onOpenChange(nextOpen);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{getTitle(action, locale)}</DialogTitle>
          <DialogDescription>{getDescription(action, locale)}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* adjust 模式：反馈输入框 */}
          {action === "adjust" && (
            <div className="space-y-2">
              <Label htmlFor="approval-feedback">
                {L(t.approval.feedback, locale)}
              </Label>
              <Textarea
                id="approval-feedback"
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder={L(t.approval.adjustPrompt, locale)}
                rows={4}
                className="resize-none"
              />
            </div>
          )}

          {/* 理由输入框（approve 可选，reject 必填，adjust 可选） */}
          <div className="space-y-2">
            <Label htmlFor="approval-reason">
              {action === "reject"
                ? L(t.approval.reason, locale).replace(
                    /（可选）|optional/i,
                    "",
                  )
                : L(t.approval.reason, locale)}
            </Label>
            <Textarea
              id="approval-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={L(t.approval.reason, locale)}
              rows={2}
              className="resize-none"
            />
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isLoading}
          >
            {L(t.common.cancel, locale)}
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!canConfirm() || isLoading}
            className={getButtonStyle(action)}
          >
            {isLoading && <Loader2 className="h-4 w-4 animate-spin mr-1.5" />}
            {L(t.common.confirm, locale)}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
