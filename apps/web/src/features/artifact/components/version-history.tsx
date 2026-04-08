/**
 * 产物版本历史列表
 *
 * 展示某产物的所有历史版本，支持选中切换预览。
 */
"use client";

import { History, Loader2 } from "lucide-react";
import { useArtifactVersionsQuery } from "@/features/artifact/api";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { ArtifactVersionItem } from "@/lib/api-client/types";

export interface VersionHistoryProps {
  artifactId: string;
  /** 当前正在预览的版本 id（与列表项 id 对齐） */
  currentVersionId?: string;
  onVersionSelect: (versionId: string) => void;
}

/** 将 ISO 时间格式化为简短日期时间 */
function formatVersionDate(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function VersionHistory({
  artifactId,
  currentVersionId,
  onVersionSelect,
}: VersionHistoryProps) {
  const { data: versions, isLoading, isError } =
    useArtifactVersionsQuery(artifactId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center gap-2 py-6 text-xs text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin shrink-0" />
        <span>加载版本历史…</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="px-3 py-4 text-center text-xs text-destructive">
        版本历史加载失败，请稍后重试
      </div>
    );
  }

  const list = versions ?? [];

  if (list.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 px-3 py-8 text-center text-xs text-muted-foreground">
        <History className="h-8 w-8 opacity-40" />
        <p>暂无历史版本</p>
      </div>
    );
  }

  return (
    <ScrollArea className="max-h-[200px]">
      <ul className="space-y-0.5 px-2 py-2" role="list">
        {list.map((v: ArtifactVersionItem) => {
          const active = v.id === currentVersionId;
          return (
            <li key={v.id}>
              <button
                type="button"
                onClick={() => onVersionSelect(v.id)}
                className={cn(
                  "w-full rounded-md px-2 py-2 text-left text-xs transition-colors",
                  active
                    ? "bg-primary/10 text-foreground ring-1 ring-primary/30"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono font-medium shrink-0">
                    v{v.version_num}
                  </span>
                  <span className="truncate text-[10px] opacity-80">
                    {formatVersionDate(v.created_at)}
                  </span>
                </div>
                <p className="mt-0.5 truncate font-medium text-foreground/90">
                  {v.title}
                </p>
              </button>
            </li>
          );
        })}
      </ul>
    </ScrollArea>
  );
}
