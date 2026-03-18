/**
 * Artifact API Hooks - 产物相关的 React Query hooks
 *
 * 提供产物列表查询。
 */
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api-client";
import type { ArtifactResponse } from "@/lib/api-client/types";

/**
 * 获取项目的产物列表
 * @param projectId - 项目 UUID
 */
export function useArtifactsQuery(projectId: string) {
  return useQuery({
    queryKey: ["artifacts", projectId],
    queryFn: () =>
      apiGet<ArtifactResponse[]>(
        `/api/v1/projects/${projectId}/artifacts`,
      ),
    enabled: !!projectId,
  });
}
