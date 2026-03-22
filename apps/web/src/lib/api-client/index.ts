/**
 * API 客户端 - 带认证的 HTTP 请求封装
 *
 * 功能：
 * - 自动附加 Authorization: Bearer <token> 头
 * - 401 时自动尝试 refresh token
 * - refresh 失败则清除登录态跳转 /login
 * - 导出类型安全的 apiGet / apiPost 方法
 */
import { ApiError } from "./errors";
import { useAuthStore } from "@/stores/auth-store";
import type { RefreshRequest, TokenResponse } from "./types";

/** API 基础地址 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** 标记是否正在刷新 token，防止并发刷新 */
let isRefreshing = false;
/** 等待 token 刷新完成的回调队列 */
let refreshQueue: Array<(token: string) => void> = [];

/**
 * 基础请求方法 - 自动附加认证头
 *
 * @param path - API 路径（如 /api/v1/projects）
 * @param init - fetch 配置
 * @returns 解析后的 JSON 数据
 */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const { accessToken } = useAuthStore.getState();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  // 401 未授权 → 尝试刷新 token
  if (res.status === 401 && accessToken) {
    const newToken = await tryRefreshToken();
    if (newToken) {
      headers["Authorization"] = `Bearer ${newToken}`;
      const retryRes = await fetch(`${API_BASE}${path}`, {
        ...init,
        headers,
      });
      if (!retryRes.ok) {
        const detail = await parseErrorDetail(retryRes);
        throw new ApiError(retryRes.status, detail);
      }
      return retryRes.json() as Promise<T>;
    }
    // refresh 也失败了，跳转登录
    handleAuthFailure();
    throw new ApiError(401, "认证已过期，请重新登录");
  }

  if (!res.ok) {
    const detail = await parseErrorDetail(res);
    throw new ApiError(res.status, detail);
  }

  // 204 No Content
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

/**
 * 从错误响应中提取 detail 信息
 */
async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    const raw = body.detail || body.message;
    if (!raw) return `HTTP ${res.status}`;
    if (typeof raw === "string") return raw;
    // FastAPI 422 返回 detail 为验证错误数组，提取 msg 字段拼接
    if (Array.isArray(raw)) {
      return raw.map((e: { msg?: string }) => e.msg ?? JSON.stringify(e)).join("; ");
    }
    return JSON.stringify(raw);
  } catch {
    return `HTTP ${res.status} ${res.statusText}`;
  }
}

/**
 * 尝试用 refresh_token 获取新的 access_token
 *
 * 使用队列机制防止并发刷新。
 * @returns 新的 access_token，失败返回 null
 */
async function tryRefreshToken(): Promise<string | null> {
  const { refreshToken } = useAuthStore.getState();
  if (!refreshToken) return null;

  // 已有刷新请求进行中，加入等待队列
  if (isRefreshing) {
    return new Promise<string>((resolve) => {
      refreshQueue.push(resolve);
    });
  }

  isRefreshing = true;

  try {
    const body: RefreshRequest = { refresh_token: refreshToken };
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) return null;

    const data: TokenResponse = await res.json();
    useAuthStore.getState().setTokens(data.access_token, data.refresh_token);

    // 通知等待队列中的请求
    refreshQueue.forEach((cb) => cb(data.access_token));
    refreshQueue = [];

    return data.access_token;
  } catch {
    return null;
  } finally {
    isRefreshing = false;
  }
}

/**
 * 认证失败时清除登录态并跳转到登录页
 */
function handleAuthFailure() {
  useAuthStore.getState().logout();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

/* ============ 导出的便捷方法 ============ */

/**
 * GET 请求
 * @param path - API 路径
 */
export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

/**
 * POST 请求
 * @param path - API 路径
 * @param body - 请求体数据
 */
export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * PUT 请求
 * @param path - API 路径
 * @param body - 请求体数据
 */
export function apiPut<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * DELETE 请求
 * @param path - API 路径
 */
export function apiDelete<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" });
}
