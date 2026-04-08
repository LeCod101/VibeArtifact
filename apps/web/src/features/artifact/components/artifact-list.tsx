/**
 * 产物列表组件
 *
 * 用于侧边栏展示项目产物，支持加载态、空态与选中高亮。
 */
"use client";

import {
  Database,
  FileCode2,
  FileQuestion,
  FileText,
  GitBranch,
  Loader2,
  Settings2,
} from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ArtifactListItem, ArtifactType } from "@/lib/api-client/types";

const TYPE_ICONS: Record<ArtifactType, typeof FileCode2> = {
  code: FileCode2,
  document: FileText,
  diagram: GitBranch,
  sql: Database,
  config: Settings2,
  other: FileQuestion,
};

export interface ArtifactListProps {
  artifacts: ArtifactListItem[] | undefined;
  isLoading: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function ArtifactList({
  artifacts,
  isLoading,
  selectedId,
  onSelect,
}: ArtifactListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!artifacts?.length) {
    return (
      <div className="px-3 py-6 text-center text-xs text-muted-foreground">
        暂无产物
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1">
      <div className="space-y-0.5 p-2">
        {artifacts.map((item) => {
          const Icon = TYPE_ICONS[item.artifact_type] ?? FileText;
          const isSelected = item.id === selectedId;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item.id)}
              className={`flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left transition-colors ${
                isSelected
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
              }`}
            >
              <Icon size={14} className="shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium">{item.title}</p>
                {item.file_path ? (
                  <p className="truncate text-[10px] text-muted-foreground">
                    {item.file_path}
                  </p>
                ) : null}
              </div>
            </button>
          );
        })}
      </div>
    </ScrollArea>
  );
}
