/**
 * Project API Hooks - 项目相关的 React Query hooks
 *
 * 提供项目列表、单个项目详情、创建项目的 query 和 mutation。
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiPut, apiDelete } from "@/lib/api-client";
import type {
  CreateProjectRequest,
  UpdateProjectRequest,
  ProjectResponse,
} from "@/lib/api-client/types";

/**
 * 获取项目列表
 * @param projectType - 可选，按 project_type 筛选
 */
export function useProjectsQuery(projectType?: string) {
  const params = projectType ? `?project_type=${encodeURIComponent(projectType)}` : "";
  return useQuery({
    queryKey: ["projects", projectType],
    queryFn: () =>
      apiGet<ProjectResponse[]>(`/api/v1/projects${params}`),
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

/**
 * 更新项目 mutation
 *
 * 更新成功后自动刷新项目详情和列表缓存。
 * @param projectId - 项目 UUID
 */
export function useUpdateProjectMutation(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateProjectRequest) =>
      apiPut<ProjectResponse>(`/api/v1/projects/${projectId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

/**
 * 删除项目 mutation
 *
 * 删除成功后自动刷新项目列表缓存。
 */
export function useDeleteProjectMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) =>
      apiDelete<void>(`/api/v1/projects/${projectId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
