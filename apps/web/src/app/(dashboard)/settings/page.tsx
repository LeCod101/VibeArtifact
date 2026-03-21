/**
 * 设置页 - 用户个人设置
 *
 * 包含个人信息、外观、安全、API 密钥管理、模型偏好、用量统计和额度购买。
 */
"use client";

import { useEffect, useState, useCallback } from "react";
import {
  User,
  Globe,
  Shield,
  Key,
  Brain,
  BarChart3,
  CreditCard,
  Plus,
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useAuthStore } from "@/stores/auth-store";
import { useSettingsStore } from "@/stores/settings-store";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** Provider 选项 */
const PROVIDERS = [
  { value: "anthropic", label: "Anthropic" },
  { value: "openai", label: "OpenAI" },
  { value: "google", label: "Google" },
  { value: "azure", label: "Azure" },
];

export default function SettingsPage() {
  const { locale, toggleLocale } = useLocale();
  const { user } = useAuthStore();
  const {
    apiKeys,
    modelPreference,
    usageSummary,
    availableModels,
    loading,
    fetchApiKeys,
    upsertApiKey,
    removeApiKey,
    validateApiKey,
    fetchModelPreference,
    updateModelPreference,
    fetchUsageSummary,
    fetchAvailableModels,
  } = useSettingsStore();

  /* ── 添加密钥对话框状态 ── */
  const [showAddKey, setShowAddKey] = useState(false);
  const [newProvider, setNewProvider] = useState("anthropic");
  const [newApiKey, setNewApiKey] = useState("");
  const [newLabel, setNewLabel] = useState("");
  const [validatingId, setValidatingId] = useState<string | null>(null);

  /* ── 加载数据 ── */
  useEffect(() => {
    fetchApiKeys();
    fetchModelPreference();
    fetchUsageSummary();
    fetchAvailableModels();
  }, [fetchApiKeys, fetchModelPreference, fetchUsageSummary, fetchAvailableModels]);

  /* ── 添加密钥 ── */
  const handleAddKey = useCallback(async () => {
    if (!newApiKey.trim()) return;
    try {
      await upsertApiKey({
        provider: newProvider,
        api_key: newApiKey,
        display_label: newLabel || undefined,
      });
      toast.success(L(t.settings.addSuccess, locale));
      setShowAddKey(false);
      setNewApiKey("");
      setNewLabel("");
    } catch {
      toast.error(L(t.common.error, locale));
    }
  }, [newProvider, newApiKey, newLabel, upsertApiKey, locale]);

  /* ── 删除密钥 ── */
  const handleDeleteKey = useCallback(
    async (keyId: string) => {
      if (!confirm(L(t.settings.deleteConfirm, locale))) return;
      try {
        await removeApiKey(keyId);
        toast.success(L(t.settings.deleteSuccess, locale));
      } catch {
        toast.error(L(t.common.error, locale));
      }
    },
    [removeApiKey, locale]
  );

  /* ── 验证密钥 ── */
  const handleValidate = useCallback(
    async (keyId: string) => {
      setValidatingId(keyId);
      try {
        const result = await validateApiKey(keyId);
        if (result.is_valid) {
          toast.success(result.message);
        } else {
          toast.error(result.message);
        }
      } catch {
        toast.error(L(t.common.error, locale));
      } finally {
        setValidatingId(null);
      }
    },
    [validateApiKey, locale]
  );

  /* ── 更新模型偏好 ── */
  const handleModelChange = useCallback(
    async (field: "reasoning_model" | "generation_model", value: string) => {
      try {
        await updateModelPreference({ [field]: value || null });
        toast.success(L(t.settings.saveSuccess, locale));
      } catch {
        toast.error(L(t.common.error, locale));
      }
    },
    [updateModelPreference, locale]
  );

  /** 获取验证状态图标 */
  const getValidationIcon = (isValid: boolean | null) => {
    if (isValid === true) return <CheckCircle size={16} className="text-green-500" />;
    if (isValid === false) return <XCircle size={16} className="text-red-500" />;
    return <AlertCircle size={16} className="text-muted-foreground" />;
  };

  /** 获取验证状态文本 */
  const getValidationText = (isValid: boolean | null) => {
    if (isValid === true) return L(t.settings.valid, locale);
    if (isValid === false) return L(t.settings.invalid, locale);
    return L(t.settings.notValidated, locale);
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* 页面标题 */}
      <div className="mb-8 animate-reveal">
        <h1 className="font-heading text-2xl font-bold tracking-tight">
          {L(t.settings.title, locale)}
        </h1>
      </div>

      <div className="space-y-6">
        {/* ══════ 个人信息 ══════ */}
        <Card className="animate-reveal" style={{ animationDelay: "0.05s" }}>
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <User size={20} className="text-foreground/70" />
              <h2 className="text-base font-bold">{L(t.settings.profile, locale)}</h2>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{L(t.settings.username, locale)}</Label>
                <Input value={user?.display_name || ""} disabled className="bg-muted" />
              </div>
              <div className="space-y-2">
                <Label>{L(t.settings.email, locale)}</Label>
                <Input value={user?.email || ""} disabled className="bg-muted" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ══════ API 密钥管理 ══════ */}
        <Card className="animate-reveal" style={{ animationDelay: "0.1s" }}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Key size={20} className="text-foreground/70" />
                <div>
                  <h2 className="text-base font-bold">{L(t.settings.apiKeys, locale)}</h2>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {L(t.settings.apiKeysDesc, locale)}
                  </p>
                </div>
              </div>
              <Button size="sm" variant="outline" onClick={() => setShowAddKey(!showAddKey)}>
                <Plus size={16} className="mr-1" />
                {L(t.settings.addKey, locale)}
              </Button>
            </div>

            {/* 添加密钥表单 */}
            {showAddKey && (
              <div className="border rounded-lg p-4 mb-4 space-y-3 bg-muted/30">
                <div className="space-y-2">
                  <Label>{L(t.settings.provider, locale)}</Label>
                  <select
                    value={newProvider}
                    onChange={(e) => setNewProvider(e.target.value)}
                    className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm"
                  >
                    {PROVIDERS.map((p) => (
                      <option key={p.value} value={p.value}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>{L(t.settings.apiKey, locale)}</Label>
                  <Input
                    type="password"
                    value={newApiKey}
                    onChange={(e) => setNewApiKey(e.target.value)}
                    placeholder={L(t.settings.apiKeyPlaceholder, locale)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>{L(t.settings.label, locale)}</Label>
                  <Input
                    value={newLabel}
                    onChange={(e) => setNewLabel(e.target.value)}
                    placeholder={L(t.settings.labelPlaceholder, locale)}
                  />
                </div>
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleAddKey} disabled={loading || !newApiKey.trim()}>
                    {L(t.settings.save, locale)}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowAddKey(false)}>
                    {L(t.common.cancel, locale)}
                  </Button>
                </div>
              </div>
            )}

            {/* 密钥列表 */}
            {apiKeys.length === 0 ? (
              <p className="text-sm text-muted-foreground">{L(t.settings.noKeys, locale)}</p>
            ) : (
              <div className="space-y-3">
                {apiKeys.map((key) => (
                  <div
                    key={key.id}
                    className="flex items-center justify-between border rounded-lg p-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      {getValidationIcon(key.is_valid)}
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm capitalize">{key.provider}</span>
                          {key.display_label && (
                            <Badge variant="secondary" className="text-[10px]">
                              {key.display_label}
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground font-mono truncate">
                          {key.masked_key}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0 ml-2">
                      <span className="text-xs text-muted-foreground mr-1">
                        {getValidationText(key.is_valid)}
                      </span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleValidate(key.id)}
                        disabled={validatingId === key.id}
                      >
                        {validatingId === key.id ? (
                          <Loader2 size={14} className="animate-spin" />
                        ) : (
                          L(t.settings.validate, locale)
                        )}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-destructive"
                        onClick={() => handleDeleteKey(key.id)}
                      >
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* ══════ 模型偏好 ══════ */}
        <Card className="animate-reveal" style={{ animationDelay: "0.15s" }}>
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <Brain size={20} className="text-foreground/70" />
              <div>
                <h2 className="text-base font-bold">{L(t.settings.modelPreference, locale)}</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {L(t.settings.modelPreferenceDesc, locale)}
                </p>
              </div>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>{L(t.settings.reasoningModel, locale)}</Label>
                <select
                  value={modelPreference?.reasoning_model || ""}
                  onChange={(e) => handleModelChange("reasoning_model", e.target.value)}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">{L(t.settings.selectModel, locale)}</option>
                  {availableModels
                    .filter((m) => m.tier === "reasoning" || m.tier === "both")
                    .map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} ({m.provider})
                      </option>
                    ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label>{L(t.settings.generationModel, locale)}</Label>
                <select
                  value={modelPreference?.generation_model || ""}
                  onChange={(e) => handleModelChange("generation_model", e.target.value)}
                  className="w-full h-9 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">{L(t.settings.selectModel, locale)}</option>
                  {availableModels
                    .filter((m) => m.tier === "generation" || m.tier === "both")
                    .map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} ({m.provider})
                      </option>
                    ))}
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ══════ 用量统计 ══════ */}
        <Card className="animate-reveal" style={{ animationDelay: "0.2s" }}>
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <BarChart3 size={20} className="text-foreground/70" />
              <div>
                <h2 className="text-base font-bold">{L(t.settings.usage, locale)}</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {L(t.settings.usageDesc, locale)}
                </p>
              </div>
            </div>

            {usageSummary && usageSummary.call_count > 0 ? (
              <>
                {/* 汇总数据 */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-3 border rounded-lg">
                    <p className="text-2xl font-bold">
                      {(usageSummary.total_prompt_tokens + usageSummary.total_completion_tokens).toLocaleString()}
                    </p>
                    <p className="text-xs text-muted-foreground">{L(t.settings.totalTokens, locale)}</p>
                  </div>
                  <div className="text-center p-3 border rounded-lg">
                    <p className="text-2xl font-bold">${usageSummary.total_cost.toFixed(4)}</p>
                    <p className="text-xs text-muted-foreground">{L(t.settings.totalCost, locale)}</p>
                  </div>
                  <div className="text-center p-3 border rounded-lg">
                    <p className="text-2xl font-bold">{usageSummary.call_count}</p>
                    <p className="text-xs text-muted-foreground">{L(t.settings.callCount, locale)}</p>
                  </div>
                </div>

                {/* 按 Provider 分组 */}
                {usageSummary.by_provider.length > 0 && (
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-muted/50">
                        <tr>
                          <th className="text-left p-2 font-medium">{L(t.settings.provider, locale)}</th>
                          <th className="text-right p-2 font-medium">{L(t.settings.promptTokens, locale)}</th>
                          <th className="text-right p-2 font-medium">{L(t.settings.completionTokens, locale)}</th>
                          <th className="text-right p-2 font-medium">{L(t.settings.totalCost, locale)}</th>
                          <th className="text-right p-2 font-medium">{L(t.settings.callCount, locale)}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {usageSummary.by_provider.map((row) => (
                          <tr key={row.provider} className="border-t">
                            <td className="p-2 capitalize">{row.provider}</td>
                            <td className="p-2 text-right">{row.total_prompt_tokens.toLocaleString()}</td>
                            <td className="p-2 text-right">{row.total_completion_tokens.toLocaleString()}</td>
                            <td className="p-2 text-right">${row.total_cost.toFixed(4)}</td>
                            <td className="p-2 text-right">{row.call_count}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            ) : (
              <p className="text-sm text-muted-foreground">{L(t.settings.noUsage, locale)}</p>
            )}
          </CardContent>
        </Card>

        {/* ══════ 外观设置 ══════ */}
        <Card className="animate-reveal" style={{ animationDelay: "0.25s" }}>
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <Globe size={20} className="text-foreground/70" />
              <h2 className="text-base font-bold">{L(t.settings.appearance, locale)}</h2>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">{L(t.settings.language, locale)}</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {locale === "zh" ? "当前：简体中文" : "Current: English"}
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={toggleLocale}>
                {locale === "zh" ? "English" : "中文"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* ══════ 额度购买（占位） ══════ */}
        <Card className="animate-reveal" style={{ animationDelay: "0.3s" }}>
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <CreditCard size={20} className="text-foreground/70" />
              <div>
                <h2 className="text-base font-bold">{L(t.settings.credits, locale)}</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {L(t.settings.creditsDesc, locale)}
                </p>
              </div>
              <Badge variant="secondary" className="text-[10px]">
                {L(t.settings.comingSoon, locale)}
              </Badge>
            </div>
            <Button disabled>
              {L(t.settings.buyCredits, locale)}
            </Button>
          </CardContent>
        </Card>

        {/* ══════ 安全区 ══════ */}
        <Card className="animate-reveal" style={{ animationDelay: "0.35s" }}>
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <Shield size={20} className="text-foreground/70" />
              <h2 className="text-base font-bold">{L(t.settings.security, locale)}</h2>
              <Badge variant="secondary" className="text-[10px]">
                {L(t.settings.comingSoon, locale)}
              </Badge>
            </div>
            <div className="space-y-4 opacity-50 pointer-events-none">
              <div className="space-y-2">
                <Label>{L(t.settings.currentPassword, locale)}</Label>
                <Input type="password" disabled />
              </div>
              <div className="space-y-2">
                <Label>{L(t.settings.newPassword, locale)}</Label>
                <Input type="password" disabled />
              </div>
              <div className="space-y-2">
                <Label>{L(t.settings.confirmPassword, locale)}</Label>
                <Input type="password" disabled />
              </div>
              <Button disabled>{L(t.settings.save, locale)}</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
