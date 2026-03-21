/**
 * Settings 状态管理 - 使用 Zustand 管理设置页面状态
 *
 * 管理 API 密钥、模型偏好、用量统计等设置数据。
 */
"use client";

import { create } from "zustand";
import { apiGet, apiPost, apiPut, apiDelete } from "@/lib/api-client";
import type {
  ApiKeyResponse,
  ApiKeyCreateRequest,
  ApiKeyValidateResponse,
  ModelPreferenceResponse,
  ModelPreferenceRequest,
  UsageSummaryResponse,
  AvailableModel,
} from "@/lib/api-client/types";

/** 设置状态接口 */
interface SettingsState {
  /** API 密钥列表 */
  apiKeys: ApiKeyResponse[];
  /** 模型偏好 */
  modelPreference: ModelPreferenceResponse | null;
  /** 用量汇总 */
  usageSummary: UsageSummaryResponse | null;
  /** 可用模型列表 */
  availableModels: AvailableModel[];
  /** 加载状态 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;

  /** 加载 API 密钥列表 */
  fetchApiKeys: () => Promise<void>;
  /** 添加/更新 API 密钥 */
  upsertApiKey: (req: ApiKeyCreateRequest) => Promise<void>;
  /** 删除 API 密钥 */
  removeApiKey: (keyId: string) => Promise<void>;
  /** 验证 API 密钥 */
  validateApiKey: (keyId: string) => Promise<ApiKeyValidateResponse>;
  /** 加载模型偏好 */
  fetchModelPreference: () => Promise<void>;
  /** 更新模型偏好 */
  updateModelPreference: (req: ModelPreferenceRequest) => Promise<void>;
  /** 加载用量汇总 */
  fetchUsageSummary: () => Promise<void>;
  /** 加载可用模型 */
  fetchAvailableModels: () => Promise<void>;
}

export const useSettingsStore = create<SettingsState>()((set) => ({
  apiKeys: [],
  modelPreference: null,
  usageSummary: null,
  availableModels: [],
  loading: false,
  error: null,

  fetchApiKeys: async () => {
    set({ loading: true, error: null });
    try {
      const keys = await apiGet<ApiKeyResponse[]>("/api/v1/settings/api-keys");
      set({ apiKeys: keys, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  upsertApiKey: async (req) => {
    set({ loading: true, error: null });
    try {
      await apiPost<ApiKeyResponse>("/api/v1/settings/api-keys", req);
      const keys = await apiGet<ApiKeyResponse[]>("/api/v1/settings/api-keys");
      set({ apiKeys: keys, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
      throw e;
    }
  },

  removeApiKey: async (keyId) => {
    set({ loading: true, error: null });
    try {
      await apiDelete(`/api/v1/settings/api-keys/${keyId}`);
      const keys = await apiGet<ApiKeyResponse[]>("/api/v1/settings/api-keys");
      set({ apiKeys: keys, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
      throw e;
    }
  },

  validateApiKey: async (keyId) => {
    const result = await apiPost<ApiKeyValidateResponse>(
      `/api/v1/settings/api-keys/${keyId}/validate`
    );
    const keys = await apiGet<ApiKeyResponse[]>("/api/v1/settings/api-keys");
    set({ apiKeys: keys });
    return result;
  },

  fetchModelPreference: async () => {
    try {
      const pref = await apiGet<ModelPreferenceResponse>(
        "/api/v1/settings/model-preference"
      );
      set({ modelPreference: pref });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  updateModelPreference: async (req) => {
    set({ loading: true, error: null });
    try {
      const pref = await apiPut<ModelPreferenceResponse>(
        "/api/v1/settings/model-preference",
        req
      );
      set({ modelPreference: pref, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
      throw e;
    }
  },

  fetchUsageSummary: async () => {
    try {
      const usage = await apiGet<UsageSummaryResponse>(
        "/api/v1/settings/usage"
      );
      set({ usageSummary: usage });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  fetchAvailableModels: async () => {
    try {
      const models = await apiGet<AvailableModel[]>(
        "/api/v1/settings/available-models"
      );
      set({ availableModels: models });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },
}));
