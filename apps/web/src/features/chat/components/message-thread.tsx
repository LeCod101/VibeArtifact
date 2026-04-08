/**
 * 消息线程组件 - 展示对话中的历史消息列表
 *
 * 按角色区分样式：user 右对齐，assistant 左对齐，system 居中。
 * 外层滚动与滚到底部由工作区页面与流式区共同负责。
 */
"use client";

import { Loader2, User, Bot, Info } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import type { MessageResponse } from "@/lib/api-client/types";

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

export function MessageThread({
  messages,
  isLoading,
}: MessageThreadProps) {
  const { locale } = useLocale();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const hasMessages = messages && messages.length > 0;

  return (
    <>
      {!hasMessages && (
        <div className="flex items-center justify-center min-h-[120px] text-sm text-muted-foreground">
          {L(t.project.noMessages, locale)}
        </div>
      )}
      {hasMessages &&
        messages!.map((msg) => <MessageBubble key={msg.id} message={msg} />)}
    </>
  );
}

function MessageBubble({ message }: { message: MessageResponse }) {
  const { role, content, created_at } = message;

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
        <div
          className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground"
          }`}
        >
          {isUser ? <User size={14} /> : <Bot size={14} />}
        </div>

        <div>
          <div
            className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
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
        </div>
      </div>
    </div>
  );
}
