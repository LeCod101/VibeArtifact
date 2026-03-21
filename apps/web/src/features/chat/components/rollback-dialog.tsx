/**
 * 回滚对话框组件 - 确认回滚操作
 *
 * 向用户警告回滚会创建新分支，
 * 显示目标快照信息，提供确认/取消按钮。
 * 回滚完成后显示操作结果（no_change/forked/switched）。
 */
"use client";

import { useState } from "react";
import { AlertTriangle, Loader2, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useRollback } from "@/features/chat/api-branches";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { ApiError } from "@/lib/api-client/errors";
import type { RollbackResponse } from "@/lib/api-client/types";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface RollbackDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  conversationId: string;
  snapshotId: string;
  onRollbackComplete: (result: RollbackResponse) => void;
}

export function RollbackDialog({
  open,
  onOpenChange,
  conversationId,
  snapshotId,
  onRollbackComplete,
}: RollbackDialogProps) {
  const { locale } = useLocale();
  const rollbackMutation = useRollback();
  const [result, setResult] = useState<RollbackResponse | null>(null);

  /**
   * 获取回滚结果的提示文本
   * 根据 action 类型返回对应的多语言文案
   */
  function getResultMessage(action: string): string {
    switch (action) {
      case "no_change":
        return L(t.branches.noChange, locale);
      case "forked":
        return L(t.branches.forked, locale);
      case "switched":
        return L(t.branches.switched, locale);
      default:
        return L(t.branches.rollbackSuccess, locale);
    }
  }

  /** 执行回滚操作 */
  async function handleRollback() {
    try {
      const res = await rollbackMutation.mutateAsync({
        conversationId,
        snapshotId,
      });
      setResult(res);
      toast.success(getResultMessage(res.action));
      onRollbackComplete(res);
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  /** 关闭对话框时重置状态 */
  function handleOpenChange(nextOpen: boolean) {
    if (!nextOpen) {
      setResult(null);
    }
    onOpenChange(nextOpen);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {L(t.branches.rollback, locale)}
          </DialogTitle>
          <DialogDescription>
            {result ? (
              <span className="flex items-center gap-2 mt-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                {getResultMessage(result.action)}
              </span>
            ) : (
              <>
                <span className="flex items-start gap-2 mt-2">
                  <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                  <span>{L(t.branches.rollbackConfirm, locale)}</span>
                </span>
                {/* 目标快照信息 */}
                <span className="block mt-3 text-xs font-mono bg-muted rounded-md px-3 py-2">
                  Snapshot: {snapshotId.substring(0, 12)}...
                </span>
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        <DialogFooter>
          {result ? (
            <Button
              variant="outline"
              onClick={() => handleOpenChange(false)}
            >
              {L(t.common.confirm, locale)}
            </Button>
          ) : (
            <>
              <Button
                variant="outline"
                onClick={() => handleOpenChange(false)}
                disabled={rollbackMutation.isPending}
              >
                {L(t.common.cancel, locale)}
              </Button>
              <Button
                onClick={handleRollback}
                disabled={rollbackMutation.isPending}
              >
                {rollbackMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1.5" />
                ) : null}
                {L(t.branches.rollback, locale)}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
