/**
 * 代码预览组件
 *
 * 使用 pre/code 展示源码；顶栏含文件名、语言标签与复制操作。
 */
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Check, Copy } from "lucide-react";

export interface CodeViewerProps {
  code: string;
  language?: string | null;
  fileName?: string | null;
}

export function CodeViewer({ code, language, fileName }: CodeViewerProps) {
  const [copied, setCopied] = useState(false);
  const copiedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (copiedTimerRef.current) {
        clearTimeout(copiedTimerRef.current);
      }
    };
  }, []);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      if (copiedTimerRef.current) {
        clearTimeout(copiedTimerRef.current);
      }
      copiedTimerRef.current = setTimeout(() => {
        setCopied(false);
        copiedTimerRef.current = null;
      }, 2000);
    } catch {
      setCopied(false);
    }
  }, [code]);

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg border border-border bg-background">
      <div className="flex shrink-0 items-center justify-between border-b border-border bg-muted/50 px-4 py-2">
        <div className="flex min-w-0 items-center gap-2 text-xs text-muted-foreground">
          {fileName ? (
            <span className="truncate font-medium text-foreground">{fileName}</span>
          ) : null}
          {language ? (
            <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-[10px] uppercase">
              {language}
            </span>
          ) : null}
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? "已复制" : "复制"}
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-auto">
        <pre className="p-4 text-sm leading-relaxed">
          <code className="whitespace-pre font-mono text-foreground">{code}</code>
        </pre>
      </div>
    </div>
  );
}
