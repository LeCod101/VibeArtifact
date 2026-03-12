/**
 * Auth 状态管理 - 使用 Zustand + persist 管理认证状态
 *
 * 持久化到 localStorage，key 为 "va-auth"。
 * 存储 accessToken、refreshToken 和用户信息。
 */
"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserResponse } from "@/lib/api-client/types";

/** 认证状态接口 */
interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserResponse | null;
  /** 保存令牌对 */
  setTokens: (access: string, refresh: string) => void;
  /** 保存用户信息 */
  setUser: (user: UserResponse) => void;
  /** 清除所有认证状态并退出登录 */
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,

      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh }),

      setUser: (user) => set({ user }),

      logout: () =>
        set({ accessToken: null, refreshToken: null, user: null }),
    }),
    {
      name: "va-auth",
    }
  )
);
