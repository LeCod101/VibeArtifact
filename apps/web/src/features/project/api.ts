/**
 * Project API Hooks - 项目相关的 React Query hooks
 *
 * 提供项目列表、单个项目详情、创建项目的 query 和 mutation。
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/lib/api-client";
import type {
  CreateProjectRequest,
  ProjectResponse,
} from "@/lib/api-client/types";

/**
 * 获取项目列表
 */
export function useProjectsQuery() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => apiGet<ProjectResponse[]>("/api/v1/projects"),
  });
}

/**
 * 获取单个项目详情
 * @param id - 项目 UUID
 */
export function useProjectQuery(id: string) {
  return useQuery({
    queryKey: ["project", id],
    queryFn: () => apiGet<ProjectResponse>(`/api/v1/projects/${id}`),
    enabled: !!id,
  });
}

/**
 * 创建项目 mutation
 *
 * 创建成功后自动刷新项目列表缓存。
 */
export function useCreateProjectMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateProjectRequest) =>
      apiPost<ProjectResponse>("/api/v1/projects", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
