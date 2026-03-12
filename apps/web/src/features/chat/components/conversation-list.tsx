/**
 * 对话列表组件 - 显示项目下的所有对话
 *
 * ScrollArea 列表，高亮选中项，"新建对话"按钮。
 */
"use client";

import { Plus, MessageSquare, Loader2 } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import type { ConversationResponse } from "@/lib/api-client/types";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface ConversationListProps {
  conversations: ConversationResponse[] | undefined;
  isLoading: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreateClick: () => void;
}

/** 格式化日期 */
function formatDate(iso: string, locale: Locale) {
  const date = new Date(iso);
  return date.toLocaleDateString(locale === "zh" ? "zh-CN" : "en-US", {
    month: "short",
    day: "numeric",
  });
}

export function ConversationList({
  conversations,
  isLoading,
  selectedId,
  onSelect,
  onCreateClick,
}: ConversationListProps) {
  const { locale } = useLocale();

  return (
    <div className="flex flex-col h-full">
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h3 className="text-sm font-bold">
          {L(t.project.conversations, locale)}
        </h3>
        <Button size="sm" variant="ghost" onClick={onCreateClick}>
          <Plus size={16} />
        </Button>
      </div>

      {/* 列表 */}
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : conversations && conversations.length > 0 ? (
          <div className="py-1">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={`w-full text-left px-4 py-3 flex items-center gap-3 transition-colors relative ${
                  selectedId === conv.id
                    ? "bg-accent/50"
                    : "hover:bg-accent/30"
                }`}
              >
                {/* 选中态左侧指示条 */}
                {selectedId === conv.id && (
                  <div className="absolute left-0 top-2 bottom-2 w-0.5 bg-foreground rounded-full" />
                )}
                <MessageSquare
                  size={16}
                  className="text-muted-foreground shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {conv.title || `#${conv.id.slice(0, 8)}`}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(conv.created_at, locale)}
                  </p>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            <MessageSquare
              size={32}
              className="text-muted-foreground mb-3"
            />
            <p className="text-sm text-muted-foreground">
              {L(t.project.noConversations, locale)}
            </p>
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
