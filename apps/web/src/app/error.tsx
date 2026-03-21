/**
 * 全局错误边界 - 页面加载异常时的降级 UI
 *
 * Next.js 要求此文件为客户端组件。
 * 提供"重试"和"返回首页"两个操作按钮。
 */
"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorPageProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    console.error("[ErrorBoundary]", error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      {/* 图标 */}
      <div className="flex items-center justify-center w-16 h-16 rounded-full bg-destructive/10 mb-6">
        <AlertTriangle size={28} className="text-destructive" />
      </div>

      {/* 标题 */}
      <h1 className="text-xl md:text-2xl font-bold text-foreground">
        出了点问题
      </h1>

      {/* 描述 */}
      <p className="mt-2 text-sm text-muted-foreground text-center max-w-md">
        页面加载时发生了错误
      </p>

      {/* 操作按钮 */}
      <div className="mt-8 flex items-center gap-3">
        <Button onClick={reset} variant="default" className="gap-2">
          <RotateCcw size={14} />
          重试
        </Button>
        <Link href="/dashboard">
          <Button variant="outline">
            返回首页
          </Button>
        </Link>
      </div>
    </div>
  );
}
