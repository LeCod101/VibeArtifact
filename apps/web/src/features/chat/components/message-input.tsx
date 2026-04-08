/**
 * 消息输入组件 - Claude 风格浮动卡片输入框
 *
 * Enter 发送，Shift+Enter 换行；实际发送由父组件通过 onSend 处理（如 SSE）。
 */
"use client";

import { useState, type KeyboardEvent } from "react";
import { Send, Loader2, Plus, StopCircle } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { Textarea } from "@/components/ui/textarea";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface MessageInputProps {
  /** 当前对话 ID（占位，供父级创建对话或埋点使用） */
  conversationId: string;
  isProcessing?: boolean;
  /** 空闲时的占位文案；未传则使用 i18n 默认文案 */
  placeholder?: string;
  /** 用户确认发送时的回调 */
  onSend: (content: string) => void | Promise<void>;
  /** 流式进行中时中止（如中止 SSE） */
  onStop?: () => void;
}

export function MessageInput({
  conversationId: _conversationId,
  isProcessing = false,
  placeholder: placeholderProp,
  onSend,
  onStop,
}: MessageInputProps) {
  const { locale } = useLocale();
  const [content, setContent] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSend() {
    const trimmed = content.trim();
    if (!trimmed || isProcessing || pending) return;

    setPending(true);
    try {
      await onSend(trimmed);
      setContent("");
    } finally {
      setPending(false);
    }
  }

  /** 键盘事件：Enter 发送，Shift+Enter 换行 */
  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  }

  const busy = isProcessing || pending;

  return (
    <div className="px-4 pb-4 pt-2 shrink-0">
      <div className="flex items-end gap-2 bg-card rounded-2xl border border-border shadow-sm px-3 py-2">
        <button
          type="button"
          className="flex items-center justify-center w-8 h-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent transition-colors shrink-0 mb-0.5"
        >
          <Plus size={18} />
        </button>

        <Textarea
          placeholder={
            busy
              ? "AI 正在思考..."
              : placeholderProp ?? L(t.project.messagePlaceholder, locale)
          }
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={busy}
          className="min-h-[36px] max-h-[120px] resize-none border-none bg-transparent shadow-none focus-visible:ring-0 px-0 disabled:cursor-not-allowed disabled:opacity-60"
        />

        {busy && onStop ? (
          <button
            type="button"
            onClick={onStop}
            className="flex items-center justify-center w-8 h-8 rounded-full bg-destructive text-destructive-foreground transition-opacity shrink-0 mb-0.5"
          >
            <StopCircle size={14} />
          </button>
        ) : (
          <button
            type="button"
            onClick={() => void handleSend()}
            disabled={!content.trim() || busy}
            className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground disabled:opacity-30 transition-opacity shrink-0 mb-0.5"
          >
            {busy ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send size={14} />
            )}
          </button>
        )}
      </div>
    </div>
  );
}
