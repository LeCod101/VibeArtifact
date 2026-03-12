/**
 * 登录页面
 *
 * 全新工业暗黑风设计：流光渐变边框卡片、SSO 快速登录、indigo/purple 主题色。
 * 登录成功后存 token、获取用户信息、跳转仪表盘。
 */
"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Loader2,
  ArrowLeft,
  Mail,
  Lock,
  Zap,
  Github,
  Globe,
} from "lucide-react";
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
      // 登录成功，获取用户信息
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
    <div className="min-h-screen bg-[#020205] flex items-center justify-center p-6 relative overflow-hidden">
      {/* 背景极光 + 点阵 */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[70%] h-[70%] bg-indigo-600/10 blur-[180px] rounded-full mix-blend-screen animate-pulse-slow" />
        <div
          className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-purple-600/15 blur-[150px] rounded-full mix-blend-screen animate-float"
          style={{ animationDelay: "2s" }}
        />
        <div className="absolute inset-0 bg-[radial-gradient(#ffffff08_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
      </div>

      {/* 返回首页 */}
      <Link
        href="/"
        className="absolute top-10 left-10 z-20 flex items-center gap-2 text-slate-500 hover:text-white transition-colors font-bold uppercase text-[10px] tracking-[0.2em] group"
      >
        <ArrowLeft
          size={14}
          className="group-hover:-translate-x-1 transition-transform"
        />
        {L(t.common.back, locale)}
      </Link>

      {/* 登录卡片 */}
      <div className="w-full max-w-[440px] relative group z-10 animate-reveal">
        {/* 流光渐变边框 */}
        <div className="absolute -inset-[1px] bg-gradient-to-br from-indigo-500/40 via-purple-500/20 to-cyan-500/40 rounded-3xl blur-[2px] group-hover:blur-[4px] transition-all" />

        <div className="relative bg-[#050508]/95 backdrop-blur-3xl border border-white/10 rounded-3xl p-10 shadow-2xl overflow-hidden">
          {/* 头部信息 */}
          <div className="flex flex-col items-center mb-10 text-center">
            <svg viewBox="0 0 300 250" className="h-20 w-auto text-white mb-6">
              <g fill="currentColor">
                <polygon points="85,40 119,108 109,128 65,40" />
                <polygon points="165,40 185,40 235,140 215,140 175,60 125,160 115,140 165,40" />
                <polygon points="150.5,105 199.5,105 207,120 143,120" />
              </g>
              <text
                x="150"
                y="215"
                fontFamily="'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif"
                fontSize="32"
                fontWeight="600"
                letterSpacing="-0.02em"
                textAnchor="middle"
                fill="currentColor"
              >
                VibeArtifact
              </text>
            </svg>
            <h2 className="text-3xl font-black text-white uppercase italic tracking-widest">
              Welcome Back
            </h2>
            <p className="text-slate-500 text-[11px] font-bold uppercase tracking-[0.2em] mt-3">
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
          <form className="space-y-6" onSubmit={handleSubmit}>
            {/* 邮箱输入 */}
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 ml-1">
                {L(t.auth.email, locale)}
              </label>
              <div className="relative">
                <Mail
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-600"
                  size={16}
                />
                <input
                  type="email"
                  placeholder={L(t.auth.emailPlaceholder, locale)}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  className="w-full h-12 bg-white/[0.03] border border-white/10 rounded-xl pl-11 pr-4 text-sm text-white placeholder:text-slate-600 focus:border-indigo-500 focus:bg-white/[0.06] transition-all outline-none"
                />
              </div>
            </div>

            {/* 密码输入 */}
            <div className="space-y-2">
              <div className="flex justify-between items-center px-1">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                  {L(t.auth.password, locale)}
                </label>
                <button
                  type="button"
                  className="text-[9px] font-bold uppercase tracking-[0.1em] text-indigo-400 hover:text-indigo-300"
                >
                  {L(
                    { zh: "忘记密码?", en: "Forgot password?" },
                    locale,
                  )}
                </button>
              </div>
              <div className="relative">
                <Lock
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-600"
                  size={16}
                />
                <input
                  type="password"
                  placeholder={L(t.auth.passwordPlaceholder, locale)}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full h-12 bg-white/[0.03] border border-white/10 rounded-xl pl-11 pr-4 text-sm text-white placeholder:text-slate-600 focus:border-indigo-500 focus:bg-white/[0.06] transition-all outline-none"
                />
              </div>
            </div>

            {/* 提交按钮 */}
            <button
              type="submit"
              disabled={loginMutation.isPending}
              className="w-full h-14 bg-white text-black rounded-xl font-black text-sm uppercase tracking-[0.2em] hover:bg-indigo-50 hover:shadow-[0_0_30px_rgba(255,255,255,0.1)] transition-all active:scale-[0.98] flex items-center justify-center gap-3 group mt-4 disabled:opacity-50"
            >
              {loginMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  {L(
                    { zh: "进入控制台", en: "Enter Console" },
                    locale,
                  )}
                  <Zap size={16} className="fill-current" />
                </>
              )}
            </button>
          </form>

          {/* SSO 单点登录 */}
          <div className="mt-10">
            <div className="relative flex items-center justify-center mb-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/5" />
              </div>
              <span className="relative px-4 bg-[#050508] text-[9px] font-black uppercase tracking-[0.3em] text-slate-600">
                {L(
                  { zh: "开发者快速登录", en: "Quick Developer Login" },
                  locale,
                )}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                className="h-12 border border-white/10 bg-white/[0.02] hover:bg-white/[0.05] rounded-xl flex items-center justify-center gap-3 transition-all group"
              >
                <Github
                  size={18}
                  className="text-slate-400 group-hover:text-white"
                />
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 group-hover:text-white">
                  GitHub
                </span>
              </button>
              <button
                type="button"
                className="h-12 border border-white/10 bg-white/[0.02] hover:bg-white/[0.05] rounded-xl flex items-center justify-center gap-3 transition-all group"
              >
                <Globe
                  size={18}
                  className="text-slate-400 group-hover:text-white"
                />
                <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 group-hover:text-white">
                  Google
                </span>
              </button>
            </div>
          </div>

          {/* 注册链接 */}
          <p className="text-center mt-10 text-[10px] font-bold uppercase tracking-[0.1em] text-slate-600">
            {L(t.auth.noAccount, locale)}
            <Link
              href="/register"
              className="ml-2 text-white hover:text-indigo-400 transition-colors underline decoration-white/20 underline-offset-4"
            >
              {L(t.auth.goRegister, locale)}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
