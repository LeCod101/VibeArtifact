/**
 * 工具调用卡片 - 展示 Agent 工具调用的状态与结果
 */
"use client";

import { useState } from "react";
import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Code2,
  Download,
  FileText,
  Globe,
  HelpCircle,
  Loader2,
  Search,
  XCircle,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import type { ToolCallEvent } from "../hooks/use-agent-sse";

/** 工具名到图标的映射 */
const TOOL_ICONS: Record<string, typeof Code2> = {
  generate_code: Code2,
  edit_code: Code2,
  explain_code: Code2,
  review_code: Code2,
  generate_document: FileText,
  generate_diagram: FileText,
  generate_sql: FileText,
  list_files: Search,
  read_file: Search,
  search_code: Search,
  export_project: Download,
  web_search: Globe,
  ask_clarification: HelpCircle,
};

/** 工具中文标签 */
const TOOL_LABELS: Record<string, string> = {
  generate_code: "生成代码",
  edit_code: "编辑代码",
  explain_code: "解释代码",
  review_code: "审查代码",
  generate_document: "生成文档",
  generate_diagram: "生成图表",
  generate_sql: "生成 SQL",
  list_files: "列出文件",
  read_file: "读取文件",
  search_code: "搜索代码",
  export_project: "导出项目",
  web_search: "网络搜索",
  ask_clarification: "请求澄清",
};

interface ToolCallCardProps {
  toolCall: ToolCallEvent;
}

export function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [expanded, setExpanded] = useState(false);
  const Icon = TOOL_ICONS[toolCall.tool] || Code2;
  const label = TOOL_LABELS[toolCall.tool] || toolCall.tool;
  const isCalling = toolCall.status === "calling";
  const isError = toolCall.status === "error";

  return (
    <Card size="sm" className="gap-0 py-0 ring-1 ring-border">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition-colors hover:bg-accent/50"
      >
        {isCalling ? (
          <Loader2 className="size-3 shrink-0 animate-spin text-muted-foreground" />
        ) : isError ? (
          <XCircle className="size-3 shrink-0 text-destructive" />
        ) : (
          <CheckCircle2 className="size-3 shrink-0 text-emerald-500" />
        )}
        <Icon className="size-3 shrink-0 text-muted-foreground" />
        <span className="font-medium text-foreground">{label}</span>
        <span className="flex-1" />
        {expanded ? (
          <ChevronDown className="size-3 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="size-3 shrink-0 text-muted-foreground" />
        )}
      </button>

      {expanded && (
        <div className="space-y-2 border-t border-border bg-muted/30 px-3 py-2">
          {Object.keys(toolCall.arguments).length > 0 && (
            <div>
              <p className="mb-1 text-muted-foreground">参数</p>
              <pre className="max-h-40 overflow-x-auto rounded bg-background p-2 text-[10px]">
                {JSON.stringify(toolCall.arguments, null, 2)}
              </pre>
            </div>
          )}
          {toolCall.result !== undefined && (
            <div>
              <p className="mb-1 text-muted-foreground">结果</p>
              <pre className="max-h-40 overflow-x-auto rounded bg-background p-2 text-[10px]">
                {typeof toolCall.result === "string"
                  ? toolCall.result
                  : JSON.stringify(toolCall.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
