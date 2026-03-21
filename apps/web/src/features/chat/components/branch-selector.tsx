/**
 * 分支选择器组件 - 显示当前活跃分支，支持下拉切换
 *
 * 下拉列表显示所有分支名称和消息数量，
 * 当前活跃分支带有高亮标记。
 * 点击后调用 switch API 切换分支。
 */
"use client";

import { useState } from "react";
import { GitBranch, Check, Loader2, ChevronDown } from "lucide-react";
import { toast } from "sonner";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useBranches, useSwitchBranch } from "@/features/chat/api-branches";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { ApiError } from "@/lib/api-client/errors";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface BranchSelectorProps {
  conversationId: string;
  activeBranchId: string | null;
  onBranchSwitch: (branchId: string) => void;
}

export function BranchSelector({
  conversationId,
  activeBranchId,
  onBranchSwitch,
}: BranchSelectorProps) {
  const { locale } = useLocale();
  const { data: branches, isLoading } = useBranches(conversationId);
  const switchMutation = useSwitchBranch();
  const [open, setOpen] = useState(false);

  /**
   * 获取分支显示名称
   * 如果 branch_name 为空，显示"主分支"
   */
  function getBranchLabel(branchName: string | null, isFirst: boolean): string {
    if (branchName) return branchName;
    if (isFirst) return L(t.branches.mainBranch, locale);
    return "branch";
  }

  /**
   * 处理分支切换
   * 调用 switch API，成功后通知父组件
   */
  async function handleSwitch(branchId: string) {
    if (branchId === activeBranchId) {
      setOpen(false);
      return;
    }

    try {
      await switchMutation.mutateAsync({
        conversationId,
        branchId,
      });
      onBranchSwitch(branchId);
      setOpen(false);
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  // 当前活跃分支信息
  const activeBranch = branches?.find((b) => b.id === activeBranchId);
  const activeLabel = activeBranch
    ? getBranchLabel(activeBranch.branch_name, branches?.indexOf(activeBranch) === 0)
    : L(t.branches.mainBranch, locale);

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger
        render={
          <Button
            variant="outline"
            size="sm"
            disabled={isLoading || !branches}
          />
        }
      >
        {isLoading ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <GitBranch className="h-3.5 w-3.5" />
        )}
        <span className="max-w-[120px] truncate">{activeLabel}</span>
        <ChevronDown className="h-3 w-3 opacity-50" />
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" sideOffset={6}>
        <DropdownMenuLabel>
          {L(t.branches.selector, locale)}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {branches?.map((branch, idx) => {
          const isActive = branch.id === activeBranchId;
          const label = getBranchLabel(branch.branch_name, idx === 0);
          // 替换 {count} 占位符
          const countLabel = L(t.branches.messageCount, locale).replace(
            "{count}",
            String(branch.message_count)
          );

          return (
            <DropdownMenuItem
              key={branch.id}
              onClick={() => handleSwitch(branch.id)}
              className="flex items-center gap-2"
            >
              {/* 活跃标记 */}
              <span className="w-4 flex items-center justify-center shrink-0">
                {isActive && <Check className="h-3.5 w-3.5" />}
              </span>
              <div className="flex flex-col min-w-0">
                <span className="truncate text-sm">{label}</span>
                <span className="text-[10px] text-muted-foreground">
                  {countLabel}
                </span>
              </div>
              {/* 切换中的加载状态 */}
              {switchMutation.isPending &&
                switchMutation.variables?.branchId === branch.id && (
                  <Loader2 className="h-3 w-3 animate-spin ml-auto" />
                )}
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
