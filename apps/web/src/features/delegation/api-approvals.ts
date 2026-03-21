/**
 * 审批 API 层
 *
 * 封装全权委托运行的审批查询和操作。
 * 与后端 /api/v1/projects/{projectId}/delegated-runs/{runId}/approvals 对接。
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/lib/api-client";
import type {
  ApprovalItemsResponse,
  ApprovalActionResponse,
  ApproveRequest,
  RejectRequest,
  AdjustRequest,
} from "@/lib/api-client/types";

/**
 * 获取待审批项
 *
 * 查询指定运行的风险、待决策和审批历史。
 * runId 为空时禁用查询。
 *
 * @param projectId - 项目 UUID
 * @param runId - 运行 UUID（为空时不请求）
 */
export function useApprovalItems(
  projectId: string,
  runId: string | undefined,
) {
  return useQuery<ApprovalItemsResponse>({
    queryKey: ["approval-items", projectId, runId],
    queryFn: () =>
      apiGet<ApprovalItemsResponse>(
        `/api/v1/projects/${projectId}/delegated-runs/${runId}/approvals`,
      ),
    enabled: !!projectId && !!runId,
    // 每 10 秒轮询一次（等待审批期间）
    refetchInterval: 10000,
  });
}

/**
 * 批准运行
 *
 * POST 请求批准当前运行，标记风险和决策为已接受。
 *
 * @param projectId - 项目 UUID
 */
export function useApproveRun(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation<ApprovalActionResponse, Error, { runId: string; reason?: string }>({
    mutationFn: ({ runId, reason }) => {
      const body: ApproveRequest = {};
      if (reason) {
        body.reason = reason;
      }
      return apiPost<ApprovalActionResponse>(
        `/api/v1/projects/${projectId}/delegated-runs/${runId}/approve`,
        body,
      );
    },
    onSuccess: (_data, variables) => {
      // 审批完成后刷新相关缓存
      queryClient.invalidateQueries({
        queryKey: ["approval-items", projectId, variables.runId],
      });
      queryClient.invalidateQueries({
        queryKey: ["delegated-run", projectId, variables.runId],
      });
    },
  });
}

/**
 * 拒绝运行
 *
 * POST 请求拒绝当前运行。
 *
 * @param projectId - 项目 UUID
 */
export function useRejectRun(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation<ApprovalActionResponse, Error, { runId: string; reason?: string }>({
    mutationFn: ({ runId, reason }) => {
      const body: RejectRequest = {};
      if (reason) {
        body.reason = reason;
      }
      return apiPost<ApprovalActionResponse>(
        `/api/v1/projects/${projectId}/delegated-runs/${runId}/reject`,
        body,
      );
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["approval-items", projectId, variables.runId],
      });
      queryClient.invalidateQueries({
        queryKey: ["delegated-run", projectId, variables.runId],
      });
    },
  });
}

/**
 * 调整运行
 *
 * POST 请求要求调整当前运行，需提供反馈内容。
 *
 * @param projectId - 项目 UUID
 */
export function useAdjustRun(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation<ApprovalActionResponse, Error, { runId: string; feedback: string; reason?: string }>({
    mutationFn: ({ runId, feedback, reason }) => {
      const body: AdjustRequest = { feedback };
      if (reason) {
        body.reason = reason;
      }
      return apiPost<ApprovalActionResponse>(
        `/api/v1/projects/${projectId}/delegated-runs/${runId}/adjust`,
        body,
      );
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["approval-items", projectId, variables.runId],
      });
      queryClient.invalidateQueries({
        queryKey: ["delegated-run", projectId, variables.runId],
      });
    },
  });
}
