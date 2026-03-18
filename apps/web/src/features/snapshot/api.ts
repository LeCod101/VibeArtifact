/**
 * Snapshot API Hooks - 快照相关的 React Query hooks
 *
 * 提供快照列表查询。
 */
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api-client";
import type { SnapshotResponse } from "@/lib/api-client/types";

/**
 * 获取项目的快照列表
 * @param projectId - 项目 UUID
 */
export function useSnapshotsQuery(projectId: string) {
  return useQuery({
    queryKey: ["snapshots", projectId],
    queryFn: () =>
      apiGet<SnapshotResponse[]>(
        `/api/v1/projects/${projectId}/snapshots`,
      ),
    enabled: !!projectId,
  });
}
