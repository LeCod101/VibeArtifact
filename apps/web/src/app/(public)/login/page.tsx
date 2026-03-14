/**
 * 登录页面 - Claude 暖色极简风格
 *
 * 暖米色背景，居中白色登录卡片，简洁表单。
 */
"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Loader2, Mail, Lock, Github, Globe } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useLoginMutation, useMeQuery } from "@/features/auth/api";
import { ApiError } from "@/lib/api-client/errors";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

export default function LoginPage() {
  const { locale } = useLocale();
  const router = useRouter();
  const loginMutation = useLoginMutation();
  const { refetch: fetchMe } = useMeQuery();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  /** 表单提交处理 */
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    try {
      await loginMutation.mutateAsync({ email, password });
      await fetchMe();
      toast.success(L(t.auth.loginSuccess, locale));
      router.push("/dashboard");
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      {/* 登录卡片 */}
      <div className="w-full max-w-[420px] animate-reveal">
        <div className="bg-card border border-border rounded-2xl p-8 shadow-lg">
          {/* 头部信息 */}
          <div className="flex flex-col items-center mb-8 text-center">
            {/* Logo 图标 */}
            <svg viewBox="60 30 180 110" className="h-12 w-12 text-foreground mb-4">
              <g fill="currentColor">
                <polygon points="85,40 119,108 109,128 65,40" />
                <polygon points="165,40 185,40 235,140 215,140 175,60 125,160 115,140 165,40" />
                <polygon points="150.5,105 199.5,105 207,120 143,120" />
              </g>
            </svg>
            <h2 className="text-2xl font-bold text-foreground">
              {L({ zh: "欢迎回来", en: "Welcome Back" }, locale)}
            </h2>
            <p className="text-sm text-muted-foreground mt-2">
              {L(
                {
                  zh: "继续您的工程自动化之旅",
                  en: "Continue your engineering automation journey",
                },
                locale,
              )}
            </p>
          </div>

          {/* 登录表单 */}
          <form className="space-y-5" onSubmit={handleSubmit}>
            {/* 邮箱输入 */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                {L(t.auth.email, locale)}
              </label>
              <div className="relative">
                <Mail
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                  size={16}
                />
                <input
                  type="email"
                  placeholder={L(t.auth.emailPlaceholder, locale)}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="w-full h-11 bg-background border border-border rounded-xl pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:ring-1 focus:ring-ring transition-all outline-none"
                />
              </div>
            </div>

            {/* 密码输入 */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-sm font-medium text-foreground">
                  {L(t.auth.password, locale)}
                </label>
                <button
                  type="button"
                  className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                >
                  {L({ zh: "忘记密码?", en: "Forgot password?" }, locale)}
                </button>
              </div>
              <div className="relative">
                <Lock
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                  size={16}
                />
                <input
                  type="password"
                  placeholder={L(t.auth.passwordPlaceholder, locale)}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full h-11 bg-background border border-border rounded-xl pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:ring-1 focus:ring-ring transition-all outline-none"
                />
              </div>
            </div>

            {/* 提交按钮 */}
            <button
              type="submit"
              disabled={loginMutation.isPending}
              className="w-full h-11 bg-primary text-primary-foreground rounded-xl font-medium text-sm hover:opacity-90 transition-all active:scale-[0.98] flex items-center justify-center gap-2 mt-2 disabled:opacity-50"
            >
              {loginMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                L(t.auth.loginBtn, locale)
              )}
            </button>
          </form>

          {/* SSO 分隔线 */}
          <div className="mt-8">
            <div className="relative flex items-center justify-center mb-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border" />
              </div>
              <span className="relative px-3 bg-card text-xs text-muted-foreground">
                {L(
                  { zh: "或通过以下方式登录", en: "Or continue with" },
                  locale,
                )}
              </span>
            </div>

            {/* SSO 按钮 */}
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                className="h-10 border border-border bg-background hover:bg-accent rounded-xl flex items-center justify-center gap-2 transition-colors"
              >
                <Github size={16} className="text-foreground" />
                <span className="text-sm font-medium text-foreground">GitHub</span>
              </button>
              <button
                type="button"
                className="h-10 border border-border bg-background hover:bg-accent rounded-xl flex items-center justify-center gap-2 transition-colors"
              >
                <Globe size={16} className="text-foreground" />
                <span className="text-sm font-medium text-foreground">Google</span>
              </button>
            </div>
          </div>

          {/* 注册链接 */}
          <p className="text-center mt-8 text-sm text-muted-foreground">
            {L(t.auth.noAccount, locale)}{" "}
            <Link
              href="/register"
              className="text-foreground font-medium hover:underline underline-offset-4"
            >
              {L(t.auth.goRegister, locale)}
            </Link>
          </p>
        </div>

        {/* 返回首页 */}
        <p className="text-center mt-4">
          <Link
            href="/"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            {L(t.common.back, locale)}
          </Link>
        </p>
      </div>
    </div>
  );
}
