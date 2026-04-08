/**
 * 流式消息组件 - Agent 回复过程中的实时渲染
 *
 * 展示：折叠的思考过程、工具调用卡片、流式正文与光标。
 */
"use client";

import { useState } from "react";
import { Bot, ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import { ToolCallCard } from "./tool-call-card";
import type { ToolCallEvent } from "../hooks/use-agent-sse";

interface StreamingMessageProps {
  thinkingText: string;
  contentText: string;
  activeToolCalls: ToolCallEvent[];
  completedToolCalls: ToolCallEvent[];
  isStreaming: boolean;
}

export function StreamingMessage({
  thinkingText,
  contentText,
  activeToolCalls,
  completedToolCalls,
  isStreaming,
}: StreamingMessageProps) {
  const [thinkingExpanded, setThinkingExpanded] = useState(false);

  const allToolCalls = [...completedToolCalls, ...activeToolCalls];

  return (
    <div className="flex justify-start">
      <div className="flex max-w-[85%] gap-2">
        <div className="relative flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <Bot className="size-3.5" />
          {isStreaming && (
            <Loader2 className="absolute -right-0.5 -top-0.5 size-3 animate-spin text-muted-foreground" />
          )}
        </div>

        <div className="min-w-0 space-y-2">
          {thinkingText && (
            <button
              type="button"
              onClick={() => setThinkingExpanded(!thinkingExpanded)}
              className="flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
            >
              {thinkingExpanded ? (
                <ChevronDown className="size-3" />
              ) : (
                <ChevronRight className="size-3" />
              )}
              <span className="font-medium">思考过程</span>
            </button>
          )}
          {thinkingExpanded && thinkingText && (
            <div className="whitespace-pre-wrap rounded-lg border-l-2 border-muted-foreground/20 bg-muted/50 px-3 py-2 text-xs leading-relaxed text-muted-foreground">
              {thinkingText}
            </div>
          )}

          {allToolCalls.length > 0 && (
            <div className="space-y-1.5">
              {allToolCalls.map((tc, i) => (
                <ToolCallCard key={`${tc.tool}-${i}`} toolCall={tc} />
              ))}
            </div>
          )}

          {contentText && (
            <div className="rounded-2xl rounded-bl-md bg-muted px-4 py-2.5 text-sm leading-relaxed text-foreground whitespace-pre-wrap">
              {contentText}
              {isStreaming && (
                <span
                  className="stream-caret ml-0.5 inline-block h-4 w-1.5 align-text-bottom bg-foreground/60"
                  aria-hidden
                />
              )}
            </div>
          )}

          {isStreaming &&
            !contentText &&
            !thinkingText &&
            allToolCalls.length === 0 && (
              <div className="rounded-2xl rounded-bl-md bg-muted px-4 py-2.5">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            )}
        </div>
      </div>
    </div>
  );
}
