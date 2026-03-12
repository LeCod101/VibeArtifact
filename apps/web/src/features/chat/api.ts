/**
 * Chat API Hooks - 对话和消息相关的 React Query hooks
 *
 * 提供对话列表、创建对话、消息列表、发送消息的 query 和 mutation。
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/lib/api-client";
import type {
  CreateConversationRequest,
  ConversationResponse,
  SaveMessageRequest,
  MessageResponse,
} from "@/lib/api-client/types";

/**
 * 获取项目下的对话列表
 * @param projectId - 项目 UUID
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
 * 创建对话 mutation
 *
 * 创建成功后自动刷新对话列表缓存。
 * @param projectId - 项目 UUID
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
 * 获取对话下的消息列表
 * @param conversationId - 对话 UUID
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

/**
 * 发送消息 mutation
 *
 * 发送成功后自动刷新消息列表缓存。
 * @param conversationId - 对话 UUID
 */
export function useSendMessageMutation(conversationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SaveMessageRequest) =>
      apiPost<MessageResponse>(
        `/api/v1/conversations/${conversationId}/messages`,
        data
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["messages", conversationId],
      });
    },
  });
}
