/**
 * 全权委托 API 层
 *
 * 封装全权委托运行的创建、查询和下载 URL 构造。
 * 与后端 /api/v1/projects/{projectId}/delegated-runs 对接。
 */
import { apiGet, apiPost } from "@/lib/api-client";

/* ============ 类型定义 ============ */

/** 创建全权委托运行的请求参数 */
export interface CreateDelegatedRunParams {
  snapshot_id?: string;
}

/** 创建全权委托运行的响应 */
export interface CreateDelegatedRunResponse {
  run_id: string;
  status: string;
}

/** 单个 agent 步骤的状态信息 */
export interface DelegatedStepData {
  agent_id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
}

/** 全权委托运行详情 */
export interface DelegatedRunData {
  run_id: string;
  status: string;
  steps: DelegatedStepData[];
  created_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  /** Gate 检查结果（needs_attention 时有值） */
  output_payload: Record<string, unknown> | null;
}

/** SSE 事件数据结构 */
export interface SSEEventData {
  event: string;
  data: {
    agent_id?: string;
    status?: string;
    run_id?: string;
    error?: string;
    [key: string]: unknown;
  };
}

/* ============ API 函数 ============ */

/**
 * 创建全权委托运行
 *
 * @param projectId - 项目 UUID
 * @param snapshotId - 快照 ID（可选，不传则使用最新快照）
 * @returns 新建的运行 ID 和初始状态
 */
export function createDelegatedRun(
  projectId: string,
  snapshotId?: string,
): Promise<CreateDelegatedRunResponse> {
  const body: CreateDelegatedRunParams = {};
  if (snapshotId) {
    body.snapshot_id = snapshotId;
  }
  return apiPost<CreateDelegatedRunResponse>(
    `/api/v1/projects/${projectId}/delegated-runs`,
    body,
  );
}

/**
 * 查询全权委托运行状态
 *
 * @param projectId - 项目 UUID
 * @param runId - 运行 UUID
 * @returns 运行详情（含各步骤状态）
 */
export function getDelegatedRun(
  projectId: string,
  runId: string,
): Promise<DelegatedRunData> {
  return apiGet<DelegatedRunData>(
    `/api/v1/projects/${projectId}/delegated-runs/${runId}`,
  );
}

/**
 * 获取 ZIP 下载 URL
 *
 * 构造完整下载路径，附带认证 token。
 * @param projectId - 项目 UUID
 * @param runId - 运行 UUID
 * @returns 完整的下载 URL 字符串
 */
export function getDownloadUrl(projectId: string, runId: string): string {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return `${base}/api/v1/projects/${projectId}/delegated-runs/${runId}/download`;
}
