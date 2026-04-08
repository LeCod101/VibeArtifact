/**
 * Chat API Hooks - v2 对话相关的 React Query hooks
 *
 * 对接 Phase 2：列表/创建对话与拉取历史消息；发送消息由 SSE（use-agent-sse 等）完成。
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/lib/api-client";
import type {
  CreateConversationRequest,
  ConversationResponse,
  MessageResponse,
} from "@/lib/api-client/types";

/**
 * 获取项目下的对话列表
 */
export function useConversationsQuery(projectId: string) {
  return useQuery({
    queryKey: ["conversations", projectId],
    queryFn: () =>
      apiGet<ConversationResponse[]>(
        `/api/v1/projects/${projectId}/conversations`
      ),
    enabled: !!projectId,
  });
}

/**
 * 创建对话 mutation（成功后刷新该项目下的对话列表）
 */
export function useCreateConversationMutation(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateConversationRequest) =>
      apiPost<ConversationResponse>(
        `/api/v1/projects/${projectId}/conversations`,
        data
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["conversations", projectId],
      });
    },
  });
}

/**
 * 获取对话消息列表
 */
export function useMessagesQuery(conversationId: string | null) {
  return useQuery({
    queryKey: ["messages", conversationId],
    queryFn: () =>
      apiGet<MessageResponse[]>(
        `/api/v1/conversations/${conversationId}/messages`
      ),
    enabled: !!conversationId,
  });
}
