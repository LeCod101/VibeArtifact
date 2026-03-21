/**
 * 快照指示器组件 - 显示在消息气泡旁边，指示快照变更
 *
 * 当消息携带 snapshot_after 时，显示一个小标记图标。
 * 鼠标悬停时显示快照 ID 的 tooltip。
 * 设计保持简洁微妙，不抢消息内容的风头。
 */
"use client";

import { Camera } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface SnapshotIndicatorProps {
  snapshotBefore?: string | null;
  snapshotAfter?: string | null;
}

export function SnapshotIndicator({
  snapshotBefore,
  snapshotAfter,
}: SnapshotIndicatorProps) {
  const { locale } = useLocale();

  // 没有 snapshotAfter 时不显示
  if (!snapshotAfter) return null;

  // 截取快照 ID 前 8 位作为简短版本号
  const shortId = snapshotAfter.substring(0, 8);

  // 确定提示文本
  const tooltipText =
    snapshotBefore && snapshotAfter
      ? L(t.branches.snapshotUpdated, locale)
      : `Snapshot: ${snapshotAfter}`;

  return (
    <div
      className="inline-flex items-center gap-1 mt-1 px-1.5 py-0.5 rounded-md bg-muted/60 text-muted-foreground cursor-default group relative"
      title={tooltipText}
    >
      <Camera className="h-3 w-3" />
      <span className="text-[10px] font-mono">
        {shortId}
      </span>
    </div>
  );
}
