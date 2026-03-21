/**
 * 消息线程组件 - 展示对话中的消息列表
 *
 * 按角色区分样式：
 * - user: 右对齐，白底黑字
 * - assistant: 左对齐，深色背景
 * - system: 居中，透明背景
 *
 * 自动滚动到底部。
 * 支持快照指示器显示和回滚操作。
 */
"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, User, Bot, Info, RotateCcw } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import type { MessageResponse } from "@/lib/api-client/types";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChangeSummary } from "@/features/chat/components/change-summary";
import { SnapshotIndicator } from "@/features/chat/components/snapshot-indicator";
import { RollbackDialog } from "@/features/chat/components/rollback-dialog";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface MessageThreadProps {
  messages: MessageResponse[] | undefined;
  isLoading: boolean;
  /** 对话 ID，用于回滚操作 */
  conversationId?: string;
  /** 回滚完成后的回调 */
  onRollbackComplete?: () => void;
}

/** 格式化消息时间 */
function formatTime(iso: string) {
  const date = new Date(iso);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function MessageThread({
  messages,
  isLoading,
  conversationId,
  onRollbackComplete,
}: MessageThreadProps) {
  const { locale } = useLocale();
  const bottomRef = useRef<HTMLDivElement>(null);

  // 回滚对话框状态
  const [rollbackTarget, setRollbackTarget] = useState<string | null>(null);

  // 新消息到达时自动滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!messages || messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        {L(t.project.noMessages, locale)}
      </div>
    );
  }

  return (
    <>
      <ScrollArea className="flex-1 px-4">
        <div className="space-y-4 py-4">
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              onRollback={
                conversationId && msg.snapshot_after_id
                  ? () => setRollbackTarget(msg.snapshot_after_id!)
                  : undefined
              }
            />
          ))}
          {/* 滚动锚点 */}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      {/* 回滚确认对话框 */}
      {conversationId && rollbackTarget && (
        <RollbackDialog
          open={!!rollbackTarget}
          onOpenChange={(open) => {
            if (!open) setRollbackTarget(null);
          }}
          conversationId={conversationId}
          snapshotId={rollbackTarget}
          onRollbackComplete={() => {
            setRollbackTarget(null);
            onRollbackComplete?.();
          }}
        />
      )}
    </>
  );
}

/** 单条消息气泡 */
function MessageBubble({
  message,
  onRollback,
}: {
  message: MessageResponse;
  onRollback?: () => void;
}) {
  const { locale } = useLocale();
  const { role, content, created_at } = message;

  // system 消息居中显示
  if (role === "system") {
    return (
      <div className="flex justify-center">
        <div className="flex items-center gap-2 text-xs text-muted-foreground max-w-[80%] text-center">
          <Info size={12} />
          <span>{content}</span>
        </div>
      </div>
    );
  }

  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`flex gap-2 max-w-[70%] ${
          isUser ? "flex-row-reverse" : "flex-row"
        }`}
      >
        {/* 头像 */}
        <div
          className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground"
          }`}
        >
          {isUser ? <User size={14} /> : <Bot size={14} />}
        </div>

        {/* 气泡 */}
        <div>
          <div
            className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
              isUser
                ? "bg-primary text-primary-foreground rounded-br-md"
                : "bg-muted text-foreground rounded-bl-md"
            }`}
          >
            {content}
          </div>

          {/* 时间 + 快照指示器 + 回滚按钮 */}
          <div
            className={`flex items-center gap-2 mt-1 ${
              isUser ? "justify-end" : "justify-start"
            }`}
          >
            <p className="text-[10px] text-muted-foreground">
              {formatTime(created_at)}
            </p>

            {/* 快照指示器：仅 assistant 消息且有 snapshot_after_id 时显示 */}
            {!isUser && message.snapshot_after_id && (
              <SnapshotIndicator
                snapshotBefore={message.snapshot_before_id}
                snapshotAfter={message.snapshot_after_id}
              />
            )}

            {/* 回滚按钮：仅有 snapshot_after_id 的 assistant 消息显示 */}
            {!isUser && onRollback && (
              <button
                type="button"
                onClick={onRollback}
                className="inline-flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors px-1 py-0.5 rounded"
                title={L(t.branches.rollbackToSnapshot, locale)}
              >
                <RotateCcw className="h-3 w-3" />
              </button>
            )}
          </div>

          {/* 助手消息的变更摘要卡片 */}
          {!isUser && message.change_summary && (
            <ChangeSummary
              summary={message.change_summary}
              className="mt-2 max-w-full"
            />
          )}
        </div>
      </div>
    </div>
  );
}
