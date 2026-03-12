/**
 * 路由保护组件 - 检查用户认证状态
 *
 * 功能：
 * - 未登录 → 重定向到 /login
 * - 已登录但 user 为空 → 自动获取 /users/me 填充
 * - 加载中显示骨架屏
 */
"use client";

import { useEffect, useMemo, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { useMeQuery } from "@/features/auth/api";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { accessToken, user } = useAuthStore();
  const { isLoading, isError } = useMeQuery();

  // 未登录或 token 失效时跳转到登录页
  useEffect(() => {
    if (!accessToken || isError) {
      router.replace("/login");
    }
  }, [accessToken, isError, router]);

  // 判断是否准备就绪：有 token 且有用户信息
  const isReady = useMemo(
    () => !!accessToken && !!user && !isLoading,
    [accessToken, user, isLoading]
  );

  // 加载中显示骨架屏
  if (!isReady) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-muted-foreground border-t-foreground" />
          <p className="text-sm text-muted-foreground">加载中...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
