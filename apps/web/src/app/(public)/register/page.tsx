/**
 * 注册页面
 *
 * 邮箱 + 显示名称 + 密码 + 确认密码表单。
 * 注册成功后自动登录并跳转仪表盘。
 */
"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useRegisterMutation, useLoginMutation, useMeQuery } from "@/features/auth/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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

  const isPending = registerMutation.isPending || loginMutation.isPending;

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        {/* Logo */}
        <svg viewBox="0 0 300 250" className="h-16 w-auto mx-auto text-foreground mb-2">
          <g fill="currentColor">
            <polygon points="85,40 119,108 109,128 65,40" />
            <polygon points="165,40 185,40 235,140 215,140 175,60 125,160 115,140 165,40" />
            <polygon points="150.5,105 199.5,105 207,120 143,120" />
          </g>
          <text
            x="150" y="215"
            fontFamily="'Inter', sans-serif"
            fontSize="32" fontWeight="600"
            letterSpacing="-0.02em"
            textAnchor="middle"
            fill="currentColor"
          >
            VibeArtifact
          </text>
        </svg>
        <CardTitle className="text-2xl">{L(t.auth.registerTitle, locale)}</CardTitle>
        <CardDescription>
          {L(t.auth.hasAccount, locale)}{" "}
          <Link href="/login" className="text-primary underline underline-offset-4">
            {L(t.auth.goLogin, locale)}
          </Link>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">{L(t.auth.email, locale)}</Label>
            <Input
              id="email"
              type="email"
              placeholder={L(t.auth.emailPlaceholder, locale)}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="displayName">{L(t.auth.displayName, locale)}</Label>
            <Input
              id="displayName"
              type="text"
              placeholder={L(t.auth.displayNamePlaceholder, locale)}
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              autoComplete="name"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">{L(t.auth.password, locale)}</Label>
            <Input
              id="password"
              type="password"
              placeholder={L(t.auth.passwordPlaceholder, locale)}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">{L(t.auth.confirmPassword, locale)}</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder={L(t.auth.confirmPasswordPlaceholder, locale)}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
          </div>
          <Button
            type="submit"
            className="w-full"
            disabled={isPending}
          >
            {isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {L(t.auth.registerBtn, locale)}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
