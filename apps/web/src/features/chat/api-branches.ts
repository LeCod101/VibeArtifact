/**
 * 分支 API Hooks - 分支管理相关的 React Query hooks
 *
 * 提供分支列表、分支树、创建分支、切换分支、fork 分支、回滚的 query 和 mutation。
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/lib/api-client";
import type {
  BranchResponse,
  BranchTreeNode,
  CreateBranchRequest,
  ForkBranchRequest,
  RollbackResponse,
} from "@/lib/api-client/types";

/**
 * 获取分支列表
 * @param conversationId - 对话 UUID
 */
export function useBranches(conversationId: string | undefined) {
  return useQuery({
    queryKey: ["branches", conversationId],
    queryFn: () =>
      apiGet<BranchResponse[]>(
        `/api/v1/conversations/${conversationId}/branches`
      ),
    enabled: !!conversationId,
  });
}

/**
 * 获取分支树
 * @param conversationId - 对话 UUID
 */
export function useBranchTree(conversationId: string | undefined) {
  return useQuery({
    queryKey: ["branchTree", conversationId],
    queryFn: () =>
      apiGet<BranchTreeNode[]>(
        `/api/v1/conversations/${conversationId}/branches/tree`
      ),
    enabled: !!conversationId,
  });
}

/**
 * 创建分支 mutation
 *
 * 创建成功后自动刷新分支列表和分支树缓存。
 */
export function useCreateBranch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      conversationId,
      data,
    }: {
      conversationId: string;
      data: CreateBranchRequest;
    }) =>
      apiPost<BranchResponse>(
        `/api/v1/conversations/${conversationId}/branches`,
        data
      ),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["branches", variables.conversationId],
      });
      queryClient.invalidateQueries({
        queryKey: ["branchTree", variables.conversationId],
      });
    },
  });
}

/**
 * 切换分支 mutation
 *
 * 切换成功后刷新分支列表、消息列表和对话缓存。
 */
export function useSwitchBranch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      conversationId,
      branchId,
    }: {
      conversationId: string;
      branchId: string;
    }) =>
      apiPost<BranchResponse>(
        `/api/v1/conversations/${conversationId}/branches/${branchId}/switch`
      ),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["branches", variables.conversationId],
      });
      queryClient.invalidateQueries({
        queryKey: ["messages", variables.conversationId],
      });
      queryClient.invalidateQueries({
        queryKey: ["conversations"],
      });
    },
  });
}

/**
 * Fork 分支 mutation
 *
 * 从指定快照点 fork 新分支，成功后刷新分支缓存。
 */
export function useForkBranch() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      conversationId,
      branchId,
      data,
    }: {
      conversationId: string;
      branchId: string;
      data: ForkBranchRequest;
    }) =>
      apiPost<BranchResponse>(
        `/api/v1/conversations/${conversationId}/branches/${branchId}/fork`,
        data
      ),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["branches", variables.conversationId],
      });
      queryClient.invalidateQueries({
        queryKey: ["branchTree", variables.conversationId],
      });
    },
  });
}

/**
 * 回滚到快照 mutation
 *
 * 回滚成功后刷新分支列表、消息列表和对话缓存。
 */
export function useRollback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      conversationId,
      snapshotId,
    }: {
      conversationId: string;
      snapshotId: string;
    }) =>
      apiPost<RollbackResponse>(
        `/api/v1/conversations/${conversationId}/rollback`,
        { snapshot_id: snapshotId }
      ),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["branches", variables.conversationId],
      });
      queryClient.invalidateQueries({
        queryKey: ["branchTree", variables.conversationId],
      });
      queryClient.invalidateQueries({
        queryKey: ["messages", variables.conversationId],
      });
      queryClient.invalidateQueries({
        queryKey: ["conversations"],
      });
    },
  });
}
