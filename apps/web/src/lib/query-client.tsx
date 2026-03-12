/**
 * TanStack Query Provider - 客户端组件
 *
 * 为整个应用提供 React Query 的查询缓存和状态管理。
 */
"use client";

import { useState, type ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            /** 窗口聚焦时不自动重新获取 */
            refetchOnWindowFocus: false,
            /** 默认重试 1 次 */
            retry: 1,
            /** 数据 5 分钟内视为新鲜 */
            staleTime: 5 * 60 * 1000,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
