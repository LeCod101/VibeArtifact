/**
 * 全权委托触发按钮
 *
 * 在 scope 确认后显示，点击创建 delegated-run 并跳转进度页。
 * 处理加载状态和 409 并发冲突错误提示。
 */
"use client";

import { useRouter } from "next/navigation";
import { Loader2, Rocket } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useCreateDelegatedRun } from "@/features/delegation/hooks/use-delegated";
import { ApiError } from "@/lib/api-client/errors";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";

interface DelegatedTriggerProps {
  /** 项目 UUID */
  projectId: string;
  /** 快照 ID（可选） */
  snapshotId?: string;
  /** 额外的 CSS 类名 */
  className?: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/**
 * 全权委托触发按钮组件
 *
 * 点击后调用 createDelegatedRun API，
 * 成功时跳转到 /projects/{id}/result?runId={runId}。
 * 409 冲突时提示"已有运行中的任务"。
 */
export function DelegatedTrigger({
  projectId,
  snapshotId,
  className,
}: DelegatedTriggerProps) {
  const router = useRouter();
  const { locale } = useLocale();
  const mutation = useCreateDelegatedRun(projectId);

  /** 处理点击事件 */
  function handleClick() {
    mutation.mutate(snapshotId, {
      onSuccess: (data) => {
        // 创建成功，跳转到结果/进度页
        router.push(
          `/projects/${projectId}/result?runId=${data.run_id}`,
        );
      },
    });
  }

  /**
   * 根据错误类型生成用户可读的提示信息
   */
  function getErrorMessage(): string | null {
    if (!mutation.error) return null;

    if (mutation.error instanceof ApiError) {
      // 409 并发冲突
      if (mutation.error.status === 409) {
        return L(t.delegation.conflictError, locale);
      }
      return mutation.error.detail;
    }
    return L(t.delegation.createError, locale);
  }

  const errorMessage = getErrorMessage();

  return (
    <div className={cn("space-y-3", className)}>
      <Button
        size="lg"
        onClick={handleClick}
        disabled={mutation.isPending}
        className="w-full gap-2"
      >
        {mutation.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Rocket className="h-4 w-4" />
        )}
        {mutation.isPending ? L(t.delegation.creating, locale) : L(t.delegation.startBtn, locale)}
      </Button>

      {/* 错误提示 */}
      {errorMessage && (
        <p className="text-sm text-red-600 bg-red-50 rounded-lg px-4 py-2">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
