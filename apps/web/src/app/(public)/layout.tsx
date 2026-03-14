/**
 * 公开页面布局 - 登录/注册共享
 *
 * 已登录用户自动跳转到 /dashboard。
 * 右上角语言切换，不强制背景色和居中（由各页面自行控制）。
 */
"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Languages } from "lucide-react";
import { useLocale } from "@/i18n/context";
import { useAuthStore } from "@/stores/auth-store";

export default function PublicLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { accessToken } = useAuthStore();
  const { locale, toggleLocale } = useLocale();

  // 已登录用户自动跳转到仪表盘
  useEffect(() => {
    if (accessToken) {
      router.replace("/dashboard");
    }
  }, [accessToken, router]);

  return (
    <div className="relative">
      {/* 语言切换按钮 */}
      <div className="fixed top-10 right-10 z-30">
        <button
          onClick={toggleLocale}
          className="flex items-center gap-2 h-9 px-4 rounded-full border border-border bg-card text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <Languages size={14} />
          {locale === "zh" ? "EN" : "中文"}
        </button>
      </div>

      {children}
    </div>
  );
}
