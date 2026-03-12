/**
 * 注册页面
 *
 * 全新工业暗黑风设计：cyan/indigo 流光渐变边框卡片。
 * 显示名称 + 邮箱 + 密码 + 确认密码表单。
 * 注册成功后自动登录并跳转仪表盘。
 */
"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Loader2,
  ArrowLeft,
  ArrowRight,
  Mail,
  Lock,
  User,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
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

    // 密码一致性校验
    if (password !== confirmPassword) {
      toast.error(L(t.auth.passwordMismatch, locale));
      return;
    }

    try {
      // 注册
      await registerMutation.mutateAsync({
        email,
        password,
        display_name: displayName || undefined,
      });

      // 自动登录
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

      {/* 注册卡片 */}
      <div className="w-full max-w-[480px] relative group z-10 animate-reveal">
        {/* 流光渐变边框 - 偏 cyan */}
        <div className="absolute -inset-[1px] bg-gradient-to-br from-cyan-500/40 via-blue-500/20 to-purple-500/40 rounded-3xl blur-[2px] group-hover:blur-[4px] transition-all" />

        <div className="relative bg-[#050508]/95 backdrop-blur-3xl border border-white/10 rounded-3xl p-10 shadow-2xl overflow-hidden">
          {/* 头部信息 */}
          <div className="flex flex-col items-center mb-10 text-center">
            <div className="w-14 h-14 bg-gradient-to-br from-cyan-500 to-indigo-600 rounded-xl flex items-center justify-center mb-6 shadow-xl shadow-cyan-500/20 -rotate-3">
              <Sparkles className="text-white w-8 h-8" />
            </div>
            <h2 className="text-3xl font-black text-white uppercase italic tracking-widest">
              Initial Account
            </h2>
            <p className="text-slate-500 text-[11px] font-bold uppercase tracking-[0.2em] mt-3 leading-relaxed">
              {L(
                {
                  zh: "加入顶尖工程团队\n开启全栈系统合成新纪元",
                  en: "Join top engineering teams\nStart a new era of full-stack synthesis",
                },
                locale,
              )}
            </p>
          </div>

          {/* 注册表单 */}
          <form className="space-y-5" onSubmit={handleSubmit}>
            {/* 显示名称 */}
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 ml-1">
                {L(t.auth.displayName, locale)}
              </label>
              <div className="relative">
                <User
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-600"
                  size={16}
                />
                <input
                  type="text"
                  placeholder={L(t.auth.displayNamePlaceholder, locale)}
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  autoComplete="name"
                  className="w-full h-12 bg-white/[0.03] border border-white/10 rounded-xl pl-11 pr-4 text-sm text-white placeholder:text-slate-600 focus:border-cyan-500 focus:bg-white/[0.06] transition-all outline-none"
                />
              </div>
            </div>

            {/* 邮箱 */}
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
                  className="w-full h-12 bg-white/[0.03] border border-white/10 rounded-xl pl-11 pr-4 text-sm text-white placeholder:text-slate-600 focus:border-cyan-500 focus:bg-white/[0.06] transition-all outline-none"
                />
              </div>
            </div>

            {/* 密码 */}
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 ml-1">
                {L(t.auth.password, locale)}
              </label>
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
                  autoComplete="new-password"
                  className="w-full h-12 bg-white/[0.03] border border-white/10 rounded-xl pl-11 pr-4 text-sm text-white placeholder:text-slate-600 focus:border-cyan-500 focus:bg-white/[0.06] transition-all outline-none"
                />
              </div>
            </div>

            {/* 确认密码 */}
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 ml-1">
                {L(t.auth.confirmPassword, locale)}
              </label>
              <div className="relative">
                <Lock
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-600"
                  size={16}
                />
                <input
                  type="password"
                  placeholder={L(t.auth.confirmPasswordPlaceholder, locale)}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                  className="w-full h-12 bg-white/[0.03] border border-white/10 rounded-xl pl-11 pr-4 text-sm text-white placeholder:text-slate-600 focus:border-cyan-500 focus:bg-white/[0.06] transition-all outline-none"
                />
              </div>
            </div>

            {/* 协议勾选 */}
            <div
              className="flex items-start gap-3 px-1 py-2 cursor-pointer group/terms"
              onClick={() => setAgreed(!agreed)}
            >
              <div
                className={`mt-1 h-4 w-4 rounded border flex items-center justify-center flex-shrink-0 transition-colors ${
                  agreed
                    ? "border-cyan-500 bg-cyan-500/20"
                    : "border-white/10 bg-white/5 group-hover/terms:border-cyan-500/50"
                }`}
              >
                {agreed && (
                  <CheckCircle2 size={10} className="text-cyan-500" />
                )}
              </div>
              <p className="text-[9px] text-slate-500 leading-normal font-bold uppercase tracking-wider">
                {L(
                  {
                    zh: "我同意 VibeArtifact 的 ",
                    en: "I agree to VibeArtifact's ",
                  },
                  locale,
                )}
                <span className="text-white">
                  {L(
                    { zh: "服务协议", en: "Terms of Service" },
                    locale,
                  )}
                </span>
                {L({ zh: " 与 ", en: " and " }, locale)}
                <span className="text-white">
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
              className="w-full h-14 bg-indigo-600 text-white rounded-xl font-black text-sm uppercase tracking-[0.2em] hover:bg-indigo-500 hover:shadow-[0_0_40px_rgba(99,102,241,0.4)] transition-all active:scale-[0.98] mt-2 flex items-center justify-center gap-3 group disabled:opacity-50"
            >
              {isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  {L(
                    { zh: "创建开发者账号", en: "Create Developer Account" },
                    locale,
                  )}
                  <ArrowRight
                    size={16}
                    className="group-hover:translate-x-1 transition-transform"
                  />
                </>
              )}
            </button>
          </form>

          {/* 登录链接 */}
          <div className="mt-8 pt-8 border-t border-white/5 text-center">
            <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-600">
              {L(t.auth.hasAccount, locale)}
              <Link
                href="/login"
                className="ml-2 text-white hover:text-cyan-400 transition-colors underline decoration-white/20 underline-offset-4"
              >
                {L(t.auth.goLogin, locale)}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
