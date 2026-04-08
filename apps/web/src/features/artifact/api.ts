/**
 * Artifact API Hooks - v2 产物相关的 React Query hooks
 *
 * 对接 Phase 2：项目产物列表、单条详情、更新与版本历史。
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPut } from "@/lib/api-client";
import type {
  ArtifactResponseV2,
  ArtifactListItem,
  ArtifactVersionItem,
  UpdateArtifactRequest,
} from "@/lib/api-client/types";

/**
 * 获取项目的产物列表
 */
export function useArtifactsQuery(projectId: string) {
  return useQuery({
    queryKey: ["artifacts", projectId],
    queryFn: () =>
      apiGet<ArtifactListItem[]>(
        `/api/v1/projects/${projectId}/artifacts`
      ),
    enabled: !!projectId,
  });
}

/**
 * 获取单个产物详情
 */
export function useArtifactQuery(artifactId: string | null) {
  return useQuery({
    queryKey: ["artifact", artifactId],
    queryFn: () =>
      apiGet<ArtifactResponseV2>(`/api/v1/artifacts/${artifactId}`),
    enabled: !!artifactId,
  });
}

/**
 * 更新产物 mutation
 */
export function useUpdateArtifactMutation(artifactId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: UpdateArtifactRequest) =>
      apiPut<ArtifactResponseV2>(
        `/api/v1/artifacts/${artifactId}`,
        data
      ),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({
        queryKey: ["artifact", artifactId],
      });
      queryClient.invalidateQueries({
        queryKey: ["artifacts", updated.project_id],
      });
    },
  });
}

/**
 * 获取产物版本历史
 */
export function useArtifactVersionsQuery(artifactId: string | null) {
  return useQuery({
    queryKey: ["artifact-versions", artifactId],
    queryFn: () =>
      apiGet<ArtifactVersionItem[]>(
        `/api/v1/artifacts/${artifactId}/versions`
      ),
    enabled: !!artifactId,
  });
}
