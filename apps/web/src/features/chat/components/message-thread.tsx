/**
 * 消息线程组件 - 展示对话中的消息列表
 *
 * 按角色区分样式：
 * - user: 右对齐，白底黑字
 * - assistant: 左对齐，深色背景
 * - system: 居中，透明背景
 *
 * 自动滚动到底部。
 */
"use client";

import { useEffect, useRef } from "react";
import { Loader2, User, Bot, Info } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import type { MessageResponse } from "@/lib/api-client/types";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChangeSummary } from "@/features/chat/components/change-summary";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface MessageThreadProps {
  messages: MessageResponse[] | undefined;
  isLoading: boolean;
}

/** 格式化消息时间 */
function formatTime(iso: string) {
  const date = new Date(iso);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function MessageThread({ messages, isLoading }: MessageThreadProps) {
  const { locale } = useLocale();
  const bottomRef = useRef<HTMLDivElement>(null);

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
    <ScrollArea className="flex-1 px-4">
      <div className="space-y-4 py-4">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {/* 滚动锚点 */}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}

/** 单条消息气泡 */
function MessageBubble({ message }: { message: MessageResponse }) {
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
          <p
            className={`text-[10px] text-muted-foreground mt-1 ${
              isUser ? "text-right" : "text-left"
            }`}
          >
            {formatTime(created_at)}
          </p>

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
