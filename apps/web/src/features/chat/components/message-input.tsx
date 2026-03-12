/**
 * 消息输入组件 - 文本框 + 发送按钮
 *
 * - 固定 role: "user"（M1 不接入 AI）
 * - Enter 发送，Shift+Enter 换行
 */
"use client";

import { useState, type KeyboardEvent } from "react";
import { Send, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useSendMessageMutation } from "@/features/chat/api";
import { Button } from "@/components/ui/button";
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
    <div className="border-t border-border p-4 bg-card">
      <div className="flex items-end gap-2">
        <Textarea
          placeholder={L(t.project.messagePlaceholder, locale)}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          className="min-h-[40px] max-h-[120px] resize-none"
        />
        <Button
          size="icon"
          onClick={handleSend}
          disabled={!content.trim() || sendMutation.isPending}
          className="shrink-0"
        >
          {sendMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send size={16} />
          )}
        </Button>
      </div>
    </div>
  );
}
