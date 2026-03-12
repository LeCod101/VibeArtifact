/**
 * Auth API Hooks - 认证相关的 React Query hooks
 *
 * 提供登录、注册、获取当前用户信息的 mutation 和 query。
 */
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiPost, apiGet } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserResponse,
} from "@/lib/api-client/types";

/**
 * 登录 mutation
 *
 * 调用 POST /api/v1/auth/login，成功后存储 token。
 */
export function useLoginMutation() {
  const { setTokens } = useAuthStore();

  return useMutation({
    mutationFn: (data: LoginRequest) =>
      apiPost<TokenResponse>("/api/v1/auth/login", data),
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token);
    },
  });
}

/**
 * 注册 mutation
 *
 * 调用 POST /api/v1/auth/register，返回 UserResponse。
 * 注册成功后需要接着调用登录接口获取 token。
 */
export function useRegisterMutation() {
  return useMutation({
    mutationFn: (data: RegisterRequest) =>
      apiPost<UserResponse>("/api/v1/auth/register", data),
  });
}

/**
 * 获取当前用户信息 query
 *
 * 调用 GET /api/v1/users/me，仅在有 token 时启用。
 */
export function useMeQuery() {
  const { accessToken, setUser } = useAuthStore();

  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const data = await apiGet<UserResponse>("/api/v1/users/me");
      setUser(data);
      return data;
    },
    enabled: !!accessToken,
  });
}
