/**
 * 产物预览面板
 *
 * 按 artifact_type 分流：code 走代码预览，其余类型走 Markdown 排版预览。
 * 支持展开版本历史并切换历史版本预览。
 */
"use client";

import { useEffect, useState } from "react";
import {
  Database,
  FileCode2,
  FileQuestion,
  FileText,
  GitBranch,
  History,
  Loader2,
  Settings2,
  X,
} from "lucide-react";
import type { ArtifactResponseV2, ArtifactType } from "@/lib/api-client/types";
import { useArtifactQuery } from "@/features/artifact/api";
import { CodeViewer } from "./code-viewer";
import { MarkdownViewer } from "./markdown-viewer";
import { VersionHistory } from "./version-history";
import { Button } from "@/components/ui/button";

const HEADER_ICONS: Record<ArtifactType, typeof FileCode2> = {
  code: FileCode2,
  document: FileText,
  diagram: GitBranch,
  sql: Database,
  config: Settings2,
  other: FileQuestion,
};

export interface ArtifactPanelProps {
  artifact: ArtifactResponseV2 | null;
  onClose?: () => void;
}

function isCodeArtifact(type: ArtifactType): boolean {
  return type === "code";
}

export function ArtifactPanel({ artifact, onClose }: ArtifactPanelProps) {
  const [versionPanelOpen, setVersionPanelOpen] = useState(false);
  const [previewVersionId, setPreviewVersionId] = useState<string | null>(null);

  const { data: previewArtifact, isLoading: previewLoading } =
    useArtifactQuery(previewVersionId);

  // 切换侧边栏选中的产物时，收起版本区并清除历史预览
  useEffect(() => {
    setPreviewVersionId(null);
    setVersionPanelOpen(false);
  }, [artifact?.id]);

  if (!artifact) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
        <FileCode2 size={40} className="mb-3 opacity-40" />
        <p className="text-sm">选择一个产物查看预览</p>
        <p className="mt-1 text-xs">Agent 生成的代码、文档将在这里展示</p>
      </div>
    );
  }

  // 收窄类型，避免内联回调中 TS 仍认为 artifact 可能为 null
  const rootArtifact = artifact;

  const displayArtifact: ArtifactResponseV2 | null =
    previewVersionId && previewArtifact
      ? previewArtifact
      : previewVersionId && previewLoading
        ? null
        : previewVersionId && !previewLoading && !previewArtifact
          ? null
          : rootArtifact;

  const currentVersionIdForList =
    previewVersionId ?? rootArtifact.id;

  const HeaderIcon = HEADER_ICONS[rootArtifact.artifact_type] ?? FileText;

  function handleVersionSelect(versionId: string) {
    if (versionId === rootArtifact.id) {
      setPreviewVersionId(null);
      return;
    }
    setPreviewVersionId(versionId);
  }

  const headerTitle =
    displayArtifact?.title ?? rootArtifact.title;
  const headerVersionNum =
    displayArtifact?.version_num ?? rootArtifact.version_num;

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-4 py-2 gap-2">
        <div className="flex min-w-0 items-center gap-2 flex-1">
          <HeaderIcon size={14} className="shrink-0 text-muted-foreground" />
          <span className="truncate text-sm font-medium">{headerTitle}</span>
          <span className="shrink-0 text-[10px] text-muted-foreground">
            v{headerVersionNum}
          </span>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <Button
            type="button"
            variant={versionPanelOpen ? "secondary" : "ghost"}
            size="icon"
            className="h-8 w-8"
            title="版本历史"
            aria-expanded={versionPanelOpen}
            aria-label="版本历史"
            onClick={() => setVersionPanelOpen((o) => !o)}
          >
            <History size={14} />
          </Button>
          {onClose ? (
            <button
              type="button"
              onClick={onClose}
              className="shrink-0 rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              aria-label="关闭预览"
            >
              <X size={14} />
            </button>
          ) : null}
        </div>
      </div>

      {versionPanelOpen ? (
        <div className="shrink-0 border-b border-border bg-muted/30">
          <VersionHistory
            artifactId={rootArtifact.id}
            currentVersionId={currentVersionIdForList}
            onVersionSelect={handleVersionSelect}
          />
        </div>
      ) : null}

      <div className="min-h-0 flex-1 p-2">
        {previewVersionId && previewLoading ? (
          <div className="flex h-full min-h-[160px] items-center justify-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>加载该版本内容…</span>
          </div>
        ) : previewVersionId && !previewLoading && !previewArtifact ? (
          <div className="flex h-full min-h-[160px] items-center justify-center px-4 text-center text-sm text-destructive">
            无法加载该版本，请重试或选择其他版本
          </div>
        ) : displayArtifact ? (
          isCodeArtifact(displayArtifact.artifact_type) ? (
            <CodeViewer
              code={displayArtifact.content}
              language={displayArtifact.language}
              fileName={displayArtifact.file_path}
            />
          ) : (
            <MarkdownViewer content={displayArtifact.content} />
          )
        ) : null}
      </div>
    </div>
  );
}
