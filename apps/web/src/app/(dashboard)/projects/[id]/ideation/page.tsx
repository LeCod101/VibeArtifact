/**
 * 想法输入页 - 生成流程的入口
 *
 * 状态机驱动的多步骤流程：
 * idle → analyzing → analyzed → contracting → contracted → confirming → confirmed
 *
 * 步骤：
 * 1. 输入想法
 * 2. 分析结果（如不需收缩直接确认，需要则显示收缩按钮）
 * 3. 收缩方案展示
 * 4. 确认 Scope
 * 5. 完成
 */
"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Sparkles, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useProjectQuery } from "@/features/project/api";
import {
  useAnalyzeMutation,
  useContractMutation,
  useConfirmScopeMutation,
} from "@/features/generation/api";
import type {
  AnalyzeResponse,
  ContractResponse,
} from "@/features/generation/api";
import { ScopeAnalysis } from "@/features/generation/components/scope-analysis";
import { CapacityDashboard } from "@/features/generation/components/capacity-dashboard";
import { ContractionResult } from "@/features/generation/components/contraction-result";
import { ScopeConfirm } from "@/features/generation/components/scope-confirm";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api-client/errors";
import { cn } from "@/lib/utils";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 流程状态 */
type FlowState =
  | "idle"
  | "analyzing"
  | "analyzed"
  | "contracting"
  | "contracted"
  | "confirming"
  | "confirmed";

/** 步骤定义 */
const STEPS = [
  { key: "input", label: t.generation.steps.input },
  { key: "analyze", label: t.generation.steps.analyze },
  { key: "contract", label: t.generation.steps.contract },
  { key: "confirm", label: t.generation.steps.confirm },
] as const;

/** 根据流程状态返回当前步骤索引（0-3） */
function getStepIndex(state: FlowState): number {
  switch (state) {
    case "idle":
    case "analyzing":
      return 0;
    case "analyzed":
      return 1;
    case "contracting":
    case "contracted":
      return 2;
    case "confirming":
    case "confirmed":
      return 3;
  }
}

export default function IdeationPage() {
  const params = useParams();
  const router = useRouter();
  const { locale } = useLocale();
  const projectId = params.id as string;

  // 项目信息
  const { data: project } = useProjectQuery(projectId);

  // 流程状态
  const [flowState, setFlowState] = useState<FlowState>("idle");
  const [userIdea, setUserIdea] = useState("");
  const [analyzeResult, setAnalyzeResult] = useState<AnalyzeResponse | null>(null);
  const [contractResult, setContractResult] = useState<ContractResponse | null>(null);

  // API mutations
  const analyzeMutation = useAnalyzeMutation(projectId);
  const contractMutation = useContractMutation(projectId);
  const confirmMutation = useConfirmScopeMutation(projectId);

  const currentStep = getStepIndex(flowState);

  /** 步骤 1：提交分析 */
  async function handleAnalyze() {
    const trimmed = userIdea.trim();
    if (!trimmed) return;

    setFlowState("analyzing");
    try {
      const result = await analyzeMutation.mutateAsync({ user_idea: trimmed });
      setAnalyzeResult(result);
      setFlowState("analyzed");
    } catch (err) {
      setFlowState("idle");
      const msg = err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  /** 步骤 2→3：开始收缩 */
  async function handleContract() {
    if (!analyzeResult) return;

    setFlowState("contracting");
    try {
      const result = await contractMutation.mutateAsync({
        scope_draft: analyzeResult.scope_draft,
        capacity_report: analyzeResult.capacity_report,
      });
      setContractResult(result);
      setFlowState("contracted");
    } catch (err) {
      setFlowState("analyzed");
      const msg = err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  /** 步骤 4：确认 Scope */
  async function handleConfirm(restore: string[], defer: string[]) {
    setFlowState("confirming");
    try {
      await confirmMutation.mutateAsync({
        restore_features: restore.length > 0 ? restore : undefined,
        defer_features: defer.length > 0 ? defer : undefined,
      });
      setFlowState("confirmed");
      toast.success(L(t.generation.confirmed, locale));
    } catch (err) {
      // 回退到 contracted 状态让用户重试
      setFlowState("contracted");
      const msg = err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  /** 重新分析：重置到 idle 状态 */
  function handleReanalyze() {
    setFlowState("idle");
    setAnalyzeResult(null);
    setContractResult(null);
  }

  /** 分析完成且不需要收缩时直接确认 */
  async function handleDirectConfirm() {
    setFlowState("confirming");
    try {
      await confirmMutation.mutateAsync({});
      setFlowState("confirmed");
      toast.success(L(t.generation.confirmed, locale));
    } catch (err) {
      setFlowState("analyzed");
      const msg = err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  return (
    <div className="flex flex-col items-center pb-12">
      {/* 面包屑 */}
      <div className="w-full max-w-4xl flex items-center gap-2 mb-6">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push(`/projects/${projectId}`)}
        >
          <ArrowLeft size={18} />
        </Button>
        <span className="text-sm text-muted-foreground">
          {project?.name}
        </span>
        <span className="text-sm text-muted-foreground">/</span>
        <span className="text-sm font-medium">
          {L(t.generation.ideationTitle, locale)}
        </span>
      </div>

      {/* 步骤指示器 */}
      <div className="w-full max-w-md mb-10 animate-reveal">
        <div className="flex items-center justify-between">
          {STEPS.map((step, idx) => (
            <div key={step.key} className="flex items-center">
              {/* 圆点 */}
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "w-3 h-3 rounded-full border-2 transition-colors",
                    idx <= currentStep
                      ? "bg-foreground border-foreground"
                      : "bg-transparent border-muted-foreground/40"
                  )}
                />
                <span
                  className={cn(
                    "text-[10px] mt-1.5 whitespace-nowrap",
                    idx <= currentStep
                      ? "text-foreground font-medium"
                      : "text-muted-foreground"
                  )}
                >
                  {L(step.label, locale)}
                </span>
              </div>
              {/* 连线 */}
              {idx < STEPS.length - 1 && (
                <div
                  className={cn(
                    "h-0.5 w-16 sm:w-24 mx-2 transition-colors",
                    idx < currentStep
                      ? "bg-foreground"
                      : "bg-muted-foreground/20"
                  )}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 主内容区 */}
      <div className="w-full max-w-4xl">
        {/* ===== 步骤 1：想法输入 ===== */}
        {(flowState === "idle" || flowState === "analyzing") && (
          <div className="space-y-4 animate-reveal">
            <h1 className="font-heading text-2xl font-bold tracking-tight">
              {L(t.generation.ideationTitle, locale)}
            </h1>
            <Textarea
              value={userIdea}
              onChange={(e) => setUserIdea(e.target.value)}
              placeholder={L(t.generation.inputPlaceholder, locale)}
              rows={6}
              disabled={flowState === "analyzing"}
              className="text-sm"
            />
            <div className="flex justify-end">
              <Button
                onClick={handleAnalyze}
                disabled={!userIdea.trim() || flowState === "analyzing"}
              >
                {flowState === "analyzing" ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {L(t.generation.analyzing, locale)}
                  </>
                ) : (
                  <>
                    <Sparkles size={14} className="mr-1.5" />
                    {L(t.generation.analyzeBtn, locale)}
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* ===== 步骤 2：分析结果 ===== */}
        {flowState === "analyzed" && analyzeResult && (
          <div className="space-y-8">
            <h1 className="font-heading text-2xl font-bold tracking-tight animate-reveal">
              {L(t.generation.analysisResult, locale)}
            </h1>

            <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6">
              {/* 左侧：功能范围 */}
              <ScopeAnalysis scopeDraft={analyzeResult.scope_draft} />

              {/* 右侧：容量仪表盘 */}
              <CapacityDashboard
                report={analyzeResult.capacity_report}
                className="h-fit lg:sticky lg:top-6"
              />
            </div>

            {/* 操作按钮 */}
            <div
              className="flex items-center justify-end gap-3 pt-4 border-t border-border animate-reveal"
              style={{ animationDelay: "0.15s" }}
            >
              <Button variant="outline" onClick={handleReanalyze}>
                {L(t.generation.reanalyze, locale)}
              </Button>

              {analyzeResult.capacity_report.needs_contraction ||
              analyzeResult.capacity_report.must_contract ? (
                <Button onClick={handleContract}>
                  <Sparkles size={14} className="mr-1.5" />
                  {L(t.generation.contractBtn, locale)}
                </Button>
              ) : (
                <Button onClick={handleDirectConfirm}>
                  {L(t.generation.confirmBtn, locale)}
                </Button>
              )}
            </div>
          </div>
        )}

        {/* ===== 步骤 2→3 过渡：收缩中 ===== */}
        {flowState === "contracting" && (
          <div className="flex flex-col items-center justify-center py-20 animate-reveal">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mb-4" />
            <p className="text-sm text-muted-foreground">
              {L(t.generation.contracting, locale)}
            </p>
          </div>
        )}

        {/* ===== 步骤 3：收缩方案 ===== */}
        {flowState === "contracted" && contractResult && (
          <div className="space-y-8">
            <ContractionResult
              decision={contractResult.decision}
              capacityBefore={contractResult.capacity_before}
              capacityAfter={contractResult.capacity_after}
            />

            {/* 进入确认 */}
            <ScopeConfirm
              scopeDraft={contractResult.scope_draft}
              onConfirm={handleConfirm}
              onReanalyze={handleReanalyze}
              isPending={false}
            />
          </div>
        )}

        {/* ===== 步骤 4：确认中 ===== */}
        {flowState === "confirming" && (
          <div className="flex flex-col items-center justify-center py-20 animate-reveal">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mb-4" />
            <p className="text-sm text-muted-foreground">
              {L(t.generation.confirming, locale)}
            </p>
          </div>
        )}

        {/* ===== 步骤 5：完成 ===== */}
        {flowState === "confirmed" && (
          <div className="flex flex-col items-center justify-center py-20 animate-reveal">
            <CheckCircle2 size={48} className="text-emerald-600 mb-4" />
            <h2 className="font-heading text-xl font-bold mb-2">
              {L(t.generation.confirmed, locale)}
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              {L(t.generation.scopeLocked, locale)}
            </p>
            <Button
              variant="outline"
              onClick={() => router.push(`/projects/${projectId}`)}
            >
              <ArrowLeft size={14} className="mr-1.5" />
              {L(t.generation.backToProject, locale)}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
