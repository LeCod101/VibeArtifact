/**
 * 导出管理页面 - 触发打包导出并打开下载链接
 */
"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Download, Loader2, Package } from "lucide-react";
import { toast } from "sonner";
import { apiPost } from "@/lib/api-client";
import { useProjectQuery } from "@/features/project/api";
import { Button } from "@/components/ui/button";
import type { ExportResponse } from "@/lib/api-client/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** 将后端返回的相对路径拼成可打开的绝对 URL */
function resolveDownloadUrl(pathOrUrl: string): string {
  if (pathOrUrl.startsWith("http://") || pathOrUrl.startsWith("https://")) {
    return pathOrUrl;
  }
  const base = API_BASE.replace(/\/$/, "");
  const path = pathOrUrl.startsWith("/") ? pathOrUrl : `/${pathOrUrl}`;
  return `${base}${path}`;
}

export default function ExportPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const { data: project } = useProjectQuery(projectId);
  const [exporting, setExporting] = useState(false);

  async function handleExport() {
    setExporting(true);
    try {
      const result = await apiPost<ExportResponse>(
        `/api/v1/projects/${projectId}/export`,
        { export_type: "zip" },
      );
      if (result.file_url) {
        window.open(resolveDownloadUrl(result.file_url), "_blank");
        toast.success("导出成功");
      } else {
        toast.info("导出任务已提交，请稍后下载");
      }
    } catch {
      toast.error("导出失败，请重试");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 md:py-12">
      <div className="flex items-center gap-3 mb-8">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push(`/project/${projectId}`)}
        >
          <ArrowLeft size={18} />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">导出项目</h1>
          <p className="text-sm text-muted-foreground">{project?.name}</p>
        </div>
      </div>

      <div className="rounded-lg border border-border p-8 text-center">
        <Package size={48} className="mx-auto mb-4 text-muted-foreground" />
        <h2 className="text-lg font-medium mb-2">打包下载</h2>
        <p className="text-sm text-muted-foreground mb-6">
          将项目中所有产物打包为 ZIP 文件下载
        </p>
        <Button onClick={handleExport} disabled={exporting} className="gap-2">
          {exporting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download size={16} />
          )}
          {exporting ? "导出中..." : "开始导出"}
        </Button>
      </div>
    </div>
  );
}
