/**
 * 消息输入组件 - Claude 风格浮动卡片输入框
 *
 * - 圆角卡片样式，带阴影浮动效果
 * - 左侧附件按钮（占位），右侧发送按钮
 * - Enter 发送，Shift+Enter 换行
 */
"use client";

import { useState, type KeyboardEvent } from "react";
import { Send, Loader2, Plus } from "lucide-react";
import { toast } from "sonner";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useSendMessageMutation } from "@/features/chat/api";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api-client/errors";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface MessageInputProps {
  conversationId: string;
}

export function MessageInput({ conversationId }: MessageInputProps) {
  const { locale } = useLocale();
  const sendMutation = useSendMessageMutation(conversationId);
  const [content, setContent] = useState("");

  async function handleSend() {
    const trimmed = content.trim();
    if (!trimmed) return;

    try {
      await sendMutation.mutateAsync({
        role: "user",
        content: trimmed,
      });
      setContent("");
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  /** 键盘事件：Enter 发送，Shift+Enter 换行 */
  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="px-4 pb-4 pt-2">
      <div className="flex items-end gap-2 bg-card rounded-2xl border border-border shadow-sm px-3 py-2">
        {/* 附件按钮（占位） */}
        <button
          type="button"
          className="flex items-center justify-center w-8 h-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors shrink-0 mb-0.5"
        >
          <Plus size={18} />
        </button>

        {/* 文本输入区 */}
        <Textarea
          placeholder={L(t.project.messagePlaceholder, locale)}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          className="min-h-[36px] max-h-[120px] resize-none border-none bg-transparent shadow-none focus-visible:ring-0 px-0"
        />

        {/* 发送按钮 */}
        <button
          type="button"
          onClick={handleSend}
          disabled={!content.trim() || sendMutation.isPending}
          className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground disabled:opacity-30 transition-opacity shrink-0 mb-0.5"
        >
          {sendMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send size={14} />
          )}
        </button>
      </div>
    </div>
  );
}
