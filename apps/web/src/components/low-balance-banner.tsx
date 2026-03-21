/**
 * 余额不足横幅通知组件
 *
 * 当用户 30 天内使用费用超过阈值时，在顶部显示提醒横幅。
 */
"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import { useSettingsStore } from "@/stores/settings-store";
import { useAuthStore } from "@/stores/auth-store";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";

/** 费用警告阈值（美元） */
const COST_WARNING_THRESHOLD = 50;

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

export function LowBalanceBanner() {
  const { locale } = useLocale();
  const { user } = useAuthStore();
  const { usageSummary, fetchUsageSummary } = useSettingsStore();
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (user) {
      fetchUsageSummary();
    }
  }, [user, fetchUsageSummary]);

  /** 没有用量数据、未达阈值或已关闭 → 不显示 */
  if (
    !usageSummary ||
    usageSummary.total_cost < COST_WARNING_THRESHOLD ||
    dismissed
  ) {
    return null;
  }

  return (
    <div className="bg-amber-50 dark:bg-amber-950/50 border-b border-amber-200 dark:border-amber-800 px-4 py-2">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-2 text-sm text-amber-800 dark:text-amber-200">
          <AlertTriangle size={16} />
          <span>
            {L(t.settings.usageWarning, locale)}{" "}
            <strong>${usageSummary.total_cost.toFixed(2)}</strong>
          </span>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="text-amber-600 hover:text-amber-800 dark:text-amber-400 dark:hover:text-amber-200"
        >
          <X size={16} />
        </button>
      </div>
    </div>
  );
}
