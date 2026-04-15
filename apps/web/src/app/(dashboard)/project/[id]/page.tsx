/**
 * 项目工作区 - Anything Builder 风格三栏布局
 *
 * 顶栏 + 左栏（对话/产物）+ 中间消息 + 右侧产物预览；SSE 发送后刷新消息与产物缓存。
 */
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Download,
  FileCode2,
  Loader2,
  MessageCircle,
  MessageSquare,
  PanelRightClose,
  PanelRightOpen,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useProjectQuery } from "@/features/project/api";
import {
  useConversationsQuery,
  useCreateConversationMutation,
  useMessagesQuery,
} from "@/features/chat/api";
import {
  useArtifactsQuery,
  useArtifactQuery,
  useCodeArtifactsQuery,
} from "@/features/artifact/api";
import { useAgentSSE } from "@/features/chat/hooks/use-agent-sse";
import { ConversationList } from "@/features/chat/components/conversation-list";
import { MessageThread } from "@/features/chat/components/message-thread";
import { MessageInput } from "@/features/chat/components/message-input";
import { StreamingMessage } from "@/features/chat/components/streaming-message";
import { WorkspaceWelcome } from "@/features/chat/components/workspace-welcome";
import { ArtifactPanel } from "@/features/artifact/components/artifact-panel";
import { ArtifactList } from "@/features/artifact/components/artifact-list";
import { Button } from "@/components/ui/button";
import type { AgentMode } from "@/lib/api-client/types";

/** 顶栏可选 Agent 模式（讨论模式带图标，便于识别） */
const MODES: { value: AgentMode; label: string; isDiscussion?: boolean }[] = [
  { value: "auto", label: "Auto" },
  { value: "discussion", label: "Discussion", isDiscussion: true },
  { value: "thinking", label: "Thinking" },
];

export default function ProjectWorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const queryClient = useQueryClient();

  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(
    null,
  );
  const [mode, setMode] = useState<AgentMode>("auto");
  const [sidebarTab, setSidebarTab] = useState<"conversations" | "artifacts">(
    "conversations",
  );
  const [rightPanelOpen, setRightPanelOpen] = useState(true);

  const { data: project, isLoading: projectLoading } =
    useProjectQuery(projectId);
  const { data: conversations, isLoading: convsLoading } =
    useConversationsQuery(projectId);
  const { data: messages, isLoading: msgsLoading } =
    useMessagesQuery(selectedConvId);
  const { data: artifacts, isLoading: artifactsLoading } =
    useArtifactsQuery(projectId);
  const { data: selectedArtifact } = useArtifactQuery(selectedArtifactId);
  // 获取项目所有 code 类型产物（含 content），供 WebContainer 项目级预览使用
  const { data: codeArtifacts } = useCodeArtifactsQuery(projectId);
  const createConvMutation = useCreateConversationMutation(projectId);

  const sse = useAgentSSE(projectId);

  /** 消息区与流式区共用滚动容器，锚点置于最底部 */
  const threadBottomRef = useRef<HTMLDivElement>(null);

  // 历史消息或流式内容变化时滚到底部
  useEffect(() => {
    threadBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [
    messages,
    sse.isStreaming,
    sse.contentText,
    sse.thinkingText,
    sse.activeToolCalls.length,
    sse.completedToolCalls.length,
    msgsLoading,
  ]);

  // 有对话列表时默认选中第一条
  useEffect(() => {
    if (conversations && conversations.length > 0 && !selectedConvId) {
      setSelectedConvId(conversations[0].id);
    }
  }, [conversations, selectedConvId]);

  // SSE 错误提示
  useEffect(() => {
    if (sse.error) {
      toast.error(sse.error);
    }
  }, [sse.error]);

  // 讨论模式：专注对话，自动关闭右侧产物预览
  useEffect(() => {
    if (mode === "discussion") {
      setRightPanelOpen(false);
    }
  }, [mode]);

  // 讨论模式：不允许停留在产物侧栏 Tab
  useEffect(() => {
    if (mode === "discussion" && sidebarTab === "artifacts") {
      setSidebarTab("conversations");
    }
  }, [mode, sidebarTab]);

  const handleSendMessage = useCallback(
    async (content: string) => {
      let convId = selectedConvId;

      if (!convId) {
        try {
          const conv = await createConvMutation.mutateAsync({
            title: content.slice(0, 50),
          });
          convId = conv.id;
          setSelectedConvId(conv.id);
        } catch {
          toast.error("创建对话失败，请重试");
          return;
        }
      }

      await sse.sendMessage(content, mode, convId);

      // 仅在流未出错时刷新缓存
      if (!sse.error) {
        await queryClient.invalidateQueries({ queryKey: ["messages", convId] });
        await queryClient.invalidateQueries({
          queryKey: ["artifacts", projectId],
        });
        await queryClient.invalidateQueries({
          queryKey: ["conversations", projectId],
        });
      }
    },
    [
      selectedConvId,
      mode,
      sse,
      createConvMutation,
      queryClient,
      projectId,
    ],
  );

  const handleCreateConversation = useCallback(async () => {
    try {
      const conv = await createConvMutation.mutateAsync({ title: "新对话" });
      setSelectedConvId(conv.id);
      setSidebarTab("conversations");
    } catch {
      toast.error("创建对话失败");
    }
  }, [createConvMutation]);

  if (projectLoading) {
    return (
      <div className="flex flex-1 items-center justify-center min-h-[50vh]">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const messagePlaceholder =
    mode === "auto"
      ? "输入消息..."
      : mode === "discussion"
        ? "讨论模式 — 仅对话，不生成代码..."
        : "深度思考模式...";

  const showWelcome =
    (!messages || messages.length === 0) &&
    !sse.isStreaming &&
    !msgsLoading;

  return (
    <div className="flex flex-1 flex-col min-h-0 h-[calc(100vh-theme(spacing.14)-theme(spacing.12))] lg:h-[calc(100vh-theme(spacing.12))] bg-background overflow-hidden">
      <header className="flex items-center justify-between h-12 px-4 border-b border-border shrink-0 gap-2">
        <div className="flex items-center gap-2 md:gap-3 min-w-0">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0"
            onClick={() => router.push("/dashboard")}
          >
            <ArrowLeft size={16} />
          </Button>
          <Link href="/dashboard" className="shrink-0">
            <svg
              viewBox="60 30 180 110"
              className="h-5 w-5 text-foreground"
              aria-hidden
            >
              <g fill="currentColor">
                <polygon points="85,40 119,108 109,128 65,40" />
                <polygon points="165,40 185,40 235,140 215,140 175,60 125,160 115,140 165,40" />
                <polygon points="150.5,105 199.5,105 207,120 143,120" />
              </g>
            </svg>
          </Link>
          <span className="text-sm font-medium truncate max-w-[120px] sm:max-w-[200px]">
            {project?.name}
          </span>
        </div>

        <div className="flex items-center gap-0.5 bg-muted rounded-lg p-0.5 shrink-0 overflow-x-auto max-w-[40vw] sm:max-w-none scrollbar-none">
          {MODES.map((m) => {
            const active = mode === m.value;
            return (
              <button
                key={m.value}
                type="button"
                onClick={() => setMode(m.value)}
                className={`inline-flex items-center justify-center gap-1 px-2 sm:px-3 py-1 rounded-md text-[10px] sm:text-xs font-medium transition-colors whitespace-nowrap shrink-0 ${
                  active
                    ? m.isDiscussion
                      ? "bg-violet-600/15 text-violet-700 dark:text-violet-300 shadow-sm ring-1 ring-violet-500/25"
                      : "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {m.isDiscussion ? (
                  <MessageCircle size={12} className="shrink-0 opacity-90" />
                ) : null}
                {m.label}
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-1 sm:gap-2 shrink-0">
          {mode !== "discussion" ? (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              title={rightPanelOpen ? "关闭预览" : "打开预览"}
            >
              {rightPanelOpen ? (
                <PanelRightClose size={16} />
              ) : (
                <PanelRightOpen size={16} />
              )}
            </Button>
          ) : null}
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1.5 text-xs"
            onClick={() => router.push(`/project/${projectId}/export`)}
          >
            <Download size={14} />
            <span className="hidden sm:inline">导出</span>
          </Button>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        <aside className="hidden md:flex w-[240px] flex-col border-r border-border shrink-0 min-h-0">
          <div className="flex border-b border-border shrink-0">
            <button
              type="button"
              onClick={() => setSidebarTab("conversations")}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${
                sidebarTab === "conversations"
                  ? "text-foreground border-b-2 border-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <MessageSquare size={12} />
              对话
            </button>
            {mode !== "discussion" ? (
              <button
                type="button"
                onClick={() => setSidebarTab("artifacts")}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-xs font-medium transition-colors ${
                  sidebarTab === "artifacts"
                    ? "text-foreground border-b-2 border-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <FileCode2 size={12} />
                产物
              </button>
            ) : null}
          </div>

          <div className="flex-1 min-h-0 flex flex-col">
            {sidebarTab === "conversations" ? (
              <ConversationList
                conversations={conversations}
                isLoading={convsLoading}
                selectedId={selectedConvId}
                onSelect={setSelectedConvId}
                onCreateClick={() => void handleCreateConversation()}
              />
            ) : (
              <ArtifactList
                artifacts={artifacts}
                isLoading={artifactsLoading}
                selectedId={selectedArtifactId}
                onSelect={(id) => {
                  setSelectedArtifactId(id);
                  setRightPanelOpen(true);
                }}
              />
            )}
          </div>
        </aside>

        <div className="flex-1 flex flex-col min-w-0 min-h-0">
          <div className="flex-1 min-h-0 overflow-y-auto px-4 py-4 space-y-4">
            {msgsLoading ? (
              <MessageThread messages={messages} isLoading />
            ) : showWelcome ? (
              <WorkspaceWelcome
                projectName={project?.name}
                onSuggestionClick={(text) => void handleSendMessage(text)}
              />
            ) : (
              <MessageThread messages={messages} isLoading={false} />
            )}
            {!showWelcome && sse.isStreaming ? (
              <StreamingMessage
                thinkingText={sse.thinkingText}
                contentText={sse.contentText}
                activeToolCalls={sse.activeToolCalls}
                completedToolCalls={sse.completedToolCalls}
                isStreaming={sse.isStreaming}
              />
            ) : null}
            <div ref={threadBottomRef} />
          </div>

          <MessageInput
            conversationId={selectedConvId ?? ""}
            isProcessing={sse.isStreaming}
            placeholder={messagePlaceholder}
            onSend={handleSendMessage}
            onStop={sse.abort}
          />
        </div>

        {rightPanelOpen && mode !== "discussion" ? (
          <aside className="hidden lg:flex w-[45%] max-w-[600px] flex-col border-l border-border min-h-0 shrink-0">
            <ArtifactPanel
              artifact={selectedArtifact ?? null}
              projectArtifacts={codeArtifacts}
              onClose={() => setRightPanelOpen(false)}
            />
          </aside>
        ) : null}
      </div>
    </div>
  );
}
