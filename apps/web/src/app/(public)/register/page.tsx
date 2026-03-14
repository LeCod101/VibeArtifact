/**
 * 注册页面 - Claude 暖色极简风格
 *
 * 暖米色背景，居中白色注册卡片，简洁表单。
 */
"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Loader2, Mail, Lock, User, CheckCircle2 } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import {
  useRegisterMutation,
  useLoginMutation,
  useMeQuery,
} from "@/features/auth/api";
import { ApiError } from "@/lib/api-client/errors";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

export default function RegisterPage() {
  const { locale } = useLocale();
  const router = useRouter();
  const registerMutation = useRegisterMutation();
  const loginMutation = useLoginMutation();
  const { refetch: fetchMe } = useMeQuery();

  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [agreed, setAgreed] = useState(false);

  const isPending = registerMutation.isPending || loginMutation.isPending;

  /** 表单提交处理 */
  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast.error(L(t.auth.passwordMismatch, locale));
      return;
    }

    try {
      await registerMutation.mutateAsync({
        email,
        password,
        display_name: displayName || undefined,
      });
      await loginMutation.mutateAsync({ email, password });
      await fetchMe();
      toast.success(L(t.auth.registerSuccess, locale));
      router.push("/dashboard");
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6">
      {/* 注册卡片 */}
      <div className="w-full max-w-[460px] animate-reveal">
        <div className="bg-card border border-border rounded-2xl p-8 shadow-lg">
          {/* 头部信息 */}
          <div className="flex flex-col items-center mb-8 text-center">
            <svg viewBox="60 30 180 110" className="h-12 w-12 text-foreground mb-4">
              <g fill="currentColor">
                <polygon points="85,40 119,108 109,128 65,40" />
                <polygon points="165,40 185,40 235,140 215,140 175,60 125,160 115,140 165,40" />
                <polygon points="150.5,105 199.5,105 207,120 143,120" />
              </g>
            </svg>
            <h2 className="text-2xl font-bold text-foreground">
              {L({ zh: "创建账号", en: "Create Account" }, locale)}
            </h2>
            <p className="text-sm text-muted-foreground mt-2">
              {L(
                {
                  zh: "开启全栈系统合成之旅",
                  en: "Start your full-stack synthesis journey",
                },
                locale,
              )}
            </p>
          </div>

          {/* 注册表单 */}
          <form className="space-y-4" onSubmit={handleSubmit}>
            {/* 显示名称 */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                {L(t.auth.displayName, locale)}
              </label>
              <div className="relative">
                <User
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                  size={16}
                />
                <input
                  type="text"
                  placeholder={L(t.auth.displayNamePlaceholder, locale)}
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  autoComplete="name"
                  className="w-full h-11 bg-background border border-border rounded-xl pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:ring-1 focus:ring-ring transition-all outline-none"
                />
              </div>
            </div>

            {/* 邮箱 */}
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

            {/* 密码 */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                {L(t.auth.password, locale)}
              </label>
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
                  autoComplete="new-password"
                  className="w-full h-11 bg-background border border-border rounded-xl pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:ring-1 focus:ring-ring transition-all outline-none"
                />
              </div>
            </div>

            {/* 确认密码 */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                {L(t.auth.confirmPassword, locale)}
              </label>
              <div className="relative">
                <Lock
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                  size={16}
                />
                <input
                  type="password"
                  placeholder={L(t.auth.confirmPasswordPlaceholder, locale)}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                  className="w-full h-11 bg-background border border-border rounded-xl pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:ring-1 focus:ring-ring transition-all outline-none"
                />
              </div>
            </div>

            {/* 协议勾选 */}
            <div
              className="flex items-start gap-3 py-2 cursor-pointer group/terms"
              onClick={() => setAgreed(!agreed)}
            >
              <div
                className={`mt-0.5 h-4 w-4 rounded border flex items-center justify-center flex-shrink-0 transition-colors ${
                  agreed
                    ? "border-primary bg-primary/10"
                    : "border-border bg-background group-hover/terms:border-primary/50"
                }`}
              >
                {agreed && (
                  <CheckCircle2 size={10} className="text-primary" />
                )}
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                {L(
                  {
                    zh: "我同意 VibeArtifact 的 ",
                    en: "I agree to VibeArtifact's ",
                  },
                  locale,
                )}
                <span className="text-foreground font-medium">
                  {L(
                    { zh: "服务协议", en: "Terms of Service" },
                    locale,
                  )}
                </span>
                {L({ zh: " 与 ", en: " and " }, locale)}
                <span className="text-foreground font-medium">
                  {L(
                    { zh: "隐私声明", en: "Privacy Policy" },
                    locale,
                  )}
                </span>
              </p>
            </div>

            {/* 提交按钮 */}
            <button
              type="submit"
              disabled={isPending}
              className="w-full h-11 bg-primary text-primary-foreground rounded-xl font-medium text-sm hover:opacity-90 transition-all active:scale-[0.98] mt-2 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                L(t.auth.registerBtn, locale)
              )}
            </button>
          </form>

          {/* 登录链接 */}
          <p className="text-center mt-6 text-sm text-muted-foreground">
            {L(t.auth.hasAccount, locale)}{" "}
            <Link
              href="/login"
              className="text-foreground font-medium hover:underline underline-offset-4"
            >
              {L(t.auth.goLogin, locale)}
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
