/**
 * 公开页面布局 - 登录/注册共享
 *
 * 深色背景居中卡片布局，右上角语言切换。
 * 已登录用户自动跳转到 /dashboard。
 */
"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Languages } from "lucide-react";
import { useLocale } from "@/i18n/context";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";

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
    <div className="min-h-screen bg-background flex flex-col items-center justify-center relative px-4">
      {/* 语言切换按钮 */}
      <div className="absolute top-6 right-6">
        <Button
          variant="outline"
          size="sm"
          onClick={toggleLocale}
          className="gap-2"
        >
          <Languages size={14} />
          {locale === "zh" ? "EN" : "中文"}
        </Button>
      </div>

      {children}
    </div>
  );
}
