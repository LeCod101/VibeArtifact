/**
 * 全权委托 React Query Hooks
 *
 * 提供全权委托运行的创建、查询、下载功能。
 * 使用 React Query 管理服务端状态与缓存。
 */
"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import {
  createDelegatedRun,
  getDelegatedRun,
  getDownloadUrl,
} from "@/features/delegation/api";
import type { DelegatedRunData } from "@/features/delegation/api";

/**
 * 创建全权委托运行 mutation
 *
 * POST 请求创建新的 delegated-run，返回 run_id。
 * 调用方可通过 onSuccess 回调获取 run_id 并跳转进度页。
 *
 * @param projectId - 项目 UUID
 */
export function useCreateDelegatedRun(projectId: string) {
  return useMutation({
    mutationFn: (snapshotId?: string) =>
      createDelegatedRun(projectId, snapshotId),
  });
}

/**
 * 查询全权委托运行状态
 *
 * GET 请求轮询运行详情，5 秒间隔。
 * 当运行完成（completed）或失败（failed）时停止轮询。
 *
 * @param projectId - 项目 UUID
 * @param runId - 运行 UUID（为空时禁用查询）
 */
export function useDelegatedRun(
  projectId: string,
  runId: string | null | undefined,
) {
  return useQuery<DelegatedRunData>({
    queryKey: ["delegated-run", projectId, runId],
    queryFn: () => getDelegatedRun(projectId, runId!),
    enabled: !!runId && !!projectId,
    // 5 秒轮询间隔
    refetchInterval: (query) => {
      const data = query.state.data;
      // 运行结束后停止轮询
      if (data?.status === "completed" || data?.status === "failed") {
        return false;
      }
      return 5000;
    },
  });
}

/**
 * 下载 ZIP 产物
 *
 * 构造带认证的下载链接并触发浏览器下载。
 * 使用 fetch + blob 方式，确保 Authorization header 被附加。
 *
 * @param projectId - 项目 UUID
 * @param runId - 运行 UUID
 * @returns 执行下载的异步函数
 */
export function useDownloadZip(projectId: string, runId: string) {
  const downloadUrl = getDownloadUrl(projectId, runId);

  async function download() {
    const token = useAuthStore.getState().accessToken;
    const headers: Record<string, string> = {};
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(downloadUrl, { headers });
    if (!res.ok) {
      throw new Error(`下载失败: HTTP ${res.status}`);
    }

    // 将响应转为 Blob 并触发下载
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `delegated-run-${runId}.zip`;
    document.body.appendChild(a);
    a.click();

    // 清理临时元素和 URL
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return { download, downloadUrl };
}
