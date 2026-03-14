/**
 * 生成流程 API Hooks
 *
 * 提供想法分析、MVP 收缩、Scope 确认的 mutation hooks。
 */
import { useMutation } from "@tanstack/react-query";
import { apiPost } from "@/lib/api-client";

/* ============ 类型定义 ============ */

/** 功能模块项 */
export interface ScopeItemData {
  name: string;
  description: string;
  priority: string;
  tags: string[];
}

/** Scope 草稿 - 分析/收缩后的功能范围 */
export interface ScopeDraftData {
  product_name: string;
  product_description: string;
  scopes: ScopeItemData[];
  deferred_items: string[];
  risks: string[];
}

/** 单个维度的容量点数 */
export interface DimensionCountData {
  dimension: string;
  count: number;
  points: number;
}

/** 容量报告 - 点数汇总和分档 */
export interface CapacityReportData {
  dimensions: DimensionCountData[];
  total_points: number;
  tier: string;
  budget: number;
  over_budget: boolean;
  needs_contraction: boolean;
  must_contract: boolean;
}

/** 分析接口响应 */
export interface AnalyzeResponse {
  scope_draft: ScopeDraftData;
  capacity_report: CapacityReportData;
  warnings: string[];
}

/** 延后功能详情 */
export interface DeferredFeatureData {
  name: string;
  reason: string;
}

/** 收缩决策 */
export interface ContractionDecisionData {
  retained_features: string[];
  deferred_features: DeferredFeatureData[];
  risks: string[];
  rationale: string;
}

/** 收缩接口响应 */
export interface ContractResponse {
  scope_draft: ScopeDraftData;
  decision: ContractionDecisionData;
  capacity_before: CapacityReportData;
  capacity_after: CapacityReportData;
  warnings: string[];
}

/** 确认 Scope 接口响应 */
export interface ConfirmScopeResponse {
  scope_draft: ScopeDraftData;
  capacity_report: CapacityReportData;
  confirmed: boolean;
  message: string;
}

/* ============ Hooks ============ */

/**
 * 分析想法 mutation
 *
 * 将用户输入的自然语言想法发送到后端，返回功能范围和容量报告。
 * @param projectId - 项目 UUID
 */
export function useAnalyzeMutation(projectId: string) {
  return useMutation({
    mutationFn: (data: { user_idea: string }) =>
      apiPost<AnalyzeResponse>(
        `/api/v1/projects/${projectId}/generation/analyze`,
        data
      ),
  });
}

/**
 * MVP 收缩 mutation
 *
 * 将分析结果发送到后端进行自动收缩，返回收缩方案。
 * @param projectId - 项目 UUID
 */
export function useContractMutation(projectId: string) {
  return useMutation({
    mutationFn: (data: {
      scope_draft: ScopeDraftData;
      capacity_report: CapacityReportData;
    }) =>
      apiPost<ContractResponse>(
        `/api/v1/projects/${projectId}/generation/contract`,
        data
      ),
  });
}

/**
 * 确认 Scope mutation
 *
 * 用户确认或微调收缩方案后，锁定最终 Scope。
 * @param projectId - 项目 UUID
 */
export function useConfirmScopeMutation(projectId: string) {
  return useMutation({
    mutationFn: (data: {
      restore_features?: string[];
      defer_features?: string[];
    }) =>
      apiPost<ConfirmScopeResponse>(
        `/api/v1/projects/${projectId}/generation/confirm-scope`,
        data
      ),
  });
}
