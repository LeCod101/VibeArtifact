/**
 * Markdown 预览组件
 *
 * 基础实现：正文使用 Tailwind Typography 的 prose 排版；后续可替换为 react-markdown。
 */
"use client";

export interface MarkdownViewerProps {
  content: string;
  title?: string | null;
}

export function MarkdownViewer({ content, title }: MarkdownViewerProps) {
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg border border-border bg-background">
      {title ? (
        <div className="shrink-0 border-b border-border bg-muted/50 px-4 py-2">
          <span className="text-xs font-medium text-foreground">{title}</span>
        </div>
      ) : null}

      <div className="min-h-0 flex-1 overflow-auto p-6">
        <div className="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap leading-relaxed text-foreground">
          {content}
        </div>
      </div>
    </div>
  );
}
