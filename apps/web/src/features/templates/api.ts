/**
 * 模板相关 API 类型定义和 React Query hooks
 *
 * 提供模板列表、详情、从模板创建项目的 query 和 mutation。
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/lib/api-client";

/** 模板列表响应 */
export interface TemplateResponse {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string | null;
  is_public: boolean;
  created_at: string;
}

/** 模板详情响应（含 snapshot_data） */
export interface TemplateDetailResponse extends TemplateResponse {
  snapshot_data: Record<string, unknown>;
}

/** 从模板创建项目请求 */
export interface CreateFromTemplateRequest {
  template_id: string;
  project_name: string;
}

/** 从模板创建项目响应 */
export interface CreateFromTemplateResponse {
  project_id: string;
  snapshot_id: string;
  message: string;
}

/**
 * 获取模板列表
 * @param category - 可选的类别过滤
 */
export function useTemplatesQuery(category?: string) {
  const params = category ? `?category=${category}` : "";
  return useQuery({
    queryKey: ["templates", category],
    queryFn: () =>
      apiGet<TemplateResponse[]>(`/api/v1/templates${params}`),
  });
}

/**
 * 获取模板详情
 * @param id - 模板 UUID
 */
export function useTemplateDetailQuery(id: string) {
  return useQuery({
    queryKey: ["template", id],
    queryFn: () =>
      apiGet<TemplateDetailResponse>(`/api/v1/templates/${id}`),
    enabled: !!id,
  });
}

/**
 * 从模板创建项目 mutation
 *
 * 创建成功后自动刷新项目列表缓存。
 */
export function useCreateFromTemplateMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateFromTemplateRequest) =>
      apiPost<CreateFromTemplateResponse>(
        "/api/v1/projects/from-template",
        data
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
