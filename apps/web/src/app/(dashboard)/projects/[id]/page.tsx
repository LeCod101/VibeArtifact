/**
 * 项目详情页 - 对话列表 + 消息线程
 *
 * 桌面端：左栏对话列表 + 右栏消息线程（双栏）
 * 移动端：对话列表与消息线程切换显示
 */
"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Lightbulb, Loader2, MessageSquare } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useProjectQuery } from "@/features/project/api";
import { useConversationsQuery } from "@/features/chat/api";
import { useMessagesQuery } from "@/features/chat/api";
import { ConversationList } from "@/features/chat/components/conversation-list";
import { CreateConversationDialog } from "@/features/chat/components/create-conversation-dialog";
import { MessageThread } from "@/features/chat/components/message-thread";
import { MessageInput } from "@/features/chat/components/message-input";
import { Button } from "@/components/ui/button";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { locale } = useLocale();
  const projectId = params.id as string;

  // 选中的对话 ID
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  // 新建对话弹窗
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // 数据查询
  const { data: project, isLoading: projectLoading } = useProjectQuery(projectId);
  const { data: conversations, isLoading: convsLoading } = useConversationsQuery(projectId);
  const { data: messages, isLoading: msgsLoading } = useMessagesQuery(selectedConvId);

  // 项目加载中
  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-theme(spacing.14)-theme(spacing.12))] lg:h-[calc(100vh-theme(spacing.12))]">
      {/* 项目标题栏 */}
      <div className="flex items-center gap-3 pb-4 border-b border-border shrink-0">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push("/dashboard")}
        >
          <ArrowLeft size={18} />
        </Button>
        <div className="flex-1">
          <h1 className="text-lg font-bold">{project?.name}</h1>
          {project?.description && (
            <p className="text-xs text-muted-foreground">{project.description}</p>
          )}
        </div>
        {/* 项目内导航 tab */}
        <nav className="flex items-center gap-1">
          <span
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-secondary text-foreground"
          >
            <MessageSquare size={16} />
            {L(t.project.conversations, locale)}
          </span>
          <Link
            href={`/projects/${projectId}/ideation`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
          >
            <Lightbulb size={16} />
            {L(t.generation.ideationTitle, locale)}
          </Link>
        </nav>
      </div>

      {/* 主内容区 */}
      <div className="flex flex-1 min-h-0 mt-4">
        {/* 对话列表：桌面端始终显示，移动端仅在未选中对话时显示 */}
        <div
          className={`border border-border rounded-lg overflow-hidden ${
            selectedConvId
              ? "hidden lg:flex lg:flex-col lg:w-[320px] lg:shrink-0"
              : "flex flex-col w-full lg:w-[320px] lg:shrink-0"
          }`}
        >
          <ConversationList
            conversations={conversations}
            isLoading={convsLoading}
            selectedId={selectedConvId}
            onSelect={setSelectedConvId}
            onCreateClick={() => setCreateDialogOpen(true)}
          />
        </div>

        {/* 消息线程：桌面端始终显示，移动端仅在选中对话时显示 */}
        <div
          className={`flex-1 flex flex-col border border-border rounded-lg overflow-hidden ${
            selectedConvId
              ? "flex lg:ml-4"
              : "hidden lg:flex lg:ml-4"
          }`}
        >
          {selectedConvId ? (
            <>
              {/* 移动端返回按钮 */}
              <div className="lg:hidden flex items-center gap-2 p-3 border-b border-border">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedConvId(null)}
                >
                  <ArrowLeft size={16} className="mr-1" />
                  {L(t.common.back, locale)}
                </Button>
              </div>
              <MessageThread messages={messages} isLoading={msgsLoading} />
              <MessageInput conversationId={selectedConvId} />
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
              {L(t.project.noConversations, locale)}
            </div>
          )}
        </div>
      </div>

      <CreateConversationDialog
        projectId={projectId}
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onCreated={(id) => setSelectedConvId(id)}
      />
    </div>
  );
}
